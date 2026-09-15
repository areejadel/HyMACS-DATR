"""
smoke_models.py — quick connectivity test for every model before the full run
============================================================================
Sends one small call to each of:
    - the six generators (Together + local ALLaM)
    - the inner judge (GPT-4o)
    - the three panel judges (Claude + Kimi + GLM)
and prints ok/fail + response time + the first reply. Catches early:
    wrong model IDs (especially Kimi/GLM on Together), wrong keys,
    exhausted credit, or empty responses — before spending on 120 runs.

Run:
    python experiments/smoke_models.py                # cloud generators + all judges
    python experiments/smoke_models.py --with-allam    # + test local ALLaM (slower)
    python experiments/smoke_models.py --only-judges    # judges only
"""
from __future__ import annotations
import sys, time, argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import GENERATORS, INNER_JUDGE, EXTERNAL_PANEL, USE_PANEL
from clients import get_client
from clients.openai_client import OpenAIClient

_PING = [{"role": "user", "content": "Reply with exactly one word: OK"}]


def _try(label: str, fn) -> bool:
    t = time.time()
    try:
        res = fn()
        dt = time.time() - t
        ok = getattr(res, "ok", False)
        txt = (getattr(res, "text", "") or "").replace("\n", " ")[:40]
        if ok:
            print(f"  [ok] {label:<34} {dt:5.1f}s  <- {txt!r}")
            return True
        print(f"  [x]  {label:<34} {dt:5.1f}s  error: {getattr(res,'error','?')}")
        return False
    except Exception as e:
        print(f"  [x]  {label:<34} {time.time()-t:5.1f}s  exception: {type(e).__name__}: {e}")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-allam", action="store_true", help="also test local ALLaM (slower)")
    ap.add_argument("--only-judges", action="store_true", help="judges only")
    args = ap.parse_args()

    results = {}

    if not args.only_judges:
        print("\n── Generators ──")
        for key, spec in GENERATORS.items():
            if spec.backend in ("local", "mlx", "cuda") and not args.with_allam:
                print(f"  [skip] {key:<34} (local — use --with-allam to test it)")
                continue
            results[key] = _try(f"{key} ({spec.family})",
                                lambda k=key: get_client(k).generate(_PING, max_tokens=16, temperature=0))

    print("\n── Inner judge ──")
    results["inner_judge"] = _try(
        f"inner_judge ({INNER_JUDGE.api_id})",
        lambda: OpenAIClient(INNER_JUDGE.api_id, temperature=0, label="inner").generate(_PING, max_tokens=16),
    )

    print("\n── External panel ──")
    if not USE_PANEL:
        print("  (USE_PANEL=0 — panel disabled)")
    from pipeline.judge_panel import _make_client
    for spec in EXTERNAL_PANEL:
        results[spec.role] = _try(
            f"{spec.role} ({spec.api_id})",
            lambda s=spec: _make_client(s).generate(_PING, max_tokens=16, temperature=0),
        )

    # ── Summary ──
    ok = [k for k, v in results.items() if v]
    bad = [k for k, v in results.items() if not v]
    print("\n" + "=" * 58)
    print(f"  ok: {len(ok)}   fail: {len(bad)}")
    if bad:
        print(f"  Failed models: {bad}")
        print("  [!] Fix these before the full run:")
        print("     - Wrong ID? Check api_id in config.py against the provider's model list.")
        print("     - Kimi/GLM: verify the exact ID on https://api.together.xyz/models")
        print("     - Key/credit? Check .env and the account balance.")
        sys.exit(1)
    print("  All models respond — ready for the full run.")
    print("=" * 58)


if __name__ == "__main__":
    main()
