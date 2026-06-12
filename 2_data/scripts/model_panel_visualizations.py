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
    "rows": "Anchor-year grid",
    "target_non_missing": "Target observed",
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
    main_panel = pd.read_csv(panel_dir / "model_panel_main_no_imputation.csv")

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
    paths["main_missingness_heatmap"] = _save_figure(
        _make_main_missingness_heatmap(main_panel),
        figures_dir / "model_panel_main_missingness_heatmap.png",
        figures_dir / "model_panel_main_missingness_heatmap.pdf",
    )
    paths["rta_distribution"] = _save_figure(
        _make_rta_distribution(main_panel),
        figures_dir / "model_panel_rta_distribution.png",
        figures_dir / "model_panel_rta_distribution.pdf",
    )
    paths["imputation_audit"] = _save_figure(
        _make_imputation_audit_figure(imputation),
        figures_dir / "model_panel_imputation_audit.png",
        figures_dir / "model_panel_imputation_audit.pdf",
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


def _make_main_missingness_heatmap(main_panel: pd.DataFrame):
    import matplotlib.pyplot as plt
    import seaborn as sns

    availability = _main_panel_availability_by_year(main_panel)
    plot_data = availability.pivot(index="feature", columns="year", values="available_share")

    sns.set_theme(style="white", context="paper")
    fig_height = max(5.5, 0.34 * len(plot_data))
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
    ax.set_title("Main Panel Feature Availability by Target Year", loc="left", fontweight="bold")
    ax.set_xlabel("Target year")
    ax.set_ylabel("")
    return fig


def _make_rta_distribution(main_panel: pd.DataFrame):
    import matplotlib.pyplot as plt
    import seaborn as sns

    column = "env_technology_rta_lag1"
    values = main_panel[column].dropna()
    values = values[values > 0]
    if values.empty:
        raise ValueError(f"{column} has no positive values to plot.")
    bins = np.geomspace(values.min(), values.max(), 42)

    sns.set_theme(style="whitegrid", context="paper")
    fig, ax = plt.subplots(figsize=(9.5, 5.2), constrained_layout=True)
    ax.hist(values, bins=bins, color="#405C82", alpha=0.86, edgecolor="white", linewidth=0.5)
    ax.axvline(1, color="#A33F2D", linewidth=2, linestyle="--", label="OECD RTA benchmark = 1")
    ax.set_xscale("log")
    ax.set_title("Environmental-Technology RTA Distribution, Main Panel", loc="left", fontweight="bold")
    ax.set_xlabel("Lagged RTA index, log scale")
    ax.set_ylabel("Observed country-year cells")
    ax.legend(frameon=False, loc="upper right")
    annotation = f"n={len(values):,}; median={values.median():.2f}; max={values.max():.2f}"
    ax.text(0.01, 0.96, annotation, transform=ax.transAxes, va="top", ha="left")
    _despine(ax)
    return fig


def _make_imputation_audit_figure(imputation: pd.DataFrame):
    import matplotlib.pyplot as plt
    import seaborn as sns

    plot_data = imputation.loc[
        imputation["imputation"].eq("linear_interpolated") & imputation["imputed_values"].gt(0)
    ].copy()
    if plot_data.empty:
        raise ValueError("No imputed values found for the retrospective sensitivity panels.")
    plot_data["panel"] = plot_data["panel_id"].map(PANEL_FAMILY_LABELS)
    plot_data["variable_label"] = plot_data["variable"].str.replace("_", " ", regex=False)
    plot_data = plot_data.sort_values(["panel_id", "imputed_values", "variable_label"], ascending=[True, False, True])

    sns.set_theme(style="whitegrid", context="paper")
    panels = list(plot_data["panel"].drop_duplicates())
    fig, axes = plt.subplots(
        nrows=len(panels),
        ncols=1,
        figsize=(10.8, max(5.0, 2.1 * len(panels))),
        constrained_layout=True,
        sharex=False,
    )
    axes = np.atleast_1d(axes)
    for ax, panel in zip(axes, panels, strict=False):
        panel_data = plot_data.loc[plot_data["panel"].eq(panel)]
        sns.barplot(data=panel_data, y="variable_label", x="imputed_values", color="#C77C5A", ax=ax)
        ax.set_title(panel, loc="left", fontweight="bold")
        ax.set_xlabel("Values filled by linear interpolation")
        ax.set_ylabel("")
        _label_horizontal_bars(ax)
        _despine(ax)
    fig.suptitle("Retrospective Interpolation Audit by Predictor", x=0.02, ha="left", fontweight="bold")
    return fig


def _ordered_coverage(coverage: pd.DataFrame, imputation: str) -> pd.DataFrame:
    ordered = coverage.loc[coverage["imputation"].eq(imputation)].copy()
    ordered["panel_order"] = ordered["panel_id"].map({panel: index for index, panel in enumerate(PANEL_FAMILY_LABELS)})
    return ordered.sort_values("panel_order")


def _main_panel_availability_by_year(main_panel: pd.DataFrame) -> pd.DataFrame:
    feature_columns = [
        column
        for column in main_panel.columns
        if column not in {"country_code", "country_name", "year", TARGET_VARIABLE}
    ]
    rows: list[dict[str, object]] = []
    for column in feature_columns:
        variable = column.removesuffix("_lag1_3_mean").removesuffix("_lag1")
        suffix = "lag1-3 mean" if column.endswith("_lag1_3_mean") else "lag1"
        feature_label = f"{variable.replace('_', ' ')} ({suffix})"
        by_year = main_panel.groupby("year")[column].apply(lambda values: values.notna().mean())
        for year, share in by_year.items():
            rows.append({"feature": feature_label, "year": int(year), "available_share": float(share)})
    return pd.DataFrame(rows)


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


def _label_horizontal_bars(ax) -> None:
    for container in ax.containers:
        labels = [f"{bar.get_width():,.0f}" if bar.get_width() > 0 else "" for bar in container]
        ax.bar_label(container, labels=labels, fontsize=7, padding=2)


def _despine(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
