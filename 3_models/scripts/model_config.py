from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]

PRIMARY_PANEL_PATH = (
    ROOT_DIR
    / "2_data"
    / "processed"
    / "model_panels"
    / "v2"
    / "model_panel_main_no_imputation.csv"
)
PRIMARY_TARGET = "env_patent_share_inventions"
ROBUSTNESS_TARGET = "env_patents_per_million"
PRIMARY_LAG_SUFFIX = "lag1_3_mean"

V2_PANEL_DIR = ROOT_DIR / "2_data" / "processed" / "model_panels" / "v2"
ROBUSTNESS_TARGET_PANEL_DIR = (
    ROOT_DIR
    / "2_data"
    / "processed"
    / "model_panels"
    / "robustness"
    / ROBUSTNESS_TARGET
    / "v2"
)
PANEL_CONFIGS = [
    {
        "panel_id": "main",
        "panel_label": "Main v2 model",
        "panel_path": PRIMARY_PANEL_PATH,
        "target_column": PRIMARY_TARGET,
        "lag_suffix": PRIMARY_LAG_SUFFIX,
        "role": "main",
    },
    {
        "panel_id": "suba",
        "panel_label": "Submodel A: RISE and high-tech exports",
        "panel_path": V2_PANEL_DIR / "model_panel_suba_no_imputation.csv",
        "target_column": PRIMARY_TARGET,
        "lag_suffix": PRIMARY_LAG_SUFFIX,
        "role": "mechanism_submodel",
    },
    {
        "panel_id": "subb",
        "panel_label": "Submodel B: R&D, co-invention, and tax",
        "panel_path": V2_PANEL_DIR / "model_panel_subb_no_imputation.csv",
        "target_column": PRIMARY_TARGET,
        "lag_suffix": PRIMARY_LAG_SUFFIX,
        "role": "mechanism_submodel",
    },
    {
        "panel_id": "subc",
        "panel_label": "Submodel C: OECD EPS",
        "panel_path": V2_PANEL_DIR / "model_panel_subc_no_imputation.csv",
        "target_column": PRIMARY_TARGET,
        "lag_suffix": PRIMARY_LAG_SUFFIX,
        "role": "mechanism_submodel",
    },
]

ROBUSTNESS_EXPERIMENT_CONFIGS = [
    {
        "panel_id": "robust_main_share_lag1_3_mean",
        "panel_label": "Share target with lag1-3 mean predictors",
        "panel_path": PRIMARY_PANEL_PATH,
        "target_column": PRIMARY_TARGET,
        "lag_suffix": "lag1_3_mean",
        "role": "robustness_primary_anchor",
        "comparison_group": "linear_robustness",
        "feature_set_role": "primary_specification",
    },
    {
        "panel_id": "robust_main_share_lag1",
        "panel_label": "Share target with common-sample lag1 predictors",
        "panel_path": PRIMARY_PANEL_PATH,
        "target_column": PRIMARY_TARGET,
        "lag_suffix": "lag1",
        "role": "robustness_timing",
        "comparison_group": "linear_robustness",
        "feature_set_role": "common_sample_lag1_timing",
    },
    {
        "panel_id": "robust_main_per_million_lag1_3_mean",
        "panel_label": "Per-million target with lag1-3 mean predictors",
        "panel_path": ROBUSTNESS_TARGET_PANEL_DIR / "model_panel_main_no_imputation.csv",
        "target_column": ROBUSTNESS_TARGET,
        "lag_suffix": "lag1_3_mean",
        "role": "robustness_target",
        "comparison_group": "linear_robustness",
        "feature_set_role": "alternative_target",
    },
    {
        "panel_id": "robust_main_per_million_lag1",
        "panel_label": "Per-million target with common-sample lag1 predictors",
        "panel_path": ROBUSTNESS_TARGET_PANEL_DIR / "model_panel_main_no_imputation.csv",
        "target_column": ROBUSTNESS_TARGET,
        "lag_suffix": "lag1",
        "role": "robustness_target_timing",
        "comparison_group": "linear_robustness",
        "feature_set_role": "alternative_target_common_sample_lag1",
    },
]

SKEW_TRANSFORM_EXPERIMENT_CONFIG = {
    "panel_id": "robust_main_share_skew_transformed_lag1_3_mean",
    "panel_label": "Share target with skew-transformed lag1-3 mean predictors",
    "panel_path": PRIMARY_PANEL_PATH,
    "target_column": PRIMARY_TARGET,
    "lag_suffix": "lag1_3_mean",
    "role": "robustness_transform",
    "comparison_group": "linear_robustness",
    "feature_set_role": "skew_transformed_main_predictors",
}

# GDP and scientific output are merged into `size_factor` upstream (see
# model_data.add_size_factor_columns), so they are no longer standalone columns.
# The PCA component is already symmetric and centered, so it needs no skew
# transform; the remaining right-skewed predictors are transformed as before.
SKEW_TRANSFORM_METHODS = {
    "fdi_net_inflows_lag1_3_mean": "asinh",
    "inflation_lag1_3_mean": "asinh",
    "co2_per_capita_ar5_lag1_3_mean": "log1p",
    "trade_openness_lag1_3_mean": "log1p",
    "env_technology_rta_lag1_3_mean": "log1p",
}

COUNTRY_CODE_COLUMN = "country_code"
COUNTRY_NAME_COLUMN = "country_name"
YEAR_COLUMN = "year"

TRAIN_SHARE = 0.80
VALIDATION_SHARE = 0.10

OUTPUT_DIR = ROOT_DIR / "3_models" / "outputs"
NOTEBOOK_DIR = ROOT_DIR / "3_models" / "notebooks"
FIGURES_DIR = ROOT_DIR / "4_analysis" / "figures" / "modeling"

SAMPLE_SUMMARY_OUTPUT = OUTPUT_DIR / "linear_model_sample_summary.csv"
SPECIFICATION_REGISTRY_OUTPUT = OUTPUT_DIR / "linear_model_specification_registry.csv"
VALIDATION_METRICS_OUTPUT = OUTPUT_DIR / "linear_model_validation_metrics.csv"
TEST_METRICS_OUTPUT = OUTPUT_DIR / "linear_model_test_metrics.csv"
PREDICTIONS_OUTPUT = OUTPUT_DIR / "linear_model_predictions.csv"
COEFFICIENTS_OUTPUT = OUTPUT_DIR / "linear_model_coefficients.csv"
RUN_SUMMARY_OUTPUT = OUTPUT_DIR / "linear_model_run_summary.md"
FIGURE_INDEX_OUTPUT = OUTPUT_DIR / "linear_model_figure_index.csv"
PANEL_SAMPLE_SUMMARY_OUTPUT = OUTPUT_DIR / "linear_model_panel_sample_summary.csv"
PANEL_VALIDATION_METRICS_OUTPUT = OUTPUT_DIR / "linear_model_panel_validation_metrics.csv"
PANEL_TEST_METRICS_OUTPUT = OUTPUT_DIR / "linear_model_panel_test_metrics.csv"
PANEL_PREDICTIONS_OUTPUT = OUTPUT_DIR / "linear_model_panel_predictions.csv"
PANEL_COEFFICIENTS_OUTPUT = OUTPUT_DIR / "linear_model_panel_coefficients.csv"
PANEL_COMPARISON_OUTPUT = OUTPUT_DIR / "linear_model_panel_comparison.csv"
NESTED_SAMPLE_SUMMARY_OUTPUT = OUTPUT_DIR / "linear_model_nested_sample_summary.csv"
NESTED_VALIDATION_METRICS_OUTPUT = OUTPUT_DIR / "linear_model_nested_validation_metrics.csv"
NESTED_TEST_METRICS_OUTPUT = OUTPUT_DIR / "linear_model_nested_test_metrics.csv"
NESTED_PREDICTIONS_OUTPUT = OUTPUT_DIR / "linear_model_nested_predictions.csv"
NESTED_COEFFICIENTS_OUTPUT = OUTPUT_DIR / "linear_model_nested_coefficients.csv"
NESTED_COMPARISON_OUTPUT = OUTPUT_DIR / "linear_model_nested_comparison.csv"
FEATURE_SPEARMAN_CORRELATION_OUTPUT = OUTPUT_DIR / "linear_model_main_feature_spearman_correlations.csv"
FEATURE_PEARSON_CORRELATION_OUTPUT = OUTPUT_DIR / "linear_model_main_feature_pearson_correlations.csv"
TOP_CORRELATED_PAIRS_OUTPUT = OUTPUT_DIR / "linear_model_top_correlated_pairs.csv"
TARGET_CORRELATIONS_OUTPUT = OUTPUT_DIR / "linear_model_target_correlations.csv"
CORRELATION_ALIGNMENT_OUTPUT = OUTPUT_DIR / "linear_model_correlation_alignment.csv"
HISTORICAL_BASELINES_OUTPUT = OUTPUT_DIR / "linear_model_historical_baselines.csv"
HISTORICAL_BASELINE_DELTA_OUTPUT = OUTPUT_DIR / "linear_model_historical_baseline_delta_summary.csv"
TOP_ERRORS_OUTPUT = OUTPUT_DIR / "linear_model_top_errors.csv"
ERROR_BY_YEAR_OUTPUT = OUTPUT_DIR / "linear_model_error_by_year_summary.csv"
ERROR_BY_TARGET_QUANTILE_OUTPUT = OUTPUT_DIR / "linear_model_error_by_target_quantile_summary.csv"
MISSINGNESS_SENSITIVITY_OUTPUT = OUTPUT_DIR / "linear_model_missingness_sensitivity.csv"
MISSINGNESS_PATTERN_SUMMARY_OUTPUT = OUTPUT_DIR / "linear_model_missingness_pattern_summary.csv"
MISSINGNESS_PATTERN_COUNTRY_DETAIL_OUTPUT = OUTPUT_DIR / "linear_model_missingness_pattern_country_detail.csv"
MISSINGNESS_INDICATOR_PLAN_OUTPUT = OUTPUT_DIR / "linear_model_missingness_indicator_plan.csv"
PERSISTENCE_AUGMENTED_COMPARISON_OUTPUT = OUTPUT_DIR / "linear_model_persistence_augmented_comparison.csv"
PERSISTENCE_AUGMENTED_TEST_METRICS_OUTPUT = OUTPUT_DIR / "linear_model_persistence_augmented_test_metrics.csv"
PERSISTENCE_AUGMENTED_COEFFICIENTS_OUTPUT = OUTPUT_DIR / "linear_model_persistence_augmented_coefficients.csv"
ROLLING_ORIGIN_SUMMARY_OUTPUT = OUTPUT_DIR / "linear_model_rolling_origin_summary.csv"
ROLLING_ORIGIN_PREDICTIONS_OUTPUT = OUTPUT_DIR / "linear_model_rolling_origin_predictions.csv"
ROLLING_ORIGIN_VALIDATION_METRICS_OUTPUT = OUTPUT_DIR / "linear_model_rolling_origin_validation_metrics.csv"
ROLLING_ORIGIN_TEST_METRICS_OUTPUT = OUTPUT_DIR / "linear_model_rolling_origin_test_metrics.csv"
ROBUSTNESS_SUMMARY_OUTPUT = OUTPUT_DIR / "linear_model_robustness_summary.csv"
ROBUSTNESS_SAMPLE_SUMMARY_OUTPUT = OUTPUT_DIR / "linear_model_robustness_sample_summary.csv"
ROBUSTNESS_VALIDATION_METRICS_OUTPUT = OUTPUT_DIR / "linear_model_robustness_validation_metrics.csv"
ROBUSTNESS_TEST_METRICS_OUTPUT = OUTPUT_DIR / "linear_model_robustness_test_metrics.csv"
ROBUSTNESS_PREDICTIONS_OUTPUT = OUTPUT_DIR / "linear_model_robustness_predictions.csv"
ROBUSTNESS_COEFFICIENTS_OUTPUT = OUTPUT_DIR / "linear_model_robustness_coefficients.csv"
ROBUSTNESS_HISTORICAL_BASELINES_OUTPUT = OUTPUT_DIR / "linear_model_robustness_historical_baselines.csv"
SKEW_TRANSFORM_PLAN_OUTPUT = OUTPUT_DIR / "linear_model_skew_transform_plan.csv"

# --- Tree model outputs ---
TREE_OUTPUT_DIR = ROOT_DIR / "3_models" / "outputs" / "tree"
TREE_VALIDATION_METRICS_OUTPUT = TREE_OUTPUT_DIR / "tree_model_validation_metrics.csv"
TREE_TEST_METRICS_OUTPUT = TREE_OUTPUT_DIR / "tree_model_test_metrics.csv"
TREE_PREDICTIONS_OUTPUT = TREE_OUTPUT_DIR / "tree_model_predictions.csv"
TREE_IMPORTANCE_OUTPUT = TREE_OUTPUT_DIR / "tree_model_feature_importance.csv"
TREE_PARTIAL_DEPENDENCE_OUTPUT = TREE_OUTPUT_DIR / "tree_model_partial_dependence.csv"
TREE_SAMPLE_SUMMARY_OUTPUT = TREE_OUTPUT_DIR / "tree_model_sample_summary.csv"
TREE_HISTORICAL_BASELINES_OUTPUT = TREE_OUTPUT_DIR / "tree_model_historical_baselines.csv"
TREE_HISTORICAL_DELTA_OUTPUT = TREE_OUTPUT_DIR / "tree_model_historical_baseline_delta_summary.csv"
TREE_RUN_SUMMARY_OUTPUT = TREE_OUTPUT_DIR / "tree_model_run_summary.md"
TREE_FIGURE_INDEX_OUTPUT = TREE_OUTPUT_DIR / "tree_model_figure_index.csv"
TREE_FIGURES_DIR = ROOT_DIR / "4_analysis" / "figures" / "tree_modeling"

# Tree extension outputs: mechanism submodels, same-sample nested comparison,
# and the robustness pack (lag1 timing + per-million target).
TREE_PANEL_TEST_METRICS_OUTPUT = TREE_OUTPUT_DIR / "tree_model_panel_test_metrics.csv"
TREE_PANEL_VALIDATION_METRICS_OUTPUT = TREE_OUTPUT_DIR / "tree_model_panel_validation_metrics.csv"
TREE_PANEL_IMPORTANCE_OUTPUT = TREE_OUTPUT_DIR / "tree_model_panel_feature_importance.csv"
TREE_NESTED_COMPARISON_OUTPUT = TREE_OUTPUT_DIR / "tree_model_nested_comparison.csv"
TREE_NESTED_TEST_METRICS_OUTPUT = TREE_OUTPUT_DIR / "tree_model_nested_test_metrics.csv"
TREE_NESTED_IMPORTANCE_OUTPUT = TREE_OUTPUT_DIR / "tree_model_nested_feature_importance.csv"
TREE_ROBUSTNESS_SUMMARY_OUTPUT = TREE_OUTPUT_DIR / "tree_model_robustness_summary.csv"
TREE_ROBUSTNESS_TEST_METRICS_OUTPUT = TREE_OUTPUT_DIR / "tree_model_robustness_test_metrics.csv"
TREE_ROBUSTNESS_HISTORICAL_BASELINES_OUTPUT = (
    TREE_OUTPUT_DIR / "tree_model_robustness_historical_baselines.csv"
)
