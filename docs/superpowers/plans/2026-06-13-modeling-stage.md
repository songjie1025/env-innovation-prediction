# Modeling Stage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a leakage-safe, reviewer-defensible modeling workflow for predicting country-year environment-related innovation from the cleaned v2 panels.

**Architecture:** Keep the notebook as the educational orchestration layer and put all modeling logic in scripts under `3_models/scripts/`. Treat the v2 no-imputation panel as the primary modeling input, use train-fold-only preprocessing for models that require imputation, and reserve retrospective linear-interpolated panels for sensitivity analysis only.

**Tech Stack:** Python, pandas, numpy, scikit-learn, xgboost, shap, matplotlib, seaborn, pytest.

---

## Current Data Contract

Primary cleaned panel package:

- `2_data/processed/model_panels/v2/model_panel_main_no_imputation.csv`
- Target: `env_patent_share_inventions`
- Active main predictors: `gdp_constant_2015_usd`, `renewable_energy_share`, `wgi_regulatory_quality`, `co2_per_capita_ar5`, `fdi_net_inflows`, `env_technology_rta`, `scientific_journal_articles`, `trade_openness`, `inflation`
- Target years: 1999-2023
- Main no-imputation sample after dropping missing target: 2612 rows, 174 countries

Second-target robustness package:

- `2_data/processed/model_panels/robustness/env_patents_per_million/v2/model_panel_main_no_imputation.csv`
- Target: `env_patents_per_million`
- Same active v2 main predictors
- Main no-imputation sample after dropping missing target: 2604 rows, 169 countries

Lag contract:

- Primary lag design: use only `*_lag1_3_mean` features to predict target year `t`.
- Lag robustness design: use only `*_lag1` features.
- Do not include both lag versions in the same primary model, because paired lag columns encode overlapping information and make interpretation less clean.

Imputation contract:

- Targets are never imputed.
- Primary modeling input is `no_imputation`.
- Model-stage imputation must be fit only on training folds.
- `linear_interpolated` panels are retrospective sensitivity datasets and are not used for primary forecasting claims.

---

## Reviewer-Defensible Analysis Design

The paper should frame the model as predictive and associational, not causal. The main claim should be: earlier country-level conditions predict future environment-related innovation, and the strongest predictors can be interpreted as model-based associations consistent or inconsistent with the literature.

Primary design choices:

1. Primary target: `env_patent_share_inventions`.
2. Robustness target: `env_patents_per_million`.
3. Primary feature timing: `lag1_3_mean`.
4. Robustness timing: `lag1`.
5. Primary sample: v2 main panel, no-imputation.
6. Primary evaluation: rolling-origin outer test blocks distributed across the available time line.
7. Hyperparameter tuning: inner rolling validation folds created inside each outer training window only.
8. Latest-period check: 2020-2023 is reported as a stress check, not as the sole evidence of model performance.

Recommended outer rolling-origin test folds for the main panel:

| Outer fold | Train years | Test years |
|---|---:|---:|
| 1 | 1999-2006 | 2007-2009 |
| 2 | 1999-2009 | 2010-2012 |
| 3 | 1999-2012 | 2013-2015 |
| 4 | 1999-2015 | 2016-2018 |
| 5 | 1999-2018 | 2019-2021 |
| 6 | 1999-2021 | 2022-2023 |

For each outer fold, tune candidate models using only years inside the outer training window. Example for outer fold 4:

| Inner fold | Train years | Validation years |
|---|---:|
| 4a | 1999-2009 | 2010-2012 |
| 4b | 1999-2012 | 2013-2015 |

This design gives out-of-sample predictions across early, middle, and late periods while preserving the rule that a row for target year `t` is never predicted by a model trained on target years later than `t`. A single late-period holdout is still useful as a stress check, but it should not be the only performance estimate.

Sliding-window sensitivity:

- Repeat the selected model with a 10-year rolling training window where feasible.
- Example: train 2004-2013 and test 2014-2016.
- This checks whether very old observations dominate the expanding-window model, but it is secondary because it uses fewer training rows.

Submodel panels should be treated as thematic robustness or mechanism screens, not as replacements for the main model, because their sample definitions and predictor families differ.

---

## File Structure

Create:

- `3_models/notebooks/modeling.ipynb`: educational notebook that calls script functions and displays results.
- `3_models/scripts/model_config.py`: constants for targets, panel paths, lag schemes, split years, model grids, and output paths.
- `3_models/scripts/model_data.py`: panel loading, schema validation, feature selection by lag suffix, and train/test matrix creation.
- `3_models/scripts/model_splits.py`: rolling-origin outer folds, inner rolling validation folds, and sliding-window sensitivity split definitions.
- `3_models/scripts/model_baselines.py`: global mean, country historical mean, and optional year-trend baselines.
- `3_models/scripts/model_estimators.py`: scikit-learn pipelines for linear, Elastic Net, tree, and XGBoost models.
- `3_models/scripts/model_evaluation.py`: metrics, prediction tables, grouped error summaries, and model comparison.
- `3_models/scripts/model_interpretation.py`: coefficients, permutation importance, optional SHAP, and partial dependence helpers.
- `3_models/scripts/run_modeling.py`: script entrypoint that reproduces the modeling outputs without notebook state.
- `tests/test_model_data.py`: tests for loading, target filtering, lag feature selection, and missingness behavior.
- `tests/test_model_splits.py`: tests for time-respecting folds and no leakage across train/validation/test.
- `tests/test_model_evaluation.py`: tests for metric calculations and baseline behavior.

Modify:

- `3_models/model_plan.md`: update open decisions with the finalized modeling design.
- `0_organization/decision_log.md`: record final model-stage decisions after implementation and verification.
- `2_data/data_dictionary.md`: add a short note that model-stage imputation is fit inside train folds.

Generated outputs:

- `3_models/outputs/model_sample_summary.csv`
- `3_models/outputs/model_metrics_inner_validation.csv`
- `3_models/outputs/model_metrics_outer_folds.csv`
- `3_models/outputs/model_predictions_outer_folds.csv`
- `3_models/outputs/model_metrics_latest_period.csv`
- `3_models/outputs/model_feature_importance.csv`
- `3_models/outputs/model_robustness_summary.csv`
- `4_analysis/figures/modeling/model_performance_comparison.png`
- `4_analysis/figures/modeling/model_prediction_scatter.png`
- `4_analysis/figures/modeling/model_error_by_year.png`
- `4_analysis/figures/modeling/model_feature_importance.png`

---

## Task 1: Lock Modeling Dataset Contract

**Files:**

- Create: `3_models/scripts/model_config.py`
- Create: `3_models/scripts/model_data.py`
- Test: `tests/test_model_data.py`

- [ ] Define panel targets and paths in `model_config.py`.
- [ ] Implement `load_model_panel(panel_path, target_column)` and validate that target values are non-missing.
- [ ] Implement `select_lag_features(panel, lag_suffix)` where `lag_suffix` is either `lag1_3_mean` or `lag1`.
- [ ] Add tests that primary target panels do not expose `env_patents_per_million` and robustness panels do not expose `env_patent_share_inventions`.
- [ ] Add tests that `lag1_3_mean` selection excludes every `lag1`-only feature and vice versa.
- [ ] Run `python3 -m pytest tests/test_model_data.py -q`.
- [ ] Commit with `git commit -m "model: add panel loading contract"`.

Success criteria:

- Loading fails loudly if the target column is absent or contains blank target values.
- Feature selection returns only the requested lag scheme.
- Predictor `NaN` values are preserved at loading time.

---

## Task 2: Implement Leakage-Safe Temporal Splits

**Files:**

- Create: `3_models/scripts/model_splits.py`
- Test: `tests/test_model_splits.py`

- [ ] Implement primary outer rolling-origin test folds for the main panel:
  - Fold 1: train 1999-2006, test 2007-2009
  - Fold 2: train 1999-2009, test 2010-2012
  - Fold 3: train 1999-2012, test 2013-2015
  - Fold 4: train 1999-2015, test 2016-2018
  - Fold 5: train 1999-2018, test 2019-2021
  - Fold 6: train 1999-2021, test 2022-2023
- [ ] Implement inner rolling validation folds that are generated from each outer fold's training years only.
- [ ] Ensure validation and test years are strictly later than their corresponding training years.
- [ ] Ensure no outer test year is present in that fold's model fitting, preprocessing fitting, imputation fitting, scaling fitting, or hyperparameter selection.
- [ ] Implement a 10-year sliding-window split generator for sensitivity analysis.
- [ ] Add tests using a toy country-year panel covering 1999-2023.
- [ ] Run `python3 -m pytest tests/test_model_splits.py -q`.
- [ ] Commit with `git commit -m "model: add temporal validation splits"`.

Success criteria:

- No row-level random split is used for primary evaluation.
- Every fold respects time order.
- Out-of-sample predictions cover early, middle, and late years after the initial training window.
- The 2020-2023 period is included as one outer test block, not treated as the only evidence of model performance.

---

## Task 3: Build Baselines

**Files:**

- Create: `3_models/scripts/model_baselines.py`
- Test: `tests/test_model_evaluation.py`

- [ ] Implement a train-set global mean baseline.
- [ ] Implement a country historical mean baseline: use each country's train-period target mean, falling back to the train global mean for countries unseen in training.
- [ ] Implement a simple linear year-trend baseline only if it uses training years to estimate the trend.
- [ ] Add tests that baselines never use validation or test target values during fitting.
- [ ] Run `python3 -m pytest tests/test_model_evaluation.py -q`.
- [ ] Commit with `git commit -m "model: add reviewer baselines"`.

Success criteria:

- Main models must beat at least the global mean baseline to be substantively useful.
- Country historical mean is reported as a strong non-ML benchmark because patent behavior is country-persistent.

---

## Task 4: Implement Candidate Models

**Files:**

- Create: `3_models/scripts/model_estimators.py`
- Modify: `requirements.txt` only if a dependency is missing from the current stack.
- Test: `tests/test_model_evaluation.py`

- [ ] Implement Ridge and Elastic Net pipelines with `SimpleImputer(strategy="median")` and `StandardScaler`, both fit inside the training fold.
- [ ] Implement Random Forest with fold-internal median imputation.
- [ ] Implement HistGradientBoostingRegressor or XGBoost with native missing-value handling as the preferred nonlinear predictor.
- [ ] Use small, predeclared grids rather than broad search:
  - Ridge alpha: `0.1`, `1.0`, `10.0`
  - Elastic Net alpha: `0.001`, `0.01`, `0.1`, `1.0`; l1_ratio: `0.2`, `0.5`, `0.8`
  - Random Forest max_depth: `3`, `5`, `None`; min_samples_leaf: `5`, `10`
  - XGBoost max_depth: `2`, `3`; learning_rate: `0.03`, `0.1`; n_estimators: `100`, `300`; subsample: `0.8`, `1.0`
- [ ] Add tests that linear-model pipelines can fit data containing predictor `NaN`.
- [ ] Add tests that imputers are inside the pipeline and are not pre-fit on the full dataset.
- [ ] Run `python3 -m pytest tests/test_model_evaluation.py -q`.
- [ ] Commit with `git commit -m "model: add candidate estimator pipelines"`.

Success criteria:

- All preprocessing lives inside the estimator pipeline.
- Outer test-fold performance is not used to choose hyperparameters inside that fold.
- Complexity is justified only if validation performance clearly improves.

---

## Task 5: Evaluate Models

**Files:**

- Create: `3_models/scripts/model_evaluation.py`
- Create: `3_models/scripts/run_modeling.py`
- Create: `3_models/notebooks/modeling.ipynb`
- Test: `tests/test_model_evaluation.py`

- [ ] Compute MAE, RMSE, out-of-sample R2 against each fold's train-set mean, and Spearman rank correlation.
- [ ] Store inner-validation metrics in `3_models/outputs/model_metrics_inner_validation.csv`.
- [ ] Store outer-fold test metrics in `3_models/outputs/model_metrics_outer_folds.csv`.
- [ ] Store out-of-sample predictions from all outer folds in `3_models/outputs/model_predictions_outer_folds.csv`.
- [ ] Store a latest-period subset summary for 2020-2023 in `3_models/outputs/model_metrics_latest_period.csv`.
- [ ] Add year-level error summaries to detect whether one period drives performance.
- [ ] Add target-quantile error summaries to detect whether the model misses high-innovation country-years.
- [ ] Run `python3 3_models/scripts/run_modeling.py`.
- [ ] Run `python3 -m pytest tests/test_model_evaluation.py -q`.
- [ ] Commit with `git commit -m "model: evaluate rolling-origin performance"`.

Success criteria:

- Model selection is performed inside each outer training window, and the corresponding outer test block remains unseen until prediction.
- Headline performance aggregates outer-fold predictions across the time line.
- 2020-2023 is reported as a latest-period stress check, not as the sole test set.
- MAE is the primary headline metric because it is easy to interpret in target units.
- RMSE and Spearman are secondary metrics.

---

## Task 6: Interpret Models

**Files:**

- Create: `3_models/scripts/model_interpretation.py`
- Modify: `3_models/notebooks/modeling.ipynb`

- [ ] For Ridge and Elastic Net, report standardized coefficients.
- [ ] For tree or boosting models, report permutation importance on pooled outer-fold out-of-sample predictions or on the latest refit model with clear labeling.
- [ ] If XGBoost is selected as the main predictive model, compute SHAP only as a secondary interpretability aid.
- [ ] Generate `4_analysis/figures/modeling/model_feature_importance.png`.
- [ ] Generate partial dependence only for the top three predictors and only within observed data ranges.
- [ ] Explicitly label interpretation as model association, not causal effect.
- [ ] Commit with `git commit -m "model: add model interpretation outputs"`.

Success criteria:

- Interpretation connects back to the literature variables.
- Correlated predictors are discussed carefully.
- The final paper does not overclaim causal policy effects.

---

## Task 7: Run Robustness and Sensitivity Analyses

**Files:**

- Modify: `3_models/scripts/run_modeling.py`
- Modify: `3_models/notebooks/modeling.ipynb`
- Modify: `3_models/scripts/model_config.py`

- [ ] Re-run the selected model class with `lag1` features instead of `lag1_3_mean`.
- [ ] Re-run the selected model class on `env_patents_per_million`.
- [ ] Run thematic submodels `suba`, `subb`, and `subc` as exploratory robustness checks.
- [ ] Run complete-case sensitivity only as a diagnostic and report the sample loss.
- [ ] Run retrospective `linear_interpolated` panel sensitivity with a clear label: not prediction-safe.
- [ ] Store summaries in `3_models/outputs/model_robustness_summary.csv`.
- [ ] Commit with `git commit -m "model: add robustness analyses"`.

Success criteria:

- The main conclusion does not depend on one target definition or one lag choice.
- Sensitivity outputs are not mixed into primary forecasting claims.

---

## Task 8: Final Reviewer Audit

**Files:**

- Modify: `3_models/model_plan.md`
- Modify: `0_organization/decision_log.md`
- Modify: `2_data/data_dictionary.md`
- Modify: `README.md` if run instructions changed.

- [ ] Add a model-stage decision log entry covering target, lag, sample, split, metric, selected model, and rejected alternatives.
- [ ] Add a short limitation note: predictive, not causal; public-data coverage constraints; patent outcome limitations.
- [ ] Add exact reproduction command: `python3 3_models/scripts/run_modeling.py`.
- [ ] Run `python3 -m pytest -q`.
- [ ] Run `python3 3_models/scripts/run_modeling.py`.
- [ ] Re-run the modeling notebook through nbconvert with output directed to `/private/tmp`.
- [ ] Commit with `git commit -m "docs: record final modeling decisions"`.

Success criteria:

- A reviewer can trace every model result to a script, split, target, and feature set.
- No final result requires manual filtering or unrecorded notebook state.
- Main claims are aligned with the data limits documented in the cleaning stage.

---

## Recommended Paper Reporting Order

1. Data and target definition.
2. Predictor timing: `t-1` to `t-3` mean predicting target year `t`.
3. Temporal validation design.
4. Baselines.
5. Main model comparison.
6. Rolling-origin out-of-sample performance, with a latest-period subset check.
7. Feature interpretation.
8. Robustness checks: lag1, second target, submodels, complete-case, retrospective interpolation.
9. Limitations: prediction not causality, patent measurement, source coverage, missingness.

## Stop Criteria Before Modeling Starts

Do not proceed if any of these are true:

- `2_data/notebooks/data_cleaning.ipynb` cannot regenerate the v2 panel outputs.
- Any model input contains missing target values.
- A planned transformation or imputation happens before the temporal split.
- A random row split is used as the main evaluation.
- Any outer test years are used during tuning for that same fold.

At the current cleaning checkpoint, none of these blockers are present.
