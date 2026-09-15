"""
run_v5.py — full experiment orchestrator (single entry point)
============================================================
Runs everything in the correct order for one subject:
    1. Sets the subject (TOPIC) before loading the config.
    2. Validates .env and API keys.
    3. Builds the RAG index for the subject (once).
    4. Runs 6 generators x 4 conditions x 5 seeds = 120 runs (with --resume).
    5. Aggregates results -> master_results.csv + summary_by_condition.csv.
    6. Computes panel agreement (Krippendorff alpha).
    7. (optional) Self-preference matrix.

Examples:
    # Quick smoke test (one generator, two conditions, one seed)
    python run_v5.py --topic backprop --smoke

    # Full run for the first subject
    python run_v5.py --topic backprop

    # Second subject (databases) after downloading its textbook
    python run_v5.py --topic normalization

    # Resume an interrupted run
    python run_v5.py --topic backprop --resume
"""
from __future__ import annotations
import os
import sys
import argparse
import time
from pathlib import Path


def parse_args():
    ap = argparse.ArgumentParser(description="v5 experiment orchestrator")
    ap.add_argument("--topic", default=os.getenv("TOPIC", "backprop"),
                    help="backprop | normalization")
    ap.add_argument("--smoke", action="store_true",
                    help="quick test: one API generator x two conditions x one seed")
    ap.add_argument("--no-rag", action="store_true", help="disable RAG for this run")
    ap.add_argument("--no-panel", action="store_true", help="single external judge instead of the panel")
    ap.add_argument("--single-judge", action="store_true", help="alias for --no-panel")
    ap.add_argument("--models", nargs="+", default=None)
    ap.add_argument("--conditions", nargs="+", default=None)
    ap.add_argument("--seeds", nargs="+", type=int, default=None)
    ap.add_argument("--resume", action="store_true",
                    help="(on by default) skip what is already complete")
    ap.add_argument("--fresh", action="store_true",
                    help="ignore resume and rerun everything from scratch")
    ap.add_argument("--skip-allam", action="store_true")
    ap.add_argument("--self-pref", action="store_true", help="run the self-preference matrix at the end")
    ap.add_argument("--quiet", action="store_true")
    return ap.parse_args()


def main():
    args = parse_args()

    # ─── 1) Set the environment before any config-dependent import ───
    os.environ["TOPIC"] = args.topic
    if args.no_rag:
        os.environ["RAG_ENABLED"] = "0"
    if args.no_panel or args.single_judge:
        os.environ["USE_PANEL"] = "0"

    sys.path.insert(0, str(Path(__file__).parent))
    from config import (
        GENERATORS, CONDITIONS, PILOT_SEEDS, validate_config,
        RAG_ENABLED, USE_PANEL, RESULTS_DIR, ACTIVE_TOPIC,
        LECTURE_TOPIC, LECTURE_TEXTBOOK_PATH,
    )

    print("\n" + "=" * 70)
    print(f"  v5 — subject: {ACTIVE_TOPIC}  ({LECTURE_TOPIC})")
    print(f"  RAG: {'on' if RAG_ENABLED else 'off'} | judge panel: {'on (3)' if USE_PANEL else 'single judge'}")
    print("=" * 70)

    # ─── 2) Validate config ───
    errors = [e for e in validate_config() if "GGUF" not in e or not args.skip_allam]
    if errors:
        print("[!] .env errors:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    # ─── 3) Build the RAG index (once) ───
    if RAG_ENABLED:
        if not Path(LECTURE_TEXTBOOK_PATH).exists():
            print(f"[!] RAG textbook not found: {LECTURE_TEXTBOOK_PATH}")
            print("   Place the textbook or run with --no-rag.")
            sys.exit(1)
        print("\n[1/4] building/loading the RAG index ...")
        from pipeline.rag import get_retriever
        get_retriever()   # builds once, saved to disk

    # ─── 4) Determine the run set ───
    if args.smoke:
        models     = args.models or ["llama_3_8b"]
        conditions = args.conditions or ["no_refine", "datr_full"]
        seeds      = args.seeds or [0]
    else:
        models     = args.models or list(GENERATORS.keys())
        conditions = args.conditions or list(CONDITIONS)
        seeds      = args.seeds or list(range(PILOT_SEEDS))
    if args.skip_allam and "allam_7b" in models:
        models.remove("allam_7b")

    from pipeline import run_single
    runs_dir = RESULTS_DIR / "runs"; runs_dir.mkdir(parents=True, exist_ok=True)

    import json
    from pipeline.runner import result_filename
    def _done(m, c, s):
        # Deterministic file per run (no timestamp) — present, valid, no error => complete
        p = runs_dir / result_filename(m, c, s)
        if not p.exists():
            return False
        try:
            d = json.load(open(p, encoding="utf-8"))
            ok = (not d.get("error")) and bool(d.get("final_lecture"))
            # Not considered complete unless the full judge panel succeeded (3)
            # => degraded runs (panel<3 due to running out of credit) are redone automatically.
            if ok and USE_PANEL and (d.get("panel_n_ok") or 0) < 3:
                ok = False
            return ok
        except Exception:
            return False   # corrupt/half-written file => safely rerun

    resume_on = not args.fresh          # resume on by default (safety)
    total = len(models) * len(conditions) * len(seeds)
    print(f"\n[2/4] running {total} experiments — models={models}  (resume: {'yes' if resume_on else 'no'})\n")
    t0 = time.time(); ok = fail = skip = 0
    idx = 0
    for m in models:
        for c in conditions:
            for s in seeds:
                idx += 1
                if resume_on and _done(m, c, s):
                    print(f"[{idx}/{total}] {m}|{c}|seed{s} -> skip (saved)"); skip += 1; continue
                print(f"[{idx}/{total}] {m}|{c}|seed{s}")
                r = run_single(m, c, s, save=True, verbose=not args.quiet)
                if r.error:
                    print(f"   [x] {r.error}"); fail += 1
                else:
                    print(f"   [ok] inner={r.final_inner_overall:.2f} ext={r.external_overall:.2f} (panel_ok={r.panel_n_ok})"); ok += 1
    print(f"\n  done in {(time.time()-t0)/60:.1f} min — ok:{ok} fail:{fail} skip:{skip}")

    # ─── 5–7) Aggregation and analysis ───
    # subprocess.run with an argument list = safe with paths containing spaces
    import subprocess
    here = Path(__file__).parent
    def _run_script(rel: str):
        subprocess.run([sys.executable, str(here / rel)], check=False)

    print("\n[3/4] aggregating results ...")
    _run_script("experiments/aggregate_results.py")

    if USE_PANEL:
        print("\n[4/4] computing panel agreement ...")
        _run_script("experiments/panel_agreement.py")

    if args.self_pref:
        print("\n[extra] self-preference matrix ...")
        _run_script("experiments/self_preference.py")

    print(f"\n[done] results in: {RESULTS_DIR}\n")


if __name__ == "__main__":
    main()
