"""
rag.py — Retrieval-Augmented Generation (RAG) for the SME agent
=====================================================
Retrieves passages from the reference textbook and injects them into the
SME prompt as the primary source.

Matches the paper settings:
    - Chunking: 1000 chars with 200 overlap  (RAG_CHUNK_SIZE / RAG_CHUNK_OVERLAP)
    - Embedding: sentence-transformers/all-MiniLM-L6-v2  (RAG_EMBED_MODEL)
    - Index: FAISS (IndexFlatIP over normalized vectors = cosine similarity)
             with an automatic NumPy fallback if faiss fails to import (e.g. on Apple Silicon).
    - Retrieval: top-k = 6  (RAG_TOP_K)

Notes:
    - sentence-transformers runs on CPU/MPS; lightweight (22M-parameter model).
    - The index is built once and saved under rag_index/<topic>/, then loaded later.

Usage:
    from pipeline.rag import get_retriever
    r = get_retriever()                  # builds/loads the active topic's index
    ctx = r.retrieve("Backpropagation chain rule gradient", k=6)
"""
from __future__ import annotations
import json
import re
import threading
from pathlib import Path
from typing import Optional

import numpy as np

from config import (
    ACTIVE_TOPIC, LECTURE_TEXTBOOK_PATH, LECTURE_TOPIC,
    RAG_EMBED_MODEL, RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP, RAG_TOP_K, RAG_INDEX_DIR,
)

_lock = threading.Lock()
_RETRIEVERS: dict[str, "TextbookRetriever"] = {}


# ──────────────────────────────────────────────────────────────────
#  Textbook text extraction (PDF or TXT)
# ──────────────────────────────────────────────────────────────────
def _read_textbook(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(
            f"Textbook file not found: {path}\n"
            f"  Place the file for topic '{ACTIVE_TOPIC}' at the path above, or update "
            f"textbook_path in config.TOPICS."
        )
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        try:
            import fitz  # PyMuPDF
        except ImportError:
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(path))
                return "\n".join((pg.extract_text() or "") for pg in reader.pages)
            except ImportError as e:
                raise ImportError(
                    "To read PDFs install one of: pip install pymupdf  or  pip install pypdf"
                ) from e
        doc = fitz.open(str(path))
        return "\n".join(doc[i].get_text() for i in range(doc.page_count))
    raise ValueError(f"Unsupported textbook extension: {suffix} (use .pdf or .txt)")


def _clean(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Character-level sliding-window chunking (matches the paper)."""
    text = _clean(text)
    if size <= 0:
        return [text] if text else []
    step = max(1, size - overlap)
    chunks = []
    for start in range(0, len(text), step):
        piece = text[start:start + size].strip()
        if len(piece) >= 50:          # skip trivially short fragments
            chunks.append(piece)
        if start + size >= len(text):
            break
    return chunks


# ──────────────────────────────────────────────────────────────────
#  Index + retrieval
# ──────────────────────────────────────────────────────────────────
class TextbookRetriever:
    """Builds a vector index for a single textbook and returns the top-k passages for any query."""

    def __init__(self, topic_key: str, textbook_path: str):
        self.topic_key = topic_key
        self.textbook_path = Path(textbook_path)
        self.index_dir = Path(RAG_INDEX_DIR) / topic_key
        self.chunks: list[str] = []
        self._embeds: Optional[np.ndarray] = None   # (N, D) normalized
        self._faiss = None
        self._model = None

    # ── embedding model (lazily loaded) ──
    def _embedder(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(RAG_EMBED_MODEL)
        return self._model

    def _embed(self, texts: list[str]) -> np.ndarray:
        vecs = self._embedder().encode(
            texts, batch_size=32, show_progress_bar=False,
            convert_to_numpy=True, normalize_embeddings=True,
        )
        return np.asarray(vecs, dtype="float32")

    # ── build/load ──
    def build(self, force: bool = False) -> "TextbookRetriever":
        if not force and self._load():
            print(f"[RAG] loaded index '{self.topic_key}' from disk ({len(self.chunks)} chunks).")
            return self

        print(f"[RAG] building index '{self.topic_key}' from {self.textbook_path.name} ...")
        raw = _read_textbook(self.textbook_path)
        self.chunks = chunk_text(raw, RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP)
        if not self.chunks:
            raise RuntimeError("No chunks were extracted from the textbook (empty file?).")
        print(f"[RAG]   {len(self.chunks)} chunks — embedding with {RAG_EMBED_MODEL} ...")
        self._embeds = self._embed(self.chunks)
        self._build_faiss()
        self._save()
        print(f"[RAG] ready  (vector dim = {self._embeds.shape[1]})")
        return self

    def _build_faiss(self):
        try:
            import faiss
            idx = faiss.IndexFlatIP(self._embeds.shape[1])   # IP over normalized vectors = cosine
            idx.add(self._embeds)
            self._faiss = idx
        except Exception as e:
            print(f"[RAG]   faiss unavailable ({type(e).__name__}) — using NumPy fallback (mathematically identical).")
            self._faiss = None

    def _save(self):
        self.index_dir.mkdir(parents=True, exist_ok=True)
        np.save(self.index_dir / "embeds.npy", self._embeds)
        (self.index_dir / "chunks.json").write_text(
            json.dumps(self.chunks, ensure_ascii=False), encoding="utf-8")
        (self.index_dir / "meta.json").write_text(json.dumps({
            "topic_key": self.topic_key,
            "textbook": str(self.textbook_path),
            "n_chunks": len(self.chunks),
            "embed_model": RAG_EMBED_MODEL,
            "chunk_size": RAG_CHUNK_SIZE,
            "chunk_overlap": RAG_CHUNK_OVERLAP,
            "dim": int(self._embeds.shape[1]),
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load(self) -> bool:
        emb_p = self.index_dir / "embeds.npy"
        chk_p = self.index_dir / "chunks.json"
        if not (emb_p.exists() and chk_p.exists()):
            return False
        try:
            self._embeds = np.load(emb_p)
            self.chunks = json.loads(chk_p.read_text(encoding="utf-8"))
            self._build_faiss()
            return len(self.chunks) > 0
        except Exception:
            return False

    # ── retrieval ──
    def retrieve(self, query: str, k: int = RAG_TOP_K) -> str:
        """Returns injection-ready text: the top k passages numbered [1]..[k]."""
        passages = self.retrieve_passages(query, k)
        return "\n\n".join(f"[{i+1}] {p}" for i, p in enumerate(passages))

    def retrieve_passages(self, query: str, k: int = RAG_TOP_K) -> list[str]:
        if self._embeds is None or not self.chunks:
            raise RuntimeError("Index not built — call build() first.")
        q = self._embed([query])                    # (1, D) normalized
        if self._faiss is not None:
            _, idx = self._faiss.search(q, min(k, len(self.chunks)))
            order = idx[0]
        else:
            sims = (self._embeds @ q[0])             # cosine since everything is normalized
            order = np.argsort(-sims)[:k]
        return [self.chunks[int(i)] for i in order if 0 <= int(i) < len(self.chunks)]


def get_retriever(topic_key: str = ACTIVE_TOPIC,
                  textbook_path: str = LECTURE_TEXTBOOK_PATH) -> TextbookRetriever:
    """Per-topic singleton — builds the index once and reuses it."""
    with _lock:
        if topic_key not in _RETRIEVERS:
            _RETRIEVERS[topic_key] = TextbookRetriever(topic_key, textbook_path).build()
        return _RETRIEVERS[topic_key]


# Direct run: build the index and test a query
if __name__ == "__main__":
    r = get_retriever()
    print(f"\nRetrieval example for topic: {LECTURE_TOPIC}\n" + "=" * 60)
    print(r.retrieve(LECTURE_TOPIC, k=3)[:1200])
