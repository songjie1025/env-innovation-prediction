# Linear Notebook Professor Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the linear-model checkpoint so it reads as a professor-grade, reviewer-defensible, beginner-teachable notebook while keeping executable logic in scripts.

**Architecture:** Keep `3_models/notebooks/modeling_linear_baseline.ipynb` as a narrative runner that calls `run_modeling.py`. Add reusable helpers under `3_models/scripts/` for artifact verification, rolling-origin evaluation, historical-baseline deltas, error decomposition, and missingness-indicator sensitivity. Extend tests first so notebook/script behavior is locked before implementation.

**Tech Stack:** Python, pandas, numpy, scikit-learn, matplotlib/seaborn, Jupyter notebook JSON, pytest.

---

### Task 1: Script-Level Reviewer Diagnostics

**Files:**
- Modify: `tests/test_model_evaluation.py`
- Modify: `tests/test_model_experiments.py`
- Modify: `3_models/scripts/model_evaluation.py`
- Modify: `3_models/scripts/model_experiments.py`

- [ ] Write failing tests for history-baseline delta summaries, year-level error summaries, target-quantile error summaries, and rolling-origin fold summaries.
- [ ] Run targeted tests and confirm failures are due to missing functions or fields.
- [ ] Implement reusable functions in scripts, keeping model training and evaluation outside the notebook.
- [ ] Re-run targeted tests and confirm they pass.

### Task 2: Pipeline Outputs and Artifact Helper

**Files:**
- Modify: `tests/test_model_notebook.py`
- Modify: `3_models/scripts/run_modeling.py`
- Modify: `3_models/scripts/model_config.py`

- [ ] Write failing tests requiring registered outputs for rolling-origin, history deltas, error decomposition, missingness indicators, and a script-level artifact verifier.
- [ ] Implement output paths, write CSV artifacts, return them through `results`, and expose `verify_generated_artifacts`.
- [ ] Re-run notebook/pipeline tests and confirm the new manifest is complete.

### Task 3: Notebook Teaching Layer

**Files:**
- Modify: `3_models/notebooks/modeling_linear_baseline.ipynb`
- Modify: `tests/test_model_notebook.py`

- [ ] Add notebook tests requiring first-checkpoint/confirmatory wording and the `Question -> Concept -> Output -> How to read -> Takeaway` teaching scaffold.
- [ ] Move the long artifact check out of the notebook cell and replace it with a helper call.
- [ ] Add concise professor-style markdown around rolling-origin evidence, history deltas, error decomposition, and missingness indicators.
- [ ] Re-run notebook tests.

### Task 4: Documentation Alignment

**Files:**
- Modify: `3_models/model_plan.md`
- Modify: `0_organization/decision_log.md`

- [ ] Update model-plan status so the current 80/10/10 notebook is labeled as the first linear checkpoint, while rolling-origin/prequential evidence is the stronger confirmatory stage.
- [ ] Add a decision-log entry recording that final reporting must center historical-baseline deltas and not overclaim feature-only forecasting.
- [ ] Run whitespace checks.

### Task 5: Verification

**Files:**
- All touched files.

- [ ] Run targeted tests for model notebook, experiments, evaluation, diagnostics, and visualization.
- [ ] Run `python3 3_models/scripts/run_modeling.py`.
- [ ] Execute the notebook with nbconvert to verify the runbook.
- [ ] Run full pytest and `git diff --check`.
