# Linear Robustness Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reviewer-defensible robustness package for the model stage using multiple linear candidates across pre-specified lag and target sensitivity settings.

**Architecture:** Keep the existing 80/10/10 chronological split and linear candidate selection protocol as the common evaluation engine. Add a small robustness registry that runs main-panel sensitivity experiments for `lag1_3_mean`, `lag1`, and the robustness target `env_patents_per_million`, then writes comparable CSV tables, figures, summary text, and notebook cells. Submodel nested tests remain separate and are not used as direct rankings.

**Tech Stack:** Python, pandas, scikit-learn linear models, matplotlib/seaborn, pytest, Jupyter nbconvert.

---

### Task 1: Robustness Experiment Contract

**Files:**
- Modify: `3_models/scripts/model_config.py`
- Modify: `3_models/scripts/model_experiments.py`
- Test: `tests/test_model_experiments.py`

- [ ] Add a robustness experiment spec that records `robustness_id`, `target_column`, `lag_suffix`, `panel_path`, and `comparison_role`.
- [ ] Add tests that assert robustness outputs include target, lag suffix, rows, countries, best model, validation MAE, test MAE, and historical-baseline delta fields.
- [ ] Keep model choice inside each robustness run based only on validation MAE.

### Task 2: Robustness Runner and Outputs

**Files:**
- Modify: `3_models/scripts/run_modeling.py`
- Test: `tests/test_model_evaluation.py`
- Test: `tests/test_model_notebook.py`

- [ ] Run main robustness experiments for the active target with `lag1_3_mean`, the active target with `lag1`, and `env_patents_per_million` with `lag1_3_mean`.
- [ ] Write `linear_model_robustness_summary.csv`, `linear_model_robustness_validation_metrics.csv`, `linear_model_robustness_test_metrics.csv`, and `linear_model_robustness_historical_baselines.csv`.
- [ ] Include a conservative skipped-status path if a future robustness panel is unavailable.

### Task 3: Robustness Figures

**Files:**
- Modify: `3_models/scripts/model_visualization.py`
- Test: `tests/test_model_visualization.py`

- [ ] Add a validation-versus-test MAE figure across robustness settings.
- [ ] Add a selected-linear-versus-country-persistence figure across robustness settings.
- [ ] Register figures in `linear_model_figure_index.csv`.

### Task 4: Notebook and Research Narrative

**Files:**
- Modify: `3_models/notebooks/modeling_linear_baseline.ipynb`
- Modify: `3_models/model_plan.md`
- Modify: `0_organization/decision_log.md`
- Test: `tests/test_model_notebook.py`

- [ ] Add an educational notebook section explaining what robustness means here: linear-family, timing, and target sensitivity.
- [ ] Report negative results explicitly when robustness settings do not beat country persistence.
- [ ] Update documentation to state that advanced models are deferred until the linear robustness package is interpreted.

### Task 5: Verification and Cross-Review

**Files:**
- No new source files unless implementation requires a small helper module.

- [ ] Run targeted tests.
- [ ] Run `python3 3_models/scripts/run_modeling.py`.
- [ ] Execute the notebook in place.
- [ ] Run full pytest and `git diff --check`.
- [ ] Ask subagents for methodology and code-quality review, then apply necessary fixes.
