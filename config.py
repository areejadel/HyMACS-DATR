"""
config.py -- Central configuration.
All settings in one place. Loaded from .env via python-dotenv.
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

# --- Load .env ---
PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")


# --- API keys ---
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


# --- ALLaM backend ---
# "local" = llama.cpp + GGUF Q4_K_M (recommended on Apple Silicon / CPU)
# "mlx"   = Apple Silicon native
# "cuda"  = NVIDIA GPU + transformers
ALLAM_BACKEND = os.getenv("ALLAM_BACKEND", "local")
ALLAM_GGUF_PATH = os.getenv("ALLAM_GGUF_PATH", "./models/allam-7b-instruct-q4_k_m.gguf")
ALLAM_GGUF_REPO = os.getenv(
    "ALLAM_GGUF_REPO",
    "Omartificial-Intelligence-Space/ALLaM-7B-Instruct-preview-Q4_K_M-GGUF",
)
ALLAM_GGUF_FILENAME = os.getenv(
    "ALLAM_GGUF_FILENAME",
    "allam-7b-instruct-preview-q4_k_m.gguf",
)
ALLAM_MLX_REPO  = os.getenv("ALLAM_MLX_REPO", "humain-ai/ALLaM-7B-Instruct-preview")


# --- Experiment hyperparameters ---
TEMPERATURE_GEN  = float(os.getenv("TEMPERATURE_GEN", "0.7"))
TEMPERATURE_EVAL = float(os.getenv("TEMPERATURE_EVAL", "0.2"))
MAX_ITERATIONS   = int(os.getenv("MAX_ITERATIONS", "3"))
QUALITY_THRESHOLD = float(os.getenv("QUALITY_THRESHOLD", "8.5"))
REGRESSION_TOLERANCE = float(os.getenv("REGRESSION_TOLERANCE", "0.5"))
PILOT_SEEDS = int(os.getenv("PILOT_SEEDS", "5"))
FULL_SEEDS  = int(os.getenv("FULL_SEEDS", "5"))


# --- Generator models ---
@dataclass
class ModelSpec:
    """Unified spec for a generator."""
    key: str                     # short internal key
    family: str                  # SDAIA / Meta / Google / Alibaba / DeepSeek
    size_b: float                # parameter count in billions
    backend: str                 # "together" / "local" / "mlx" / "cuda"
    api_id: str                  # provider identifier
    label: str                   # human-readable name
    context_tokens: int = 131072 # context window (input+output); used for prompt budgeting


GENERATORS: dict[str, ModelSpec] = {
    "allam_7b": ModelSpec(
        key="allam_7b",
        family="SDAIA",
        size_b=7,
        backend=ALLAM_BACKEND,
        api_id="ALLaM-AI/ALLaM-7B-Instruct-preview",
        label="ALLaM-7B-Instruct-preview",
        context_tokens=4096,     # small ALLaM context window
    ),
    "llama_3_8b": ModelSpec(
        key="llama_3_8b",
        family="Meta",
        size_b=8,
        backend="together",
        api_id="meta-llama/Meta-Llama-3-8B-Instruct-Lite",
        label="Llama-3-8B-Instruct",
        context_tokens=8192,   # original Llama-3 has an 8K window
    ),
    "llama_3_3_70b": ModelSpec(
        key="llama_3_3_70b",
        family="Meta",
        size_b=70,
        backend="together",
        api_id="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        label="Llama-3.3-70B-Instruct",
        context_tokens=131072,
    ),
    "qwen3_235b": ModelSpec(
        key="qwen3_235b",
        family="Alibaba",
        size_b=235,           # MoE (~22B active)
        backend="together",
        api_id="Qwen/Qwen3-235B-A22B-Instruct-2507-FP8",
        label="Qwen3-235B-A22B-Instruct",
        context_tokens=131072,
    ),
    "deepseek_v3_1": ModelSpec(
        key="deepseek_v3_1",
        family="DeepSeek",
        size_b=671,           # MoE
        backend="together",
        api_id="deepseek-ai/DeepSeek-V4-Pro",
        label="DeepSeek-V4-Pro",
        context_tokens=131072,
    ),
    "gemma_4_31b": ModelSpec(
        key="gemma_4_31b",
        family="Google",
        size_b=31,
        backend="together",
        api_id="google/gemma-4-31B-it",
        label="Gemma-4-31B-Instruct",
        context_tokens=131072,
    ),
}


# --- Judge models ---
@dataclass
class JudgeSpec:
    role: str
    backend: str
    api_id: str
    temperature: float


INNER_JUDGE = JudgeSpec(
    role="inner_judge",
    backend="openai",
    api_id="gpt-4o",
    temperature=TEMPERATURE_EVAL,
)

EXTERNAL_JUDGE = JudgeSpec(
    role="external_judge",
    backend="anthropic",
    api_id="claude-sonnet-4-6",
    temperature=TEMPERATURE_EVAL,
)

# External judge panel: three cross-family judges, aggregated by the median.
# A panel reduces single-judge bias and increases reliability (Verga et al., 2024).
# All three belong to families different from every generator, breaking
# self-preference bias (Panickssery et al., 2024).
# Note: provider identifiers may change; verify the exact api_id against the
# provider model list before running. Disable a judge by removing it here.
EXTERNAL_PANEL: list[JudgeSpec] = [
    JudgeSpec(role="judge_claude", backend="anthropic",
              api_id="claude-sonnet-4-6",      temperature=TEMPERATURE_EVAL),
    JudgeSpec(role="judge_kimi",   backend="together",
              api_id="moonshotai/Kimi-K2.6",   temperature=TEMPERATURE_EVAL),
    JudgeSpec(role="judge_glm",    backend="together",
              api_id="zai-org/GLM-5.1",        temperature=TEMPERATURE_EVAL),
]

# Family of each judge (used by the self-preference analysis: same vs cross family).
JUDGE_FAMILY = {
    "inner_judge":  "OpenAI",
    "judge_claude": "Anthropic",
    "judge_kimi":   "Moonshot",
    "judge_glm":    "Zhipu",
}

USE_PANEL = os.getenv("USE_PANEL", "1") == "1"   # 0 = single external judge


# --- Eight-dimension rubric ---
RUBRIC_DIMENSIONS = [
    "academic_accuracy",
    "pedagogical_effectiveness",
    "clarity_organization",
    "practical_relevance",
    "completeness",
    "engagement_potential",
    "technical_quality",
    "innovation",
]

# Maps each dimension to the agent responsible for it.
DIMENSION_TO_AGENT = {
    "academic_accuracy":         "sme",
    "pedagogical_effectiveness": "pedagogy",
    "clarity_organization":      "clarity",
    "practical_relevance":       "sme",
    "completeness":              "sme",
    "engagement_potential":      "engagement",
    "technical_quality":         "clarity",
    "innovation":                "engagement",
}


# --- Conditions ---
CONDITIONS = [
    "no_refine",        # single generation, no iteration
    "self_refine",      # iterate all four agents without targeting
    "datr_no_guard",    # DATR routing without the regression check
    "datr_full",        # DATR routing + regression guard
]


# --- Lecture subjects (two, for cross-subject generalization) ---
# Each subject: title + reference + textbook file for RAG (PDF or TXT).
# The active subject is selected via env: TOPIC=backprop or TOPIC=normalization
@dataclass
class TopicSpec:
    key: str
    topic: str
    reference: str
    textbook_path: str          # path to the textbook file (PDF/TXT) for RAG
    target_length: int = 12000  # characters (~30-minute lecture)


TOPICS: dict[str, TopicSpec] = {
    "backprop": TopicSpec(
        key="backprop",
        topic="Backpropagation in Neural Networks",
        reference="Goodfellow et al. (2016), Deep Learning, Chapter 6",
        textbook_path=os.getenv("BACKPROP_TEXTBOOK", "./books/deep_learning_ch6.pdf"),
    ),
    "normalization": TopicSpec(
        key="normalization",
        topic="Normalization Forms and Database Schema Design (1NF-BCNF)",
        reference="Elmasri & Navathe (2016), Fundamentals of Database Systems, Ch. 14-15",
        textbook_path=os.getenv("NORMALIZATION_TEXTBOOK", "./books/database_systems.pdf"),
    ),
}

ACTIVE_TOPIC = os.getenv("TOPIC", "backprop")
if ACTIVE_TOPIC not in TOPICS:
    raise ValueError(f"TOPIC='{ACTIVE_TOPIC}' is unknown. Choose one of: {list(TOPICS)}")

_T = TOPICS[ACTIVE_TOPIC]
LECTURE_TOPIC = _T.topic
LECTURE_REFERENCE = _T.reference
LECTURE_TARGET_LENGTH = _T.target_length
LECTURE_TEXTBOOK_PATH = _T.textbook_path


# --- RAG ---
# Matches the paper: 1000-char chunks / 200 overlap, all-MiniLM-L6-v2, FAISS, top-k=6.
RAG_ENABLED   = os.getenv("RAG_ENABLED", "1") == "1"
RAG_EMBED_MODEL = os.getenv("RAG_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
RAG_CHUNK_SIZE    = int(os.getenv("RAG_CHUNK_SIZE", "1000"))
RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))
RAG_TOP_K         = int(os.getenv("RAG_TOP_K", "6"))
RAG_INDEX_DIR     = PROJECT_ROOT / "rag_index"   # per-subject index cache


# --- Output paths (separate results per subject) ---
RESULTS_DIR = PROJECT_ROOT / "results" / ACTIVE_TOPIC
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# --- Validation ---
def validate_config() -> list[str]:
    """Check configuration before running. Returns a list of error strings."""
    errors = []
    if not TOGETHER_API_KEY or TOGETHER_API_KEY.startswith("your_"):
        errors.append("TOGETHER_API_KEY is not set in .env")
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-your_"):
        errors.append("OPENAI_API_KEY is not set in .env")
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY.startswith("sk-ant-your_"):
        errors.append("ANTHROPIC_API_KEY is not set in .env")
    if ALLAM_BACKEND not in ("mlx", "local", "cuda"):
        errors.append(f"ALLAM_BACKEND='{ALLAM_BACKEND}' is invalid (use mlx, local, or cuda)")
    if ALLAM_BACKEND == "local" and not Path(ALLAM_GGUF_PATH).exists():
        errors.append(f"ALLaM GGUF file not found: {ALLAM_GGUF_PATH}\n  run: python download_allam_gguf.py")
    return errors


if __name__ == "__main__":
    errors = validate_config()
    if errors:
        print("Configuration errors:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("Configuration OK")
        print(f"  Generators: {list(GENERATORS.keys())}")
        print(f"  Inner judge: {INNER_JUDGE.api_id}")
        print(f"  External judge: {EXTERNAL_JUDGE.api_id}")
        print(f"  ALLaM backend: {ALLAM_BACKEND}")
