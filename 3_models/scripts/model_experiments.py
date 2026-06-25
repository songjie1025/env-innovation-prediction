from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from model_data import (
    chronological_split_for_years,
    chronological_train_validation_test_split,
    load_model_panel,
    matrix_from_panel,
    select_lag_features,
)
from model_estimators import build_linear_model_candidates
from model_evaluation import (
    build_historical_baseline_comparison,
    coefficient_table,
    evaluate_candidates_on_validation,
    evaluate_selected_model,
    select_best_validation_model,
)


@dataclass(frozen=True)
class PanelSpec:
    panel_id: str
    panel_label: str
    panel_path: str | Path | None
    target_column: str
    lag_suffix: str
    role: str
    comparison_group: str | None = None
    feature_set_role: str | None = None


def run_panel_linear_experiment(
    spec: PanelSpec,
    *,
    random_state: int,
    train_share: float = 0.80,
    validation_share: float = 0.10,
    year_column: str = "year",
    split_years: dict[str, list[int]] | None = None,
) -> dict[str, Any]:
    """Run the shared chronological linear-model protocol for one model panel."""
    if spec.panel_path is None:
        raise ValueError("panel_path is required when running an experiment from disk")
    panel = load_model_panel(spec.panel_path, spec.target_column)
    return run_panel_linear_experiment_from_panel(
        spec,
        panel,
        feature_columns=None,
        random_state=random_state,
        train_share=train_share,
        validation_share=validation_share,
        year_column=year_column,
        split_years=split_years,
    )


def run_panel_linear_experiment_from_panel(
    spec: PanelSpec,
    panel: pd.DataFrame,
    *,
    feature_columns: list[str] | None,
    random_state: int,
    train_share: float = 0.80,
    validation_share: float = 0.10,
    year_column: str = "year",
    split_years: dict[str, list[int]] | None = None,
) -> dict[str, Any]:
    """Run the linear-model protocol on an already constructed in-memory panel."""
    panel = _validate_panel_frame(panel, spec.target_column)
    if feature_columns is None:
        feature_columns = select_lag_features(panel, spec.lag_suffix)
    else:
        missing_features = sorted(set(feature_columns).difference(panel.columns))
        if missing_features:
            raise ValueError(f"Panel missing requested feature columns: {missing_features}")
    if split_years is None:
        split = chronological_train_validation_test_split(
            panel,
            year_column=year_column,
            train_share=train_share,
            validation_share=validation_share,
        )
    else:
        split = chronological_split_for_years(
            panel,
            train_years=split_years["train"],
            validation_years=split_years["validation"],
            test_years=split_years["test"],
            year_column=year_column,
        )

    x_train, y_train = matrix_from_panel(split.train, feature_columns, spec.target_column)
    x_validation, y_validation = matrix_from_panel(split.validation, feature_columns, spec.target_column)
    x_test, y_test = matrix_from_panel(split.test, feature_columns, spec.target_column)
    _attach_year_attrs(x_train, split.train_years)
    _attach_year_attrs(x_validation, split.validation_years)

    candidates = build_linear_model_candidates(random_state=random_state)
    validation_metrics, _ = evaluate_candidates_on_validation(
        candidates,
        x_train,
        y_train,
        x_validation,
        y_validation,
    )
    best_model = select_best_validation_model(validation_metrics)

    train_validation = pd.concat([split.train, split.validation], ignore_index=True)
    x_train_validation, y_train_validation = matrix_from_panel(
        train_validation,
        feature_columns,
        spec.target_column,
    )
    test_metrics, fitted_model, test_predictions = evaluate_selected_model(
        candidates[best_model],
        best_model,
        x_train_validation,
        y_train_validation,
        x_test,
        y_test,
        score_baseline_mean=float(y_train.mean()),
    )

    predictions = split.test.loc[:, ["country_code", "country_name", "year", spec.target_column]].copy()
    predictions["model"] = best_model
    predictions["observed"] = predictions[spec.target_column]
    predictions["prediction"] = test_predictions
    predictions["error"] = predictions[spec.target_column] - predictions["prediction"]
    predictions["absolute_error"] = predictions["error"].abs()

    sample_summary = _sample_summary(panel, feature_columns, split, spec, year_column)
    coefficients = coefficient_table(fitted_model, feature_columns, best_model)

    validation_metrics = _with_panel_context(validation_metrics, spec)
    test_metrics = _with_panel_context(test_metrics, spec)
    predictions = _with_panel_context(predictions, spec)
    coefficients = _with_panel_context(coefficients, spec)

    _add_metric_sample_context(
        validation_metrics,
        comparison_scope=_comparison_scope(spec),
        panel=panel,
        feature_columns=feature_columns,
        split_rows={
            "train_rows": len(split.train),
            "validation_rows": len(split.validation),
        },
        split_countries={
            "train_countries": split.train["country_code"].nunique(),
            "validation_countries": split.validation["country_code"].nunique(),
        },
    )
    _add_metric_sample_context(
        test_metrics,
        comparison_scope=_comparison_scope(spec),
        panel=panel,
        feature_columns=feature_columns,
        split_rows={
            "train_validation_rows": len(train_validation),
            "test_rows": len(split.test),
        },
        split_countries={
            "train_validation_countries": train_validation["country_code"].nunique(),
            "test_countries": split.test["country_code"].nunique(),
        },
    )
    test_metrics["train_year_start"] = min(split.train_years)
    test_metrics["train_year_end"] = max(split.train_years)
    test_metrics["validation_year_start"] = min(split.validation_years)
    test_metrics["validation_year_end"] = max(split.validation_years)
    test_metrics["test_year_start"] = min(split.test_years)
    test_metrics["test_year_end"] = max(split.test_years)

    return {
        "panel_id": spec.panel_id,
        "panel_label": spec.panel_label,
        "panel_role": spec.role,
        "comparison_group": spec.comparison_group,
        "feature_set_role": spec.feature_set_role,
        "target_column": spec.target_column,
        "lag_suffix": spec.lag_suffix,
        "panel": panel,
        "split": split,
        "best_model": best_model,
        "feature_columns": feature_columns,
        "split_years": {
            "train": split.train_years,
            "validation": split.validation_years,
            "test": split.test_years,
        },
        "fitted_model": fitted_model,
        "sample_summary": sample_summary,
        "validation_metrics": validation_metrics,
        "test_metrics": test_metrics,
        "predictions": predictions,
        "coefficients": coefficients,
    }


def run_rolling_origin_linear_evaluation(
    spec: PanelSpec,
    *,
    panel: pd.DataFrame | None = None,
    feature_columns: list[str] | None = None,
    random_state: int,
    initial_pretest_years: int = 8,
    validation_years: int = 2,
    test_window_years: int = 3,
    year_column: str = "year",
) -> dict[str, pd.DataFrame]:
    """Run expanding-window rolling-origin checks with validation inside each pre-test window."""
    if panel is None:
        if spec.panel_path is None:
            raise ValueError("Either panel or spec.panel_path is required")
        panel = load_model_panel(spec.panel_path, spec.target_column)
    else:
        panel = _validate_panel_frame(panel, spec.target_column)
    if feature_columns is None:
        feature_columns = select_lag_features(panel, spec.lag_suffix)

    years = sorted(int(year) for year in panel[year_column].dropna().unique())
    if initial_pretest_years <= validation_years:
        raise ValueError("initial_pretest_years must be greater than validation_years")
    if test_window_years < 1:
        raise ValueError("test_window_years must be at least 1")
    if len(years) < initial_pretest_years + test_window_years:
        raise ValueError("Not enough years for rolling-origin evaluation")

    fold_rows = []
    prediction_tables = []
    validation_tables = []
    test_tables = []
    fold_number = 1
    test_start_index = initial_pretest_years
    while test_start_index < len(years):
        pretest_years = years[:test_start_index]
        train_years = pretest_years[:-validation_years]
        inner_validation_years = pretest_years[-validation_years:]
        test_years = years[test_start_index : min(test_start_index + test_window_years, len(years))]
        fold_id = f"fold_{fold_number}"
        fold_spec = PanelSpec(
            panel_id=f"{spec.panel_id}_{fold_id}",
            panel_label=f"{spec.panel_label} rolling-origin {fold_id}",
            panel_path=None,
            target_column=spec.target_column,
            lag_suffix=spec.lag_suffix,
            role="rolling_origin_confirmatory",
            comparison_group=spec.comparison_group or "rolling_origin",
            feature_set_role=spec.feature_set_role or "feature_only",
        )
        experiment = run_panel_linear_experiment_from_panel(
            fold_spec,
            panel,
            feature_columns=feature_columns,
            random_state=random_state,
            split_years={
                "train": train_years,
                "validation": inner_validation_years,
                "test": test_years,
            },
        )
        history = build_historical_baseline_comparison(
            split=experiment["split"],
            target_column=spec.target_column,
            model_predictions=experiment["predictions"],
            model_name=str(experiment["best_model"]),
        )
        best_history = _best_prediction_safe_history_baseline(history, str(experiment["best_model"]))
        test_metrics = experiment["test_metrics"].iloc[0]
        best_validation = _best_validation_row(experiment)
        best_history_mae = float(best_history["mae"]) if best_history is not None else float("nan")
        fold_rows.append(
            {
                "fold_id": fold_id,
                "panel_id": spec.panel_id,
                "target_column": spec.target_column,
                "lag_suffix": spec.lag_suffix,
                "best_model": experiment["best_model"],
                "train_year_start": min(train_years),
                "train_year_end": max(train_years),
                "validation_year_start": min(inner_validation_years),
                "validation_year_end": max(inner_validation_years),
                "test_year_start": min(test_years),
                "test_year_end": max(test_years),
                "validation_mae": float(best_validation["mae"]),
                "test_mae": float(test_metrics["mae"]),
                "test_rmse": float(test_metrics["rmse"]),
                "test_oos_r2_vs_train_mean": float(test_metrics["oos_r2_vs_train_mean"]),
                "test_spearman": float(test_metrics["spearman"])
                if pd.notna(test_metrics["spearman"])
                else float("nan"),
                "n_test": int(test_metrics["n_test"]),
                "best_historical_baseline_model": (
                    str(best_history["model"]) if best_history is not None else None
                ),
                "best_historical_baseline_mae": best_history_mae,
                "delta_mae_selected_minus_best_history": float(test_metrics["mae"]) - best_history_mae,
                "beats_best_historical_baseline": bool(float(test_metrics["mae"]) < best_history_mae)
                if pd.notna(best_history_mae)
                else False,
            }
        )
        predictions = experiment["predictions"].copy()
        predictions.insert(0, "fold_id", fold_id)
        prediction_tables.append(predictions)
        validation = experiment["validation_metrics"].copy()
        validation.insert(0, "fold_id", fold_id)
        validation_tables.append(validation)
        test = experiment["test_metrics"].copy()
        test.insert(0, "fold_id", fold_id)
        test_tables.append(test)

        fold_number += 1
        test_start_index += test_window_years

    if not fold_rows:
        raise ValueError("Rolling-origin configuration produced no complete test folds")
    return {
        "fold_summary": pd.DataFrame(fold_rows),
        "fold_predictions": pd.concat(prediction_tables, ignore_index=True),
        "validation_metrics": pd.concat(validation_tables, ignore_index=True),
        "test_metrics": pd.concat(test_tables, ignore_index=True),
    }


def combine_experiment_tables(experiments: list[dict[str, Any]]) -> dict[str, pd.DataFrame]:
    """Combine homogeneous output tables across panel experiments."""
    if not experiments:
        raise ValueError("At least one experiment is required")
    combined = {
        "sample_summary": pd.concat([item["sample_summary"] for item in experiments], ignore_index=True),
        "validation_metrics": pd.concat([item["validation_metrics"] for item in experiments], ignore_index=True),
        "test_metrics": pd.concat([item["test_metrics"] for item in experiments], ignore_index=True),
        "predictions": pd.concat([item["predictions"] for item in experiments], ignore_index=True),
        "coefficients": pd.concat([item["coefficients"] for item in experiments], ignore_index=True),
    }
    combined["panel_comparison"] = _panel_comparison(experiments)
    return combined


def build_block_safe_target_history_feature(
    *,
    panel: pd.DataFrame,
    split,
    target_column: str,
    feature_name: str = "target_history_preblock",
) -> pd.DataFrame:
    """Add a target-history feature without using validation/test labels inside their blocks."""
    key_columns = ["country_code", "year"]
    _validate_panel_frame(panel, target_column)
    output = panel.drop(columns=[feature_name], errors="ignore").copy()

    global_train_mean = float(split.train[target_column].mean())
    train_history = split.train.sort_values(key_columns).copy()
    train_history[feature_name] = (
        train_history.groupby("country_code")[target_column].shift(1).fillna(global_train_mean)
    )

    latest_train_targets = _latest_country_targets(split.train, target_column)
    validation_history = split.validation.loc[:, key_columns].copy()
    validation_history[feature_name] = (
        validation_history["country_code"].map(latest_train_targets).fillna(global_train_mean)
    )

    train_validation = pd.concat([split.train, split.validation], ignore_index=True)
    latest_train_validation_targets = _latest_country_targets(train_validation, target_column)
    global_train_validation_mean = float(train_validation[target_column].mean())
    test_history = split.test.loc[:, key_columns].copy()
    test_history[feature_name] = (
        test_history["country_code"].map(latest_train_validation_targets).fillna(global_train_validation_mean)
    )

    history = pd.concat(
        [
            train_history.loc[:, key_columns + [feature_name]],
            validation_history,
            test_history,
        ],
        ignore_index=True,
    )
    return (
        output.merge(history, on=key_columns, how="left", validate="one_to_one")
        .sort_values(["year", "country_code"])
        .reset_index(drop=True)
    )


def build_skew_transformed_panel(
    *,
    panel: pd.DataFrame,
    feature_columns: list[str],
    transform_methods: dict[str, str],
) -> tuple[pd.DataFrame, list[str], pd.DataFrame]:
    """Create deterministic skew-reduced feature columns while preserving missingness."""
    output = panel.copy()
    transformed_features: list[str] = []
    plan_rows = []
    allowed_methods = {"identity", "log1p", "asinh"}

    for feature in feature_columns:
        if feature not in output.columns:
            raise ValueError(f"Panel missing requested feature column: {feature}")
        method = transform_methods.get(feature, "identity")
        if method not in allowed_methods:
            raise ValueError(f"Unsupported skew transform method for {feature}: {method}")
        if method == "identity":
            model_feature = feature
        else:
            model_feature = f"skew_{method}__{feature}"
            values = output[feature].astype(float)
            if method == "log1p":
                non_missing = values.dropna()
                if (non_missing <= -1).any():
                    raise ValueError(f"log1p transform requires values > -1 for {feature}")
                output[model_feature] = np.log1p(values)
            elif method == "asinh":
                output[model_feature] = np.arcsinh(values)
        transformed_features.append(model_feature)
        plan_rows.append(
            {
                "source_feature": feature,
                "model_feature": model_feature,
                "transformation": method,
                "missing_values_preserved": bool(output[feature].isna().equals(output[model_feature].isna())),
            }
        )

    return output, transformed_features, pd.DataFrame(plan_rows)


def build_missingness_indicator_panel(
    *,
    panel: pd.DataFrame,
    feature_columns: list[str],
    indicator_prefix: str = "missing__",
) -> tuple[pd.DataFrame, list[str], pd.DataFrame]:
    """Add binary missingness indicators while preserving the original predictor columns."""
    output = panel.copy()
    indicator_features = []
    plan_rows = []
    for feature in feature_columns:
        if feature not in output.columns:
            raise ValueError(f"Panel missing requested feature column: {feature}")
        indicator_feature = f"{indicator_prefix}{feature}"
        if indicator_feature in output.columns:
            raise ValueError(f"Indicator feature already exists: {indicator_feature}")
        output[indicator_feature] = output[feature].isna().astype(int)
        indicator_features.append(indicator_feature)
        plan_rows.append(
            {
                "source_feature": feature,
                "indicator_feature": indicator_feature,
                "missing_rows": int(output[indicator_feature].sum()),
                "missing_share": float(output[indicator_feature].mean()),
                "original_missing_values_preserved": bool(output[feature].isna().equals(output[indicator_feature].eq(1))),
            }
        )
    return output, list(feature_columns) + indicator_features, pd.DataFrame(plan_rows)


def build_persistence_augmented_comparison_table(
    *,
    feature_experiment: dict[str, Any],
    augmented_experiment: dict[str, Any],
    historical_baselines: pd.DataFrame,
) -> pd.DataFrame:
    """Compare feature-only, history-only, and feature-plus-history test performance."""
    feature_validation = _best_validation_row(feature_experiment)
    augmented_validation = _best_validation_row(augmented_experiment)
    feature_test = feature_experiment["test_metrics"].iloc[0]
    augmented_test = augmented_experiment["test_metrics"].iloc[0]
    history_candidates = historical_baselines[
        ~historical_baselines["prediction_rule"].eq("selected_linear_model")
    ].copy()
    if "uses_test_labels" in history_candidates.columns:
        history_candidates = history_candidates[~history_candidates["uses_test_labels"].fillna(False)].copy()
    if history_candidates.empty:
        raise ValueError("historical_baselines must include at least one prediction-safe standalone baseline row")
    history_row = history_candidates.sort_values(["mae", "rmse", "model"], na_position="last").iloc[0]

    rows = [
        _persistence_comparison_row(
            model_stage="feature_only_linear",
            model=str(feature_experiment["best_model"]),
            prediction_rule="main predictors only; no lagged target predictor",
            includes_main_predictors=True,
            includes_target_history=False,
            validation_mae=float(feature_validation["mae"]),
            validation_rmse=float(feature_validation["rmse"]),
            test_row=feature_test,
            uses_test_labels=False,
            test_year_start=int(feature_test["test_year_start"]),
            test_year_end=int(feature_test["test_year_end"]),
            comparison_note="Primary feature-only model selected by validation MAE.",
        ),
        _persistence_comparison_row(
            model_stage="history_only_baseline",
            model=str(history_row["model"]),
            prediction_rule=str(history_row["prediction_rule"]),
            includes_main_predictors=False,
            includes_target_history=True,
            validation_mae=float("nan"),
            validation_rmse=float("nan"),
            test_row=history_row,
            uses_test_labels=bool(history_row["uses_test_labels"]),
            test_year_start=int(feature_test["test_year_start"]),
            test_year_end=int(feature_test["test_year_end"]),
            comparison_note="Standalone historical target baseline; not part of the main model.",
        ),
        _persistence_comparison_row(
            model_stage="persistence_augmented_linear",
            model=str(augmented_experiment["best_model"]),
            prediction_rule="main predictors plus block-safe target history feature",
            includes_main_predictors=True,
            includes_target_history=True,
            validation_mae=float(augmented_validation["mae"]),
            validation_rmse=float(augmented_validation["rmse"]),
            test_row=augmented_test,
            uses_test_labels=False,
            test_year_start=int(augmented_test["test_year_start"]),
            test_year_end=int(augmented_test["test_year_end"]),
            comparison_note="Augmented comparison model; not a replacement for the feature-only main model.",
        ),
    ]
    return pd.DataFrame(rows).sort_values(["test_mae", "test_rmse", "model_stage"]).reset_index(drop=True)


def build_nested_submodel_panel(
    *,
    main_panel: pd.DataFrame,
    sub_panel: pd.DataFrame,
    main_feature_columns: list[str],
    submodel_feature_columns: list[str],
    target_column: str,
) -> pd.DataFrame:
    """Build a same-row panel containing main controls and one submodel feature set."""
    key_columns = ["country_code", "year"]
    display_columns = ["country_code", "country_name", "year", target_column]
    main_columns = key_columns + main_feature_columns
    sub_columns = display_columns + submodel_feature_columns
    overlapping_features = sorted(set(main_feature_columns).intersection(submodel_feature_columns))
    if overlapping_features:
        raise ValueError(f"Main and submodel feature columns overlap: {overlapping_features}")

    missing_main = sorted(set(main_columns).difference(main_panel.columns))
    missing_sub = sorted(set(sub_columns).difference(sub_panel.columns))
    if missing_main:
        raise ValueError(f"Main panel missing nested columns: {missing_main}")
    if missing_sub:
        raise ValueError(f"Submodel panel missing nested columns: {missing_sub}")

    nested = sub_panel.loc[:, sub_columns].merge(
        main_panel.loc[:, main_columns],
        on=key_columns,
        how="inner",
        validate="one_to_one",
    )
    ordered_columns = display_columns + main_feature_columns + submodel_feature_columns
    return nested.loc[:, ordered_columns].sort_values(["year", "country_code"]).reset_index(drop=True)


def build_nested_comparison_table(experiments: list[dict[str, Any]]) -> pd.DataFrame:
    """Summarize same-sample main-controls versus main-plus-submodel comparisons."""
    rows = []
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for experiment in experiments:
        group = experiment.get("comparison_group")
        role = experiment.get("feature_set_role")
        if not group or not role:
            continue
        grouped.setdefault(str(group), {})[str(role)] = experiment

    for group, members in sorted(grouped.items()):
        if "main_controls" not in members or "main_plus_submodel" not in members:
            continue
        baseline = members["main_controls"]
        augmented = members["main_plus_submodel"]
        baseline_validation = _best_validation_row(baseline)
        augmented_validation = _best_validation_row(augmented)
        baseline_test = baseline["test_metrics"].iloc[0]
        augmented_test = augmented["test_metrics"].iloc[0]
        baseline_sample = baseline["sample_summary"][baseline["sample_summary"]["split"].eq("all")].iloc[0]
        rows.append(
            {
                "comparison_group": group,
                "comparison_scope": "same_sample_nested",
                "baseline_panel_id": baseline["panel_id"],
                "baseline_label": baseline["panel_label"],
                "baseline_best_model": baseline["best_model"],
                "baseline_feature_columns": len(baseline["feature_columns"]),
                "augmented_panel_id": augmented["panel_id"],
                "augmented_label": augmented["panel_label"],
                "augmented_best_model": augmented["best_model"],
                "augmented_feature_columns": len(augmented["feature_columns"]),
                "rows": int(baseline_sample["rows"]),
                "countries": int(baseline_sample["countries"]),
                "test_year_start": int(baseline_test["test_year_start"]),
                "test_year_end": int(baseline_test["test_year_end"]),
                "baseline_validation_mae": float(baseline_validation["mae"]),
                "augmented_validation_mae": float(augmented_validation["mae"]),
                "delta_validation_mae_augmented_minus_baseline": float(
                    augmented_validation["mae"] - baseline_validation["mae"]
                ),
                "baseline_test_mae": float(baseline_test["mae"]),
                "augmented_test_mae": float(augmented_test["mae"]),
                "delta_test_mae_augmented_minus_baseline": float(augmented_test["mae"] - baseline_test["mae"]),
                "improves_primary_test_mae": bool(augmented_test["mae"] < baseline_test["mae"]),
                "baseline_test_rmse": float(baseline_test["rmse"]),
                "augmented_test_rmse": float(augmented_test["rmse"]),
                "baseline_test_oos_r2_vs_train_mean": float(baseline_test["oos_r2_vs_train_mean"]),
                "augmented_test_oos_r2_vs_train_mean": float(augmented_test["oos_r2_vs_train_mean"]),
                "baseline_test_spearman": float(baseline_test["spearman"]),
                "augmented_test_spearman": float(augmented_test["spearman"]),
            }
        )
    return pd.DataFrame(rows)


def build_robustness_summary_table(
    experiments: list[dict[str, Any]],
    historical_baselines_by_panel_id: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Summarize pre-specified robustness experiments against history baselines."""
    rows: list[dict[str, object]] = []
    for experiment in experiments:
        panel_id = str(experiment["panel_id"])
        all_sample = experiment["sample_summary"][experiment["sample_summary"]["split"].eq("all")].iloc[0]
        best_validation = _best_validation_row(experiment)
        test_metrics = experiment["test_metrics"].iloc[0]
        split_years = experiment["split_years"]
        history = historical_baselines_by_panel_id.get(panel_id, pd.DataFrame())
        best_history = _best_prediction_safe_history_baseline(history, str(experiment["best_model"]))
        best_history_mae = float(best_history["mae"]) if best_history is not None else float("nan")
        test_mae = float(test_metrics["mae"])

        rows.append(
            {
                "robustness_id": panel_id,
                "robustness_label": experiment["panel_label"],
                "target_column": experiment["target_column"],
                "lag_suffix": experiment["lag_suffix"],
                "comparison_role": experiment.get("feature_set_role"),
                "panel_role": experiment["panel_role"],
                "best_model": experiment["best_model"],
                "rows": int(all_sample["rows"]),
                "countries": int(all_sample["countries"]),
                "feature_columns": len(experiment["feature_columns"]),
                "train_year_start": min(split_years["train"]),
                "train_year_end": max(split_years["train"]),
                "validation_year_start": min(split_years["validation"]),
                "validation_year_end": max(split_years["validation"]),
                "test_year_start": min(split_years["test"]),
                "test_year_end": max(split_years["test"]),
                "validation_mae": float(best_validation["mae"]),
                "validation_rmse": float(best_validation["rmse"]),
                "test_mae": test_mae,
                "test_rmse": float(test_metrics["rmse"]),
                "test_oos_r2_vs_train_mean": float(test_metrics["oos_r2_vs_train_mean"]),
                "test_spearman": float(test_metrics["spearman"]),
                "n_test": int(test_metrics["n_test"]),
                "best_historical_baseline_model": (
                    str(best_history["model"]) if best_history is not None else None
                ),
                "best_historical_baseline_mae": best_history_mae,
                "delta_test_mae_selected_minus_best_history": test_mae - best_history_mae,
                "beats_best_historical_baseline": bool(test_mae < best_history_mae)
                if pd.notna(best_history_mae)
                else False,
                "selection_rule": "lowest_validation_mae_then_rmse_then_model_name",
            }
        )
    return pd.DataFrame(rows).sort_values(["target_column", "lag_suffix", "robustness_id"]).reset_index(drop=True)


def _validate_panel_frame(panel: pd.DataFrame, target_column: str) -> pd.DataFrame:
    if target_column not in panel.columns:
        raise ValueError(f"Missing target column: {target_column}")
    if panel[target_column].isna().any():
        raise ValueError("Panel contains missing target values")
    duplicate_keys = panel.duplicated(["country_code", "year"], keep=False)
    if duplicate_keys.any():
        raise ValueError("Duplicate country-year keys found in panel frame")
    return panel.sort_values(["year", "country_code"]).reset_index(drop=True)


def _best_validation_row(experiment: dict[str, Any]) -> pd.Series:
    return (
        experiment["validation_metrics"][experiment["validation_metrics"]["model"].eq(experiment["best_model"])]
        .sort_values(["mae", "rmse", "model"], na_position="last")
        .iloc[0]
    )


def _latest_country_targets(panel: pd.DataFrame, target_column: str) -> pd.Series:
    return (
        panel.sort_values(["country_code", "year"])
        .groupby("country_code", as_index=True)
        .tail(1)
        .set_index("country_code")[target_column]
    )


def _persistence_comparison_row(
    *,
    model_stage: str,
    model: str,
    prediction_rule: str,
    includes_main_predictors: bool,
    includes_target_history: bool,
    validation_mae: float,
    validation_rmse: float,
    test_row: pd.Series,
    uses_test_labels: bool,
    test_year_start: int,
    test_year_end: int,
    comparison_note: str,
) -> dict[str, object]:
    return {
        "model_stage": model_stage,
        "model": model,
        "prediction_rule": prediction_rule,
        "includes_main_predictors": bool(includes_main_predictors),
        "includes_target_history": bool(includes_target_history),
        "uses_test_labels": bool(uses_test_labels),
        "validation_mae": validation_mae,
        "validation_rmse": validation_rmse,
        "test_mae": float(test_row["mae"]),
        "test_rmse": float(test_row["rmse"]),
        "test_oos_r2_vs_train_mean": float(test_row["oos_r2_vs_train_mean"]),
        "test_spearman": float(test_row["spearman"]) if pd.notna(test_row["spearman"]) else float("nan"),
        "n_test": int(test_row["n_test"]),
        "test_year_start": int(test_year_start),
        "test_year_end": int(test_year_end),
        "comparison_note": comparison_note,
    }


def _attach_year_attrs(matrix: pd.DataFrame, years: list[int]) -> None:
    matrix.attrs["year_start"] = min(years)
    matrix.attrs["year_end"] = max(years)


def _sample_summary(panel, feature_columns, split, spec: PanelSpec, year_column: str) -> pd.DataFrame:
    rows = []
    for split_name, split_panel, years in [
        ("train", split.train, split.train_years),
        ("validation", split.validation, split.validation_years),
        ("test", split.test, split.test_years),
    ]:
        rows.append(_sample_row(split_name, split_panel, years, feature_columns, spec))
    rows.append(
        _sample_row(
            "all",
            panel,
            sorted(int(year) for year in panel[year_column].unique()),
            feature_columns,
            spec,
        )
    )
    return pd.DataFrame(rows)


def _sample_row(
    split_name: str,
    split_panel: pd.DataFrame,
    years: list[int],
    feature_columns: list[str],
    spec: PanelSpec,
) -> dict[str, object]:
    feature_frame = split_panel.loc[:, feature_columns]
    return {
        "panel_id": spec.panel_id,
        "panel_label": spec.panel_label,
        "panel_role": spec.role,
        "comparison_group": spec.comparison_group,
        "feature_set_role": spec.feature_set_role,
        "target_column": spec.target_column,
        "lag_suffix": spec.lag_suffix,
        "comparison_scope": _comparison_scope(spec),
        "split": split_name,
        "year_start": min(years),
        "year_end": max(years),
        "years": len(years),
        "rows": len(split_panel),
        "countries": split_panel["country_code"].nunique(),
        "target_non_missing": int(split_panel[spec.target_column].notna().sum()),
        "feature_columns": len(feature_columns),
        "complete_feature_rows": int(feature_frame.notna().all(axis=1).sum()),
        "any_feature_missing_rows": int(feature_frame.isna().any(axis=1).sum()),
    }


def _with_panel_context(table: pd.DataFrame, spec: PanelSpec) -> pd.DataFrame:
    output = table.copy()
    output.insert(0, "lag_suffix", spec.lag_suffix)
    output.insert(0, "target_column", spec.target_column)
    output.insert(0, "feature_set_role", spec.feature_set_role)
    output.insert(0, "comparison_group", spec.comparison_group)
    output.insert(0, "panel_role", spec.role)
    output.insert(0, "panel_label", spec.panel_label)
    output.insert(0, "panel_id", spec.panel_id)
    return output


def _add_metric_sample_context(
    table: pd.DataFrame,
    *,
    comparison_scope: str,
    panel: pd.DataFrame,
    feature_columns: list[str],
    split_rows: dict[str, int],
    split_countries: dict[str, int],
) -> None:
    table["comparison_scope"] = comparison_scope
    table["panel_rows"] = len(panel)
    table["panel_countries"] = panel["country_code"].nunique()
    table["feature_columns"] = len(feature_columns)
    for column, value in split_rows.items():
        table[column] = int(value)
    for column, value in split_countries.items():
        table[column] = int(value)


def _comparison_scope(spec: PanelSpec) -> str:
    if spec.feature_set_role in {"main_controls", "main_plus_submodel"}:
        return "same_sample_nested"
    return "own_sample_not_direct_ranking"


def _panel_comparison(experiments: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for experiment in experiments:
        all_sample = experiment["sample_summary"][experiment["sample_summary"]["split"].eq("all")].iloc[0]
        best_validation = (
            experiment["validation_metrics"]
            .sort_values(["mae", "rmse", "model"], na_position="last")
            .iloc[0]
        )
        test_metrics = experiment["test_metrics"].iloc[0]
        split_years = experiment["split_years"]
        rows.append(
            {
                "panel_id": experiment["panel_id"],
                "panel_label": experiment["panel_label"],
                "panel_role": experiment["panel_role"],
                "target_column": experiment["target_column"],
                "lag_suffix": experiment["lag_suffix"],
                "best_model": experiment["best_model"],
                "feature_columns": len(experiment["feature_columns"]),
                "rows": int(all_sample["rows"]),
                "countries": int(all_sample["countries"]),
                "train_year_start": min(split_years["train"]),
                "train_year_end": max(split_years["train"]),
                "validation_year_start": min(split_years["validation"]),
                "validation_year_end": max(split_years["validation"]),
                "test_year_start": min(split_years["test"]),
                "test_year_end": max(split_years["test"]),
                "validation_mae": float(best_validation["mae"]),
                "validation_rmse": float(best_validation["rmse"]),
                "test_mae": float(test_metrics["mae"]),
                "test_rmse": float(test_metrics["rmse"]),
                "test_oos_r2_vs_train_mean": float(test_metrics["oos_r2_vs_train_mean"]),
                "test_spearman": float(test_metrics["spearman"]),
                "n_test": int(test_metrics["n_test"]),
            }
        )
    return pd.DataFrame(rows)


def _best_prediction_safe_history_baseline(
    historical_baselines: pd.DataFrame,
    selected_model: str,
) -> pd.Series | None:
    if historical_baselines.empty:
        return None
    comparison = historical_baselines.copy()
    if "uses_test_labels" in comparison.columns:
        comparison = comparison[~comparison["uses_test_labels"].astype(bool)]
    comparison = comparison[~comparison["model"].eq(selected_model)]
    if comparison.empty:
        return None
    return comparison.sort_values(["mae", "rmse", "model"], na_position="last").iloc[0]
