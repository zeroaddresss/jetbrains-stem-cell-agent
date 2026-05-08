# Evolving Stem Agent

Research project for building a **stem agent** that evolves into a Python bug-fix specialist. Built for JetBrains' AI Engineering intern role.
**See `WRITEUP.md` for detailed write-up.**

The repository includes:

- A fixed stem loop (issue -> inspect files -> propose patch -> run tests).
- A bounded policy search space and hill-climbing evolution.
- A frozen 18-task benchmark with hidden-test evaluation (`9 train / 3 val / 6 test`).
- End-to-end study orchestration and reporting artifacts.

## Deliverables

- Scope: constrained to repository-level Python bug fixing.
- Task domain: single-bug repair tasks with hidden-test acceptance.
- Architecture: minimal stem agent + bounded policy evolution (model fixed during comparison).
- Evaluation method: frozen benchmark split with before/after measurement (`baseline vs evolved`) and artifact-backed reporting.

Deliverables mapping:

- Working runnable code: this repository + commands below.
- Measurable before/after: `run-study` outputs (`split_summaries.csv`, `study_summary.json`).
- Write-up (approach, experiments, surprises, failures, next steps): see `WRITEUP.md` for full details.

## Current Status

The project is fully runnable and includes runs executed via OpenRouter (`deepseek/deepseek-v4-pro` as model)

Recent study outputs:

- Pilot G1: `results/deepseek-pilot-g1`
- Main G2: `results/deepseek-main-g2-rerun`

Headline from pilot G1:

- Test solved: `0/6` baseline -> `6/6` evolved (`delta=+6`)

Note:

- We also report a deeper search run (`G2`) as an ablation (`0/6` -> `5/6`).
- We treat `G1` as the primary result and `G2` as a cost-aware search-depth comparison.

## Reviewer Quickstart

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[openai,dev]"
cp .env.example .env
```

Edit `.env` and set at least:

- `OPENAI_MODEL=deepseek/deepseek-v4-pro`

Then choose one provider mode:

- **OpenRouter mode** (used for our reported runs):
  - `OPENROUTER_API_KEY=<your_key>`
  - `OPENAI_BASE_URL=https://openrouter.ai/api/v1`
- **OpenAI mode** (if reviewer only has OpenAI key):
  - `OPENAI_API_KEY=<your_key>`
  - keep `OPENAI_BASE_URL` unset/commented

In OpenAI mode, remember to set `OPENAI_MODEL` to a model available on your OpenAI account (or pass `--model`).

Then run a low-cost smoke study:

```bash
stem-agent run-study \
  --backend openai \
  --generations 1 \
  --patience 1 \
  --results-dir results/reviewer-smoke \
  --train-task-ids task_001,task_002 \
  --val-task-ids task_003 \
  --test-task-ids task_001,task_003
```

## Reproducing the Full Experimental Workflow

1) Full-benchmark pilot (`G1`):

```bash
stem-agent run-study \
  --backend openai \
  --generations 1 \
  --patience 1 \
  --results-dir results/deepseek-pilot-g1
```

2) Main run (`G2`) only if G1 signal is positive:

```bash
stem-agent run-study \
  --backend openai \
  --generations 2 \
  --patience 1 \
  --results-dir results/deepseek-main-g2-rerun
```

Interpretation guideline:

- `G1` is the primary run for headline reporting.
- `G2` is reported as an ablation on evolution depth (not as a replacement headline).

3) Optional test-only confirmation:

```bash
stem-agent evaluate --split test --backend openai --policy-file results/deepseek-pilot-g1/baseline_policy.yaml
stem-agent evaluate --split test --backend openai --policy-file results/deepseek-pilot-g1/best_policy.yaml
```

## Generated Artifacts

Each `run-study` directory contains:

- `study_summary.json`: full machine-readable run summary.
- `split_summaries.csv`: baseline/evolved aggregate metrics by split.
- `task_runs.csv`: per-task outcomes and backend error fields.
- `report.md`: human-readable markdown report.
- `baseline_policy.yaml`: fixed baseline policy used.
- `best_policy.yaml`: selected evolved policy.

## OpenAI-Compatible Backend Notes

- `.env` is auto-loaded by the CLI.
- If `OPENAI_API_KEY` is missing, backend falls back to `OPENROUTER_API_KEY`.
- Model comes from `--model` first, then env (`OPENAI_MODEL`, `OPENROUTER_MODEL`, `STEM_AGENT_MODEL`).
- If `OPENAI_BASE_URL` is set to OpenRouter, requests will go to OpenRouter even when `OPENAI_API_KEY` is present.
  For direct OpenAI usage, leave `OPENAI_BASE_URL` unset.
- Response parsing is hardened (direct JSON, fenced JSON, embedded object extraction).
- Backend failures are task-level controlled failures, not run-level crashes.

## Useful Commands

Describe benchmark and frozen split:

```bash
stem-agent describe-benchmark
```

Run one task with heuristic backend:

```bash
stem-agent run-task --task-id task_001 --backend heuristic
```

Run unit tests:

```bash
pytest
```

## Repository Layout

```text
benchmark/              Task dataset and frozen splits.
private_eval/           Hidden tests used by the runner.
src/stem_agent/         Agent, runner, benchmark loader, evolution, study CLI.
tests/                  Automated tests (including backend/reporting robustness).
WRITEUP.md              Final project write-up for reviewers.
results/                Generated study artifacts (git-ignored).
```
