# HyMACS: Cross-Family Panel Evaluation and Dimension-Aware Refinement of LLM-Generated Lectures

Reference implementation for the paper *"Reliable Cross-Family Evaluation of
LLM-Generated University Lectures."* A multi-agent pipeline generates a
university-level lecture, grounds it in a reference textbook via retrieval-augmented
generation (RAG), refines it with Dimension-Aware Targeted Refinement (DATR) and a
Regression-Guard, and evaluates it with an inner judge plus a cross-family panel of
three external LLM judges.

## Overview

- **Generators (6):** ALLaM-7B (local), Llama-3-8B, Llama-3.3-70B, Gemma-4-31B,
  Qwen3-235B, DeepSeek-V4-Pro (hosted).
- **Inner judge:** GPT-4o (formative, drives the DATR loop).
- **External panel:** Claude-Sonnet, Kimi-K2.6, GLM-5.1 (median aggregation;
  cross-family with respect to every generator).
- **Design:** 6 generators x 4 conditions x 5 seeds x 2 subjects = 240 runs.

## Repository layout

```
config.py            Central configuration (models, judges, RAG, topics)
run_v5.py            Main orchestrator (one subject end-to-end)
agents/              Specialist generation agents (SME, Pedagogy, Clarity, Engagement)
clients/             Unified LLM client interfaces (hosted API + local backends)
pipeline/            Generator, RAG, DATR router, inner judge, external panel, runner
experiments/         Analysis: aggregation, panel agreement, self-preference,
                     significance tests, figures, human-evaluation packaging
```

## Setup

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in your API keys
```

### API keys
Three providers are required. Put your keys in `.env` (never commit it):

- `TOGETHER_API_KEY` — hosted generators and two panel judges
- `OPENAI_API_KEY` — inner judge (GPT-4o)
- `ANTHROPIC_API_KEY` — one panel judge (Claude)

### Reference textbooks (RAG) — not included
The two subjects are grounded in copyrighted textbooks that are **not redistributed
with this repository**. Obtain them separately and place the PDFs under `books/`,
then set their paths in `.env`:

| Subject | Expected file (configurable) |
|---------|------------------------------|
| Backpropagation | a Deep Learning textbook chapter PDF |
| Normalization   | a Database Systems textbook PDF |

If you do not have the textbooks, run with `RAG_ENABLED=0` to disable grounding.

## Running

```bash
python experiments/smoke_models.py            # verify all models respond
python run_v5.py --topic backprop             # full study for one subject
python run_v5.py --topic normalization
```

Each run is saved atomically; re-running the same command resumes from where it stopped.

### Analysis
```bash
python experiments/aggregate_results.py       # master CSV + per-condition summary
python experiments/panel_agreement.py         # inter-judge reliability (Krippendorff alpha)
python experiments/self_preference.py         # self-preference matrix
python experiments/stats_v5.py                # paired Wilcoxon significance tests
python experiments/figures_v5.py              # paper figures
```

### Human evaluation
```bash
python experiments/build_human_eval.py        # select + anonymize lectures, build rater form
python experiments/assign_raters.py --raters 15 --coverage 3
```

## License
Released under the MIT License (see `LICENSE`).

## Human evaluation materials
The `human_eval/` folder contains the anonymized lectures, calibration anchors, and the blank
rating form used in the faculty validation. Rater identities, individual scores, and comments
are intentionally withheld; aggregate results are reported in the paper.
