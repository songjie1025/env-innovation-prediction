from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone


def compute_regression_metrics(
    y_true: pd.Series | np.ndarray,
    y_pred: pd.Series | np.ndarray,
    train_mean: float,
) -> dict[str, float]:
    """Compute headline regression metrics for one held-out split."""
    y_true_array = np.asarray(y_true, dtype=float)
    y_pred_array = np.asarray(y_pred, dtype=float)
    residuals = y_true_array - y_pred_array
    mae = float(np.mean(np.abs(residuals)))
    rmse = float(math.sqrt(np.mean(residuals**2)))
    denominator = float(np.sum((y_true_array - train_mean) ** 2))
    oos_r2 = float("nan") if denominator == 0 else float(1 - np.sum(residuals**2) / denominator)
    if len(np.unique(y_true_array)) < 2 or len(np.unique(y_pred_array)) < 2:
        spearman = float("nan")
    else:
        spearman = pd.Series(y_true_array).corr(pd.Series(y_pred_array), method="spearman")
    return {
        "mae": mae,
        "rmse": rmse,
        "oos_r2_vs_train_mean": oos_r2,
        "spearman": float(spearman) if pd.notna(spearman) else float("nan"),
    }


def evaluate_candidates_on_validation(
    candidates: dict[str, object],
    x_train: pd.DataFrame,
    y_train: pd.Series,
    x_validation: pd.DataFrame,
    y_validation: pd.Series,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Fit each candidate on train years only and score on validation years."""
    rows: list[dict[str, object]] = []
    fitted_models: dict[str, object] = {}
    train_mean = float(y_train.mean())
    for model_name, estimator in candidates.items():
        fitted = clone(estimator)
        fitted.fit(x_train, y_train)
        predictions = fitted.predict(x_validation)
        metrics = compute_regression_metrics(y_validation, predictions, train_mean)
        rows.append(
            {
                "model": model_name,
                "split": "validation",
                "train_year_start": int(x_train.attrs.get("year_start", -1)),
                "train_year_end": int(x_train.attrs.get("year_end", -1)),
                "validation_year_start": int(x_validation.attrs.get("year_start", -1)),
                "validation_year_end": int(x_validation.attrs.get("year_end", -1)),
                "n_train": int(len(y_train)),
                "n_validation": int(len(y_validation)),
                **metrics,
            }
        )
        fitted_models[model_name] = fitted
    return pd.DataFrame(rows).sort_values(["mae", "rmse", "model"]).reset_index(drop=True), fitted_models


def select_best_validation_model(validation_metrics: pd.DataFrame) -> str:
    """Select the model with the lowest validation MAE, then RMSE, then name."""
    required = {"model", "split", "mae"}
    missing = required.difference(validation_metrics.columns)
    if missing:
        raise ValueError(f"Validation metrics missing required columns: {sorted(missing)}")
    validation_rows = validation_metrics[validation_metrics["split"].eq("validation")]
    if validation_rows.empty:
        raise ValueError("No validation metrics available for model selection")
    sort_columns = ["mae"]
    if "rmse" in validation_rows.columns:
        sort_columns.append("rmse")
    sort_columns.append("model")
    sorted_rows = validation_rows.sort_values(sort_columns, na_position="last")
    return str(sorted_rows.iloc[0]["model"])


def evaluate_selected_model(
    estimator,
    model_name: str,
    x_train_validation: pd.DataFrame,
    y_train_validation: pd.Series,
    x_test: pd.DataFrame,
    y_test: pd.Series,
    score_baseline_mean: float,
) -> tuple[pd.DataFrame, object, np.ndarray]:
    """Refit the selected model on train+validation years and score the final test block."""
    fitted = clone(estimator)
    fitted.fit(x_train_validation, y_train_validation)
    predictions = fitted.predict(x_test)
    metrics = compute_regression_metrics(y_test, predictions, score_baseline_mean)
    row = {
        "model": model_name,
        "split": "test",
        "n_train_validation": int(len(y_train_validation)),
        "n_test": int(len(y_test)),
        "oos_r2_baseline_mean": float(score_baseline_mean),
        **metrics,
    }
    return pd.DataFrame([row]), fitted, predictions


def build_historical_baseline_comparison(
    *,
    split,
    target_column: str,
    model_predictions: pd.DataFrame,
    model_name: str,
) -> pd.DataFrame:
    """Compare the selected model with prediction-safe historical target baselines."""
    train_validation = pd.concat([split.train, split.validation], ignore_index=True)
    test = split.test.loc[:, ["country_code", "country_name", "year", target_column]].copy()
    score_baseline_mean = float(split.train[target_column].mean())
    global_train_validation_mean = float(train_validation[target_column].mean())
    country_train_validation_mean = train_validation.groupby("country_code")[target_column].mean()
    latest_country_targets = (
        train_validation.sort_values(["country_code", "year"])
        .groupby("country_code", as_index=True)
        .tail(1)
        .set_index("country_code")[target_column]
    )

    rows = [
        _baseline_metric_row(
            model_name=model_name,
            prediction_rule="selected_model",
            y_true=model_predictions[target_column],
            y_pred=model_predictions["prediction"],
            train_mean=score_baseline_mean,
            n_test=len(model_predictions),
            uses_test_labels=False,
        )
    ]
    rows.append(
        _baseline_metric_row(
            model_name="global_train_validation_mean",
            prediction_rule="constant mean of train+validation targets",
            y_true=test[target_column],
            y_pred=np.repeat(global_train_validation_mean, len(test)),
            train_mean=score_baseline_mean,
            n_test=len(test),
            uses_test_labels=False,
        )
    )
    country_mean_predictions = (
        test["country_code"].map(country_train_validation_mean).fillna(global_train_validation_mean)
    )
    rows.append(
        _baseline_metric_row(
            model_name="country_train_validation_mean",
            prediction_rule="country mean target through validation period, global fallback",
            y_true=test[target_column],
            y_pred=country_mean_predictions,
            train_mean=score_baseline_mean,
            n_test=len(test),
            uses_test_labels=False,
        )
    )
    latest_predictions = (
        test["country_code"]
        .map(latest_country_targets)
        .fillna(country_mean_predictions)
        .fillna(global_train_validation_mean)
    )
    rows.append(
        _baseline_metric_row(
            model_name="country_last_pretest_holdconstant",
            prediction_rule="country latest observed train+validation target held constant",
            y_true=test[target_column],
            y_pred=latest_predictions,
            train_mean=score_baseline_mean,
            n_test=len(test),
            uses_test_labels=False,
        )
    )
    return pd.DataFrame(rows).sort_values(["mae", "rmse", "model"]).reset_index(drop=True)


def build_historical_baseline_delta_summary(
    historical_baselines: pd.DataFrame,
) -> pd.DataFrame:
    """Compare the selected feature model against each prediction-safe history baseline."""
    required_columns = {"model", "prediction_rule", "mae", "rmse"}
    missing_columns = sorted(required_columns.difference(historical_baselines.columns))
    if missing_columns:
        raise ValueError(f"historical_baselines missing required columns: {missing_columns}")

    selected_rows = historical_baselines[
        historical_baselines["prediction_rule"].eq("selected_model")
    ].copy()
    if selected_rows.empty:
        raise ValueError("historical_baselines must include the selected_model row")
    selected = selected_rows.sort_values(["mae", "rmse", "model"], na_position="last").iloc[0]

    baselines = historical_baselines[
        ~historical_baselines["prediction_rule"].eq("selected_model")
    ].copy()
    if "uses_test_labels" in baselines.columns:
        baselines = baselines[~baselines["uses_test_labels"].fillna(False)].copy()
    if baselines.empty:
        raise ValueError("historical_baselines must include at least one prediction-safe baseline")

    rows = []
    for _, baseline in baselines.sort_values(["mae", "rmse", "model"], na_position="last").iterrows():
        delta_mae = float(selected["mae"] - baseline["mae"])
        delta_rmse = float(selected["rmse"] - baseline["rmse"])
        selected_beats = bool(delta_mae < 0)
        if selected_beats:
            interpretation = (
                "The feature-only model beats this historical baseline on test MAE; "
                "still interpret the result as predictive association, not causality."
            )
        else:
            interpretation = (
                "The feature-only model trails this historical baseline on test MAE; "
                "do not claim that external predictors beat national historical persistence."
            )
        rows.append(
            {
                "selected_model": selected["model"],
                "baseline_model": baseline["model"],
                "baseline_prediction_rule": baseline["prediction_rule"],
                "selected_mae": float(selected["mae"]),
                "baseline_mae": float(baseline["mae"]),
                "delta_mae_selected_minus_baseline": delta_mae,
                "selected_rmse": float(selected["rmse"]),
                "baseline_rmse": float(baseline["rmse"]),
                "delta_rmse_selected_minus_baseline": delta_rmse,
                "selected_beats_baseline": selected_beats,
                "professor_interpretation": interpretation,
            }
        )
    return pd.DataFrame(rows).reset_index(drop=True)


def build_error_decomposition_tables(
    predictions: pd.DataFrame,
    *,
    target_column: str,
    quantiles: int = 4,
) -> dict[str, pd.DataFrame]:
    """Summarize prediction errors by year and target quantile."""
    required_columns = {"year", target_column, "prediction"}
    missing_columns = sorted(required_columns.difference(predictions.columns))
    if missing_columns:
        raise ValueError(f"predictions missing required columns: {missing_columns}")
    if quantiles < 2:
        raise ValueError("quantiles must be at least 2")

    frame = predictions.loc[:, ["year", target_column, "prediction"]].copy()
    frame[target_column] = frame[target_column].astype(float)
    frame["prediction"] = frame["prediction"].astype(float)
    frame["error"] = frame[target_column] - frame["prediction"]
    frame["absolute_error"] = frame["error"].abs()
    by_year_rows = []
    for year, group in frame.groupby("year", sort=True):
        row = _error_summary_row(group).to_dict()
        row["year"] = int(year)
        by_year_rows.append(row)
    by_year = pd.DataFrame(by_year_rows)[
        ["year", "n_test", "mae", "rmse", "mean_error", "median_absolute_error"]
    ]
    by_year["year"] = by_year["year"].astype(int)
    by_year["n_test"] = by_year["n_test"].astype(int)

    quantile_count = min(quantiles, int(frame[target_column].nunique()))
    if quantile_count < 2:
        by_quantile = pd.DataFrame(
            columns=[
                "target_quantile",
                "n_test",
                "target_min",
                "target_max",
                "mae",
                "rmse",
                "mean_error",
                "median_absolute_error",
            ]
        )
    else:
        labels = [f"Q{index}" for index in range(1, quantile_count + 1)]
        frame["target_quantile"] = pd.qcut(
            frame[target_column],
            q=quantile_count,
            labels=labels,
            duplicates="drop",
        )
        quantile_rows = []
        for target_quantile, group in frame.dropna(subset=["target_quantile"]).groupby(
            "target_quantile",
            observed=True,
            sort=True,
        ):
            row = _target_quantile_error_summary_row(group, target_column=target_column).to_dict()
            row["target_quantile"] = str(target_quantile)
            quantile_rows.append(row)
        by_quantile = pd.DataFrame(quantile_rows)[
            [
                "target_quantile",
                "n_test",
                "target_min",
                "target_max",
                "mae",
                "rmse",
                "mean_error",
                "median_absolute_error",
            ]
        ]
        by_quantile["n_test"] = by_quantile["n_test"].astype(int)
    return {"by_year": by_year, "by_target_quantile": by_quantile}


def build_top_prediction_errors(
    predictions: pd.DataFrame,
    *,
    target_column: str,
    limit: int = 20,
) -> pd.DataFrame:
    """Return the largest absolute test-set misses for failure-mode inspection."""
    required_columns = {"country_code", "country_name", "year", target_column, "prediction"}
    missing_columns = sorted(required_columns.difference(predictions.columns))
    if missing_columns:
        raise ValueError(f"Predictions missing required columns: {missing_columns}")
    output = predictions.loc[:, ["country_code", "country_name", "year", target_column, "prediction"]].copy()
    output = output.rename(columns={target_column: "observed"})
    output["error"] = output["observed"] - output["prediction"]
    output["absolute_error"] = output["error"].abs()
    output = output.sort_values(["absolute_error", "country_code", "year"], ascending=[False, True, True]).head(limit)
    output.insert(0, "rank", range(1, len(output) + 1))
    return output.reset_index(drop=True)


def _error_summary_row(group: pd.DataFrame) -> pd.Series:
    residuals = group["error"].to_numpy(dtype=float)
    return pd.Series(
        {
            "n_test": int(len(group)),
            "mae": float(np.mean(np.abs(residuals))),
            "rmse": float(math.sqrt(np.mean(residuals**2))),
            "mean_error": float(np.mean(residuals)),
            "median_absolute_error": float(np.median(np.abs(residuals))),
        }
    )


def _target_quantile_error_summary_row(group: pd.DataFrame, *, target_column: str) -> pd.Series:
    row = _error_summary_row(group)
    row["target_min"] = float(group[target_column].min())
    row["target_max"] = float(group[target_column].max())
    return row[
        [
            "n_test",
            "target_min",
            "target_max",
            "mae",
            "rmse",
            "mean_error",
            "median_absolute_error",
        ]
    ]


def coefficient_table(fitted_pipeline, feature_columns: list[str], model_name: str) -> pd.DataFrame:
    """Return standardized-feature coefficients for fitted linear estimators."""
    model = fitted_pipeline.named_steps["model"]
    coefficients = getattr(model, "coef_", None)
    if coefficients is None:
        return pd.DataFrame(columns=["model", "feature", "coefficient", "abs_coefficient"])
    coefficient_array = np.ravel(coefficients)
    table = pd.DataFrame(
        {
            "model": model_name,
            "feature": feature_columns,
            "coefficient": coefficient_array,
        }
    )
    table["abs_coefficient"] = table["coefficient"].abs()
    return table.sort_values("abs_coefficient", ascending=False).reset_index(drop=True)


def feature_importance_table(fitted_pipeline, feature_columns: list[str], model_name: str) -> pd.DataFrame:
    """Return feature importances for fitted tree-based estimators."""
    model = fitted_pipeline.named_steps["model"]
    importances = getattr(model, "feature_importances_", None)
    if importances is None:
        return pd.DataFrame(columns=["model", "feature", "importance"])
    importance_array = np.ravel(importances)
    table = pd.DataFrame(
        {
            "model": model_name,
            "feature": feature_columns,
            "importance": importance_array,
        }
    )
    return table.sort_values("importance", ascending=False).reset_index(drop=True)


def _baseline_metric_row(
    *,
    model_name: str,
    prediction_rule: str,
    y_true,
    y_pred,
    train_mean: float,
    n_test: int,
    uses_test_labels: bool,
) -> dict[str, object]:
    metrics = compute_regression_metrics(y_true, y_pred, train_mean)
    return {
        "model": model_name,
        "split": "test",
        "prediction_rule": prediction_rule,
        "n_test": int(n_test),
        "uses_test_labels": bool(uses_test_labels),
        **metrics,
    }


def write_markdown_summary(
    output_path: str | Path,
    *,
    best_model: str,
    split_years: dict[str, list[int]],
    validation_metrics: pd.DataFrame,
    test_metrics: pd.DataFrame,
    heading: str = "Linear Model Run Summary",
) -> None:
    lines = [
        f"# {heading}",
        "",
        f"Best validation model: `{best_model}`",
        "",
        "## Chronological Split",
        "",
        f"- Train years: {min(split_years['train'])}-{max(split_years['train'])}",
        f"- Validation years: {min(split_years['validation'])}-{max(split_years['validation'])}",
        f"- Test years: {min(split_years['test'])}-{max(split_years['test'])}",
        "",
        "## Best Validation Metrics",
        "",
        _dataframe_to_markdown(validation_metrics[validation_metrics["model"].eq(best_model)]),
        "",
        "## Final Test Metrics",
        "",
        _dataframe_to_markdown(test_metrics),
        "",
        "The selected model is chosen by validation MAE. The final test block is the latest",
        "contiguous period and is not used for model selection.",
    ]
    Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


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
