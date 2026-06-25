# Model Plan

This file documents the modeling strategy for the project.

The model plan should stay aligned with the organization file, the decision log, the variable framework, and the data dictionary. Specific model choices should be added only after the predictor subset and panel coverage are known.

## Modeling Goal

Predict future country-level environment-related innovation using `env_patent_share_inventions` and a small set of interpretable predictors from public country-year panel data.

The model should support two outputs:

1. Predictive performance: how well the model forecasts the target variable.
2. Substantive interpretation: which predictors are most associated with future environment-related innovation.

## Current Status

The main target variable and main predictor timing specification are fixed:

1. Main target: `env_patent_share_inventions` / `PT_INV.DEV.ENV_PAT._Z`.
2. Main timing: for each selected predictor `x`, use `x_lag1_3_mean`, the mean of years `t-1`, `t-2`, and `t-3`, to predict target year `t`.

The active v2 main panel fixes the first main-model predictor subset after the pre-modeling reassessment. The first modeling checkpoint uses the v2 no-imputation main panel, `*_lag1_3_mean` features, and a simple chronological 80/10/10 train/validation/test split confirmed after teacher consultation on 2026-06-17. The first runnable pipeline focuses on interpretable linear models and chooses the candidate with the lowest validation MAE before reporting final test performance on the latest contiguous period.

The current model-stage extension also runs the active v2 no-imputation Submodel A, Submodel B, and Submodel C panels through the same linear protocol. Pure submodel results are mechanism and robustness diagnostics, not replacements for the main model, because the panels have different countries, years, anchors, and test windows. The comparable submodel test is same-sample and nested: for each submodel sample, the pipeline compares main predictors only against main predictors plus the submodel predictors on exactly the same country-year rows. Main-model train+validation correlation diagnostics are included to explain why ElasticNet is useful under correlated predictors and to connect coefficients back to predictor-target associations without using held-out test labels. Reviewer-driven diagnostics now also report prediction-safe historical target baselines, historical-baseline delta summaries, top absolute test errors, year-level and target-quantile error decomposition, predictor missingness pattern diagnostics among target-observed model rows, complete-case missingness sensitivity, and missingness-indicator sensitivity runs that reuse the primary split years.

The pipeline now also runs a persistence-augmented linear comparison on the main panel. This comparison adds `target_history_preblock` to the main predictors, where validation rows use only the latest training-period target for the same country and test rows use only the latest train+validation-period target for the same country. It is not a replacement for the primary feature-only model; it answers a separate question about whether external predictors add useful signal after national historical inertia is explicitly included. In the current run, the best feature-only model has test MAE 1.038, the persistence-augmented Lasso has test MAE 0.359, and the strongest standalone history-only baseline has test MAE 0.312. Therefore the notebook should present historical inertia as the dominant forecasting benchmark while keeping the feature-only model as the primary interpretable baseline.

The active robustness pack keeps the analysis within interpretable linear models while broadening the linear candidate family to ordinary least squares, Ridge, Lasso, and ElasticNet. It runs limited main-panel sensitivity settings for common-sample `lag1` versus `lag1_3_mean` timing, skew-transformed main predictors, and the alternative `env_patents_per_million` target. Each setting selects the linear candidate by validation MAE only, reports final test performance once, and compares the selected feature model with target-history baselines in that same target scale. In the current robustness run, none of the selected linear feature models beats its strongest prediction-safe historical baseline, so the model-stage narrative should emphasize interpretable associations and limited rank-order signal rather than superior short-horizon forecasting over national historical inertia.

The skew-transformed main-predictor check is a negative result but still informative. StandardScaler was already used in the primary linear pipeline, but standard scaling does not reduce skewness. The transformed setting applies `log1p` to positive right-skewed predictors, `asinh` to signed skewed predictors, and leaves bounded or near-symmetric predictors unchanged before the same imputation and scaling pipeline. In the current run, this setting worsens validation MAE from 0.809 to 1.382 and test MAE from 1.038 to 1.541, so skewness reduction alone does not explain the feature-only linear model's weakness.

The notebook also includes a confirmatory rolling-origin check for the main feature-only linear model. Each fold trains on earlier years, validates inside the pre-test window, then tests the next held-out block; the final shorter block is retained as the latest-period stress fold. This rolling-origin table is stronger evidence about temporal stability than the first contiguous 80/10/10 checkpoint, but it must still be read against prediction-safe historical baselines rather than as a new post-test tuning loop.

Before finalizing the model strategy, complete:

1. Literature-based predictor selection in `1_literature_review/variable_framework.md`.
2. Data-source verification in `2_data/data_dictionary.md`.
3. Initial processed panel construction in `2_data/processed/`.
4. Predictor role assignment for the manual CSV and candidate catalog variables.
5. Interpretation of the generated linear robustness runs for the lag-1 feature set and `env_patents_per_million` target.
6. Optional common-sample sensitivity checks if the report needs direct metric comparisons across main and submodel panels.

## Default Modeling Workflow

1. Build a clean country-year modeling panel.
2. Create three-year lagged moving-average predictors using years `t-1`, `t-2`, and `t-3` for year `t` innovation.
3. Split data in a way that respects time and panel structure.
4. Train a simple interpretable baseline.
5. Evaluate predictive performance.
6. Interpret predictor importance.
7. Add a more complex model only if it improves the research question and can still be explained clearly.

## Candidate Baselines

| Model | Role | Why it may be useful | Status |
|---|---|---|---|
| Global and country-history target baselines | Required naive benchmark | Shows whether feature models improve beyond global mean and national target persistence | Active |
| Linear regression | Simple statistical baseline | Easy to interpret and useful for checking direction and scale | Candidate |
| Lasso | Sparse regularized linear baseline | Tests whether a more aggressively sparse linear model is favored under validation | Candidate |
| Elastic Net | Regularized linear baseline | Handles correlated predictors while remaining interpretable | Candidate |
| Persistence-augmented linear model | Historical-inertia comparison | Tests main predictors plus block-safe past target information without using validation or test labels inside the held-out blocks | Active comparison |
| Skew-transformed linear model | Linear robustness check | Tests whether log/asinh transformations of long-tailed predictors improve the same feature-only linear protocol before nonlinear models | Active robustness |

For the first model-stage run, ElasticNet is the selected main-panel validation model. Ridge, Lasso, ordinary linear regression, and other ElasticNet penalties remain in the validation table as transparent candidate comparisons. The regularization grid is finite rather than exhaustive: Ridge alpha in `[0.1, 1, 10]`, Lasso alpha in `[0.001, 0.01, 0.1, 1]`, and ElasticNet alpha in `[0.001, 0.01, 0.1, 1]` with l1_ratio in `[0.2, 0.5, 0.8]`. Predictors are median-imputed and standardized inside each pipeline, but the target is not standardized; therefore alpha values are target-scale dependent and should not be described as a fully tuned regularization protocol. The final interpretation must also compare the selected model against prediction-safe target-history baselines; in the current run, the country last-pretest baseline outperforms ElasticNet on primary test MAE, so the feature model should not be described as beating national historical persistence.

## Candidate Advanced Models

Advanced models are optional and should be justified by data quality, sample size, and research value.

| Model | Role | Why it may be useful | Status |
|---|---|---|---|
| Random Forest | Nonlinear benchmark | Captures nonlinear relationships and interactions | Optional |
| Gradient boosting | Strong predictive model | May improve forecast accuracy with structured tabular data | Optional |

Stacking or large ensembles should not be used unless there is a clear reason and enough data to support them.

## Evaluation

For the first linear baseline, use MAE as the primary validation and test metric because it is easy to interpret in target units. Report RMSE, out-of-sample R-squared against the training-period mean, and Spearman rank correlation as secondary metrics.

Candidate metrics:

1. RMSE for prediction error in original units.
2. MAE for robust average error.
3. R-squared or out-of-sample R-squared for explained variation.
4. Rank-based metrics if relative country ordering is more important than exact values.

Evaluation should avoid time leakage. The active first-stage split uses the earliest 80% of distinct target years for training, the next 10% for validation, and the latest 10% for testing. Random row-level splits are not preferred for panel forecasting unless clearly justified.

The first 80/10/10 split should be described as a course-friendly first linear checkpoint. The stronger temporal-stability check is the confirmatory rolling-origin evaluation, where each fold uses only earlier target years for model fitting and validation before scoring the next held-out period. Rolling-origin fold results must be summarized by fold-level MAE/RMSE/Spearman and by delta against the best prediction-safe history baseline.

The persistence-augmented comparison uses a block-safe target-history feature rather than a within-test rolling lag. Validation rows receive only pre-validation country target history from the training block; test rows receive only pre-test country target history from the train+validation block. This makes the comparison conservative and aligned with the current contiguous 80/10/10 protocol.

Robustness runs reuse this same split rule and validation-only model selection. The lag1 rows are common-sample timing sensitivities: they reuse the same generated panels as the `lag1_3_mean` rows and swap only the selected lag feature columns, rather than rebuilding a larger natural lag1 sample. The robustness rows should not be used to choose a new primary model after viewing test performance. Different targets have different MAE units, so the alternative-target rows should be interpreted against their own historical baselines rather than directly ranked against the main target's MAE.

The skew-transformed row is also a common-sample sensitivity. It keeps the primary target and primary split years, transforms only selected main predictors deterministically, and then uses the same median-imputation and StandardScaler pipeline. Because it is evaluated after the primary model is fixed, it should be interpreted as evidence about scale-shape robustness, not as a post-hoc primary-model replacement.

Submodel A, Submodel B, and Submodel C use the same split rule inside their own panel windows. Their metric tables must report rows, countries, train/validation/test years, and a comparison-scope flag because the pure submodel samples are not identical to the main-model sample. The primary comparability table is the nested same-sample table: `main_on_subX` versus `main_plus_subX`, where the row set, split years, countries, and target values are identical within each pair.

Every reporting table should center the historical-baseline delta before making a forecasting statement. Positive delta MAE means the selected feature model is worse than the best prediction-safe country-history baseline. OOS R2 against a global train mean and high Spearman rank correlation can still be useful diagnostics, but they do not justify the claim that external predictors beat national historical persistence.

## Interpretability

Interpretation should match the model type:

1. Linear models: coefficients, standardized coefficients, and confidence or uncertainty checks where appropriate.
2. Tree-based models: permutation importance and partial dependence.
3. Gradient boosting models: SHAP or permutation importance, if the final model justifies the added complexity.

Interpretation should connect back to the literature and the variable framework.

For the current ElasticNet baseline, interpretation uses standardized coefficients plus train+validation correlation diagnostics:

1. Predictor-predictor correlation matrices and top correlated pairs show collinearity pressure.
2. Predictor-target correlations show simple association on the fitted imputed/scaled train+validation design matrix when available.
3. Coefficient-versus-correlation alignment shows where nonzero ElasticNet signs match or diverge from simple correlations.
4. Coefficients shrunk to zero are marked as shrinkage outcomes, not sign-aligned effects.
5. These diagnostics are explanatory only and should not be used to remove features after inspecting test performance.

## Output Locations

| Path | Purpose |
|---|---|
| `3_models/scripts/` | Modeling scripts and experiment code |
| `3_models/outputs/` | Model outputs, metrics, saved summaries, and importance tables |
| `4_analysis/figures/` | Final figures used for interpretation or reporting |
| `4_analysis/tables/` | Final tables used for interpretation or reporting |

Large trained model files should not be committed unless explicitly needed and small enough for Git.

The current model-stage notebook regenerates both main-model files and panel-level extension files under `3_models/outputs/`, including `linear_model_specification_registry.csv`, `linear_model_panel_comparison.csv`, `linear_model_nested_comparison.csv`, `linear_model_historical_baselines.csv`, `linear_model_historical_baseline_delta_summary.csv`, `linear_model_persistence_augmented_comparison.csv`, `linear_model_persistence_augmented_test_metrics.csv`, `linear_model_persistence_augmented_coefficients.csv`, `linear_model_skew_transform_plan.csv`, `linear_model_top_errors.csv`, `linear_model_error_by_year_summary.csv`, `linear_model_error_by_target_quantile_summary.csv`, `linear_model_missingness_pattern_summary.csv`, `linear_model_missingness_pattern_country_detail.csv`, `linear_model_missingness_sensitivity.csv`, `linear_model_missingness_indicator_plan.csv`, `linear_model_rolling_origin_summary.csv`, rolling-origin metrics and predictions, `linear_model_robustness_summary.csv`, `linear_model_robustness_validation_metrics.csv`, `linear_model_robustness_test_metrics.csv`, `linear_model_robustness_historical_baselines.csv`, panel-level and nested metrics/predictions/coefficients, and main-model correlation diagnostics. Figures for model comparison, nested incremental comparisons, historical-baseline comparison, failure modes, missingness pattern counts, missingness sensitivity, linear robustness, and correlation diagnostics are written under `4_analysis/figures/modeling/` and indexed in `linear_model_figure_index.csv`.

## Open Decisions

Record final choices in `0_organization/decision_log.md`.

1. Main predictor subset.
2. Robustness and exploratory predictor sets.
3. Whether additional nonlinear models are justified after the linear checkpoint, rolling-origin check, and historical-baseline deltas are interpreted.
4. Final report wording for the feature-only baseline, historical baselines, persistence-augmented comparison, and rolling-origin evidence without post-test model fishing.
5. Whether to add a common-sample submodel comparison for direct metric rankings.
6. Whether an advanced model is justified.
7. Final interpretability method beyond the first ElasticNet coefficient and correlation diagnostics.
