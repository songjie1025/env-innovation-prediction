from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

from data_common import ROOT_DIR
from model_panel_cleaning import TARGET_VARIABLE


FIGURES_DIR = ROOT_DIR / "4_analysis" / "figures" / "model_panels"
PANEL_FAMILY_LABELS = {
    "main": "Main",
    "suba": "Sub A",
    "subb": "Sub B",
    "subc": "Sub C",
}
SAMPLE_STAGE_LABELS = {
    "anchor_year_grid_rows": "Anchor-year grid",
    "rows": "Target-observed panel",
    "target_lag1_complete_rows": "Target + lag1 complete",
    "target_lag1_3_mean_complete_rows": "Target + lag1-3 mean complete",
}


def make_model_panel_figures(
    panel_dir: Path | str,
    figures_dir: Path | str = FIGURES_DIR,
) -> dict[str, str]:
    """Create model-panel readiness figures from the generated panel outputs."""
    panel_dir = Path(panel_dir)
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    _configure_matplotlib()

    coverage = pd.read_csv(panel_dir / "model_panel_coverage_summary.csv")
    imputation = pd.read_csv(panel_dir / "model_panel_imputation_summary.csv")
    no_imputation_panels = _load_no_imputation_panels(panel_dir, coverage)

    paths: dict[str, str] = {}
    paths["sample_funnel"] = _save_figure(
        _make_sample_funnel_figure(coverage),
        figures_dir / "model_panel_sample_funnel.png",
        figures_dir / "model_panel_sample_funnel.pdf",
    )
    paths["prediction_safe_comparison"] = _save_figure(
        _make_prediction_safe_comparison_figure(coverage),
        figures_dir / "model_panel_prediction_safe_comparison.png",
        figures_dir / "model_panel_prediction_safe_comparison.pdf",
    )
    paths["feature_availability_heatmap"] = _save_figure(
        _make_feature_availability_heatmap(no_imputation_panels),
        figures_dir / "model_panel_feature_availability_heatmap.png",
        figures_dir / "model_panel_feature_availability_heatmap.pdf",
    )
    paths["missingness_burden"] = _save_figure(
        _make_missingness_burden_figure(coverage, imputation),
        figures_dir / "model_panel_missingness_burden.png",
        figures_dir / "model_panel_missingness_burden.pdf",
    )
    return paths


def _make_sample_funnel_figure(coverage: pd.DataFrame):
    import matplotlib.pyplot as plt
    import seaborn as sns

    no_imputation = _ordered_coverage(coverage, "no_imputation")
    plot_data = no_imputation.melt(
        id_vars=["panel_id"],
        value_vars=list(SAMPLE_STAGE_LABELS),
        var_name="stage",
        value_name="row_count",
    )
    plot_data["panel"] = plot_data["panel_id"].map(PANEL_FAMILY_LABELS)
    plot_data["stage_label"] = plot_data["stage"].map(SAMPLE_STAGE_LABELS)

    sns.set_theme(style="whitegrid", context="paper")
    fig, ax = plt.subplots(figsize=(11.5, 5.6), constrained_layout=True)
    palette = ["#405C82", "#5F8B95", "#D99B52", "#9E4F3F"]
    sns.barplot(data=plot_data, x="panel", y="row_count", hue="stage_label", palette=palette, ax=ax)
    ax.set_title("Sample Construction Funnel, No-Imputation Panels", loc="left", fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Country-year rows")
    ax.legend(title="", ncols=2, frameon=False, loc="upper right")
    _label_grouped_bars(ax)
    _despine(ax)
    return fig


def _make_prediction_safe_comparison_figure(coverage: pd.DataFrame):
    import matplotlib.pyplot as plt
    import seaborn as sns

    plot_data = coverage.copy()
    plot_data["panel"] = plot_data["panel_id"].map(PANEL_FAMILY_LABELS)
    plot_data["input_type"] = np.where(
        plot_data["prediction_safe"],
        "No imputation: prediction-safe",
        "Linear interpolation: retrospective sensitivity",
    )

    sns.set_theme(style="whitegrid", context="paper")
    fig, ax = plt.subplots(figsize=(10.8, 5.2), constrained_layout=True)
    sns.barplot(
        data=plot_data,
        x="panel",
        y="target_lag1_3_mean_complete_rows",
        hue="input_type",
        palette=["#405C82", "#C77C5A"],
        ax=ax,
    )
    ax.set_title("Effective Three-Year-Lag Modeling Sample", loc="left", fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Rows with target and complete lag1-3 mean features")
    ax.legend(title="", frameon=False, loc="upper right")
    _label_grouped_bars(ax)
    _despine(ax)
    return fig


def _make_feature_availability_heatmap(no_imputation_panels: dict[str, pd.DataFrame]):
    import matplotlib.pyplot as plt
    import seaborn as sns

    availability = _panel_feature_availability_by_year(no_imputation_panels)
    plot_data = availability.pivot(index="feature", columns="year", values="available_share")

    sns.set_theme(style="white", context="paper")
    fig_height = max(6.4, 0.28 * len(plot_data))
    fig, ax = plt.subplots(figsize=(13.8, fig_height), constrained_layout=True)
    sns.heatmap(
        plot_data,
        cmap=sns.color_palette("crest", as_cmap=True),
        vmin=0,
        vmax=1,
        linewidths=0.25,
        linecolor="#FFFFFF",
        cbar_kws={"label": "Non-missing share"},
        ax=ax,
    )
    _draw_panel_group_separators(ax, availability)
    ax.set_title("Feature Availability by Target Year, All No-Imputation Panels", loc="left", fontweight="bold")
    ax.set_xlabel("Target year")
    ax.set_ylabel("")
    return fig


def _make_missingness_burden_figure(coverage: pd.DataFrame, imputation: pd.DataFrame):
    import matplotlib.pyplot as plt
    import seaborn as sns

    no_imputation = _ordered_coverage(coverage, "no_imputation")
    retention_rows: list[dict[str, object]] = []
    for _, row in no_imputation.iterrows():
        denominator = row["rows"] if row["rows"] else np.nan
        for column, label in [
            ("target_lag1_complete_rows", "Lag1 complete"),
            ("target_lag1_3_mean_complete_rows", "Lag1-3 mean complete"),
        ]:
            retention_rows.append(
                {
                    "panel_id": row["panel_id"],
                    "panel": PANEL_FAMILY_LABELS.get(row["panel_id"], row["panel_id"]),
                    "lag_scheme": label,
                    "retained_share": row[column] / denominator,
                }
            )
    retention = pd.DataFrame(retention_rows)

    fill = (
        imputation.loc[imputation["imputation"].eq("linear_interpolated")]
        .groupby("panel_id", as_index=False)["imputed_values"]
        .sum()
    )
    fill = no_imputation[["panel_id"]].merge(fill, on="panel_id", how="left").fillna({"imputed_values": 0})
    fill["panel"] = fill["panel_id"].map(PANEL_FAMILY_LABELS)

    sns.set_theme(style="whitegrid", context="paper")
    fig, axes = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(10.8, 7.6),
        constrained_layout=True,
    )
    sns.barplot(
        data=retention,
        x="panel",
        y="retained_share",
        hue="lag_scheme",
        palette=["#405C82", "#D99B52"],
        ax=axes[0],
    )
    axes[0].set_title("No-Imputation Complete-Feature Retention", loc="left", fontweight="bold")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Share of target-observed rows")
    axes[0].set_ylim(0, 1)
    axes[0].legend(title="", frameon=False, loc="upper right")
    _label_percentage_bars(axes[0])
    _despine(axes[0])

    sns.barplot(data=fill, x="panel", y="imputed_values", color="#C77C5A", ax=axes[1])
    axes[1].set_title("Retrospective Linear-Interpolation Fill Scale", loc="left", fontweight="bold")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Predictor cells filled")
    _label_grouped_bars(axes[1])
    _despine(axes[1])
    fig.suptitle("Global Missingness Burden by Model Panel", x=0.02, ha="left", fontweight="bold")
    return fig


def _ordered_coverage(coverage: pd.DataFrame, imputation: str) -> pd.DataFrame:
    ordered = coverage.loc[coverage["imputation"].eq(imputation)].copy()
    ordered["panel_order"] = ordered["panel_id"].map({panel: index for index, panel in enumerate(PANEL_FAMILY_LABELS)})
    return ordered.sort_values("panel_order")


def _load_no_imputation_panels(panel_dir: Path, coverage: pd.DataFrame) -> dict[str, pd.DataFrame]:
    panel_ids = _ordered_coverage(coverage, "no_imputation")["panel_id"].drop_duplicates()
    panels: dict[str, pd.DataFrame] = {}
    for panel_id in panel_ids:
        panel_path = panel_dir / f"model_panel_{panel_id}_no_imputation.csv"
        if panel_path.exists():
            panels[str(panel_id)] = pd.read_csv(panel_path)
    if not panels:
        raise FileNotFoundError(f"No no-imputation panel CSVs found in {panel_dir}.")
    return panels


def _panel_feature_availability_by_year(no_imputation_panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    excluded = {"country_code", "country_name", "year", TARGET_VARIABLE}
    for panel_order, (panel_id, panel) in enumerate(no_imputation_panels.items()):
        panel_label = PANEL_FAMILY_LABELS.get(panel_id, panel_id)
        feature_columns = [column for column in panel.columns if column not in excluded]
        for feature_order, column in enumerate(feature_columns):
            feature_label = f"{panel_label} | {_feature_label(column)}"
            by_year = panel.groupby("year")[column].apply(lambda values: values.notna().mean())
            for year, share in by_year.items():
                rows.append(
                    {
                        "panel_id": panel_id,
                        "panel_order": panel_order,
                        "feature_order": feature_order,
                        "feature": feature_label,
                        "year": int(year),
                        "available_share": float(share),
                    }
                )
    availability = pd.DataFrame(rows)
    if availability.empty:
        raise ValueError("No feature columns found in no-imputation panels.")
    availability = availability.sort_values(["panel_order", "feature_order", "year"])
    return availability


def _feature_label(column: str) -> str:
    variable = column.removesuffix("_lag1_3_mean").removesuffix("_lag1")
    suffix = "lag1-3 mean" if column.endswith("_lag1_3_mean") else "lag1"
    return f"{variable.replace('_', ' ')} ({suffix})"


def _draw_panel_group_separators(ax, availability: pd.DataFrame) -> None:
    ordered_features = availability[["feature", "panel_id", "panel_order", "feature_order"]].drop_duplicates()
    ordered_features = ordered_features.sort_values(["panel_order", "feature_order"]).reset_index(drop=True)
    panel_changes = ordered_features["panel_id"].ne(ordered_features["panel_id"].shift()).to_numpy()
    for index, is_change in enumerate(panel_changes):
        if is_change and index > 0:
            ax.axhline(index, color="#2F3A45", linewidth=0.8)


def _configure_matplotlib() -> None:
    cache_dir = ROOT_DIR / ".cache" / "matplotlib"
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache_dir))
    import matplotlib

    matplotlib.use("Agg", force=True)


def _save_figure(fig, png_path: Path, pdf_path: Path) -> str:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    import matplotlib.pyplot as plt

    plt.close(fig)
    return str(png_path)


def _label_grouped_bars(ax) -> None:
    for container in ax.containers:
        labels = [f"{bar.get_height():,.0f}" if bar.get_height() > 0 else "" for bar in container]
        ax.bar_label(container, labels=labels, fontsize=7, padding=2)


def _label_percentage_bars(ax) -> None:
    for container in ax.containers:
        labels = [f"{bar.get_height():.0%}" if bar.get_height() > 0 else "" for bar in container]
        ax.bar_label(container, labels=labels, fontsize=7, padding=2)


def _label_horizontal_bars(ax) -> None:
    for container in ax.containers:
        labels = [f"{bar.get_width():,.0f}" if bar.get_width() > 0 else "" for bar in container]
        ax.bar_label(container, labels=labels, fontsize=7, padding=2)


def _despine(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
