from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from model_config import (  # noqa: E402
    COEFFICIENTS_OUTPUT,
    CORRELATION_ALIGNMENT_OUTPUT,
    ERROR_BY_TARGET_QUANTILE_OUTPUT,
    ERROR_BY_YEAR_OUTPUT,
    FEATURE_PEARSON_CORRELATION_OUTPUT,
    FEATURE_SPEARMAN_CORRELATION_OUTPUT,
    FIGURE_INDEX_OUTPUT,
    FIGURES_DIR,
    HISTORICAL_BASELINE_DELTA_OUTPUT,
    HISTORICAL_BASELINES_OUTPUT,
    MISSINGNESS_INDICATOR_PLAN_OUTPUT,
    MISSINGNESS_SENSITIVITY_OUTPUT,
    MISSINGNESS_PATTERN_COUNTRY_DETAIL_OUTPUT,
    MISSINGNESS_PATTERN_SUMMARY_OUTPUT,
    NESTED_COEFFICIENTS_OUTPUT,
    NESTED_COMPARISON_OUTPUT,
    NESTED_PREDICTIONS_OUTPUT,
    NESTED_SAMPLE_SUMMARY_OUTPUT,
    NESTED_TEST_METRICS_OUTPUT,
    NESTED_VALIDATION_METRICS_OUTPUT,
    OUTPUT_DIR,
    PANEL_COEFFICIENTS_OUTPUT,
    PANEL_COMPARISON_OUTPUT,
    PANEL_CONFIGS,
    PANEL_PREDICTIONS_OUTPUT,
    PANEL_SAMPLE_SUMMARY_OUTPUT,
    PANEL_TEST_METRICS_OUTPUT,
    PANEL_VALIDATION_METRICS_OUTPUT,
    PERSISTENCE_AUGMENTED_COEFFICIENTS_OUTPUT,
    PERSISTENCE_AUGMENTED_COMPARISON_OUTPUT,
    PERSISTENCE_AUGMENTED_TEST_METRICS_OUTPUT,
    PREDICTIONS_OUTPUT,
    PRIMARY_LAG_SUFFIX,
    PRIMARY_PANEL_PATH,
    PRIMARY_TARGET,
    ROLLING_ORIGIN_PREDICTIONS_OUTPUT,
    ROLLING_ORIGIN_SUMMARY_OUTPUT,
    ROLLING_ORIGIN_TEST_METRICS_OUTPUT,
    ROLLING_ORIGIN_VALIDATION_METRICS_OUTPUT,
    ROBUSTNESS_COEFFICIENTS_OUTPUT,
    ROBUSTNESS_EXPERIMENT_CONFIGS,
    ROBUSTNESS_HISTORICAL_BASELINES_OUTPUT,
    ROBUSTNESS_PREDICTIONS_OUTPUT,
    ROBUSTNESS_SAMPLE_SUMMARY_OUTPUT,
    ROBUSTNESS_SUMMARY_OUTPUT,
    ROBUSTNESS_TEST_METRICS_OUTPUT,
    ROBUSTNESS_VALIDATION_METRICS_OUTPUT,
    ROOT_DIR,
    RUN_SUMMARY_OUTPUT,
    SAMPLE_SUMMARY_OUTPUT,
    SKEW_TRANSFORM_EXPERIMENT_CONFIG,
    SKEW_TRANSFORM_METHODS,
    SKEW_TRANSFORM_PLAN_OUTPUT,
    SPECIFICATION_REGISTRY_OUTPUT,
    TEST_METRICS_OUTPUT,
    TARGET_CORRELATIONS_OUTPUT,
    TOP_ERRORS_OUTPUT,
    TOP_CORRELATED_PAIRS_OUTPUT,
    TRAIN_SHARE,
    TREE_FIGURE_INDEX_OUTPUT,
    TREE_FIGURES_DIR,
    TREE_HISTORICAL_BASELINES_OUTPUT,
    TREE_HISTORICAL_DELTA_OUTPUT,
    TREE_IMPORTANCE_OUTPUT,
    TREE_NESTED_COMPARISON_OUTPUT,
    TREE_NESTED_IMPORTANCE_OUTPUT,
    TREE_NESTED_TEST_METRICS_OUTPUT,
    TREE_OUTPUT_DIR,
    TREE_PANEL_IMPORTANCE_OUTPUT,
    TREE_PANEL_TEST_METRICS_OUTPUT,
    TREE_PANEL_VALIDATION_METRICS_OUTPUT,
    TREE_PARTIAL_DEPENDENCE_OUTPUT,
    TREE_PREDICTIONS_OUTPUT,
    TREE_ROBUSTNESS_HISTORICAL_BASELINES_OUTPUT,
    TREE_ROBUSTNESS_SUMMARY_OUTPUT,
    TREE_ROBUSTNESS_TEST_METRICS_OUTPUT,
    TREE_RUN_SUMMARY_OUTPUT,
    TREE_SAMPLE_SUMMARY_OUTPUT,
    TREE_TEST_METRICS_OUTPUT,
    TREE_VALIDATION_METRICS_OUTPUT,
    VALIDATION_METRICS_OUTPUT,
    VALIDATION_SHARE,
)
from model_diagnostics import build_correlation_diagnostics, build_missingness_pattern_diagnostics  # noqa: E402
from model_evaluation import (  # noqa: E402
    build_error_decomposition_tables,
    build_historical_baseline_delta_summary,
    build_historical_baseline_comparison,
    build_top_prediction_errors,
    write_markdown_summary,
)
from model_experiments import PanelSpec, combine_experiment_tables, run_panel_linear_experiment  # noqa: E402
from model_experiments import (  # noqa: E402
    build_block_safe_target_history_feature,
    build_missingness_indicator_panel,
    build_nested_comparison_table,
    build_nested_submodel_panel,
    build_persistence_augmented_comparison_table,
    build_robustness_summary_table,
    build_skew_transformed_panel,
    run_panel_linear_experiment_from_panel,
    run_panel_tree_experiment,
    run_rolling_origin_linear_evaluation,
)
from model_experiments import _run_tree_experiment_from_panel  # noqa: E402
from model_visualization import (  # noqa: E402
    build_partial_dependence_table,
    make_correlation_diagnostic_figures,
    make_linear_model_figures,
    make_missingness_pattern_figures,
    make_model_comparison_figures,
    make_nested_comparison_figures,
    make_review_diagnostic_figures,
    make_robustness_figures,
    make_tree_model_figures,
)


def run_linear_modeling() -> dict[str, object]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_manifest = build_output_manifest()

    panel_specs = [PanelSpec(**config) for config in PANEL_CONFIGS]
    experiments = [
        run_panel_linear_experiment(
            spec,
            random_state=42,
            train_share=TRAIN_SHARE,
            validation_share=VALIDATION_SHARE,
        )
        for spec in panel_specs
    ]
    experiments_by_id = {experiment["panel_id"]: experiment for experiment in experiments}
    main_experiment = experiments_by_id["main"]
    combined_tables = combine_experiment_tables(experiments)
    nested_experiments = _run_nested_experiments(experiments_by_id)
    nested_tables = combine_experiment_tables(nested_experiments)
    nested_comparison = build_nested_comparison_table(nested_experiments)
    robustness_experiments, skew_transform_plan = _run_robustness_experiments(main_experiment)
    robustness_tables = combine_experiment_tables(robustness_experiments)
    robustness_historical_by_id, robustness_historical_baselines = _build_robustness_historical_baselines(
        robustness_experiments
    )
    robustness_summary = build_robustness_summary_table(
        robustness_experiments,
        robustness_historical_by_id,
    )
    specification_registry = _build_specification_registry()

    sample_summary = main_experiment["sample_summary"]
    validation_metrics = main_experiment["validation_metrics"]
    test_metrics = main_experiment["test_metrics"]
    predictions = main_experiment["predictions"]
    coefficients = main_experiment["coefficients"]
    feature_columns = main_experiment["feature_columns"]
    best_model = main_experiment["best_model"]
    persistence_augmented_experiment = _run_persistence_augmented_experiment(main_experiment)
    missingness_pattern_summary, missingness_pattern_country_detail = build_missingness_pattern_diagnostics(
        panel=main_experiment["panel"],
        feature_columns=feature_columns,
    )

    sample_summary.to_csv(SAMPLE_SUMMARY_OUTPUT, index=False)
    specification_registry.to_csv(SPECIFICATION_REGISTRY_OUTPUT, index=False)
    validation_metrics.to_csv(VALIDATION_METRICS_OUTPUT, index=False)
    test_metrics.to_csv(TEST_METRICS_OUTPUT, index=False)
    predictions.to_csv(PREDICTIONS_OUTPUT, index=False)
    coefficients.to_csv(COEFFICIENTS_OUTPUT, index=False)
    combined_tables["sample_summary"].to_csv(PANEL_SAMPLE_SUMMARY_OUTPUT, index=False)
    combined_tables["validation_metrics"].to_csv(PANEL_VALIDATION_METRICS_OUTPUT, index=False)
    combined_tables["test_metrics"].to_csv(PANEL_TEST_METRICS_OUTPUT, index=False)
    combined_tables["predictions"].to_csv(PANEL_PREDICTIONS_OUTPUT, index=False)
    combined_tables["coefficients"].to_csv(PANEL_COEFFICIENTS_OUTPUT, index=False)
    panel_comparison = combined_tables["panel_comparison"].copy()
    panel_comparison["comparison_scope"] = "own_sample_not_direct_ranking"
    panel_comparison.to_csv(PANEL_COMPARISON_OUTPUT, index=False)
    historical_baselines = build_historical_baseline_comparison(
        split=main_experiment["split"],
        target_column=PRIMARY_TARGET,
        model_predictions=predictions,
        model_name=best_model,
    )
    historical_delta_summary = build_historical_baseline_delta_summary(historical_baselines)
    persistence_augmented_comparison = build_persistence_augmented_comparison_table(
        feature_experiment=main_experiment,
        augmented_experiment=persistence_augmented_experiment,
        historical_baselines=historical_baselines,
    )
    top_errors = build_top_prediction_errors(predictions, target_column=PRIMARY_TARGET)
    error_decomposition = build_error_decomposition_tables(predictions, target_column=PRIMARY_TARGET)
    missingness_sensitivity, missingness_indicator_plan = _run_missingness_sensitivity(main_experiment)
    rolling_origin = run_rolling_origin_linear_evaluation(
        PanelSpec(
            panel_id="main",
            panel_label="Main v2 model",
            panel_path=None,
            target_column=PRIMARY_TARGET,
            lag_suffix="lag1_3_mean",
            role="rolling_origin_confirmatory",
            comparison_group="main",
            feature_set_role="feature_only",
        ),
        panel=main_experiment["panel"],
        feature_columns=feature_columns,
        random_state=42,
    )
    historical_baselines.to_csv(HISTORICAL_BASELINES_OUTPUT, index=False)
    historical_delta_summary.to_csv(HISTORICAL_BASELINE_DELTA_OUTPUT, index=False)
    persistence_augmented_comparison.to_csv(PERSISTENCE_AUGMENTED_COMPARISON_OUTPUT, index=False)
    persistence_augmented_experiment["test_metrics"].to_csv(PERSISTENCE_AUGMENTED_TEST_METRICS_OUTPUT, index=False)
    persistence_augmented_experiment["coefficients"].to_csv(PERSISTENCE_AUGMENTED_COEFFICIENTS_OUTPUT, index=False)
    top_errors.to_csv(TOP_ERRORS_OUTPUT, index=False)
    error_decomposition["by_year"].to_csv(ERROR_BY_YEAR_OUTPUT, index=False)
    error_decomposition["by_target_quantile"].to_csv(ERROR_BY_TARGET_QUANTILE_OUTPUT, index=False)
    missingness_sensitivity.to_csv(MISSINGNESS_SENSITIVITY_OUTPUT, index=False)
    missingness_indicator_plan.to_csv(MISSINGNESS_INDICATOR_PLAN_OUTPUT, index=False)
    rolling_origin["fold_summary"].to_csv(ROLLING_ORIGIN_SUMMARY_OUTPUT, index=False)
    rolling_origin["fold_predictions"].to_csv(ROLLING_ORIGIN_PREDICTIONS_OUTPUT, index=False)
    rolling_origin["validation_metrics"].to_csv(ROLLING_ORIGIN_VALIDATION_METRICS_OUTPUT, index=False)
    rolling_origin["test_metrics"].to_csv(ROLLING_ORIGIN_TEST_METRICS_OUTPUT, index=False)
    missingness_pattern_summary.to_csv(MISSINGNESS_PATTERN_SUMMARY_OUTPUT, index=False)
    missingness_pattern_country_detail.to_csv(MISSINGNESS_PATTERN_COUNTRY_DETAIL_OUTPUT, index=False)
    robustness_summary.to_csv(ROBUSTNESS_SUMMARY_OUTPUT, index=False)
    robustness_tables["sample_summary"].to_csv(ROBUSTNESS_SAMPLE_SUMMARY_OUTPUT, index=False)
    robustness_tables["validation_metrics"].to_csv(ROBUSTNESS_VALIDATION_METRICS_OUTPUT, index=False)
    robustness_tables["test_metrics"].to_csv(ROBUSTNESS_TEST_METRICS_OUTPUT, index=False)
    robustness_tables["predictions"].to_csv(ROBUSTNESS_PREDICTIONS_OUTPUT, index=False)
    robustness_tables["coefficients"].to_csv(ROBUSTNESS_COEFFICIENTS_OUTPUT, index=False)
    robustness_historical_baselines.to_csv(ROBUSTNESS_HISTORICAL_BASELINES_OUTPUT, index=False)
    skew_transform_plan.to_csv(SKEW_TRANSFORM_PLAN_OUTPUT, index=False)
    nested_tables["sample_summary"].to_csv(NESTED_SAMPLE_SUMMARY_OUTPUT, index=False)
    nested_tables["validation_metrics"].to_csv(NESTED_VALIDATION_METRICS_OUTPUT, index=False)
    nested_tables["test_metrics"].to_csv(NESTED_TEST_METRICS_OUTPUT, index=False)
    nested_tables["predictions"].to_csv(NESTED_PREDICTIONS_OUTPUT, index=False)
    nested_tables["coefficients"].to_csv(NESTED_COEFFICIENTS_OUTPUT, index=False)
    nested_comparison.to_csv(NESTED_COMPARISON_OUTPUT, index=False)

    correlation_diagnostics = build_correlation_diagnostics(
        split=main_experiment["split"],
        feature_columns=feature_columns,
        target_column=PRIMARY_TARGET,
        coefficients=coefficients,
        panel_id=main_experiment["panel_id"],
        panel_label=main_experiment["panel_label"],
        fitted_model=main_experiment["fitted_model"],
    )
    correlation_diagnostics["spearman_feature_correlations"].to_csv(FEATURE_SPEARMAN_CORRELATION_OUTPUT)
    correlation_diagnostics["pearson_feature_correlations"].to_csv(FEATURE_PEARSON_CORRELATION_OUTPUT)
    correlation_diagnostics["top_correlated_pairs"].to_csv(TOP_CORRELATED_PAIRS_OUTPUT, index=False)
    correlation_diagnostics["target_correlations"].to_csv(TARGET_CORRELATIONS_OUTPUT, index=False)
    correlation_diagnostics["coefficient_correlation_alignment"].to_csv(
        CORRELATION_ALIGNMENT_OUTPUT,
        index=False,
    )

    figure_paths = make_linear_model_figures(
        panel=main_experiment["panel"],
        feature_columns=feature_columns,
        target_column=PRIMARY_TARGET,
        sample_summary=sample_summary,
        validation_metrics=validation_metrics,
        predictions=predictions,
        coefficients=coefficients,
        figures_dir=FIGURES_DIR,
    )
    figure_paths.update(
        make_model_comparison_figures(
            sample_summary=combined_tables["sample_summary"],
            test_metrics=combined_tables["test_metrics"],
            validation_metrics=combined_tables["validation_metrics"],
            coefficients=combined_tables["coefficients"],
            figures_dir=FIGURES_DIR,
        )
    )
    figure_paths.update(
        make_nested_comparison_figures(
            nested_comparison=nested_comparison,
            figures_dir=FIGURES_DIR,
        )
    )
    figure_paths.update(
        make_correlation_diagnostic_figures(
            spearman_feature_correlations=correlation_diagnostics["spearman_feature_correlations"],
            target_correlations=correlation_diagnostics["target_correlations"],
            coefficient_alignment=correlation_diagnostics["coefficient_correlation_alignment"],
            figures_dir=FIGURES_DIR,
        )
    )
    figure_paths.update(
        make_review_diagnostic_figures(
            historical_baselines=historical_baselines,
            top_errors=top_errors.head(10),
            missingness_sensitivity=missingness_sensitivity,
            figures_dir=FIGURES_DIR,
        )
    )
    figure_paths.update(
        make_missingness_pattern_figures(
            missingness_pattern_summary=missingness_pattern_summary,
            figures_dir=FIGURES_DIR,
        )
    )
    figure_paths.update(
        make_robustness_figures(
            robustness_summary=robustness_summary,
            figures_dir=FIGURES_DIR,
        )
    )
    pd.DataFrame(_figure_index_rows(figure_paths)).to_csv(FIGURE_INDEX_OUTPUT, index=False)
    write_markdown_summary(
        RUN_SUMMARY_OUTPUT,
        best_model=best_model,
        split_years=main_experiment["split_years"],
        validation_metrics=validation_metrics,
        test_metrics=test_metrics,
    )
    _append_submodel_summary(
        RUN_SUMMARY_OUTPUT,
        panel_comparison,
        nested_comparison,
        correlation_diagnostics,
        historical_baselines,
        historical_delta_summary,
        persistence_augmented_comparison,
        missingness_pattern_summary,
        missingness_sensitivity,
        error_decomposition["by_year"],
        error_decomposition["by_target_quantile"],
        rolling_origin["fold_summary"],
        robustness_summary,
    )

    return {
        "best_model": best_model,
        "feature_columns": feature_columns,
        "sample_summary": sample_summary,
        "specification_registry": specification_registry,
        "validation_metrics": validation_metrics,
        "test_metrics": test_metrics,
        "predictions": predictions,
        "coefficients": coefficients,
        "experiments": experiments_by_id,
        "panel_sample_summary": combined_tables["sample_summary"],
        "panel_validation_metrics": combined_tables["validation_metrics"],
        "panel_test_metrics": combined_tables["test_metrics"],
        "panel_predictions": combined_tables["predictions"],
        "panel_coefficients": combined_tables["coefficients"],
        "panel_comparison": panel_comparison,
        "historical_baselines": historical_baselines,
        "historical_delta_summary": historical_delta_summary,
        "history_delta_summary": historical_delta_summary,
        "persistence_augmented_comparison": persistence_augmented_comparison,
        "persistence_augmented_test_metrics": persistence_augmented_experiment["test_metrics"],
        "persistence_augmented_coefficients": persistence_augmented_experiment["coefficients"],
        "top_errors": top_errors,
        "error_by_year": error_decomposition["by_year"],
        "error_by_target_quantile": error_decomposition["by_target_quantile"],
        "missingness_sensitivity": missingness_sensitivity,
        "missingness_indicator_plan": missingness_indicator_plan,
        "rolling_origin_summary": rolling_origin["fold_summary"],
        "rolling_origin_predictions": rolling_origin["fold_predictions"],
        "rolling_origin_validation_metrics": rolling_origin["validation_metrics"],
        "rolling_origin_test_metrics": rolling_origin["test_metrics"],
        "missingness_pattern_summary": missingness_pattern_summary,
        "missingness_pattern_country_detail": missingness_pattern_country_detail,
        "robustness_summary": robustness_summary,
        "robustness_sample_summary": robustness_tables["sample_summary"],
        "robustness_validation_metrics": robustness_tables["validation_metrics"],
        "robustness_test_metrics": robustness_tables["test_metrics"],
        "robustness_predictions": robustness_tables["predictions"],
        "robustness_coefficients": robustness_tables["coefficients"],
        "robustness_historical_baselines": robustness_historical_baselines,
        "skew_transform_plan": skew_transform_plan,
        "nested_sample_summary": nested_tables["sample_summary"],
        "nested_validation_metrics": nested_tables["validation_metrics"],
        "nested_test_metrics": nested_tables["test_metrics"],
        "nested_predictions": nested_tables["predictions"],
        "nested_coefficients": nested_tables["coefficients"],
        "nested_comparison": nested_comparison,
        "correlation_diagnostics": correlation_diagnostics,
        "outputs": output_manifest,
        "figure_paths": figure_paths,
    }


def build_output_manifest() -> dict[str, Path]:
    return {
        "sample_summary": SAMPLE_SUMMARY_OUTPUT,
        "specification_registry": SPECIFICATION_REGISTRY_OUTPUT,
        "validation_metrics": VALIDATION_METRICS_OUTPUT,
        "test_metrics": TEST_METRICS_OUTPUT,
        "predictions": PREDICTIONS_OUTPUT,
        "coefficients": COEFFICIENTS_OUTPUT,
        "panel_sample_summary": PANEL_SAMPLE_SUMMARY_OUTPUT,
        "panel_validation_metrics": PANEL_VALIDATION_METRICS_OUTPUT,
        "panel_test_metrics": PANEL_TEST_METRICS_OUTPUT,
        "panel_predictions": PANEL_PREDICTIONS_OUTPUT,
        "panel_coefficients": PANEL_COEFFICIENTS_OUTPUT,
        "panel_comparison": PANEL_COMPARISON_OUTPUT,
        "historical_baselines": HISTORICAL_BASELINES_OUTPUT,
        "historical_baseline_delta_summary": HISTORICAL_BASELINE_DELTA_OUTPUT,
        "persistence_augmented_comparison": PERSISTENCE_AUGMENTED_COMPARISON_OUTPUT,
        "persistence_augmented_test_metrics": PERSISTENCE_AUGMENTED_TEST_METRICS_OUTPUT,
        "persistence_augmented_coefficients": PERSISTENCE_AUGMENTED_COEFFICIENTS_OUTPUT,
        "top_errors": TOP_ERRORS_OUTPUT,
        "error_by_year": ERROR_BY_YEAR_OUTPUT,
        "error_by_target_quantile": ERROR_BY_TARGET_QUANTILE_OUTPUT,
        "missingness_sensitivity": MISSINGNESS_SENSITIVITY_OUTPUT,
        "missingness_indicator_plan": MISSINGNESS_INDICATOR_PLAN_OUTPUT,
        "missingness_pattern_summary": MISSINGNESS_PATTERN_SUMMARY_OUTPUT,
        "missingness_pattern_country_detail": MISSINGNESS_PATTERN_COUNTRY_DETAIL_OUTPUT,
        "rolling_origin_summary": ROLLING_ORIGIN_SUMMARY_OUTPUT,
        "rolling_origin_predictions": ROLLING_ORIGIN_PREDICTIONS_OUTPUT,
        "rolling_origin_validation_metrics": ROLLING_ORIGIN_VALIDATION_METRICS_OUTPUT,
        "rolling_origin_test_metrics": ROLLING_ORIGIN_TEST_METRICS_OUTPUT,
        "robustness_summary": ROBUSTNESS_SUMMARY_OUTPUT,
        "robustness_sample_summary": ROBUSTNESS_SAMPLE_SUMMARY_OUTPUT,
        "robustness_validation_metrics": ROBUSTNESS_VALIDATION_METRICS_OUTPUT,
        "robustness_test_metrics": ROBUSTNESS_TEST_METRICS_OUTPUT,
        "robustness_predictions": ROBUSTNESS_PREDICTIONS_OUTPUT,
        "robustness_coefficients": ROBUSTNESS_COEFFICIENTS_OUTPUT,
        "robustness_historical_baselines": ROBUSTNESS_HISTORICAL_BASELINES_OUTPUT,
        "skew_transform_plan": SKEW_TRANSFORM_PLAN_OUTPUT,
        "nested_sample_summary": NESTED_SAMPLE_SUMMARY_OUTPUT,
        "nested_validation_metrics": NESTED_VALIDATION_METRICS_OUTPUT,
        "nested_test_metrics": NESTED_TEST_METRICS_OUTPUT,
        "nested_predictions": NESTED_PREDICTIONS_OUTPUT,
        "nested_coefficients": NESTED_COEFFICIENTS_OUTPUT,
        "nested_comparison": NESTED_COMPARISON_OUTPUT,
        "feature_spearman_correlations": FEATURE_SPEARMAN_CORRELATION_OUTPUT,
        "feature_pearson_correlations": FEATURE_PEARSON_CORRELATION_OUTPUT,
        "top_correlated_pairs": TOP_CORRELATED_PAIRS_OUTPUT,
        "target_correlations": TARGET_CORRELATIONS_OUTPUT,
        "correlation_alignment": CORRELATION_ALIGNMENT_OUTPUT,
        "run_summary": RUN_SUMMARY_OUTPUT,
        "figure_index": FIGURE_INDEX_OUTPUT,
    }


def _run_persistence_augmented_experiment(main_experiment: dict[str, object]) -> dict[str, object]:
    history_feature = "target_history_preblock"
    augmented_panel = build_block_safe_target_history_feature(
        panel=main_experiment["panel"],
        split=main_experiment["split"],
        target_column=PRIMARY_TARGET,
        feature_name=history_feature,
    )
    spec = PanelSpec(
        panel_id="main_persistence_augmented",
        panel_label="Main predictors plus block-safe target history",
        panel_path=None,
        target_column=PRIMARY_TARGET,
        lag_suffix="lag1_3_mean",
        role="persistence_augmented",
        comparison_group="main",
        feature_set_role="main_plus_block_safe_target_history",
    )
    return run_panel_linear_experiment_from_panel(
        spec,
        augmented_panel,
        feature_columns=list(main_experiment["feature_columns"]) + [history_feature],
        random_state=42,
        train_share=TRAIN_SHARE,
        validation_share=VALIDATION_SHARE,
        split_years=main_experiment["split_years"],
    )


def _run_nested_experiments(experiments_by_id: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    main_experiment = experiments_by_id["main"]
    main_panel = main_experiment["panel"]
    main_features = list(main_experiment["feature_columns"])
    nested_experiments = []
    for sub_id in ["suba", "subb", "subc"]:
        sub_experiment = experiments_by_id[sub_id]
        sub_features = list(sub_experiment["feature_columns"])
        nested_panel = build_nested_submodel_panel(
            main_panel=main_panel,
            sub_panel=sub_experiment["panel"],
            main_feature_columns=main_features,
            submodel_feature_columns=sub_features,
            target_column=PRIMARY_TARGET,
        )
        baseline_spec = PanelSpec(
            panel_id=f"main_on_{sub_id}",
            panel_label=f"Main controls on {sub_id.upper()} sample",
            panel_path=None,
            target_column=PRIMARY_TARGET,
            lag_suffix="lag1_3_mean",
            role="nested_baseline",
            comparison_group=sub_id,
            feature_set_role="main_controls",
        )
        augmented_spec = PanelSpec(
            panel_id=f"main_plus_{sub_id}",
            panel_label=f"Main controls plus {sub_id.upper()} predictors",
            panel_path=None,
            target_column=PRIMARY_TARGET,
            lag_suffix="lag1_3_mean",
            role="nested_augmented",
            comparison_group=sub_id,
            feature_set_role="main_plus_submodel",
        )
        nested_experiments.append(
            run_panel_linear_experiment_from_panel(
                baseline_spec,
                nested_panel,
                feature_columns=main_features,
                random_state=42,
                train_share=TRAIN_SHARE,
                validation_share=VALIDATION_SHARE,
            )
        )
        nested_experiments.append(
            run_panel_linear_experiment_from_panel(
                augmented_spec,
                nested_panel,
                feature_columns=main_features + sub_features,
                random_state=42,
                train_share=TRAIN_SHARE,
                validation_share=VALIDATION_SHARE,
            )
        )
    return nested_experiments


def _build_specification_registry() -> pd.DataFrame:
    rows = []
    model_grid = (
        "OLS; Ridge alpha=[0.1,1,10]; Lasso alpha=[0.001,0.01,0.1,1]; "
        "ElasticNet alpha=[0.001,0.01,0.1,1], l1_ratio=[0.2,0.5,0.8]"
    )
    scaling_note = (
        "predictors are median-imputed and standardized inside each pipeline; "
        "target is not standardized, so regularization alpha is target-scale dependent"
    )
    for config in PANEL_CONFIGS:
        rows.append(
            {
                "spec_id": config["panel_id"],
                "target": config["target_column"],
                "lag_scheme": config["lag_suffix"],
                "panel": _project_relative_path(config["panel_path"]),
                "sample_rule": "chronological_80_10_10_by_distinct_target_year",
                "imputation_rule": "no_imputation_panel_with_train_fold_median_imputation_inside_sklearn_pipeline",
                "model_family": "OLS_Ridge_Lasso_ElasticNet",
                "model_grid": model_grid,
                "scaling_note": scaling_note,
                "selection_metric": "validation_mae",
                "primary_or_robustness": config["role"],
                "design_reason": "active_v2_panel_or_mechanism_submodel",
            }
        )
    for config in ROBUSTNESS_EXPERIMENT_CONFIGS:
        rows.append(
            {
                "spec_id": config["panel_id"],
                "target": config["target_column"],
                "lag_scheme": config["lag_suffix"],
                "panel": _project_relative_path(config["panel_path"]),
                "sample_rule": "chronological_80_10_10_by_distinct_target_year",
                "imputation_rule": "no_imputation_panel_with_train_fold_median_imputation_inside_sklearn_pipeline",
                "model_family": "OLS_Ridge_Lasso_ElasticNet",
                "model_grid": model_grid,
                "scaling_note": scaling_note,
                "selection_metric": "validation_mae",
                "primary_or_robustness": config["role"],
                "design_reason": "lag_timing_or_alternative_target_robustness",
            }
        )
    rows.append(
        {
            "spec_id": SKEW_TRANSFORM_EXPERIMENT_CONFIG["panel_id"],
            "target": SKEW_TRANSFORM_EXPERIMENT_CONFIG["target_column"],
            "lag_scheme": SKEW_TRANSFORM_EXPERIMENT_CONFIG["lag_suffix"],
            "panel": _project_relative_path(SKEW_TRANSFORM_EXPERIMENT_CONFIG["panel_path"]),
            "sample_rule": "chronological_80_10_10_by_distinct_target_year",
            "imputation_rule": (
                "deterministic_skew_transform_then_train_fold_median_imputation_inside_sklearn_pipeline"
            ),
            "model_family": "OLS_Ridge_Lasso_ElasticNet",
            "model_grid": model_grid,
            "scaling_note": scaling_note,
            "selection_metric": "validation_mae",
            "primary_or_robustness": SKEW_TRANSFORM_EXPERIMENT_CONFIG["role"],
            "design_reason": "skewed_predictor_scale_robustness_before_nonlinear_models",
        }
    )
    return pd.DataFrame(rows)


def _run_robustness_experiments(
    main_experiment: dict[str, object],
) -> tuple[list[dict[str, object]], pd.DataFrame]:
    experiments = []
    for config in ROBUSTNESS_EXPERIMENT_CONFIGS:
        spec = PanelSpec(**config)
        experiments.append(
            run_panel_linear_experiment(
                spec,
                random_state=42,
                train_share=TRAIN_SHARE,
                validation_share=VALIDATION_SHARE,
            )
        )
    skew_experiment, skew_transform_plan = _run_skew_transformed_robustness_experiment(main_experiment)
    experiments.append(skew_experiment)
    return experiments, skew_transform_plan


def _run_skew_transformed_robustness_experiment(
    main_experiment: dict[str, object],
) -> tuple[dict[str, object], pd.DataFrame]:
    transformed_panel, transformed_features, transform_plan = build_skew_transformed_panel(
        panel=main_experiment["panel"],
        feature_columns=list(main_experiment["feature_columns"]),
        transform_methods=SKEW_TRANSFORM_METHODS,
    )
    transform_plan.insert(0, "panel_id", SKEW_TRANSFORM_EXPERIMENT_CONFIG["panel_id"])
    transform_plan["rationale"] = transform_plan["transformation"].map(
        {
            "log1p": "positive right-skewed scale compressed before standardization",
            "asinh": "signed right-skewed scale compressed while retaining negative values",
            "identity": "kept on original scale before standardization because skew is limited or bounded",
        }
    )
    spec = PanelSpec(**SKEW_TRANSFORM_EXPERIMENT_CONFIG)
    experiment = run_panel_linear_experiment_from_panel(
        spec,
        transformed_panel,
        feature_columns=transformed_features,
        random_state=42,
        train_share=TRAIN_SHARE,
        validation_share=VALIDATION_SHARE,
        split_years=main_experiment["split_years"],
    )
    return experiment, transform_plan


def _build_robustness_historical_baselines(
    robustness_experiments: list[dict[str, object]],
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    by_id: dict[str, pd.DataFrame] = {}
    contextual_tables = []
    for experiment in robustness_experiments:
        baselines = build_historical_baseline_comparison(
            split=experiment["split"],
            target_column=str(experiment["target_column"]),
            model_predictions=experiment["predictions"],
            model_name=str(experiment["best_model"]),
        )
        by_id[str(experiment["panel_id"])] = baselines
        contextual = baselines.copy()
        contextual.insert(0, "lag_suffix", experiment["lag_suffix"])
        contextual.insert(0, "target_column", experiment["target_column"])
        contextual.insert(0, "robustness_label", experiment["panel_label"])
        contextual.insert(0, "robustness_id", experiment["panel_id"])
        contextual_tables.append(contextual)
    return by_id, pd.concat(contextual_tables, ignore_index=True)


def _run_missingness_sensitivity(main_experiment: dict[str, object]) -> tuple[pd.DataFrame, pd.DataFrame]:
    feature_columns = list(main_experiment["feature_columns"])
    primary_sample = main_experiment["sample_summary"]
    primary_all = primary_sample[primary_sample["split"].eq("all")].iloc[0]
    primary_test = main_experiment["test_metrics"].iloc[0]
    rows = [
        {
            "analysis": "primary_median_imputed_all_rows",
            "panel_id": main_experiment["panel_id"],
            "best_model": main_experiment["best_model"],
            "rows": int(primary_all["rows"]),
            "countries": int(primary_all["countries"]),
            "feature_columns": len(feature_columns),
            "test_rows": int(primary_test["n_test"]),
            "test_countries": int(primary_test["test_countries"]),
            "test_year_start": int(primary_test["test_year_start"]),
            "test_year_end": int(primary_test["test_year_end"]),
            "test_mae": float(primary_test["mae"]),
            "test_rmse": float(primary_test["rmse"]),
            "test_oos_r2_vs_train_mean": float(primary_test["oos_r2_vs_train_mean"]),
            "test_spearman": float(primary_test["spearman"]),
            "comparison_note": "Primary model uses all rows with train-fold median imputation.",
        }
    ]

    complete_panel = main_experiment["panel"].dropna(subset=feature_columns).reset_index(drop=True)
    complete_spec = PanelSpec(
        panel_id="main_complete_case",
        panel_label="Main v2 complete-case sensitivity",
        panel_path=None,
        target_column=PRIMARY_TARGET,
        lag_suffix="lag1_3_mean",
        role="missingness_sensitivity",
        comparison_group="main",
        feature_set_role="complete_case",
    )
    complete_result = run_panel_linear_experiment_from_panel(
        complete_spec,
        complete_panel,
        feature_columns=feature_columns,
        random_state=42,
        train_share=TRAIN_SHARE,
        validation_share=VALIDATION_SHARE,
        split_years=main_experiment["split_years"],
    )
    complete_all = complete_result["sample_summary"][complete_result["sample_summary"]["split"].eq("all")].iloc[0]
    complete_test = complete_result["test_metrics"].iloc[0]
    rows.append(
        {
            "analysis": "complete_case_refit",
            "panel_id": complete_result["panel_id"],
            "best_model": complete_result["best_model"],
            "rows": int(complete_all["rows"]),
            "countries": int(complete_all["countries"]),
            "feature_columns": len(feature_columns),
            "test_rows": int(complete_test["n_test"]),
            "test_countries": int(complete_test["test_countries"]),
            "test_year_start": int(complete_test["test_year_start"]),
            "test_year_end": int(complete_test["test_year_end"]),
            "test_mae": float(complete_test["mae"]),
            "test_rmse": float(complete_test["rmse"]),
            "test_oos_r2_vs_train_mean": float(complete_test["oos_r2_vs_train_mean"]),
            "test_spearman": float(complete_test["spearman"]),
            "comparison_note": (
                "Rows with any missing active predictor are dropped, then the model is rerun "
                "using the primary train/validation/test years."
            ),
        }
    )

    indicator_panel, indicator_features, indicator_plan = build_missingness_indicator_panel(
        panel=main_experiment["panel"],
        feature_columns=feature_columns,
    )
    indicator_spec = PanelSpec(
        panel_id="main_missingness_indicator",
        panel_label="Main v2 missingness-indicator sensitivity",
        panel_path=None,
        target_column=PRIMARY_TARGET,
        lag_suffix="lag1_3_mean",
        role="missingness_sensitivity",
        comparison_group="main",
        feature_set_role="missingness_indicators",
    )
    indicator_result = run_panel_linear_experiment_from_panel(
        indicator_spec,
        indicator_panel,
        feature_columns=indicator_features,
        random_state=42,
        train_share=TRAIN_SHARE,
        validation_share=VALIDATION_SHARE,
        split_years=main_experiment["split_years"],
    )
    indicator_all = indicator_result["sample_summary"][indicator_result["sample_summary"]["split"].eq("all")].iloc[0]
    indicator_test = indicator_result["test_metrics"].iloc[0]
    rows.append(
        {
            "analysis": "missingness_indicator_refit",
            "panel_id": indicator_result["panel_id"],
            "best_model": indicator_result["best_model"],
            "rows": int(indicator_all["rows"]),
            "countries": int(indicator_all["countries"]),
            "feature_columns": len(indicator_features),
            "test_rows": int(indicator_test["n_test"]),
            "test_countries": int(indicator_test["test_countries"]),
            "test_year_start": int(indicator_test["test_year_start"]),
            "test_year_end": int(indicator_test["test_year_end"]),
            "test_mae": float(indicator_test["mae"]),
            "test_rmse": float(indicator_test["rmse"]),
            "test_oos_r2_vs_train_mean": float(indicator_test["oos_r2_vs_train_mean"]),
            "test_spearman": float(indicator_test["spearman"]),
            "comparison_note": (
                "Adds one binary missingness indicator per active predictor while preserving "
                "the original train-fold median imputation pipeline."
            ),
        }
    )
    return pd.DataFrame(rows), indicator_plan


def _append_submodel_summary(
    output_path: Path,
    panel_comparison: pd.DataFrame,
    nested_comparison: pd.DataFrame,
    diagnostics: dict[str, object],
    historical_baselines: pd.DataFrame,
    historical_delta_summary: pd.DataFrame,
    persistence_augmented_comparison: pd.DataFrame,
    missingness_pattern_summary: pd.DataFrame,
    missingness_sensitivity: pd.DataFrame,
    error_by_year: pd.DataFrame,
    error_by_target_quantile: pd.DataFrame,
    rolling_origin_summary: pd.DataFrame,
    robustness_summary: pd.DataFrame,
) -> None:
    if nested_comparison["improves_primary_test_mae"].any():
        nested_interpretation = (
            "At least one submodel augmentation improves primary test MAE in the current run; "
            "validation direction and uncertainty checks are still needed before making a mechanism claim."
        )
    else:
        nested_interpretation = (
            "In the current run, none of the submodel augmentations improves primary test MAE; "
            "positive delta values mean the augmented feature set is worse on the primary metric."
        )
    lines = [
        "",
        "## Mechanism Submodel Comparison",
        "",
        "Submodel scores are own-sample diagnostics because the model panels have different",
        "country and year coverage. They should not be read as a direct ranking against the",
        "main model unless a separate common country-year sample is constructed.",
        "",
        _dataframe_to_markdown(
            panel_comparison[
                [
                    "panel_id",
                    "panel_label",
                    "best_model",
                    "rows",
                    "countries",
                    "test_year_start",
                    "test_year_end",
                    "test_mae",
                    "test_rmse",
                    "test_oos_r2_vs_train_mean",
                    "test_spearman",
                    "comparison_scope",
                ]
            ]
        ),
        "",
        "## Same-Sample Nested Submodel Tests",
        "",
        "Each nested comparison uses the same country-year rows for the main-controls",
        "baseline and the main-plus-submodel augmented model. This is the preferred",
        "incremental-value comparison for SubA, SubB, and SubC predictors.",
        "",
        _dataframe_to_markdown(
            nested_comparison[
                [
                    "comparison_group",
                    "baseline_label",
                    "augmented_label",
                    "rows",
                    "countries",
                    "baseline_validation_mae",
                    "augmented_validation_mae",
                    "delta_validation_mae_augmented_minus_baseline",
                    "test_year_start",
                    "test_year_end",
                    "baseline_test_mae",
                    "augmented_test_mae",
                    "delta_test_mae_augmented_minus_baseline",
                    "improves_primary_test_mae",
                    "comparison_scope",
                ]
            ]
        ),
        "",
        nested_interpretation,
        "",
        "## Historical Target Baselines",
        "",
        "These baselines use only target history available before the final test block. They",
        "are required because country-level patent shares are persistent over time.",
        "",
        _dataframe_to_markdown(
            historical_baselines[
                [
                    "model",
                    "prediction_rule",
                    "n_test",
                    "uses_test_labels",
                    "mae",
                    "rmse",
                    "oos_r2_vs_train_mean",
                    "spearman",
                ]
            ]
        ),
        "",
        "## Historical Baseline Delta Summary",
        "",
        "This table is the headline forecasting check. Positive delta MAE means the",
        "feature-only model is worse than a prediction-safe historical target baseline.",
        "",
        _dataframe_to_markdown(
            historical_delta_summary[
                [
                    "selected_model",
                    "baseline_model",
                    "selected_mae",
                    "baseline_mae",
                    "delta_mae_selected_minus_baseline",
                    "selected_beats_baseline",
                    "professor_interpretation",
                ]
            ]
        ),
        "",
        "## Persistence-Augmented Model",
        "",
        "The primary model remains feature-only so that the notebook can ask whether",
        "economic, energy, policy, and science predictors forecast environmental",
        "innovation beyond simple country persistence. The augmented comparison adds",
        "`target_history_preblock`, a block-safe target-history feature: validation",
        "years use only training-period target history, and test years use only",
        "train+validation target history.",
        "",
        _dataframe_to_markdown(
            persistence_augmented_comparison[
                [
                    "model_stage",
                    "model",
                    "includes_main_predictors",
                    "includes_target_history",
                    "validation_mae",
                    "test_year_start",
                    "test_year_end",
                    "test_mae",
                    "test_rmse",
                    "test_oos_r2_vs_train_mean",
                    "test_spearman",
                ]
            ]
        ),
        "",
        "## Missingness Pattern Diagnostics",
        "",
        "The feature-level missingness plot and tables separate late-start coverage,",
        "early-ending series, bounded coverage windows, intermittent gaps, and countries",
        "with no observed value for a predictor among target-observed model rows. Internal",
        "gaps take priority over bounded-window labels when both occur in a country-feature",
        "sequence. This matters because train-fold median imputation is a conservative",
        "baseline, but the interpretation differs when a source starts late versus when",
        "isolated observations are missing inside an otherwise covered time series.",
        "",
        _dataframe_to_markdown(
            missingness_pattern_summary[
                [
                    "feature",
                    "missing_share",
                    "complete_countries",
                    "late_start_countries",
                    "early_end_countries",
                    "bounded_coverage_window_countries",
                    "intermittent_gaps_countries",
                    "all_missing_countries",
                ]
            ]
        ),
        "",
        "## Missingness Sensitivity",
        "",
        "The primary panel preserves missing predictors and imputes inside the sklearn",
        "pipeline. The complete-case rerun drops rows with any missing active predictor,",
        "and the missingness-indicator rerun keeps all rows while adding one binary",
        "indicator per active predictor. Both reuse the primary train/validation/test",
        "years so that the final test block remains comparable.",
        "",
        _dataframe_to_markdown(
            missingness_sensitivity[
                [
                    "analysis",
                    "best_model",
                    "rows",
                    "countries",
                    "test_rows",
                    "test_mae",
                    "test_rmse",
                    "test_oos_r2_vs_train_mean",
                    "test_spearman",
                ]
            ]
        ),
        "",
        "## Error Decomposition",
        "",
        "These summaries show whether aggregate MAE hides concentrated errors in recent",
        "years or high-target country-years.",
        "",
        "By test year:",
        "",
        _dataframe_to_markdown(error_by_year),
        "",
        "By target quantile:",
        "",
        _dataframe_to_markdown(error_by_target_quantile),
        "",
        "## Confirmatory Rolling-Origin Check",
        "",
        "The rolling-origin table distributes held-out blocks through time. It is stronger",
        "confirmatory evidence than the first contiguous 80/10/10 checkpoint, while still",
        "keeping validation inside each pre-test window.",
        "",
        _dataframe_to_markdown(
            rolling_origin_summary[
                [
                    "fold_id",
                    "train_year_start",
                    "train_year_end",
                    "validation_year_start",
                    "validation_year_end",
                    "test_year_start",
                    "test_year_end",
                    "best_model",
                    "validation_mae",
                    "test_mae",
                    "best_historical_baseline_model",
                    "best_historical_baseline_mae",
                    "delta_mae_selected_minus_best_history",
                    "beats_best_historical_baseline",
                ]
            ]
        ),
        "",
        "## Linear Robustness Pack",
        "",
        "These robustness experiments are a limited, protocol-defined sensitivity package,",
        "not a test-set model search. Each setting uses the same chronological 80/10/10",
        "split rule and chooses among OLS, Ridge, Lasso, and ElasticNet candidates by",
        "validation MAE before scoring the final test block. The lag1 rows are",
        "common-sample timing sensitivities because they reuse the same generated panels",
        "and swap only the selected lag feature columns.",
        "",
        "The regularization grid is finite rather than exhaustive: Ridge alpha in",
        "[0.1, 1, 10], Lasso alpha in [0.001, 0.01, 0.1, 1], and ElasticNet alpha in",
        "[0.001, 0.01, 0.1, 1] with l1_ratio in [0.2, 0.5, 0.8]. Predictors are",
        "standardized inside each pipeline, but the target is not standardized; therefore",
        "regularization strength is target-scale dependent.",
        "",
        _dataframe_to_markdown(
            robustness_summary[
                [
                    "robustness_id",
                    "target_column",
                    "lag_suffix",
                    "best_model",
                    "rows",
                    "countries",
                    "test_year_start",
                    "test_year_end",
                    "validation_mae",
                    "test_mae",
                    "best_historical_baseline_model",
                    "best_historical_baseline_mae",
                    "delta_test_mae_selected_minus_best_history",
                    "beats_best_historical_baseline",
                ]
            ]
        ),
        "",
        "The MAE scale differs across target variables, so target-robustness rows should be",
        "read against their own historical baselines rather than as direct cross-target",
        "rankings.",
        "",
        "## Main-Model Correlation Diagnostics",
        "",
        f"Correlation diagnostics use train+validation rows only: {diagnostics['analysis_year_start']}-"
        f"{diagnostics['analysis_year_end']}, n={diagnostics['analysis_rows']}.",
        f"Correlation design: {diagnostics['correlation_design']}.",
        "They are diagnostic checks for collinearity and coefficient interpretation, not a",
        "post-test feature-selection rule.",
    ]
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def verify_generated_artifacts(
    *,
    results: dict[str, object],
    run_started_at: float,
    project_root: str | Path = ROOT_DIR,
) -> dict[str, pd.DataFrame]:
    """Verify registered output and figure artifacts were regenerated by this run."""
    project_root = Path(project_root).resolve()
    outputs = results.get("outputs", {})
    figure_paths = results.get("figure_paths", {})
    if not isinstance(outputs, dict) or not outputs:
        raise AssertionError("No outputs were registered by run_linear_modeling().")
    if not isinstance(figure_paths, dict):
        raise AssertionError("figure_paths must be a dictionary.")

    artifact_rows = []
    missing_artifacts = []
    stale_artifacts = []
    empty_artifacts = []
    output_filenames = [Path(path).name for path in outputs.values()]
    duplicate_output_filenames = sorted({name for name in output_filenames if output_filenames.count(name) > 1})
    if duplicate_output_filenames:
        raise AssertionError(f"Duplicate output filenames registered: {duplicate_output_filenames}")

    for name, path in outputs.items():
        artifact_path = Path(path)
        if not artifact_path.exists():
            missing_artifacts.append(str(artifact_path))
            continue
        if artifact_path.stat().st_size <= 0:
            empty_artifacts.append(str(artifact_path))
        if artifact_path.stat().st_mtime < run_started_at:
            stale_artifacts.append(str(artifact_path))
        artifact_rows.append(
            {
                "artifact": name,
                "suffix": artifact_path.suffix,
                "path": str(artifact_path),
                "exists": True,
                "bytes": artifact_path.stat().st_size,
            }
        )

    figure_index_path = Path(outputs["figure_index"])
    figure_index = pd.read_csv(figure_index_path)
    required_figure_index_columns = {"figure", "path", "pdf_path"}
    missing_figure_index_columns = sorted(required_figure_index_columns.difference(figure_index.columns))
    if missing_figure_index_columns:
        raise AssertionError(f"Figure index missing required columns: {missing_figure_index_columns}")
    if figure_index.empty:
        raise AssertionError("Figure index has no rows.")
    expected_figure_names = set(figure_paths)
    actual_figure_names = set(figure_index["figure"])
    missing_figures = sorted(expected_figure_names.difference(actual_figure_names))
    extra_figures = sorted(actual_figure_names.difference(expected_figure_names))
    if missing_figures:
        raise AssertionError(f"Missing figure index rows: {missing_figures}")
    if extra_figures:
        raise AssertionError(f"Unexpected figure index rows: {extra_figures}")

    figure_index_lookup = figure_index.set_index("figure")
    for name, png_path in figure_paths.items():
        png_path = Path(png_path)
        pdf_path = png_path.with_suffix(".pdf")
        try:
            expected_png_index_path = str(png_path.resolve().relative_to(project_root))
            expected_pdf_index_path = str(pdf_path.resolve().relative_to(project_root))
        except ValueError:
            expected_png_index_path = str(png_path.resolve())
            expected_pdf_index_path = str(pdf_path.resolve())
        actual_png_index_path = str(figure_index_lookup.loc[name, "path"])
        actual_pdf_index_path = str(figure_index_lookup.loc[name, "pdf_path"])
        if actual_png_index_path != expected_png_index_path:
            raise AssertionError(
                f"Figure index path mismatch for {name}: {actual_png_index_path} != {expected_png_index_path}"
            )
        if actual_pdf_index_path != expected_pdf_index_path:
            raise AssertionError(
                f"Figure index PDF path mismatch for {name}: {actual_pdf_index_path} != {expected_pdf_index_path}"
            )
        for artifact_path in [png_path, pdf_path]:
            if not artifact_path.exists():
                missing_artifacts.append(str(artifact_path))
                continue
            if artifact_path.stat().st_size <= 0:
                empty_artifacts.append(str(artifact_path))
            if artifact_path.stat().st_mtime < run_started_at:
                stale_artifacts.append(str(artifact_path))
            artifact_rows.append(
                {
                    "artifact": name,
                    "suffix": artifact_path.suffix,
                    "path": str(artifact_path),
                    "exists": True,
                    "bytes": artifact_path.stat().st_size,
                }
            )

    if missing_artifacts:
        raise AssertionError(f"Missing generated artifacts: {missing_artifacts}")
    if empty_artifacts:
        raise AssertionError(f"Empty generated artifact(s): {empty_artifacts}")
    if stale_artifacts:
        raise AssertionError(f"Artifacts were not regenerated by this notebook run: {stale_artifacts}")

    artifact_table = pd.DataFrame(artifact_rows).sort_values(["suffix", "artifact"]).reset_index(drop=True)
    artifact_count_summary = pd.DataFrame(
        [
            {"check": "registered_outputs", "count": len(outputs)},
            {"check": "indexed_figures", "count": len(figure_index)},
            {"check": "verified_files", "count": len(artifact_table)},
        ]
    )
    artifact_suffix_summary = (
        artifact_table.groupby("suffix", as_index=False)
        .agg(files=("artifact", "size"), bytes=("bytes", "sum"))
        .sort_values("suffix")
    )
    return {
        "artifact_table": artifact_table,
        "artifact_count_summary": artifact_count_summary,
        "artifact_suffix_summary": artifact_suffix_summary,
    }


def _project_relative_path(path: str | Path) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(ROOT_DIR))
    except ValueError:
        return str(resolved)


def _figure_index_rows(figure_paths: dict[str, str]) -> list[dict[str, str]]:
    return [
        {
            "figure": name,
            "path": _project_relative_path(path),
            "pdf_path": _project_relative_path(Path(path).with_suffix(".pdf")),
        }
        for name, path in figure_paths.items()
    ]


def _dataframe_to_markdown(data: pd.DataFrame) -> str:
    if data.empty:
        return "_No rows._"
    columns = list(data.columns)
    rows = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in data.iterrows():
        values = []
        for column in columns:
            value = row[column]
            values.append("" if pd.isna(value) else str(value))
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def _run_tree_panel_experiments() -> dict[str, dict[str, object]]:
    """Run the tree protocol on the main panel and the three mechanism submodels."""
    experiments_by_id: dict[str, dict[str, object]] = {}
    for config in PANEL_CONFIGS:
        spec = PanelSpec(
            panel_id=config["panel_id"],
            panel_label=config["panel_label"],
            panel_path=config["panel_path"],
            target_column=config["target_column"],
            lag_suffix=config["lag_suffix"],
            role=config["role"],
            comparison_group="tree",
            feature_set_role="primary_specification",
        )
        experiments_by_id[config["panel_id"]] = run_panel_tree_experiment(
            spec,
            random_state=42,
            train_share=TRAIN_SHARE,
            validation_share=VALIDATION_SHARE,
        )
    return experiments_by_id


def _run_tree_nested_experiments(
    experiments_by_id: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    """Same-sample nested tree comparison: main controls vs main + submodel predictors."""
    main_experiment = experiments_by_id["main"]
    main_panel = main_experiment["panel"]
    main_features = list(main_experiment["feature_columns"])
    nested_experiments: list[dict[str, object]] = []
    for sub_id in ["suba", "subb", "subc"]:
        sub_experiment = experiments_by_id[sub_id]
        sub_features = list(sub_experiment["feature_columns"])
        nested_panel = build_nested_submodel_panel(
            main_panel=main_panel,
            sub_panel=sub_experiment["panel"],
            main_feature_columns=main_features,
            submodel_feature_columns=sub_features,
            target_column=PRIMARY_TARGET,
        )
        baseline_spec = PanelSpec(
            panel_id=f"main_on_{sub_id}_tree",
            panel_label=f"Tree main controls on {sub_id.upper()} sample",
            panel_path=None,
            target_column=PRIMARY_TARGET,
            lag_suffix="lag1_3_mean",
            role="nested_baseline",
            comparison_group=sub_id,
            feature_set_role="main_controls",
        )
        augmented_spec = PanelSpec(
            panel_id=f"main_plus_{sub_id}_tree",
            panel_label=f"Tree main controls plus {sub_id.upper()} predictors",
            panel_path=None,
            target_column=PRIMARY_TARGET,
            lag_suffix="lag1_3_mean",
            role="nested_augmented",
            comparison_group=sub_id,
            feature_set_role="main_plus_submodel",
        )
        nested_experiments.append(
            _run_tree_experiment_from_panel(
                baseline_spec,
                nested_panel,
                feature_columns=main_features,
                random_state=42,
                train_share=TRAIN_SHARE,
                validation_share=VALIDATION_SHARE,
            )
        )
        nested_experiments.append(
            _run_tree_experiment_from_panel(
                augmented_spec,
                nested_panel,
                feature_columns=main_features + sub_features,
                random_state=42,
                train_share=TRAIN_SHARE,
                validation_share=VALIDATION_SHARE,
            )
        )
    return nested_experiments


def _run_tree_robustness_experiments() -> list[dict[str, object]]:
    """Tree robustness pack: lag1 timing sensitivity and the per-million target."""
    experiments: list[dict[str, object]] = []
    for config in ROBUSTNESS_EXPERIMENT_CONFIGS:
        spec = PanelSpec(
            panel_id=config["panel_id"],
            panel_label=config["panel_label"],
            panel_path=config["panel_path"],
            target_column=config["target_column"],
            lag_suffix=config["lag_suffix"],
            role=config["role"],
            comparison_group="tree_robustness",
            feature_set_role=config["feature_set_role"],
        )
        experiments.append(
            run_panel_tree_experiment(
                spec,
                random_state=42,
                train_share=TRAIN_SHARE,
                validation_share=VALIDATION_SHARE,
            )
        )
    return experiments


def run_tree_modeling() -> dict[str, object]:
    """Run tree model (RF/XGBoost) baseline with historical comparison on main panel."""
    TREE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TREE_FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    spec = PanelSpec(
        panel_id="main_tree",
        panel_label="Main v2 — tree models",
        panel_path=PRIMARY_PANEL_PATH,
        target_column=PRIMARY_TARGET,
        lag_suffix=PRIMARY_LAG_SUFFIX,
        role="main_tree",
        comparison_group="tree",
        feature_set_role="primary_specification",
    )
    experiment = run_panel_tree_experiment(
        spec,
        random_state=42,
        train_share=TRAIN_SHARE,
        validation_share=VALIDATION_SHARE,
    )

    # ---- Save outputs ----
    experiment["sample_summary"].to_csv(TREE_SAMPLE_SUMMARY_OUTPUT, index=False)
    experiment["validation_metrics"].to_csv(TREE_VALIDATION_METRICS_OUTPUT, index=False)
    experiment["test_metrics"].to_csv(TREE_TEST_METRICS_OUTPUT, index=False)
    experiment["predictions"].to_csv(TREE_PREDICTIONS_OUTPUT, index=False)
    experiment["importance"].to_csv(TREE_IMPORTANCE_OUTPUT, index=False)

    # ---- Historical baselines ----
    historical = build_historical_baseline_comparison(
        split=experiment["split"],
        target_column=PRIMARY_TARGET,
        model_predictions=experiment["predictions"],
        model_name=experiment["best_model"],
    )
    historical_delta = build_historical_baseline_delta_summary(historical)
    historical.to_csv(TREE_HISTORICAL_BASELINES_OUTPUT, index=False)
    historical_delta.to_csv(TREE_HISTORICAL_DELTA_OUTPUT, index=False)

    # ---- Figures ----
    from model_data import matrix_from_panel as _matrix_from_panel

    feature_columns = experiment["feature_columns"]
    train_validation = pd.concat(
        [experiment["split"].train, experiment["split"].validation], ignore_index=True
    )
    x_tv, _ = _matrix_from_panel(train_validation, feature_columns, PRIMARY_TARGET)
    partial_dependence_features = (
        experiment["importance"].dropna(subset=["feature", "importance"])
        .sort_values("importance", ascending=False)["feature"]
        .head(3)
        .tolist()
    )
    partial_dependence = build_partial_dependence_table(
        fitted_model=experiment["fitted_model"],
        x_reference=x_tv,
        feature_columns=feature_columns,
        features_to_plot=partial_dependence_features,
        grid_resolution=25,
    )
    partial_dependence.to_csv(TREE_PARTIAL_DEPENDENCE_OUTPUT, index=False)

    figure_paths = make_tree_model_figures(
        panel=experiment["panel"],
        feature_columns=feature_columns,
        target_column=PRIMARY_TARGET,
        sample_summary=experiment["sample_summary"],
        validation_metrics=experiment["validation_metrics"],
        predictions=experiment["predictions"],
        importance=experiment["importance"],
        fitted_model=experiment["fitted_model"],
        x_train_validation=x_tv,
        figures_dir=TREE_FIGURES_DIR,
        partial_dependence=partial_dependence,
    )
    pd.DataFrame(_figure_index_rows(figure_paths)).to_csv(TREE_FIGURE_INDEX_OUTPUT, index=False)

    # ---- Summary ----
    best_model = experiment["best_model"]
    split_years = experiment["split_years"]
    write_markdown_summary(
        TREE_RUN_SUMMARY_OUTPUT,
        best_model=best_model,
        split_years=split_years,
        validation_metrics=experiment["validation_metrics"],
        test_metrics=experiment["test_metrics"],
        heading="Tree Model Run Summary",
    )
    with open(TREE_RUN_SUMMARY_OUTPUT, "a") as fh:
        fh.write("\n## Historical Baseline Comparison\n\n")
        fh.write(_dataframe_to_markdown(historical))
        fh.write("\n\n## Historical Baseline Delta Summary\n\n")
        fh.write(_dataframe_to_markdown(historical_delta))
        fh.write("\n\n## Partial Dependence Diagnostic\n\n")
        if partial_dependence.empty:
            fh.write("No partial dependence table was generated because no valid feature grid was available.\n")
        else:
            fh.write(
                "Computed on train+validation rows for the top predictors ranked by the fitted "
                "tree model's impurity-based feature importance. This is a fitted-model response "
                "diagnostic, not a causal estimate; PDP curves may average over feature "
                "combinations that are sparse or absent in the observed panel.\n\n"
            )
            pdp_summary = (
                partial_dependence.groupby(["feature_rank", "feature_label"], as_index=False)
                .agg(
                    grid_points=("grid_value", "count"),
                    centered_response_min=("centered_average_prediction", "min"),
                    centered_response_max=("centered_average_prediction", "max"),
                )
                .sort_values("feature_rank")
            )
            fh.write(_dataframe_to_markdown(pdp_summary.round(4)))
        fh.write("\n")
    experiment["partial_dependence"] = partial_dependence

    # ---- Mechanism submodels + same-sample nested comparison ----
    # Trees can capture nonlinear/interaction effects that the linear nested test
    # may miss, so this is the most informative tree extension (esp. EPS, R&D).
    panel_experiments = _run_tree_panel_experiments()
    panel_test_metrics = pd.concat(
        [exp["test_metrics"] for exp in panel_experiments.values()], ignore_index=True
    )
    panel_test_metrics["comparison_scope"] = "own_sample_not_direct_ranking"
    panel_validation_metrics = pd.concat(
        [exp["validation_metrics"] for exp in panel_experiments.values()], ignore_index=True
    )
    panel_importance = pd.concat(
        [exp["importance"] for exp in panel_experiments.values()], ignore_index=True
    )
    panel_test_metrics.to_csv(TREE_PANEL_TEST_METRICS_OUTPUT, index=False)
    panel_validation_metrics.to_csv(TREE_PANEL_VALIDATION_METRICS_OUTPUT, index=False)
    panel_importance.to_csv(TREE_PANEL_IMPORTANCE_OUTPUT, index=False)

    nested_experiments = _run_tree_nested_experiments(panel_experiments)
    nested_comparison = build_nested_comparison_table(nested_experiments)
    nested_test_metrics = pd.concat(
        [exp["test_metrics"] for exp in nested_experiments], ignore_index=True
    )
    nested_importance = pd.concat(
        [exp["importance"] for exp in nested_experiments], ignore_index=True
    )
    nested_comparison.to_csv(TREE_NESTED_COMPARISON_OUTPUT, index=False)
    nested_test_metrics.to_csv(TREE_NESTED_TEST_METRICS_OUTPUT, index=False)
    nested_importance.to_csv(TREE_NESTED_IMPORTANCE_OUTPUT, index=False)

    # ---- Robustness pack: lag1 (t-1) timing + per-million target ----
    robustness_experiments = _run_tree_robustness_experiments()
    robustness_historical_by_id, robustness_historical_baselines = (
        _build_robustness_historical_baselines(robustness_experiments)
    )
    robustness_summary = build_robustness_summary_table(
        robustness_experiments,
        robustness_historical_by_id,
    )
    robustness_test_metrics = pd.concat(
        [exp["test_metrics"] for exp in robustness_experiments], ignore_index=True
    )
    robustness_summary.to_csv(TREE_ROBUSTNESS_SUMMARY_OUTPUT, index=False)
    robustness_test_metrics.to_csv(TREE_ROBUSTNESS_TEST_METRICS_OUTPUT, index=False)
    robustness_historical_baselines.to_csv(
        TREE_ROBUSTNESS_HISTORICAL_BASELINES_OUTPUT, index=False
    )

    with open(TREE_RUN_SUMMARY_OUTPUT, "a") as fh:
        fh.write("\n## Mechanism Submodel Own-Sample Comparison (Tree)\n\n")
        fh.write(
            "Own-sample diagnostics only; panels have different country/year coverage "
            "and are not a direct ranking against the main model.\n\n"
        )
        fh.write(
            _dataframe_to_markdown(
                panel_test_metrics.loc[
                    :, ["panel_id", "panel_label", "model", "mae", "rmse", "oos_r2_vs_train_mean", "spearman"]
                ]
            )
        )
        fh.write("\n\n## Same-Sample Nested Submodel Tests (Tree)\n\n")
        fh.write(
            "Each comparison uses the same country-year rows for main-controls and "
            "main-plus-submodel. A negative delta means the submodel predictors help.\n\n"
        )
        fh.write(
            _dataframe_to_markdown(
                nested_comparison.loc[
                    :,
                    [
                        "comparison_group",
                        "rows",
                        "countries",
                        "baseline_test_mae",
                        "augmented_test_mae",
                        "delta_test_mae_augmented_minus_baseline",
                        "improves_primary_test_mae",
                    ],
                ]
            )
        )
        fh.write("\n\n## Tree Robustness Pack (lag1 timing + per-million target)\n\n")
        fh.write(
            _dataframe_to_markdown(
                robustness_summary.loc[
                    :,
                    [
                        "robustness_id",
                        "target_column",
                        "lag_suffix",
                        "best_model",
                        "test_mae",
                        "best_historical_baseline_mae",
                        "delta_test_mae_selected_minus_best_history",
                        "beats_best_historical_baseline",
                    ],
                ]
            )
        )
        fh.write("\n")

    experiment["panel_experiments"] = panel_experiments
    experiment["nested_comparison"] = nested_comparison
    experiment["robustness_summary"] = robustness_summary
    return experiment


if __name__ == "__main__":
    import sys

    run_tree = "--tree" in sys.argv
    run_both = "--both" in sys.argv or (not run_tree)

    if run_both:
        print("=== Running linear model pipeline ===")
        results = run_linear_modeling()
        best = results["best_model"]
        test_metrics = results["test_metrics"].iloc[0]
        print(f"Best validation model: {best}")
        print(
            "Final test metrics: "
            f"MAE={test_metrics['mae']:.4f}, "
            f"RMSE={test_metrics['rmse']:.4f}, "
            f"OOS R2={test_metrics['oos_r2_vs_train_mean']:.4f}, "
            f"Spearman={test_metrics['spearman']:.4f}"
        )
        print(f"Outputs written to: {OUTPUT_DIR}")

    if run_both or run_tree:
        print("\n=== Running tree model pipeline ===")
        tree_results = run_tree_modeling()
        t_best = tree_results["best_model"]
        t_metrics = tree_results["test_metrics"].iloc[0]
        print(f"Best validation model: {t_best}")
        print(
            "Final test metrics: "
            f"MAE={t_metrics['mae']:.4f}, "
            f"RMSE={t_metrics['rmse']:.4f}, "
            f"OOS R2={t_metrics['oos_r2_vs_train_mean']:.4f}, "
            f"Spearman={t_metrics['spearman']:.4f}"
        )
        print(f"Outputs written to: {TREE_OUTPUT_DIR}")
