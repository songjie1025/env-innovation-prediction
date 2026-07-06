"""Persistence-adjusted target experiments.

This script keeps the model pipeline unchanged and only changes the target form:

1. `delta_lag1` is the main supplemental task:
   y_t - y_{i,t-1}
2. `log_ratio_lag1` is a robustness task:
   log(y_t / y_{i,t-1})

The experiment compares Linear, RandomForest, and XGBoost separately for every
active v2 panel and for both `lag1_3_mean` and `lag1` predictor sets. Notebook
logic should call this script rather than duplicate computation.

Run:
    python 3_models/scripts/persistence_adjusted_modeling.py
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from model_config import OUTPUT_DIR, PANEL_CONFIGS, TRAIN_SHARE, VALIDATION_SHARE
from model_data import (
    chronological_train_validation_test_split,
    load_model_panel,
    matrix_from_panel,
    select_lag_features,
)
from model_estimators import build_linear_model_candidates, build_tree_model_candidates
from model_evaluation import (
    coefficient_table,
    evaluate_candidates_on_validation,
    evaluate_selected_model,
    feature_importance_table,
    select_best_validation_model,
)


FIG_DIR = Path(__file__).resolve().parents[2] / "4_analysis" / "figures" / "paper"
PERSISTENCE_OUTPUT = OUTPUT_DIR / "persistence_adjusted_model_family_comparison.csv"
PERSISTENCE_SUMMARY_OUTPUT = OUTPUT_DIR / "persistence_adjusted_model_family_summary.csv"
PERSISTENCE_RUN_SUMMARY_OUTPUT = OUTPUT_DIR / "persistence_adjusted_run_summary.md"
PERSISTENCE_IMPORTANCE_OUTPUT = OUTPUT_DIR / "persistence_adjusted_native_importance.csv"
PERSISTENCE_TOP_IMPORTANCE_OUTPUT = OUTPUT_DIR / "persistence_adjusted_top_interpretation_features.csv"
PERSISTENCE_LEVEL_CORRECTION_OUTPUT = OUTPUT_DIR / "persistence_adjusted_level_correction_predictions.csv"
PERSISTENCE_LEVEL_CORRECTION_SUMMARY_OUTPUT = OUTPUT_DIR / "persistence_adjusted_level_correction_summary.csv"
PERSISTENCE_VALIDATION_LEVEL_CORRECTION_OUTPUT = OUTPUT_DIR / "persistence_adjusted_validation_level_correction_predictions.csv"
PERSISTENCE_VALIDATION_LEVEL_CORRECTION_SUMMARY_OUTPUT = OUTPUT_DIR / "persistence_adjusted_validation_level_correction_summary.csv"
PERSISTENCE_VALIDATION_SELECTION_OUTPUT = OUTPUT_DIR / "persistence_adjusted_validation_model_selection.csv"
PERSISTENCE_VALIDATION_SELECTED_TEST_LEVEL_CORRECTION_OUTPUT = (
    OUTPUT_DIR / "persistence_adjusted_validation_selected_test_level_correction_predictions.csv"
)
PERSISTENCE_VALIDATION_SELECTED_TEST_LEVEL_CORRECTION_SUMMARY_OUTPUT = (
    OUTPUT_DIR / "persistence_adjusted_validation_selected_test_level_correction_summary.csv"
)
PERSISTENCE_FIGURE_OUTPUT = FIG_DIR / "fig12_persistence_adjusted_family_comparison.png"
PERSISTENCE_FIGURE_PDF_OUTPUT = FIG_DIR / "fig12_persistence_adjusted_family_comparison.pdf"
PERSISTENCE_IMPORTANCE_FIGURE_OUTPUT = FIG_DIR / "fig13_persistence_adjusted_delta_feature_roles.png"
PERSISTENCE_IMPORTANCE_FIGURE_PDF_OUTPUT = FIG_DIR / "fig13_persistence_adjusted_delta_feature_roles.pdf"
PERSISTENCE_SELECTION_FIGURE_OUTPUT = FIG_DIR / "fig14_persistence_adjusted_validation_selection.png"
PERSISTENCE_SELECTION_FIGURE_PDF_OUTPUT = FIG_DIR / "fig14_persistence_adjusted_validation_selection.pdf"

LAGS = ["lag1_3_mean", "lag1"]
TARGET_VARIANTS = [
    {
        "variant": "delta_lag1",
        "target_role": "main_supplement",
        "target_suffix": "delta_from_previous_year",
        "description": "Annual change from the same country's previous calendar-year target value.",
    },
    {
        "variant": "log_ratio_lag1",
        "target_role": "robustness",
        "target_suffix": "log_ratio_from_previous_year",
        "description": "Log ratio relative to the same country's previous calendar-year target value.",
    },
]

PANEL_SHORT = {"main": "Main", "suba": "SubA", "subb": "SubB", "subc": "SubC"}
FAMILY_COLORS = {"Linear": "#2F6DB5", "RandomForest": "#D9822B", "XGBoost": "#2E8B6F"}


def build_family_candidates(random_state: int = 42) -> dict[str, dict[str, Any]]:
    """Return separate candidate dictionaries for each model family."""
    linear = build_linear_model_candidates(random_state=random_state)
    tree = build_tree_model_candidates(random_state=random_state)
    families = {
        "Linear": linear,
        "RandomForest": {name: model for name, model in tree.items() if name.startswith("rf")},
        "XGBoost": {name: model for name, model in tree.items() if name.startswith("xgb")},
    }
    empty_families = [family for family, candidates in families.items() if not candidates]
    if empty_families:
        raise ValueError(f"Model family split produced empty candidate set(s): {empty_families}")
    return families


def build_persistence_adjusted_panel(
    panel: pd.DataFrame,
    *,
    target_column: str,
    variant: str,
) -> tuple[pd.DataFrame, str, dict[str, str]]:
    """Add a persistence-adjusted target and drop rows without prior target history."""
    metadata = _variant_metadata(variant)
    adjusted_target = f"{target_column}_{metadata['target_suffix']}"
    output = panel.sort_values(["country_code", "year"]).copy()
    output["previous_target_value"] = output.groupby("country_code")[target_column].shift(1)
    output["previous_target_year"] = output.groupby("country_code")["year"].shift(1)
    output["target_year_gap"] = output["year"] - output["previous_target_year"]
    non_annual_pairs = int(output["previous_target_value"].notna().sum() - output["target_year_gap"].eq(1).sum())

    if variant == "delta_lag1":
        output[adjusted_target] = output[target_column] - output["previous_target_value"]
    elif variant == "log_ratio_lag1":
        current = output[target_column].astype(float)
        previous = output["previous_target_value"].astype(float)
        positive_pair = current.gt(0) & previous.gt(0)
        output[adjusted_target] = np.nan
        output.loc[positive_pair, adjusted_target] = np.log(current[positive_pair] / previous[positive_pair])
    else:
        raise ValueError(f"Unsupported persistence-adjusted target variant: {variant}")

    annual = output["target_year_gap"].eq(1)
    adjusted = output[annual & output[adjusted_target].notna()].copy()
    if adjusted.empty:
        raise ValueError(f"Persistence-adjusted target produced no usable rows: {variant}")
    metadata["dropped_non_annual_pairs"] = str(non_annual_pairs)
    if variant == "log_ratio_lag1":
        nonpositive_pairs = int((annual & output["previous_target_value"].notna()).sum() - adjusted[adjusted_target].notna().sum())
        metadata["dropped_nonpositive_pairs"] = str(nonpositive_pairs)
    else:
        metadata["dropped_nonpositive_pairs"] = "0"
    return adjusted.reset_index(drop=True), adjusted_target, metadata


def build_native_importance_table(
    fitted_pipeline,
    feature_columns: list[str],
    *,
    model_name: str,
    family: str,
) -> pd.DataFrame:
    """Return a within-model normalized native importance table."""
    if family == "Linear":
        native = coefficient_table(fitted_pipeline, feature_columns, model_name)
        if native.empty:
            return _empty_importance_table()
        output = native.rename(columns={"coefficient": "signed_importance"}).copy()
        output["raw_importance"] = output["signed_importance"]
        output["abs_importance"] = output["abs_coefficient"]
        output["importance_kind"] = "standardized_coefficient"
    else:
        native = feature_importance_table(fitted_pipeline, feature_columns, model_name)
        if native.empty:
            return _empty_importance_table()
        output = native.rename(columns={"importance": "raw_importance"}).copy()
        output["signed_importance"] = np.nan
        output["abs_importance"] = output["raw_importance"].abs()
        output["importance_kind"] = "tree_feature_importance"

    total = float(output["abs_importance"].sum())
    output["normalized_importance"] = output["abs_importance"] / total if total > 0 else 0.0
    output["feature_label"] = output["feature"].map(_clean_feature_label)
    return output[
        [
            "model",
            "feature",
            "feature_label",
            "importance_kind",
            "raw_importance",
            "signed_importance",
            "abs_importance",
            "normalized_importance",
        ]
    ].sort_values("normalized_importance", ascending=False).reset_index(drop=True)


def run_persistence_adjusted_family_comparison(random_state: int = 42) -> pd.DataFrame:
    """Run family-separated model comparisons for delta and log-ratio targets."""
    results, _, _, _ = _run_persistence_adjusted_family_artifacts(random_state=random_state)
    return results


def _run_persistence_adjusted_family_artifacts(
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run family-separated model comparisons and collect native importance tables."""
    families = build_family_candidates(random_state=random_state)
    rows = []
    importance_frames = []
    level_correction_frames = []
    validation_level_correction_frames = []
    for target_variant in TARGET_VARIANTS:
        variant = target_variant["variant"]
        for cfg in PANEL_CONFIGS:
            original_target = cfg["target_column"]
            panel = load_model_panel(cfg["panel_path"], original_target)
            adjusted_panel, adjusted_target, metadata = build_persistence_adjusted_panel(
                panel,
                target_column=original_target,
                variant=variant,
            )
            for lag in LAGS:
                features = select_lag_features(adjusted_panel, lag)
                split = chronological_train_validation_test_split(
                    adjusted_panel,
                    train_share=TRAIN_SHARE,
                    validation_share=VALIDATION_SHARE,
                )
                x_train, y_train = matrix_from_panel(split.train, features, adjusted_target)
                x_validation, y_validation = matrix_from_panel(split.validation, features, adjusted_target)
                train_validation = pd.concat([split.train, split.validation], ignore_index=True)
                x_train_validation, y_train_validation = matrix_from_panel(
                    train_validation,
                    features,
                    adjusted_target,
                )
                x_test, y_test = matrix_from_panel(split.test, features, adjusted_target)
                zero_baseline = _zero_change_baseline(y_test)
                validation_zero_baseline = _zero_change_baseline(y_validation)

                for family, candidates in families.items():
                    validation_metrics, fitted_validation_models = evaluate_candidates_on_validation(
                        candidates,
                        x_train,
                        y_train,
                        x_validation,
                        y_validation,
                    )
                    if variant == "delta_lag1":
                        for _, validation_candidate in validation_metrics.iterrows():
                            candidate_model = str(validation_candidate["model"])
                            validation_predictions = fitted_validation_models[candidate_model].predict(x_validation)
                            validation_level_correction_frames.append(
                                build_validation_block_level_correction_predictions(
                                    split=split,
                                    source_target_column=original_target,
                                    delta_predictions=validation_predictions,
                                    history_panel=panel,
                                    metadata={
                                        "target_variant": variant,
                                        "target_role": metadata["target_role"],
                                        "adjusted_target_column": adjusted_target,
                                        "source_target_column": original_target,
                                        "panel_id": cfg["panel_id"],
                                        "panel_label": cfg["panel_label"],
                                        "lag_suffix": lag,
                                        "family": family,
                                        "best_model": candidate_model,
                                        "validation_delta_mae": float(validation_candidate["mae"]),
                                        "validation_delta_rmse": float(validation_candidate["rmse"]),
                                        "zero_change_validation_mae": validation_zero_baseline["mae"],
                                        "delta_validation_mae_vs_zero_change": float(validation_candidate["mae"])
                                        - validation_zero_baseline["mae"],
                                    },
                                )
                            )
                    best_model = select_best_validation_model(validation_metrics)
                    best_validation = validation_metrics[validation_metrics["model"].eq(best_model)].iloc[0]
                    test_metrics, fitted_model, test_predictions = evaluate_selected_model(
                        candidates[best_model],
                        best_model,
                        x_train_validation,
                        y_train_validation,
                        x_test,
                        y_test,
                        score_baseline_mean=float(y_train.mean()),
                    )
                    test_row = test_metrics.iloc[0]
                    rows.append(
                        {
                            "target_variant": variant,
                            "target_role": metadata["target_role"],
                            "adjusted_target_column": adjusted_target,
                            "source_target_column": original_target,
                            "dropped_non_annual_pairs": int(metadata["dropped_non_annual_pairs"]),
                            "dropped_nonpositive_pairs": int(metadata["dropped_nonpositive_pairs"]),
                            "panel_id": cfg["panel_id"],
                            "panel_label": cfg["panel_label"],
                            "lag_suffix": lag,
                            "family": family,
                            "best_model": best_model,
                            "n_features": len(features),
                            "panel_rows": len(adjusted_panel),
                            "panel_countries": adjusted_panel["country_code"].nunique(),
                            "train_year_start": min(split.train_years),
                            "train_year_end": max(split.train_years),
                            "validation_year_start": min(split.validation_years),
                            "validation_year_end": max(split.validation_years),
                            "test_year_start": min(split.test_years),
                            "test_year_end": max(split.test_years),
                            "n_train": len(split.train),
                            "n_validation": len(split.validation),
                            "n_test": int(test_row["n_test"]),
                            "validation_mae": float(best_validation["mae"]),
                            "test_mae": float(test_row["mae"]),
                            "test_minus_validation_mae": float(test_row["mae"]) - float(best_validation["mae"]),
                            "test_rmse": float(test_row["rmse"]),
                            "test_oos_r2_vs_train_mean": float(test_row["oos_r2_vs_train_mean"]),
                            "test_spearman": float(test_row["spearman"])
                            if pd.notna(test_row["spearman"])
                            else np.nan,
                            "zero_change_baseline_mae": zero_baseline["mae"],
                            "zero_change_baseline_rmse": zero_baseline["rmse"],
                            "delta_test_mae_vs_zero_change": float(test_row["mae"]) - zero_baseline["mae"],
                            "beats_zero_change_baseline": bool(float(test_row["mae"]) < zero_baseline["mae"]),
                        }
                    )
                    importance = build_native_importance_table(
                        fitted_model,
                        features,
                        model_name=best_model,
                        family=family,
                    )
                    if not importance.empty:
                        importance_frames.append(
                            importance.assign(
                                target_variant=variant,
                                target_role=metadata["target_role"],
                                adjusted_target_column=adjusted_target,
                                panel_id=cfg["panel_id"],
                                panel_label=cfg["panel_label"],
                                lag_suffix=lag,
                                family=family,
                                validation_mae=float(best_validation["mae"]),
                                test_mae=float(test_row["mae"]),
                                zero_change_baseline_mae=zero_baseline["mae"],
                                n_test=int(test_row["n_test"]),
                            )
                        )
                    if variant == "delta_lag1":
                        level_correction_frames.append(
                            build_block_safe_level_correction_predictions(
                                split=split,
                                source_target_column=original_target,
                                delta_predictions=test_predictions,
                                history_panel=panel,
                                metadata={
                                    "target_variant": variant,
                                    "target_role": metadata["target_role"],
                                    "adjusted_target_column": adjusted_target,
                                    "source_target_column": original_target,
                                    "panel_id": cfg["panel_id"],
                                    "panel_label": cfg["panel_label"],
                                    "lag_suffix": lag,
                                    "family": family,
                                    "best_model": best_model,
                                    "validation_mae": float(best_validation["mae"]),
                                    "delta_test_mae": float(test_row["mae"]),
                                    "zero_change_baseline_mae": zero_baseline["mae"],
                                    "delta_test_mae_vs_zero_change": float(test_row["mae"]) - zero_baseline["mae"],
                                },
                            )
                        )
                print(f"  done: {variant} / {cfg['panel_id']} / {lag}")
    importance_columns = [
        "target_variant",
        "target_role",
        "adjusted_target_column",
        "panel_id",
        "panel_label",
        "lag_suffix",
        "family",
        "model",
        "feature",
        "feature_label",
        "importance_kind",
        "raw_importance",
        "signed_importance",
        "abs_importance",
        "normalized_importance",
        "validation_mae",
        "test_mae",
        "zero_change_baseline_mae",
        "n_test",
    ]
    if importance_frames:
        importance_output = pd.concat(importance_frames, ignore_index=True).loc[:, importance_columns]
    else:
        importance_output = pd.DataFrame(columns=importance_columns)
    if level_correction_frames:
        level_correction_output = pd.concat(level_correction_frames, ignore_index=True)
    else:
        level_correction_output = pd.DataFrame()
    if validation_level_correction_frames:
        validation_level_correction_output = pd.concat(validation_level_correction_frames, ignore_index=True)
    else:
        validation_level_correction_output = pd.DataFrame()
    return pd.DataFrame(rows), importance_output, level_correction_output, validation_level_correction_output


def summarize_persistence_adjusted_results(results: pd.DataFrame) -> pd.DataFrame:
    """Validation-selected family per target variant, panel, and lag."""
    sort_columns = [
        "target_variant",
        "panel_id",
        "lag_suffix",
        "validation_mae",
        "family",
        "best_model",
    ]
    best = results.sort_values(sort_columns).groupby(
        ["target_variant", "target_role", "panel_id", "panel_label", "lag_suffix"],
        as_index=False,
    ).first()
    return best[
        [
            "target_variant",
            "target_role",
            "panel_id",
            "panel_label",
            "lag_suffix",
            "family",
            "best_model",
            "validation_mae",
            "test_mae",
            "test_minus_validation_mae",
            "zero_change_baseline_mae",
            "delta_test_mae_vs_zero_change",
            "beats_zero_change_baseline",
            "test_spearman",
            "n_test",
            "dropped_non_annual_pairs",
            "dropped_nonpositive_pairs",
        ]
    ]


def summarize_top_interpretation_features(
    importance: pd.DataFrame,
    summary: pd.DataFrame,
    *,
    target_variant: str = "delta_lag1",
    lag_suffix: str = "lag1_3_mean",
    top_n: int = 6,
) -> pd.DataFrame:
    """Top native-importance features for validation-selected models."""
    if importance.empty:
        return pd.DataFrame()
    selected = summary[
        summary["target_variant"].eq(target_variant) & summary["lag_suffix"].eq(lag_suffix)
    ][["target_variant", "panel_id", "lag_suffix", "family", "best_model"]].rename(
        columns={"best_model": "model"}
    )
    if selected.empty:
        return pd.DataFrame()
    output = importance.merge(
        selected,
        on=["target_variant", "panel_id", "lag_suffix", "family", "model"],
        how="inner",
    ).copy()
    output = output.sort_values(
        ["panel_id", "normalized_importance", "feature"],
        ascending=[True, False, True],
    )
    output["feature_rank"] = output.groupby("panel_id").cumcount() + 1
    output = output[output["feature_rank"].le(top_n)].copy()
    output["importance_direction"] = np.select(
        [
            output["signed_importance"].gt(0),
            output["signed_importance"].lt(0),
            output["signed_importance"].notna() & output["signed_importance"].abs().le(1e-12),
        ],
        ["positive_coefficient", "negative_coefficient", "zero_coefficient"],
        default="unsigned_tree_importance",
    )
    return output.reset_index(drop=True)


def build_block_safe_level_correction_predictions(
    *,
    split,
    source_target_column: str,
    delta_predictions: np.ndarray,
    metadata: dict[str, Any],
    history_panel: pd.DataFrame | None = None,
    forecast_frame: pd.DataFrame | None = None,
    forecast_years: list[int] | None = None,
    pretest_years: list[int] | None = None,
    forecast_block: str = "test",
    country_anchor_source: str = "country_latest_train_validation_target",
    global_anchor_source: str = "global_train_validation_mean",
) -> pd.DataFrame:
    """Convert predicted deltas into level forecasts without test-block target leakage.

    Forecast rows are recursively forecast from the latest country target
    available before the forecast block. The recursion updates with predicted
    deltas only, so later held-out years never receive earlier held-out labels
    as anchors.
    """
    test = (split.test if forecast_frame is None else forecast_frame).reset_index(drop=True).copy()
    predicted_delta = np.asarray(delta_predictions, dtype=float)
    if len(predicted_delta) != len(test):
        raise ValueError(
            "delta_predictions must align one-to-one with forecast rows: "
            f"{len(predicted_delta)} predictions for {len(test)} rows"
        )
    required_columns = {"country_code", "country_name", "year", source_target_column}
    missing = sorted(required_columns.difference(test.columns))
    if missing:
        raise ValueError(f"split.test missing required level-correction columns: {missing}")

    if pretest_years is None:
        pretest_year_set = set(split.train_years + split.validation_years)
    else:
        pretest_year_set = set(pretest_years)
    if history_panel is None:
        if pretest_years is None:
            pretest_history = pd.concat([split.train, split.validation], ignore_index=True).copy()
        else:
            split_history = pd.concat([split.train, split.validation, split.test], ignore_index=True)
            pretest_history = split_history[split_history["year"].isin(pretest_year_set)].copy()
    else:
        pretest_history = history_panel[history_panel["year"].isin(pretest_year_set)].copy()
    missing_history = sorted(required_columns.difference(pretest_history.columns))
    if missing_history:
        raise ValueError(f"history panel missing required level-correction columns: {missing_history}")
    if pretest_history.empty:
        raise ValueError("No pre-test target history available for level correction")

    global_anchor = float(pretest_history[source_target_column].mean())
    latest_country_targets = (
        pretest_history.sort_values(["country_code", "year"])
        .groupby("country_code", as_index=True)
        .tail(1)
        .set_index("country_code")[source_target_column]
    )
    latest_country_years = (
        pretest_history.sort_values(["country_code", "year"])
        .groupby("country_code", as_index=True)
        .tail(1)
        .set_index("country_code")["year"]
    )

    test["predicted_delta"] = predicted_delta
    rows: list[dict[str, object]] = []
    metadata_values = dict(metadata)
    active_forecast_years = split.test_years if forecast_years is None else forecast_years
    first_forecast_year = min(active_forecast_years)
    for country_code, country_rows in test.sort_values(["country_code", "year"]).groupby("country_code", sort=True):
        country_rows = country_rows.sort_values("year")
        country_test_years = [int(year) for year in country_rows["year"].tolist()]
        test_path_is_consecutive = country_test_years == list(range(country_test_years[0], country_test_years[-1] + 1))
        if country_code in latest_country_targets.index:
            anchor = float(latest_country_targets.loc[country_code])
            anchor_year = int(latest_country_years.loc[country_code])
            anchor_source = country_anchor_source
            if anchor_year >= first_forecast_year:
                raise ValueError(
                    "Level-correction country anchor must be before the forecast block: "
                    f"{country_code} anchor {anchor_year}, forecast starts {first_forecast_year}"
                )
            anchor_gap = country_test_years[0] - anchor_year
            forecast_path_eligible = bool(anchor_gap == 1 and test_path_is_consecutive)
        else:
            anchor = global_anchor
            anchor_year = np.nan
            anchor_source = global_anchor_source
            anchor_gap = np.nan
            forecast_path_eligible = False
        running_level = anchor
        for _, row in country_rows.iterrows():
            observed = float(row[source_target_column])
            history_prediction = anchor
            if forecast_path_eligible:
                running_level = running_level + float(row["predicted_delta"])
                corrected_prediction = running_level
                corrected_error = abs(observed - corrected_prediction)
            else:
                corrected_prediction = np.nan
                corrected_error = np.nan
            output_row = {
                **metadata_values,
                "country_code": row["country_code"],
                "country_name": row["country_name"],
                "year": int(row["year"]),
                "forecast_block": forecast_block,
                "observed_level": observed,
                "history_anchor_value": anchor,
                "history_anchor_year": anchor_year,
                "history_anchor_source": anchor_source,
                "anchor_to_first_forecast_gap_years": anchor_gap,
                "anchor_to_first_test_gap_years": anchor_gap,
                "forecast_path_is_consecutive": test_path_is_consecutive,
                "test_path_is_consecutive": test_path_is_consecutive,
                "forecast_path_eligible": forecast_path_eligible,
                "history_only_prediction": history_prediction,
                "predicted_delta": float(row["predicted_delta"]),
                "corrected_level_prediction": corrected_prediction,
                "absolute_error_history": abs(observed - history_prediction),
                "absolute_error_corrected": corrected_error,
                "uses_test_label_for_anchor": False,
            }
            if "previous_target_value" in row.index:
                output_row["actual_previous_target_value"] = row["previous_target_value"]
            rows.append(output_row)
    output = pd.DataFrame(rows).sort_values(["year", "country_code"]).reset_index(drop=True)
    key_columns = [
        column
        for column in ["target_variant", "panel_id", "lag_suffix", "family", "best_model", "country_code", "year"]
        if column in output.columns
    ]
    if output.duplicated(key_columns).any():
        duplicates = int(output.duplicated(key_columns, keep=False).sum())
        raise ValueError(f"Level-correction output has duplicate forecast keys: {duplicates} rows")
    return output


def build_validation_block_level_correction_predictions(
    *,
    split,
    source_target_column: str,
    delta_predictions: np.ndarray,
    metadata: dict[str, Any],
    history_panel: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Convert validation-block delta predictions to levels using train-only anchors."""
    return build_block_safe_level_correction_predictions(
        split=split,
        source_target_column=source_target_column,
        delta_predictions=delta_predictions,
        metadata=metadata,
        history_panel=history_panel,
        forecast_frame=split.validation,
        forecast_years=split.validation_years,
        pretest_years=split.train_years,
        forecast_block="validation",
        country_anchor_source="country_latest_train_target",
        global_anchor_source="global_train_mean",
    )


def summarize_level_correction_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    """Summarize block-safe corrected level forecasts against history-only baselines."""
    required_columns = {
        "observed_level",
        "history_only_prediction",
        "corrected_level_prediction",
    }
    missing = sorted(required_columns.difference(predictions.columns))
    if missing:
        raise ValueError(f"level correction predictions missing required columns: {missing}")
    group_columns = [
        column
        for column in [
            "target_variant",
            "target_role",
            "forecast_block",
            "panel_id",
            "panel_label",
            "lag_suffix",
            "family",
            "best_model",
        ]
        if column in predictions.columns
    ]
    if not group_columns:
        grouped = [((), predictions)]
    else:
        grouped = predictions.groupby(group_columns, dropna=False)

    rows = []
    for keys, group in grouped:
        key_values = keys if isinstance(keys, tuple) else (keys,)
        row = dict(zip(group_columns, key_values))
        base_eligible = (
            group["forecast_path_eligible"].fillna(False).astype(bool)
            if "forecast_path_eligible" in group.columns
            else pd.Series(True, index=group.index)
        )
        fallback_anchor = (
            group["history_anchor_source"].astype(str).str.startswith("global_")
            if "history_anchor_source" in group.columns
            else pd.Series(False, index=group.index)
        )
        eligible = base_eligible & ~fallback_anchor
        eligible_group = group[eligible].copy()
        fallback_count = (
            int(fallback_anchor.sum())
            if "history_anchor_source" in group.columns
            else 0
        )
        excluded_count = int((~eligible).sum())
        if eligible_group.empty:
            history_metrics = _basic_prediction_metrics([], [])
            corrected_metrics = _basic_prediction_metrics([], [])
            test_year_start = np.nan
            test_year_end = np.nan
        else:
            observed = eligible_group["observed_level"].astype(float)
            history_prediction = eligible_group["history_only_prediction"].astype(float)
            corrected_prediction = eligible_group["corrected_level_prediction"].astype(float)
            history_metrics = _basic_prediction_metrics(observed, history_prediction)
            corrected_metrics = _basic_prediction_metrics(observed, corrected_prediction)
            test_year_start = int(eligible_group["year"].min()) if "year" in eligible_group.columns else np.nan
            test_year_end = int(eligible_group["year"].max()) if "year" in eligible_group.columns else np.nan
        row.update(
            {
                "n_forecast": int(len(eligible_group)),
                "n_test": int(len(eligible_group)),
                "n_forecast_total": int(len(group)),
                "n_test_total": int(len(group)),
                "n_forecast_excluded_anchor_gap": excluded_count,
                "n_test_excluded_anchor_gap": excluded_count,
                "global_fallback_anchor_rows": fallback_count,
                "test_year_start": test_year_start,
                "test_year_end": test_year_end,
                "history_only_mae": history_metrics["mae"],
                "corrected_level_mae": corrected_metrics["mae"],
                "delta_corrected_mae_minus_history": corrected_metrics["mae"] - history_metrics["mae"],
                "beats_history_only": bool(corrected_metrics["mae"] < history_metrics["mae"])
                if pd.notna(corrected_metrics["mae"]) and pd.notna(history_metrics["mae"])
                else False,
                "history_only_rmse": history_metrics["rmse"],
                "corrected_level_rmse": corrected_metrics["rmse"],
                "delta_corrected_rmse_minus_history": corrected_metrics["rmse"] - history_metrics["rmse"],
                "history_only_spearman": history_metrics["spearman"],
                "corrected_level_spearman": corrected_metrics["spearman"],
            }
        )
        rows.append(row)
    sort_columns = [column for column in ["target_variant", "panel_id", "lag_suffix", "family"] if column in group_columns]
    output = pd.DataFrame(rows)
    return output.sort_values(sort_columns).reset_index(drop=True) if sort_columns else output


def select_validation_level_models(validation_summary: pd.DataFrame) -> pd.DataFrame:
    """Select one level-forecasting specification per target and panel using validation only."""
    required_columns = {
        "target_variant",
        "panel_id",
        "lag_suffix",
        "family",
        "best_model",
        "corrected_level_mae",
        "corrected_level_rmse",
    }
    count_column = "n_forecast" if "n_forecast" in validation_summary.columns else "n_test"
    required_columns.add(count_column)
    missing = sorted(required_columns.difference(validation_summary.columns))
    if missing:
        raise ValueError(f"validation_summary missing required selection columns: {missing}")
    candidates = validation_summary.copy()
    if "n_forecast" not in candidates.columns and "n_test" in candidates.columns:
        candidates["n_forecast"] = candidates["n_test"]
    if "forecast_block" in candidates.columns:
        candidates = candidates[candidates["forecast_block"].eq("validation")].copy()
    candidates = candidates[
        candidates["n_forecast"].gt(0) & candidates["corrected_level_mae"].notna()
    ].copy()
    if candidates.empty:
        return pd.DataFrame(
            columns=list(validation_summary.columns)
            + ["selection_metric", "selection_scope", "selection_rank"]
        )
    group_columns = [
        column
        for column in ["target_variant", "target_role", "panel_id", "panel_label"]
        if column in candidates.columns
    ]
    sort_columns = group_columns + [
        "corrected_level_mae",
        "corrected_level_rmse",
        "lag_suffix",
        "family",
        "best_model",
    ]
    selected = candidates.sort_values(sort_columns, na_position="last").groupby(
        group_columns,
        as_index=False,
    ).first()
    selected["selection_metric"] = "validation_corrected_level_mae"
    selected["selection_scope"] = "target_variant_panel"
    selected["selection_rank"] = 1
    return selected.reset_index(drop=True)


def build_validation_selected_test_level_correction_predictions(
    validation_selection: pd.DataFrame,
    *,
    random_state: int = 42,
) -> pd.DataFrame:
    """Evaluate validation-level-selected specs once on the held-out test block."""
    if validation_selection.empty:
        return pd.DataFrame()
    families = build_family_candidates(random_state=random_state)
    panel_configs = {cfg["panel_id"]: cfg for cfg in PANEL_CONFIGS}
    frames = []
    for _, selected in validation_selection.iterrows():
        variant = str(selected["target_variant"])
        cfg = panel_configs[str(selected["panel_id"])]
        original_target = cfg["target_column"]
        panel = load_model_panel(cfg["panel_path"], original_target)
        adjusted_panel, adjusted_target, metadata = build_persistence_adjusted_panel(
            panel,
            target_column=original_target,
            variant=variant,
        )
        lag = str(selected["lag_suffix"])
        family = str(selected["family"])
        model_name = str(selected["best_model"])
        features = select_lag_features(adjusted_panel, lag)
        split = chronological_train_validation_test_split(
            adjusted_panel,
            train_share=TRAIN_SHARE,
            validation_share=VALIDATION_SHARE,
        )
        train_validation = pd.concat([split.train, split.validation], ignore_index=True)
        x_train_validation, y_train_validation = matrix_from_panel(
            train_validation,
            features,
            adjusted_target,
        )
        x_test, y_test = matrix_from_panel(split.test, features, adjusted_target)
        test_metrics, _, test_predictions = evaluate_selected_model(
            families[family][model_name],
            model_name,
            x_train_validation,
            y_train_validation,
            x_test,
            y_test,
            score_baseline_mean=float(split.train[adjusted_target].mean()),
        )
        test_row = test_metrics.iloc[0]
        frames.append(
            build_block_safe_level_correction_predictions(
                split=split,
                source_target_column=original_target,
                delta_predictions=test_predictions,
                history_panel=panel,
                metadata={
                    "target_variant": variant,
                    "target_role": metadata["target_role"],
                    "adjusted_target_column": adjusted_target,
                    "source_target_column": original_target,
                    "panel_id": cfg["panel_id"],
                    "panel_label": cfg["panel_label"],
                    "lag_suffix": lag,
                    "family": family,
                    "best_model": model_name,
                    "selection_metric": selected.get("selection_metric", "validation_corrected_level_mae"),
                    "validation_corrected_level_mae": float(selected["corrected_level_mae"]),
                    "validation_history_only_mae": float(selected["history_only_mae"]),
                    "delta_test_mae": float(test_row["mae"]),
                },
            )
        )
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _basic_prediction_metrics(y_true, y_pred) -> dict[str, float]:
    observed = np.asarray(y_true, dtype=float)
    prediction = np.asarray(y_pred, dtype=float)
    finite = np.isfinite(observed) & np.isfinite(prediction)
    observed = observed[finite]
    prediction = prediction[finite]
    if len(observed) == 0:
        return {"mae": np.nan, "rmse": np.nan, "spearman": np.nan}
    residuals = observed - prediction
    mae = float(np.mean(np.abs(residuals)))
    rmse = float(np.sqrt(np.mean(np.square(residuals))))
    if len(np.unique(observed)) < 2 or len(np.unique(prediction)) < 2:
        spearman = np.nan
    else:
        spearman = pd.Series(observed).corr(pd.Series(prediction), method="spearman")
    return {
        "mae": mae,
        "rmse": rmse,
        "spearman": float(spearman) if pd.notna(spearman) else np.nan,
    }


def write_run_summary(
    results: pd.DataFrame,
    summary: pd.DataFrame,
    level_correction_summary: pd.DataFrame | None = None,
    validation_selection: pd.DataFrame | None = None,
) -> None:
    """Write a compact markdown summary for notebook display."""
    lines = [
        "# Persistence-Adjusted Target Run Summary",
        "",
        "This run treats the original level-target persistence result as the first finding, then adds a supplemental target task.",
        "",
        "Target variants:",
        "",
    ]
    for item in TARGET_VARIANTS:
        lines.append(f"- `{item['variant']}` ({item['target_role']}): {item['description']}")
    lines.extend(
        [
            "",
            "All rows use the same chronological 80/10/10 split rule within each adjusted panel.",
            "The baseline is a zero-change baseline on the adjusted target, equivalent to predicting no movement from the previous calendar-year target value.",
            "",
            "## Validation-Selected Family Per Panel And Lag",
            "",
            _table_to_markdown(summary),
            "",
        ]
    )
    if level_correction_summary is not None and not level_correction_summary.empty:
        lines.extend(
            [
                "## Block-Safe Delta-To-Level Correction",
                "",
                "Delta predictions are recursively added to the latest pre-test country target value.",
                "The corrected level forecast is compared with the country latest pre-test hold-constant baseline on the original level target scale.",
                "",
                _table_to_markdown(
                    level_correction_summary[
                        [
                            "target_variant",
                            "panel_id",
                            "lag_suffix",
                            "family",
                            "best_model",
                            "history_only_mae",
                            "corrected_level_mae",
                            "delta_corrected_mae_minus_history",
                            "beats_history_only",
                            "corrected_level_spearman",
                            "n_forecast",
                            "n_forecast_total",
                            "n_forecast_excluded_anchor_gap",
                            "global_fallback_anchor_rows",
                        ]
                    ]
                ),
                "",
            ]
        )
    if validation_selection is not None and not validation_selection.empty:
        lines.extend(
            [
                "## Validation-Only Level-Forecast Model Selection",
                "",
                "Candidate delta models are selected using validation corrected-level MAE only.",
                "Test corrected-level results are not used in this selection table.",
                "",
                _table_to_markdown(
                    validation_selection[
                        [
                            "target_variant",
                            "panel_id",
                            "lag_suffix",
                            "family",
                            "best_model",
                            "history_only_mae",
                            "corrected_level_mae",
                            "delta_corrected_mae_minus_history",
                            "beats_history_only",
                            "n_forecast",
                            "n_forecast_total",
                            "n_forecast_excluded_anchor_gap",
                            "selection_metric",
                        ]
                    ]
                ),
                "",
            ]
        )
    lines.extend(
        [
            "## Full Family Comparison",
            "",
            _table_to_markdown(
                results[
                    [
                        "target_variant",
                        "panel_id",
                        "lag_suffix",
                        "family",
                        "best_model",
                        "validation_mae",
                        "test_mae",
                        "test_minus_validation_mae",
                        "zero_change_baseline_mae",
                        "delta_test_mae_vs_zero_change",
                        "beats_zero_change_baseline",
                        "n_test",
                        "dropped_non_annual_pairs",
                        "dropped_nonpositive_pairs",
                    ]
                ]
            ),
            "",
        ]
    )
    PERSISTENCE_RUN_SUMMARY_OUTPUT.write_text("\n".join(lines))


def make_persistence_adjusted_figure(results: pd.DataFrame) -> None:
    """Write a compact figure comparing families against zero-change baseline."""
    os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "env_innovation_matplotlib"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="whitegrid", context="paper", font_scale=1.05)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    plot_data = results[
        results["target_variant"].eq("delta_lag1") & results["lag_suffix"].eq("lag1_3_mean")
    ].copy()
    if plot_data.empty:
        return
    panels = [panel for panel in ["main", "suba", "subb", "subc"] if panel in set(plot_data["panel_id"])]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    fig.suptitle("Delta target family comparison (test MAE, lag1-3 mean predictors)", fontweight="bold")
    for ax, panel_id in zip(axes.ravel(), panels):
        panel_data = plot_data[plot_data["panel_id"].eq(panel_id)]
        families = ["Linear", "RandomForest", "XGBoost"]
        values = [float(panel_data[panel_data["family"].eq(family)]["test_mae"].iloc[0]) for family in families]
        baseline = float(panel_data["zero_change_baseline_mae"].iloc[0])
        bars = ax.bar(families, values, color=[FAMILY_COLORS[family] for family in families], edgecolor="white")
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value, f"{value:.3f}", ha="center", va="bottom", fontsize=9)
        ax.axhline(baseline, color="#1F2937", linestyle="--", linewidth=1.4)
        ax.set_title(f"{PANEL_SHORT.get(panel_id, panel_id)}", loc="left")
        ax.set_ylabel("MAE")
        ax.set_ylim(0, max(max(values), baseline) * 1.25 if max(max(values), baseline) > 0 else 1)
    fig.savefig(PERSISTENCE_FIGURE_OUTPUT, bbox_inches="tight")
    fig.savefig(PERSISTENCE_FIGURE_PDF_OUTPUT, bbox_inches="tight")
    plt.close(fig)


def make_persistence_adjusted_importance_figure(top_importance: pd.DataFrame) -> None:
    """Write a compact top-feature figure for validation-selected delta models."""
    if top_importance.empty:
        return
    os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "env_innovation_matplotlib"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="whitegrid", context="paper", font_scale=1.0)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    panels = [panel for panel in ["main", "suba", "subb", "subc"] if panel in set(top_importance["panel_id"])]
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.5), constrained_layout=False)
    fig.subplots_adjust(left=0.27, right=0.98, top=0.90, bottom=0.12, hspace=0.38, wspace=0.75)
    fig.suptitle("Top predictor roles in validation-selected delta models", fontweight="bold")
    direction_colors = {
        "positive_coefficient": "#2E8B6F",
        "negative_coefficient": "#B85C5C",
        "zero_coefficient": "#9CA3AF",
        "unsigned_tree_importance": "#4C78A8",
    }
    for ax, panel_id in zip(axes.ravel(), panels):
        panel_data = top_importance[top_importance["panel_id"].eq(panel_id)].copy()
        panel_data = panel_data.sort_values("normalized_importance", ascending=True)
        colors = [direction_colors[item] for item in panel_data["importance_direction"]]
        ax.barh(panel_data["feature_label"], panel_data["normalized_importance"] * 100, color=colors)
        model_label = f"{panel_data['family'].iloc[0]}: {panel_data['model'].iloc[0]}"
        ax.set_title(f"{PANEL_SHORT.get(panel_id, panel_id)} | {model_label}", loc="left", fontsize=10)
        ax.set_xlabel("Within-model native importance (%)")
        ax.set_ylabel("")
        ax.tick_params(axis="y", labelsize=8)
        max_value = float((panel_data["normalized_importance"] * 100).max())
        ax.set_xlim(0, max(max_value * 1.05, 1.0))
    for ax in axes.ravel()[len(panels) :]:
        ax.axis("off")
    fig.text(
        0.5,
        0.035,
        "Within-model normalized native importance; coefficient sign is shown only for linear models.",
        ha="center",
        fontsize=8,
        color="#4B5563",
    )
    fig.savefig(PERSISTENCE_IMPORTANCE_FIGURE_OUTPUT, bbox_inches="tight")
    fig.savefig(PERSISTENCE_IMPORTANCE_FIGURE_PDF_OUTPUT, bbox_inches="tight")
    plt.close(fig)


def make_persistence_validation_selection_figure(
    validation_selection: pd.DataFrame,
    selected_test_level_summary: pd.DataFrame,
) -> None:
    """Write validation-selection diagnostics without using test for selection."""
    if validation_selection.empty:
        return
    os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "env_innovation_matplotlib"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="whitegrid", context="paper", font_scale=1.0)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    selected = validation_selection.copy()
    selected["panel_short"] = selected["panel_id"].map(PANEL_SHORT).fillna(selected["panel_id"])
    join_keys = [
        column
        for column in ["target_variant", "panel_id", "lag_suffix", "family", "best_model"]
        if column in selected.columns and column in selected_test_level_summary.columns
    ]
    gap = selected.merge(
        selected_test_level_summary,
        on=join_keys,
        how="left",
        suffixes=("_validation", "_test"),
    )
    gap["panel_short"] = gap["panel_id"].map(PANEL_SHORT).fillna(gap["panel_id"])

    family_short = {"RandomForest": "RF", "XGBoost": "XGB", "Linear": "Linear"}
    selected["tick_label"] = (
        selected["panel_short"]
        + "\n"
        + selected["family"].map(family_short).fillna(selected["family"])
        + " "
        + selected["lag_suffix"].replace({"lag1_3_mean": "lag1-3", "lag1": "lag1"})
    )

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8), constrained_layout=True)
    x = np.arange(len(selected))
    width = 0.36
    axes[0].bar(
        x - width / 2,
        selected["history_only_mae"],
        width=width,
        label="History-only",
        color="#9CA3AF",
    )
    axes[0].bar(
        x + width / 2,
        selected["corrected_level_mae"],
        width=width,
        label="Delta-corrected",
        color="#2F6DB5",
    )
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(selected["tick_label"], rotation=0)
    axes[0].set_title("Validation-only selected specs", loc="left", fontweight="bold")
    axes[0].set_ylabel("Validation level MAE")
    axes[0].legend(frameon=False)

    finite_gap = gap.dropna(subset=["corrected_level_mae_validation", "corrected_level_mae_test"]).copy()
    if not finite_gap.empty:
        axes[1].scatter(
            finite_gap["corrected_level_mae_validation"],
            finite_gap["corrected_level_mae_test"],
            s=70,
            color="#D9822B",
            edgecolor="white",
            linewidth=0.8,
        )
        for _, row in finite_gap.iterrows():
            axes[1].text(
                float(row["corrected_level_mae_validation"]),
                float(row["corrected_level_mae_test"]),
                str(row["panel_short"]),
                fontsize=8,
                ha="left",
                va="bottom",
            )
        max_value = float(
            np.nanmax(
                [
                    finite_gap["corrected_level_mae_validation"].max(),
                    finite_gap["corrected_level_mae_test"].max(),
                ]
            )
        )
        axes[1].plot([0, max_value], [0, max_value], color="#6B7280", linestyle="--", linewidth=1)
        axes[1].set_xlim(0, max_value * 1.08 if max_value > 0 else 1)
        axes[1].set_ylim(0, max_value * 1.08 if max_value > 0 else 1)
    axes[1].set_title("Generalization gap after validation selection", loc="left", fontweight="bold")
    axes[1].set_xlabel("Validation corrected-level MAE")
    axes[1].set_ylabel("Test corrected-level MAE")

    fig.savefig(PERSISTENCE_SELECTION_FIGURE_OUTPUT, bbox_inches="tight")
    fig.savefig(PERSISTENCE_SELECTION_FIGURE_PDF_OUTPUT, bbox_inches="tight")
    plt.close(fig)


def load_validation_selection_notebook_tables(output_dir: Path = OUTPUT_DIR) -> dict[str, pd.DataFrame]:
    """Load display-ready validation-selection tables for notebooks."""
    paths = {
        "family_summary": output_dir / PERSISTENCE_SUMMARY_OUTPUT.name,
        "validation_level_summary": output_dir / PERSISTENCE_VALIDATION_LEVEL_CORRECTION_SUMMARY_OUTPUT.name,
        "validation_selection": output_dir / PERSISTENCE_VALIDATION_SELECTION_OUTPUT.name,
        "validation_selected_test_level_summary": output_dir
        / PERSISTENCE_VALIDATION_SELECTED_TEST_LEVEL_CORRECTION_SUMMARY_OUTPUT.name,
    }
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing validation-selection artifact(s): {missing}")
    family_summary = pd.read_csv(paths["family_summary"])
    validation_level_summary = pd.read_csv(paths["validation_level_summary"])
    validation_selection = pd.read_csv(paths["validation_selection"])
    validation_selected_test_level_summary = pd.read_csv(paths["validation_selected_test_level_summary"])
    validation_candidates = validation_level_summary.sort_values(
        [
            "target_variant",
            "panel_id",
            "corrected_level_mae",
            "corrected_level_rmse",
            "lag_suffix",
            "family",
            "best_model",
        ],
        na_position="last",
    ).reset_index(drop=True)
    join_keys = [
        column
        for column in ["target_variant", "panel_id", "lag_suffix", "family", "best_model"]
        if column in validation_selection.columns and column in validation_selected_test_level_summary.columns
    ]
    validation_test_gap = validation_selection.merge(
        validation_selected_test_level_summary,
        on=join_keys,
        how="left",
        suffixes=("_validation", "_test"),
    )
    if {"corrected_level_mae_validation", "corrected_level_mae_test"}.issubset(validation_test_gap.columns):
        validation_test_gap["test_minus_validation_corrected_level_mae"] = (
            validation_test_gap["corrected_level_mae_test"]
            - validation_test_gap["corrected_level_mae_validation"]
        )
    return {
        "family_summary": family_summary,
        "validation_level_summary": validation_level_summary,
        "validation_candidates": validation_candidates,
        "validation_selection": validation_selection,
        "validation_selected_test_level_summary": validation_selected_test_level_summary,
        "validation_test_gap": validation_test_gap,
    }


def _validation_artifact_schema(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop legacy test-named aliases from validation-facing artifacts."""
    legacy_columns = [
        "anchor_to_first_test_gap_years",
        "test_path_is_consecutive",
        "n_test",
        "n_test_total",
        "n_test_excluded_anchor_gap",
    ]
    return frame.drop(columns=[column for column in legacy_columns if column in frame.columns])


def run_and_write_outputs(random_state: int = 42) -> dict[str, pd.DataFrame]:
    """Run the experiment and write CSV, markdown, and figure outputs."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results, importance, level_correction, validation_level_correction = _run_persistence_adjusted_family_artifacts(
        random_state=random_state
    )
    summary = summarize_persistence_adjusted_results(results)
    level_correction_summary = summarize_level_correction_predictions(level_correction)
    validation_level_correction_summary = summarize_level_correction_predictions(validation_level_correction)
    validation_selection = select_validation_level_models(validation_level_correction_summary)
    validation_selected_test_level_correction = build_validation_selected_test_level_correction_predictions(
        validation_selection,
        random_state=random_state,
    )
    validation_selected_test_level_correction_summary = summarize_level_correction_predictions(
        validation_selected_test_level_correction
    )
    top_importance = summarize_top_interpretation_features(importance, summary)
    results.to_csv(PERSISTENCE_OUTPUT, index=False)
    summary.to_csv(PERSISTENCE_SUMMARY_OUTPUT, index=False)
    importance.to_csv(PERSISTENCE_IMPORTANCE_OUTPUT, index=False)
    top_importance.to_csv(PERSISTENCE_TOP_IMPORTANCE_OUTPUT, index=False)
    level_correction.to_csv(PERSISTENCE_LEVEL_CORRECTION_OUTPUT, index=False)
    level_correction_summary.to_csv(PERSISTENCE_LEVEL_CORRECTION_SUMMARY_OUTPUT, index=False)
    _validation_artifact_schema(validation_level_correction).to_csv(
        PERSISTENCE_VALIDATION_LEVEL_CORRECTION_OUTPUT,
        index=False,
    )
    _validation_artifact_schema(validation_level_correction_summary).to_csv(
        PERSISTENCE_VALIDATION_LEVEL_CORRECTION_SUMMARY_OUTPUT,
        index=False,
    )
    _validation_artifact_schema(validation_selection).to_csv(
        PERSISTENCE_VALIDATION_SELECTION_OUTPUT,
        index=False,
    )
    validation_selected_test_level_correction.to_csv(
        PERSISTENCE_VALIDATION_SELECTED_TEST_LEVEL_CORRECTION_OUTPUT,
        index=False,
    )
    validation_selected_test_level_correction_summary.to_csv(
        PERSISTENCE_VALIDATION_SELECTED_TEST_LEVEL_CORRECTION_SUMMARY_OUTPUT,
        index=False,
    )
    write_run_summary(results, summary, level_correction_summary, validation_selection)
    make_persistence_adjusted_figure(results)
    make_persistence_adjusted_importance_figure(top_importance)
    make_persistence_validation_selection_figure(
        validation_selection,
        validation_selected_test_level_correction_summary,
    )
    return {
        "results": results,
        "summary": summary,
        "importance": importance,
        "top_importance": top_importance,
        "level_correction": level_correction,
        "level_correction_summary": level_correction_summary,
        "validation_level_correction": validation_level_correction,
        "validation_level_correction_summary": validation_level_correction_summary,
        "validation_selection": validation_selection,
        "validation_selected_test_level_correction": validation_selected_test_level_correction,
        "validation_selected_test_level_correction_summary": validation_selected_test_level_correction_summary,
    }


def _variant_metadata(variant: str) -> dict[str, str]:
    for item in TARGET_VARIANTS:
        if item["variant"] == variant:
            return dict(item)
    raise ValueError(f"Unsupported persistence-adjusted target variant: {variant}")


def _table_to_markdown(frame: pd.DataFrame) -> str:
    try:
        return frame.to_markdown(index=False)
    except ImportError:
        return "```text\n" + frame.to_string(index=False) + "\n```"


def _empty_importance_table() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "model",
            "feature",
            "feature_label",
            "importance_kind",
            "raw_importance",
            "signed_importance",
            "abs_importance",
            "normalized_importance",
        ]
    )


def _clean_feature_label(feature: str) -> str:
    label = feature
    label = label.replace("_lag1_3_mean", " (lag 1-3 mean)")
    label = label.replace("_lag1", " (lag 1)")
    label = label.replace("env_patent_share_inventions", "environmental patent share")
    label = label.replace("env_technology_rta", "environmental technology RTA")
    label = label.replace("co2_per_capita_ar5", "CO2 per capita")
    label = label.replace("fdi_net_inflows", "FDI net inflows")
    label = label.replace("gdp_constant_2015_usd", "GDP")
    label = label.replace("scientific_journal_articles", "scientific articles")
    label = label.replace("high_tech_exports_pct_manufactured_exports", "high-tech export share")
    label = label.replace("high_tech_exports", "high-tech exports")
    label = label.replace("researchers_per_million", "researchers per million")
    label = label.replace("rd_expenditure_pct_gdp", "R&D expenditure share")
    label = label.replace("rd_expenditure_gdp", "R&D expenditure share")
    label = label.replace("patent_co_inventions_share", "co-invention share")
    label = label.replace("env_co_invention_share", "environmental co-invention share")
    label = label.replace("environmental_tax_revenue_pct_gdp", "environmental tax revenue")
    label = label.replace("size_factor", "economic/research scale factor")
    label = label.replace("rise_", "RISE ")
    label = label.replace("eps_", "EPS ")
    label = label.replace("_", " ")
    return label


def _zero_change_baseline(y_test: pd.Series) -> dict[str, float]:
    observed = y_test.to_numpy(dtype=float)
    return {
        "mae": float(np.mean(np.abs(observed))),
        "rmse": float(np.sqrt(np.mean(np.square(observed)))),
    }


def main() -> None:
    outputs = run_and_write_outputs(random_state=42)
    print("\n=== Persistence-adjusted target summary ===")
    print(
        outputs["summary"][
            [
                "target_variant",
                "panel_id",
                "lag_suffix",
                "family",
                "best_model",
                "test_mae",
                "test_minus_validation_mae",
                "zero_change_baseline_mae",
                "delta_test_mae_vs_zero_change",
                "beats_zero_change_baseline",
            ]
        ].to_string(index=False)
    )
    print(f"\nwrote {PERSISTENCE_OUTPUT}")
    print(f"wrote {PERSISTENCE_SUMMARY_OUTPUT}")
    print(f"wrote {PERSISTENCE_RUN_SUMMARY_OUTPUT}")
    print(f"wrote {PERSISTENCE_IMPORTANCE_OUTPUT}")
    print(f"wrote {PERSISTENCE_TOP_IMPORTANCE_OUTPUT}")
    print(f"wrote {PERSISTENCE_LEVEL_CORRECTION_OUTPUT}")
    print(f"wrote {PERSISTENCE_LEVEL_CORRECTION_SUMMARY_OUTPUT}")
    print(f"wrote {PERSISTENCE_VALIDATION_LEVEL_CORRECTION_OUTPUT}")
    print(f"wrote {PERSISTENCE_VALIDATION_LEVEL_CORRECTION_SUMMARY_OUTPUT}")
    print(f"wrote {PERSISTENCE_VALIDATION_SELECTION_OUTPUT}")
    print(f"wrote {PERSISTENCE_VALIDATION_SELECTED_TEST_LEVEL_CORRECTION_OUTPUT}")
    print(f"wrote {PERSISTENCE_VALIDATION_SELECTED_TEST_LEVEL_CORRECTION_SUMMARY_OUTPUT}")
    print(f"wrote {PERSISTENCE_FIGURE_OUTPUT}")
    print(f"wrote {PERSISTENCE_IMPORTANCE_FIGURE_OUTPUT}")
    print(f"wrote {PERSISTENCE_SELECTION_FIGURE_OUTPUT}")


if __name__ == "__main__":
    main()
