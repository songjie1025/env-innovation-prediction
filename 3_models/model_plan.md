# Model Plan

This file documents the modeling strategy for the project.

The model plan should stay aligned with the organization file, the variable framework, and the data dictionary. Specific model choices should be added only after the target variable, predictor list, and panel coverage are known.

## Modeling Goal

Predict future country-level environment-related innovation using a small set of interpretable predictors from public country-year panel data.

The model should support two outputs:

1. Predictive performance: how well the model forecasts the target variable.
2. Substantive interpretation: which predictors are most associated with future environment-related innovation.

## Current Status

The final target variable, predictor list, sample coverage, evaluation metric, and model family are not yet fixed.

Before finalizing the model strategy, complete:

1. Literature-based predictor selection in `1_literature_review/variable_framework.md`.
2. Data-source verification in `2_data/data_dictionary.md`.
3. Initial processed panel construction in `2_data/processed/`.
4. Target-variable decision in `0_organization/decision_log.md`.

## Default Modeling Workflow

1. Build a clean country-year modeling panel.
2. Create lagged predictors, usually using year `t-1` predictors for year `t` innovation.
3. Split data in a way that respects time and panel structure.
4. Train a simple interpretable baseline.
5. Evaluate predictive performance.
6. Interpret predictor importance.
7. Add a more complex model only if it improves the research question and can still be explained clearly.

## Candidate Baselines

| Model | Role | Why it may be useful | Status |
|---|---|---|---|
| Mean or country-group baseline | Naive benchmark | Shows whether ML improves beyond a simple reference point | Candidate |
| Linear regression | Simple statistical baseline | Easy to interpret and useful for checking direction and scale | Candidate |
| Elastic Net | Regularized linear baseline | Handles correlated predictors while remaining interpretable | Candidate |

## Candidate Advanced Models

Advanced models are optional and should be justified by data quality, sample size, and research value.

| Model | Role | Why it may be useful | Status |
|---|---|---|---|
| Random Forest | Nonlinear benchmark | Captures nonlinear relationships and interactions | Optional |
| Gradient boosting | Strong predictive model | May improve forecast accuracy with structured tabular data | Optional |

Stacking or large ensembles should not be used unless there is a clear reason and enough data to support them.

## Evaluation

Evaluation metrics should be chosen after inspecting the target variable.

Candidate metrics:

1. RMSE for prediction error in original units.
2. MAE for robust average error.
3. R-squared or out-of-sample R-squared for explained variation.
4. Rank-based metrics if relative country ordering is more important than exact values.

Evaluation should avoid time leakage. Random row-level splits are not preferred for panel forecasting unless clearly justified.

## Interpretability

Interpretation should match the model type:

1. Linear models: coefficients, standardized coefficients, and confidence or uncertainty checks where appropriate.
2. Tree-based models: permutation importance and partial dependence.
3. Gradient boosting models: SHAP or permutation importance, if the final model justifies the added complexity.

Interpretation should connect back to the literature and the variable framework.

## Output Locations

| Path | Purpose |
|---|---|
| `3_models/scripts/` | Modeling scripts and experiment code |
| `3_models/outputs/` | Model outputs, metrics, saved summaries, and importance tables |
| `4_analysis/figures/` | Final figures used for interpretation or reporting |
| `4_analysis/tables/` | Final tables used for interpretation or reporting |

Large trained model files should not be committed unless explicitly needed and small enough for Git.

## Open Decisions

Record final choices in `0_organization/decision_log.md`.

1. Main target variable.
2. Main train-test or validation strategy.
3. Primary evaluation metric.
4. Final baseline model.
5. Whether an advanced model is justified.
6. Final interpretability method.
