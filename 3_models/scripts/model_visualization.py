from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd


def build_candidate_comparison(validation_metrics: pd.DataFrame) -> pd.DataFrame:
    """Rank linear candidates by validation MAE and mark the selected model.

    The modeling pipeline selects the candidate with the lowest validation MAE
    without touching the test block. This table makes that selection explicit
    for the report and the notebook: it returns every candidate sorted from best
    to worst validation MAE, with a 1-based ``rank`` and an ``is_selected`` flag
    on the minimum-MAE row (the model whose coefficients are reported).
    """
    keep = [c for c in ("model", "mae", "rmse", "oos_r2_vs_train_mean", "spearman") if c in validation_metrics.columns]
    ranked = validation_metrics.loc[:, keep].sort_values("mae").reset_index(drop=True).copy()
    ranked.insert(0, "rank", ranked.index + 1)
    ranked["is_selected"] = ranked["mae"] == ranked["mae"].min()
    return ranked


def make_linear_model_figures(
    *,
    panel: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    sample_summary: pd.DataFrame,
    validation_metrics: pd.DataFrame,
    predictions: pd.DataFrame,
    coefficients: pd.DataFrame,
    figures_dir: str | Path,
) -> dict[str, str]:
    """Create educational figures for the first linear modeling checkpoint."""
    cache_dir = Path(tempfile.gettempdir()) / "env_innovation_matplotlib"
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache_dir))
    os.environ.setdefault("XDG_CACHE_HOME", str(cache_dir))

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    paths: dict[str, str] = {}
    paths["split_rows"] = _save_figure(
        _plot_split_rows(panel, sample_summary, sns, plt),
        figures_dir / "linear_model_split_rows.png",
    )
    paths["target_distribution"] = _save_figure(
        _plot_target_distribution(panel, target_column, sns, plt),
        figures_dir / "linear_model_target_distribution.png",
    )
    paths["feature_missingness"] = _save_figure(
        _plot_feature_missingness(panel, feature_columns, sns, plt),
        figures_dir / "linear_model_feature_missingness.png",
    )
    paths["validation_mae"] = _save_figure(
        _plot_validation_mae(validation_metrics, sns, plt),
        figures_dir / "linear_model_validation_mae.png",
    )
    paths["actual_vs_predicted"] = _save_figure(
        _plot_actual_vs_predicted(predictions, target_column, sns, plt),
        figures_dir / "linear_model_actual_vs_predicted.png",
    )
    paths["error_by_year"] = _save_figure(
        _plot_error_by_year(predictions, sns, plt),
        figures_dir / "linear_model_error_by_year.png",
    )
    paths["coefficients"] = _save_figure(
        _plot_coefficients(coefficients, sns, plt),
        figures_dir / "linear_model_coefficients.png",
    )
    return paths


def make_model_comparison_figures(
    *,
    sample_summary: pd.DataFrame,
    test_metrics: pd.DataFrame,
    validation_metrics: pd.DataFrame,
    coefficients: pd.DataFrame,
    figures_dir: str | Path,
) -> dict[str, str]:
    """Create figures comparing the main model with mechanism submodels."""
    _prepare_matplotlib_cache()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    paths: dict[str, str] = {}
    paths["panel_sample_comparison"] = _save_figure(
        _plot_panel_sample_comparison(sample_summary, sns, plt),
        figures_dir / "linear_model_panel_sample_comparison.png",
    )
    paths["test_metric_comparison"] = _save_figure(
        _plot_test_metric_comparison(test_metrics, sns, plt),
        figures_dir / "linear_model_panel_test_metric_comparison.png",
    )
    paths["submodel_coefficients"] = _save_figure(
        _plot_submodel_coefficients(coefficients, sns, plt),
        figures_dir / "linear_model_submodel_coefficients.png",
    )
    paths["panel_validation_mae"] = _save_figure(
        _plot_panel_validation_mae(validation_metrics, sns, plt),
        figures_dir / "linear_model_panel_validation_mae.png",
    )
    return paths


def make_correlation_diagnostic_figures(
    *,
    spearman_feature_correlations: pd.DataFrame,
    target_correlations: pd.DataFrame,
    coefficient_alignment: pd.DataFrame,
    figures_dir: str | Path,
) -> dict[str, str]:
    """Create figures explaining ElasticNet under correlated predictors."""
    _prepare_matplotlib_cache()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    paths: dict[str, str] = {}
    paths["main_feature_correlation_heatmap"] = _save_figure(
        _plot_feature_correlation_heatmap(spearman_feature_correlations, sns, plt),
        figures_dir / "linear_model_main_feature_correlation_heatmap.png",
    )
    paths["main_target_correlations"] = _save_figure(
        _plot_target_correlations(target_correlations, sns, plt),
        figures_dir / "linear_model_main_target_correlations.png",
    )
    paths["main_coefficient_correlation_alignment"] = _save_figure(
        _plot_coefficient_correlation_alignment(coefficient_alignment, sns, plt),
        figures_dir / "linear_model_main_coefficient_correlation_alignment.png",
    )
    return paths


def make_nested_comparison_figures(
    *,
    nested_comparison: pd.DataFrame,
    figures_dir: str | Path,
) -> dict[str, str]:
    """Create same-sample nested comparison figures."""
    _prepare_matplotlib_cache()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    paths: dict[str, str] = {}
    paths["nested_test_mae_comparison"] = _save_figure(
        _plot_nested_test_mae_comparison(nested_comparison, sns, plt),
        figures_dir / "linear_model_nested_test_mae_comparison.png",
    )
    paths["nested_test_mae_delta"] = _save_figure(
        _plot_nested_test_mae_delta(nested_comparison, sns, plt),
        figures_dir / "linear_model_nested_test_mae_delta.png",
    )
    return paths


def make_review_diagnostic_figures(
    *,
    historical_baselines: pd.DataFrame,
    top_errors: pd.DataFrame,
    missingness_sensitivity: pd.DataFrame,
    figures_dir: str | Path,
) -> dict[str, str]:
    """Create reviewer-driven diagnostic figures for baselines and failure modes."""
    _prepare_matplotlib_cache()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    paths: dict[str, str] = {}
    paths["historical_baseline_mae"] = _save_figure(
        _plot_historical_baseline_mae(historical_baselines, sns, plt),
        figures_dir / "linear_model_historical_baseline_mae.png",
    )
    paths["top_absolute_errors"] = _save_figure(
        _plot_top_absolute_errors(top_errors, sns, plt),
        figures_dir / "linear_model_top_absolute_errors.png",
    )
    paths["missingness_sensitivity_mae"] = _save_figure(
        _plot_missingness_sensitivity_mae(missingness_sensitivity, sns, plt),
        figures_dir / "linear_model_missingness_sensitivity_mae.png",
    )
    return paths


def make_robustness_figures(
    *,
    robustness_summary: pd.DataFrame,
    figures_dir: str | Path,
) -> dict[str, str]:
    """Create figures for pre-specified linear robustness experiments."""
    _prepare_matplotlib_cache()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    paths: dict[str, str] = {}
    paths["robustness_validation_test_mae"] = _save_figure(
        _plot_robustness_validation_test_mae(robustness_summary, sns, plt),
        figures_dir / "linear_model_robustness_validation_test_mae.png",
    )
    paths["robustness_history_delta"] = _save_figure(
        _plot_robustness_history_delta(robustness_summary, sns, plt),
        figures_dir / "linear_model_robustness_history_delta.png",
    )
    return paths


def make_missingness_pattern_figures(
    *,
    missingness_pattern_summary: pd.DataFrame,
    figures_dir: str | Path,
) -> dict[str, str]:
    """Create figures that distinguish structural and intermittent predictor gaps."""
    _prepare_matplotlib_cache()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    return {
        "missingness_pattern_counts": _save_figure(
            _plot_missingness_pattern_counts(missingness_pattern_summary, plt),
            figures_dir / "linear_model_missingness_pattern_counts.png",
        )
    }


def _prepare_matplotlib_cache() -> None:
    cache_dir = Path(tempfile.gettempdir()) / "env_innovation_matplotlib"
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache_dir))
    os.environ.setdefault("XDG_CACHE_HOME", str(cache_dir))


def _plot_split_rows(panel: pd.DataFrame, sample_summary: pd.DataFrame, sns, plt):
    split_lookup = _year_to_split(sample_summary)
    plot_data = panel.groupby("year", as_index=False).size().rename(columns={"size": "rows"})
    plot_data["split"] = plot_data["year"].map(split_lookup).fillna("unused")

    fig, ax = plt.subplots(figsize=(10.8, 4.8), constrained_layout=True)
    sns.barplot(
        data=plot_data,
        x="year",
        y="rows",
        hue="split",
        palette={"train": "#405C82", "validation": "#D99B52", "test": "#9E4F3F", "unused": "#BBBBBB"},
        ax=ax,
    )
    ax.set_title("Country-Year Rows by Chronological Split", loc="left", fontweight="bold")
    ax.set_xlabel("Target year")
    ax.set_ylabel("Rows")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(title="", frameon=False, ncols=3)
    _despine(ax)
    return fig


def _plot_target_distribution(panel: pd.DataFrame, target_column: str, sns, plt):
    target = panel[target_column].dropna().astype(float)
    fig, axes = plt.subplots(ncols=2, figsize=(11.2, 4.8), constrained_layout=True)
    sns.histplot(target, bins=40, color="#405C82", ax=axes[0])
    axes[0].set_title("Raw Target Distribution", loc="left", fontweight="bold")
    axes[0].set_xlabel(target_column)
    axes[0].set_ylabel("Rows")
    sns.histplot(np.log1p(target.clip(lower=0)), bins=40, color="#5F8B95", ax=axes[1])
    axes[1].set_title("Log1p Target Distribution", loc="left", fontweight="bold")
    axes[1].set_xlabel(f"log1p({target_column})")
    axes[1].set_ylabel("Rows")
    for ax in axes:
        _despine(ax)
    return fig


def _plot_feature_missingness(panel: pd.DataFrame, feature_columns: list[str], sns, plt):
    plot_data = (
        panel.loc[:, feature_columns]
        .isna()
        .mean()
        .rename("missing_share")
        .reset_index()
        .rename(columns={"index": "feature"})
        .sort_values("missing_share")
    )
    plot_data["feature_label"] = plot_data["feature"].map(_clean_feature_label)

    fig, ax = plt.subplots(figsize=(10.8, 5.2), constrained_layout=True)
    sns.barplot(data=plot_data, y="feature_label", x="missing_share", color="#C77C5A", ax=ax)
    ax.set_title("Predictor Missingness Before Train-Fold Imputation", loc="left", fontweight="bold")
    ax.set_xlabel("Missing share")
    ax.set_ylabel("")
    ax.set_xlim(0, max(0.05, float(plot_data["missing_share"].max()) * 1.15))
    ax.xaxis.set_major_formatter(lambda x, pos: f"{x:.0%}")
    _despine(ax)
    return fig


def _plot_validation_mae(validation_metrics: pd.DataFrame, sns, plt):
    plot_data = validation_metrics.sort_values("mae").head(12).copy()
    selected_model = plot_data.iloc[0]["model"]
    plot_data["model_label"] = plot_data["model"].str.replace("_", " ", regex=False)
    plot_data = plot_data.sort_values("mae", ascending=False)
    bar_colors = ["#C44E52" if model == selected_model else "#405C82" for model in plot_data["model"]]

    fig, ax = plt.subplots(figsize=(10.8, 6.2), constrained_layout=True)
    sns.barplot(data=plot_data, y="model_label", x="mae", palette=bar_colors, hue="model_label", legend=False, ax=ax)
    ax.set_title("Validation MAE by Linear Candidate (red = selected)", loc="left", fontweight="bold")
    ax.set_xlabel("Validation MAE")
    ax.set_ylabel("")
    _despine(ax)
    return fig


def _plot_actual_vs_predicted(predictions: pd.DataFrame, target_column: str, sns, plt):
    fig, ax = plt.subplots(figsize=(6.4, 5.8), constrained_layout=True)
    sns.scatterplot(
        data=predictions,
        x=target_column,
        y="prediction",
        hue="year",
        palette="viridis",
        s=42,
        edgecolor="white",
        linewidth=0.4,
        ax=ax,
    )
    lower = float(min(predictions[target_column].min(), predictions["prediction"].min()))
    upper = float(max(predictions[target_column].max(), predictions["prediction"].max()))
    ax.plot([lower, upper], [lower, upper], color="#333333", linewidth=1, linestyle="--")
    ax.set_title("Test Set: Actual vs Predicted", loc="left", fontweight="bold")
    ax.set_xlabel("Observed target")
    ax.set_ylabel("Predicted target")
    ax.legend(title="Year", frameon=False)
    _despine(ax)
    return fig


def _plot_error_by_year(predictions: pd.DataFrame, sns, plt):
    fig, ax = plt.subplots(figsize=(8.6, 4.8), constrained_layout=True)
    sns.boxplot(data=predictions, x="year", y="error", color="#D99B52", fliersize=2, ax=ax)
    sns.stripplot(data=predictions, x="year", y="error", color="#405C82", alpha=0.45, size=3, ax=ax)
    ax.axhline(0, color="#333333", linewidth=1, linestyle="--")
    ax.set_title("Test Prediction Errors by Year", loc="left", fontweight="bold")
    ax.set_xlabel("Test year")
    ax.set_ylabel("Observed - predicted")
    _despine(ax)
    return fig


def _plot_coefficients(coefficients: pd.DataFrame, sns, plt):
    plot_data = coefficients.sort_values("abs_coefficient").copy()
    plot_data["feature_label"] = plot_data["feature"].map(_clean_feature_label)
    plot_data["sign"] = np.where(plot_data["coefficient"] >= 0, "positive", "negative")

    fig, ax = plt.subplots(figsize=(10.8, 5.6), constrained_layout=True)
    sns.barplot(
        data=plot_data,
        y="feature_label",
        x="coefficient",
        hue="sign",
        dodge=False,
        palette={"positive": "#405C82", "negative": "#9E4F3F"},
        ax=ax,
    )
    ax.axvline(0, color="#333333", linewidth=1)
    ax.set_title("Standardized Linear Coefficients", loc="left", fontweight="bold")
    ax.set_xlabel("Coefficient after median imputation and scaling")
    ax.set_ylabel("")
    legend = ax.get_legend()
    if legend is not None:
        legend.remove()
    _despine(ax)
    return fig


def _plot_panel_sample_comparison(sample_summary: pd.DataFrame, sns, plt):
    plot_data = sample_summary[sample_summary["split"].eq("all")].copy()
    plot_data = plot_data.sort_values("rows", ascending=False)

    fig, axes = plt.subplots(ncols=2, figsize=(12.0, 4.8), constrained_layout=True)
    sns.barplot(data=plot_data, x="rows", y="panel_label", color="#405C82", ax=axes[0])
    axes[0].set_title("Rows by Model Panel", loc="left", fontweight="bold")
    axes[0].set_xlabel("Rows")
    axes[0].set_ylabel("")
    sns.barplot(data=plot_data, x="countries", y="panel_label", color="#5F8B95", ax=axes[1])
    axes[1].set_title("Countries by Model Panel", loc="left", fontweight="bold")
    axes[1].set_xlabel("Countries")
    axes[1].set_ylabel("")
    for ax in axes:
        _despine(ax)
    return fig


def _plot_test_metric_comparison(test_metrics: pd.DataFrame, sns, plt):
    plot_data = test_metrics.copy().sort_values("mae")
    metrics = [
        ("mae", "Own-Sample Test MAE"),
        ("rmse", "Own-Sample Test RMSE"),
        ("oos_r2_vs_train_mean", "Own-Sample Test OOS R2"),
    ]
    fig, axes = plt.subplots(ncols=3, figsize=(14.0, 4.8), constrained_layout=True)
    for ax, (metric, title) in zip(axes, metrics):
        metric_data = plot_data.sort_values(metric, ascending=metric != "oos_r2_vs_train_mean")
        sns.barplot(data=metric_data, x=metric, y="panel_label", color="#405C82", ax=ax)
        ax.set_title(title, loc="left", fontweight="bold")
        ax.set_xlabel(metric)
        ax.set_ylabel("")
        _despine(ax)
    return fig


def _plot_submodel_coefficients(coefficients: pd.DataFrame, sns, plt):
    plot_data = coefficients.copy()
    if "panel_id" in plot_data.columns:
        plot_data = plot_data[~plot_data["panel_id"].eq("main")].copy()
    if plot_data.empty:
        plot_data = coefficients.copy()
    plot_data["feature_label"] = plot_data["feature"].map(_clean_feature_label)
    plot_data = (
        plot_data.sort_values(["panel_label", "abs_coefficient"], ascending=[True, False])
        .groupby("panel_label", as_index=False, group_keys=False)
        .head(6)
    )
    plot_data["signed_label"] = plot_data["feature_label"] + " (" + plot_data["panel_label"] + ")"
    plot_data = plot_data.sort_values("coefficient")

    fig, ax = plt.subplots(figsize=(11.8, 7.0), constrained_layout=True)
    sns.barplot(
        data=plot_data,
        x="coefficient",
        y="signed_label",
        hue="panel_label",
        dodge=False,
        ax=ax,
    )
    ax.axvline(0, color="#333333", linewidth=1)
    ax.set_title("Submodel Standardized Coefficients", loc="left", fontweight="bold")
    ax.set_xlabel("Coefficient after median imputation and scaling")
    ax.set_ylabel("")
    ax.legend(title="", frameon=False)
    _despine(ax)
    return fig


def _plot_panel_validation_mae(validation_metrics: pd.DataFrame, sns, plt):
    sort_columns = [column for column in ["panel_id", "mae", "rmse", "model"] if column in validation_metrics.columns]
    plot_data = (
        validation_metrics.sort_values(sort_columns)
        .groupby("panel_id", as_index=False, group_keys=False)
        .head(5)
        .copy()
    )
    plot_data["model_label"] = plot_data["model"].str.replace("_", " ", regex=False)
    plot_data["candidate_label"] = plot_data["panel_label"] + ": " + plot_data["model_label"]
    plot_data = plot_data.sort_values("mae", ascending=False)

    fig, ax = plt.subplots(figsize=(11.8, 7.2), constrained_layout=True)
    sns.barplot(data=plot_data, x="mae", y="candidate_label", hue="panel_label", dodge=False, ax=ax)
    ax.set_title("Top Validation MAE Candidates by Panel", loc="left", fontweight="bold")
    ax.set_xlabel("Validation MAE")
    ax.set_ylabel("")
    ax.legend(title="", frameon=False)
    _despine(ax)
    return fig


def _plot_feature_correlation_heatmap(spearman_feature_correlations: pd.DataFrame, sns, plt):
    matrix = spearman_feature_correlations.copy()
    matrix.index = [_clean_feature_label(index) for index in matrix.index]
    matrix.columns = [_clean_feature_label(column) for column in matrix.columns]
    fig, ax = plt.subplots(figsize=(9.5, 7.8), constrained_layout=True)
    sns.heatmap(
        matrix,
        vmin=-1,
        vmax=1,
        cmap="vlag",
        square=True,
        linewidths=0.4,
        cbar_kws={"label": "Spearman correlation"},
        ax=ax,
    )
    ax.set_title("Main Model Feature Correlations", loc="left", fontweight="bold")
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", rotation=0)
    return fig


def _plot_target_correlations(target_correlations: pd.DataFrame, sns, plt):
    plot_data = target_correlations.sort_values("correlation").copy()
    plot_data["feature_label"] = plot_data["feature"].map(_clean_feature_label)
    fig, ax = plt.subplots(figsize=(10.8, 5.8), constrained_layout=True)
    sns.barplot(data=plot_data, x="correlation", y="feature_label", color="#5F8B95", ax=ax)
    ax.axvline(0, color="#333333", linewidth=1)
    ax.set_title("Main Model Predictor-Target Correlations", loc="left", fontweight="bold")
    ax.set_xlabel("Spearman correlation in train+validation rows")
    ax.set_ylabel("")
    _despine(ax)
    return fig


def _plot_coefficient_correlation_alignment(coefficient_alignment: pd.DataFrame, sns, plt):
    plot_data = coefficient_alignment.copy()
    if "abs_coefficient" not in plot_data.columns:
        plot_data["abs_coefficient"] = plot_data["coefficient"].abs()
    if "sign_aligned" not in plot_data.columns:
        plot_data["sign_aligned"] = np.sign(plot_data["coefficient"]).eq(np.sign(plot_data["target_correlation"]))
    plot_data["feature_label"] = plot_data["feature"].map(_clean_feature_label)
    fig, ax = plt.subplots(figsize=(7.4, 5.8), constrained_layout=True)
    sns.scatterplot(
        data=plot_data,
        x="target_correlation",
        y="coefficient",
        size="abs_coefficient",
        hue="sign_aligned",
        palette={True: "#405C82", False: "#9E4F3F"},
        sizes=(50, 220),
        ax=ax,
    )
    for _, row in plot_data.iterrows():
        ax.annotate(row["feature_label"], (row["target_correlation"], row["coefficient"]), fontsize=8, alpha=0.8)
    ax.axhline(0, color="#333333", linewidth=1, linestyle="--")
    ax.axvline(0, color="#333333", linewidth=1, linestyle="--")
    ax.set_title("ElasticNet Coefficients vs Target Correlations", loc="left", fontweight="bold")
    ax.set_xlabel("Train+validation Spearman correlation with target")
    ax.set_ylabel("Standardized ElasticNet coefficient")
    ax.legend(title="", frameon=False)
    _despine(ax)
    return fig


def _plot_nested_test_mae_comparison(nested_comparison: pd.DataFrame, sns, plt):
    plot_data = []
    for _, row in nested_comparison.iterrows():
        plot_data.append(
            {
                "comparison_group": row["comparison_group"],
                "feature_set": "Main controls",
                "test_mae": row["baseline_test_mae"],
            }
        )
        plot_data.append(
            {
                "comparison_group": row["comparison_group"],
                "feature_set": "Main + submodel",
                "test_mae": row["augmented_test_mae"],
            }
        )
    plot_frame = pd.DataFrame(plot_data)
    fig, ax = plt.subplots(figsize=(9.8, 5.2), constrained_layout=True)
    sns.barplot(
        data=plot_frame,
        x="comparison_group",
        y="test_mae",
        hue="feature_set",
        palette={"Main controls": "#405C82", "Main + submodel": "#D99B52"},
        ax=ax,
    )
    ax.set_title("Same-Sample Nested Test MAE", loc="left", fontweight="bold")
    ax.set_xlabel("Submodel sample")
    ax.set_ylabel("Test MAE")
    ax.legend(title="", frameon=False)
    _despine(ax)
    return fig


def _plot_nested_test_mae_delta(nested_comparison: pd.DataFrame, sns, plt):
    plot_data = nested_comparison.copy()
    plot_data["improved"] = plot_data["delta_test_mae_augmented_minus_baseline"] < 0
    fig, ax = plt.subplots(figsize=(9.8, 4.8), constrained_layout=True)
    sns.barplot(
        data=plot_data,
        x="delta_test_mae_augmented_minus_baseline",
        y="comparison_group",
        hue="improved",
        dodge=False,
        palette={True: "#405C82", False: "#9E4F3F"},
        ax=ax,
    )
    ax.axvline(0, color="#333333", linewidth=1)
    ax.set_title("Incremental MAE: Main + Submodel Minus Main Controls", loc="left", fontweight="bold")
    ax.set_xlabel("Delta test MAE; negative means augmented model is better")
    ax.set_ylabel("Submodel sample")
    legend = ax.get_legend()
    if legend is not None:
        legend.remove()
    _despine(ax)
    return fig


def _plot_historical_baseline_mae(historical_baselines: pd.DataFrame, sns, plt):
    plot_data = historical_baselines.copy().sort_values("mae", ascending=False)
    plot_data["model_label"] = plot_data["model"].str.replace("_", " ", regex=False)
    if "prediction_rule" in plot_data.columns:
        plot_data["is_selected_model"] = plot_data["prediction_rule"].eq("selected_model")
    else:
        plot_data["is_selected_model"] = plot_data["model"].str.contains("elastic|linear|ridge", regex=True)

    fig, ax = plt.subplots(figsize=(10.8, 4.8), constrained_layout=True)
    sns.barplot(
        data=plot_data,
        x="mae",
        y="model_label",
        hue="is_selected_model",
        dodge=False,
        palette={True: "#405C82", False: "#9E4F3F"},
        ax=ax,
    )
    ax.set_title("Test MAE Versus Historical Target Baselines", loc="left", fontweight="bold")
    ax.set_xlabel("Test MAE")
    ax.set_ylabel("")
    legend = ax.get_legend()
    if legend is not None:
        legend.remove()
    _despine(ax)
    return fig


def _plot_top_absolute_errors(top_errors: pd.DataFrame, sns, plt):
    plot_data = top_errors.copy().sort_values("absolute_error", ascending=True)
    plot_data["country_year"] = (
        plot_data["country_name"].astype(str) + " (" + plot_data["year"].astype(str) + ")"
    )

    fig, ax = plt.subplots(figsize=(10.8, 5.2), constrained_layout=True)
    sns.barplot(data=plot_data, x="absolute_error", y="country_year", color="#9E4F3F", ax=ax)
    ax.set_title("Largest Absolute Test Errors", loc="left", fontweight="bold")
    ax.set_xlabel("Absolute error")
    ax.set_ylabel("")
    _despine(ax)
    return fig


def _plot_missingness_sensitivity_mae(missingness_sensitivity: pd.DataFrame, sns, plt):
    plot_data = missingness_sensitivity.copy().sort_values("test_mae", ascending=False)
    plot_data["analysis_label"] = plot_data["analysis"].str.replace("_", " ", regex=False)

    fig, ax = plt.subplots(figsize=(10.8, 4.8), constrained_layout=True)
    sns.barplot(data=plot_data, x="test_mae", y="analysis_label", color="#C77C5A", ax=ax)
    for _, row in plot_data.iterrows():
        ax.text(
            row["test_mae"],
            row["analysis_label"],
            f" n={int(row['test_rows'])}",
            va="center",
            ha="left",
            fontsize=9,
        )
    ax.set_title("Missingness Sensitivity: Test MAE", loc="left", fontweight="bold")
    ax.set_xlabel("Test MAE")
    ax.set_ylabel("")
    _despine(ax)
    return fig


def _plot_robustness_validation_test_mae(robustness_summary: pd.DataFrame, sns, plt):
    plot_data = robustness_summary.copy()
    plot_data["setting"] = plot_data["robustness_label"].astype(str)
    metric_rows = []
    for _, row in plot_data.iterrows():
        metric_rows.append({"setting": row["setting"], "split": "validation", "mae": row["validation_mae"]})
        metric_rows.append({"setting": row["setting"], "split": "test", "mae": row["test_mae"]})
    metric_frame = pd.DataFrame(metric_rows)

    fig, ax = plt.subplots(figsize=(11.6, 5.6), constrained_layout=True)
    sns.barplot(
        data=metric_frame,
        x="mae",
        y="setting",
        hue="split",
        palette={"validation": "#405C82", "test": "#D99B52"},
        ax=ax,
    )
    ax.set_title("Linear Robustness: Validation and Test MAE", loc="left", fontweight="bold")
    ax.set_xlabel("MAE in each target's original units")
    ax.set_ylabel("")
    ax.legend(title="", frameon=False)
    _despine(ax)
    return fig


def _plot_robustness_history_delta(robustness_summary: pd.DataFrame, sns, plt):
    plot_data = robustness_summary.copy()
    plot_data["setting"] = plot_data["robustness_label"].astype(str)
    plot_data["beats_history"] = plot_data["delta_test_mae_selected_minus_best_history"] < 0
    plot_data = plot_data.sort_values("delta_test_mae_selected_minus_best_history", ascending=False)

    fig, ax = plt.subplots(figsize=(11.6, 5.2), constrained_layout=True)
    sns.barplot(
        data=plot_data,
        x="delta_test_mae_selected_minus_best_history",
        y="setting",
        hue="beats_history",
        dodge=False,
        palette={True: "#405C82", False: "#9E4F3F"},
        ax=ax,
    )
    ax.axvline(0, color="#333333", linewidth=1)
    ax.set_title("Selected Linear Model Minus Best Historical Baseline", loc="left", fontweight="bold")
    ax.set_xlabel("Delta test MAE; negative means selected linear model is better")
    ax.set_ylabel("")
    legend = ax.get_legend()
    if legend is not None:
        legend.remove()
    _despine(ax)
    return fig


def _plot_missingness_pattern_counts(missingness_pattern_summary: pd.DataFrame, plt):
    pattern_columns = [
        "complete_countries",
        "late_start_countries",
        "early_end_countries",
        "bounded_coverage_window_countries",
        "intermittent_gaps_countries",
        "all_missing_countries",
    ]
    pattern_labels = {
        "complete_countries": "Complete",
        "late_start_countries": "Late start",
        "early_end_countries": "Early end",
        "bounded_coverage_window_countries": "Bounded window",
        "intermittent_gaps_countries": "Intermittent gaps",
        "all_missing_countries": "All missing",
    }
    palette = {
        "complete_countries": "#405C82",
        "late_start_countries": "#D99B52",
        "early_end_countries": "#5F8B95",
        "bounded_coverage_window_countries": "#8C6BB1",
        "intermittent_gaps_countries": "#9E4F3F",
        "all_missing_countries": "#707070",
    }
    plot_data = missingness_pattern_summary.copy()
    missing_columns = [column for column in pattern_columns if column not in plot_data.columns]
    if missing_columns:
        raise ValueError(f"missing pattern columns: {missing_columns}")
    plot_data["feature_label"] = plot_data["feature"].map(_clean_feature_label)
    plot_data["non_complete_countries"] = plot_data[pattern_columns[1:]].sum(axis=1)
    plot_data = plot_data.sort_values(["non_complete_countries", "feature_label"], ascending=[True, False])

    fig, ax = plt.subplots(figsize=(11.8, 6.2), constrained_layout=True)
    left = np.zeros(len(plot_data))
    y_positions = np.arange(len(plot_data))
    for column in pattern_columns:
        values = plot_data[column].astype(float).to_numpy()
        ax.barh(
            y_positions,
            values,
            left=left,
            label=pattern_labels[column],
            color=palette[column],
        )
        left += values

    ax.set_yticks(y_positions)
    ax.set_yticklabels(plot_data["feature_label"])
    ax.set_title("Predictor Missingness Patterns by Country", loc="left", fontweight="bold")
    ax.set_xlabel("Countries")
    ax.set_ylabel("")
    ax.legend(title="", frameon=False, ncols=2, loc="lower right")
    _despine(ax)
    return fig


def _save_figure(fig, png_path: Path) -> str:
    pdf_path = png_path.with_suffix(".pdf")
    fig.savefig(png_path, dpi=180)
    fig.savefig(pdf_path)
    import matplotlib.pyplot as plt

    plt.close(fig)
    return str(png_path)


def _year_to_split(sample_summary: pd.DataFrame) -> dict[int, str]:
    lookup: dict[int, str] = {}
    for _, row in sample_summary.iterrows():
        split = str(row["split"])
        if split == "all":
            continue
        for year in range(int(row["year_start"]), int(row["year_end"]) + 1):
            lookup[year] = split
    return lookup


def _clean_feature_label(feature: str) -> str:
    label = feature.replace("_lag1_3_mean", "")
    return label.replace("_", " ")


PARTIAL_DEPENDENCE_COLUMNS = [
    "feature",
    "feature_label",
    "feature_rank",
    "grid_index",
    "grid_value",
    "average_prediction",
    "centered_average_prediction",
    "n_reference",
]


def build_partial_dependence_table(
    *,
    fitted_model,
    x_reference: pd.DataFrame,
    feature_columns: list[str],
    features_to_plot: list[str],
    grid_resolution: int = 25,
) -> pd.DataFrame:
    """Compute model-level partial dependence values from a reference matrix.

    This deliberately averages predictions over the train+validation design
    matrix supplied by the caller. It is an interpretation diagnostic for the
    fitted model, not a tuning criterion and not a causal estimate.
    """
    missing_columns = sorted(set(feature_columns) - set(x_reference.columns))
    if missing_columns:
        raise ValueError(f"Missing reference columns for PDP: {missing_columns}")
    if grid_resolution < 1:
        raise ValueError("grid_resolution must be at least 1")

    x_base = x_reference.loc[:, feature_columns].copy()
    rows: list[dict[str, object]] = []
    for feature_rank, feature in enumerate(features_to_plot, start=1):
        if feature not in x_base.columns:
            raise ValueError(f"PDP feature is not in reference matrix: {feature}")

        values = pd.to_numeric(x_base[feature], errors="coerce").dropna().to_numpy()
        if values.size == 0:
            continue

        unique_values = np.unique(values.astype(float))
        if unique_values.size <= grid_resolution:
            grid = unique_values
        else:
            quantiles = np.linspace(0.05, 0.95, grid_resolution)
            grid = np.unique(np.quantile(values.astype(float), quantiles))

        feature_rows: list[dict[str, object]] = []
        for grid_index, grid_value in enumerate(grid, start=1):
            x_grid = x_base.copy()
            x_grid[feature] = float(grid_value)
            predictions = np.asarray(fitted_model.predict(x_grid), dtype=float)
            feature_rows.append(
                {
                    "feature": feature,
                    "feature_label": _clean_feature_label(feature),
                    "feature_rank": feature_rank,
                    "grid_index": grid_index,
                    "grid_value": float(grid_value),
                    "average_prediction": float(np.nanmean(predictions)),
                    "n_reference": int(len(x_base)),
                }
            )

        center = float(np.mean([row["average_prediction"] for row in feature_rows]))
        for row in feature_rows:
            row["centered_average_prediction"] = float(row["average_prediction"] - center)
            rows.append(row)

    if not rows:
        return pd.DataFrame(columns=PARTIAL_DEPENDENCE_COLUMNS)
    return pd.DataFrame(rows, columns=PARTIAL_DEPENDENCE_COLUMNS).sort_values(
        ["feature_rank", "grid_index"]
    ).reset_index(drop=True)


def _despine(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# ---------------------------------------------------------------------------
# Tree model figures
# ---------------------------------------------------------------------------


def make_tree_model_figures(
    *,
    panel: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    sample_summary: pd.DataFrame,
    validation_metrics: pd.DataFrame,
    predictions: pd.DataFrame,
    importance: pd.DataFrame,
    fitted_model,
    x_train_validation: pd.DataFrame,
    figures_dir: str | Path,
    partial_dependence: pd.DataFrame | None = None,
) -> dict[str, str]:
    """Create diagnostic and interpretation figures for tree model checkpoint."""
    _prepare_matplotlib_cache()
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    paths: dict[str, str] = {}
    paths["importance"] = _save_figure(
        _plot_feature_importance(importance, sns, plt),
        figures_dir / "tree_model_feature_importance.png",
    )
    paths["actual_vs_predicted"] = _save_figure(
        _plot_actual_vs_predicted(predictions, target_column, sns, plt),
        figures_dir / "tree_model_actual_vs_predicted.png",
    )
    paths["error_by_year"] = _save_figure(
        _plot_error_by_year(predictions, sns, plt),
        figures_dir / "tree_model_error_by_year.png",
    )
    if partial_dependence is not None and not partial_dependence.empty:
        paths["partial_dependence"] = _save_figure(
            _plot_partial_dependence(partial_dependence, sns, plt),
            figures_dir / "tree_model_partial_dependence.png",
        )

    # SHAP summary — optional dependency. Skip with a clear notice instead of
    # silently swallowing failures (never hide errors).
    shap_sample = x_train_validation.iloc[:500]
    try:
        import shap  # noqa: F401
    except ImportError:
        print(
            "[tree figures] SHAP not installed; skipping SHAP summary figure. "
            "Install with `pip install shap` to enable it."
        )
    else:
        try:
            shap_fig = _plot_shap_summary(fitted_model, shap_sample, feature_columns, plt)
            paths["shap_summary"] = _save_figure(
                shap_fig,
                figures_dir / "tree_model_shap_summary.png",
            )
        except Exception as error:  # pragma: no cover - diagnostic path
            print(f"[tree figures] SHAP summary figure failed: {error!r}")

    return paths


def _plot_partial_dependence(partial_dependence: pd.DataFrame, sns, plt):
    """Line plots of centered partial dependence for selected predictors."""
    data = partial_dependence.sort_values(["feature_rank", "grid_index"]).copy()
    features = data[["feature", "feature_label"]].drop_duplicates().to_dict("records")
    n_features = len(features)
    fig_height = max(2.6 * n_features, 3.2)
    fig, axes = plt.subplots(n_features, 1, figsize=(8, fig_height), squeeze=False)
    palette = sns.color_palette("deep", n_colors=max(n_features, 1))

    for axis_index, feature_info in enumerate(features):
        ax = axes[axis_index][0]
        feature_data = data[data["feature"] == feature_info["feature"]]
        ax.plot(
            feature_data["grid_value"],
            feature_data["centered_average_prediction"],
            marker="o",
            linewidth=2,
            color=palette[axis_index],
        )
        ax.axhline(0, color="#666666", linewidth=0.8, linestyle="--")
        ax.set_xlabel(str(feature_info["feature_label"]).title())
        ax.set_ylabel("Centered avg. prediction")
        _despine(ax)

    fig.suptitle("Tree Model — Partial Dependence (Top Predictors)")
    fig.text(
        0.01,
        0.01,
        "Computed on train+validation rows; diagnostic only, not causal.",
        fontsize=8,
        color="#4d4d4d",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    return fig


def _plot_feature_importance(importance: pd.DataFrame, sns, plt):
    """Horizontal bar chart of feature importances."""
    data = importance.sort_values("importance", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(data["feature"].apply(_clean_feature_label), data["importance"], color="#5b9bd5")
    ax.set_xlabel("Feature Importance")
    ax.set_title("Tree Model — Feature Importance")
    _despine(ax)
    fig.tight_layout()
    return fig


def _plot_shap_summary(fitted_model, x_sample, feature_columns, plt):
    """SHAP beeswarm summary using TreeExplainer.

    The model was trained on pipeline-preprocessed inputs, so the explainer must
    receive the same preprocessing (imputation). We apply every pipeline step
    except the final model, and explain exactly the rows we plot so the SHAP
    matrix and the feature matrix always share the same shape.
    """
    import shap

    model = fitted_model.named_steps["model"]
    preprocessor = fitted_model[:-1]
    x_processed = preprocessor.transform(x_sample)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(x_processed)
    display_features = [_clean_feature_label(f) for f in feature_columns]
    fig = plt.figure(figsize=(10, 6))
    shap.summary_plot(
        shap_values,
        x_processed,
        feature_names=display_features,
        show=False,
        max_display=len(feature_columns),
    )
    plt.title("SHAP Summary (Tree Model)")
    fig.tight_layout()
    return fig


def _prepare_matplotlib_cache():
    import os
    import tempfile
    from pathlib import Path

    cache_dir = Path(tempfile.gettempdir()) / "env_innovation_matplotlib"
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache_dir))
    os.environ.setdefault("XDG_CACHE_HOME", str(cache_dir))
