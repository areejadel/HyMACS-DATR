# v6 — re-evaluation, shared-draft refinement, and cross-judging

This folder contains every experiment reported in the paper beyond the original
240-run study. It **imports the pipeline from the repository root unchanged**
(agents, DATR router, inner judge) and writes all outputs to `results_v6/`.

| Script | What it does | Paper section |
|---|---|---|
| `exp2_rejudge_panel.py` | Re-judges the 240 lectures with the current panel (Kimi-K3, GLM-5.2, temperature 0.2; Claude-Sonnet-4.6 kept) and re-judges 48 lectures for test–retest | Reliability, robustness to judge replacement |
| `exp3_gpt4o_panel_prompt.py` | GPT-4o with the panel's exact prompt (model vs. prompt) | Single-judge compression |
| `exp5_length_control.py` | Strong generators' lectures truncated to 4000 characters | Length check |
| `exp4_cross_judge.py` | 36 lectures judged by all six generators and the three panel judges | Calibrated self-preference |
| `exp1_shared_draft.py` | Five refinement methods applied to the **same** 60 drafts (300 runs) | Refinement from a shared draft |
| `exp6_allam_precision.py` | Optional: ALLaM at full precision on GPU | — |
| `analyze_v6.py` | All statistics → `results_v6/report_v6.md` and `results_v6/tables/` | all |
| `paper/` | `paper_stats.py`, `export_fig_data.py`, `make_figs.py`: every number and figure in the paper | all |

## Models and hosting

| Role | Model | Host |
|---|---|---|
| Panel judge | Claude-Sonnet-4.6 | Anthropic |
| Panel judge | Kimi-K3 (successor of Kimi-K2.6) | Together |
| Panel judge | GLM-5.2 (successor of GLM-5.1) | Together |
| Inner judge | GPT-4o | OpenAI |
| Generator | ALLaM-7B (4-bit GGUF) | local |
| Generator | Llama-3-8B-Instruct (4-bit GGUF) | local |
| Generator | Llama-3.3-70B-Instruct-Turbo | Together |
| Generator | Gemma-4-31B, Qwen3-235B-A22B-2507, DeepSeek-V4-Pro | OpenRouter (same weights; provider pinned) |

Routes are defined in `routes.py` and `judges.py` and can be overridden with
environment variables (`V6_ROUTE_<model>=backend:id`, `V6_JUDGE_<role>=backend:id`).
The archived scores of the original panel (Kimi-K2.6, GLM-5.1) are kept in the
v5 run files under `../results/`; the successor panel's scores are in
`results_v6/judgements.jsonl`.

## Running

```bash
pip install -r requirements_v6.txt        # in the same environment as the root pipeline
# API keys in ../.env: TOGETHER_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, OPENROUTER_API_KEY
python download_llama3_gguf.py            # local Llama-3-8B (~4.9 GB)

python estimate_cost.py                   # cost per provider, no API calls
bash run_all.sh smoke                     # one tiny call per model
bash run_all.sh judges                    # exp2, exp3, exp5, exp4
bash run_all.sh exp1                      # shared-draft refinement (local models run in the background)
bash run_extra.sh                         # Gemma / Qwen / DeepSeek via OpenRouter
bash run_all.sh analyze                   # report + tables

python paper/paper_stats.py results_v6 results_v6/paper_v6_stats ..
python paper/export_fig_data.py
python paper/make_figs.py paper/figures
```

Every script is resumable: re-running the same command skips finished work.
`--mock` runs any experiment with fake clients and no API calls.

## Spend guard

All model calls pass through `guard.py`, which stops the run (and saves nothing
partial) on repeated failures, a high failure rate, per-provider spend caps, or a
`results_v6/STOP` file. Rate-limit responses (HTTP 429) are retried with back-off
and do not count as failures. Runs in which any agent call failed, or whose panel
returned fewer than three scores, are marked as errors and redone on the next launch.

## What is not included

API keys, the reference textbooks, local model weights, and the human raters'
individual responses (only per-lecture aggregates are released, as stated in the paper).
