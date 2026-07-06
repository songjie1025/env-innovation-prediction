from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon

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


# ============================================================
# Paper concept figures (integrated 2026-07-06)
# ============================================================
# ---- fig1_target_selection ----


# ── palette (matches project colour family) ──────────────────────────────────
C_REJECTED  = "#B94040"   # red
C_ROBUST    = "#C87D2A"   # amber
C_MAIN      = "#2F6B4E"   # forest green
C_NEUTRAL   = "#4A5568"   # dark grey
C_BORDER    = "#E2E8F0"   # light border
C_BG        = "#FAFAFA"

# ── candidate definitions ─────────────────────────────────────────────────────
CANDIDATES = [
    {
        "var": "env_patent_share_tech",
        "label": "env_patent_share_tech\n(PT_TECH)",
        "desc": "Env. technologies as % of all\ndomestic technologies",
        "issue": "Values can exceed 100 %.\nInternal portfolio share —\nnot globally comparable.\nExclusion risk: misleading\nfor cross-country analysis.",
        "outcome": "REJECTED",
        "outcome_label": "Diagnostic only",
        "color": C_REJECTED,
        "fate_short": "Excluded",
    },
    {
        "var": "env_patents_per_million",
        "label": "env_patents_per_million\n(INV_PS)",
        "desc": "Env. inventions\nper million people",
        "issue": "Size-normalised intensity;\ncoverage slightly lower.\nSensitive to small-country\npopulation effects.",
        "outcome": "ROBUSTNESS",
        "outcome_label": "Robustness target",
        "color": C_ROBUST,
        "fate_short": "Retained as\nrobustness check",
    },
    {
        "var": "env_patent_share_inventions",
        "label": "env_patent_share_inventions\n(PT_INV)  ✓",
        "desc": "Country's % contribution to\nglobal env-related inventions\n(rows sum ≈ 100 by year)",
        "issue": "Globally interpretable share.\n3,538 obs · 202 countries\n1990–2023. Clear unit:\nworld-contribution percent.",
        "outcome": "MAIN TARGET",
        "outcome_label": "Main target",
        "color": C_MAIN,
        "fate_short": "Selected as\nmain target",
    },
]


def make_target_selection_figure(
    out_dir: str | Path | None = None,
    stem: str = "fig1_target_selection",
) -> dict[str, str]:
    """Return paths dict; save PNG + PDF when *out_dir* is given."""
    fig, ax = plt.subplots(figsize=(14, 7.2))
    fig.patch.set_facecolor(C_BG)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7.2)
    ax.axis("off")

    # ── title ──────────────────────────────────────────────────────────────────
    ax.text(
        7, 6.85, "Target Variable Selection — Three OECD Patent Candidates",
        ha="center", va="center", fontsize=13, fontweight="bold", color=C_NEUTRAL,
    )

    # ── OECD source box ────────────────────────────────────────────────────────
    src_box = FancyBboxPatch(
        (3.8, 6.1), 6.4, 0.55,
        boxstyle="round,pad=0.12", linewidth=1.2,
        edgecolor="#718096", facecolor="#EDF2F7",
    )
    ax.add_patch(src_box)
    ax.text(
        7, 6.37, "OECD Patents Environment Dataset  ·  OECD.ENV.EPI:DSD_PAT_IND@DF_PAT_IND",
        ha="center", va="center", fontsize=9, color="#4A5568",
    )

    xs = [2.3, 7.0, 11.7]   # x-centres of the three candidate cards
    card_w, card_h = 3.9, 4.6
    card_y = 1.0             # bottom of cards

    for i, cand in enumerate(CANDIDATES):
        xc = xs[i]
        xl = xc - card_w / 2

        # ── connector from source ──────────────────────────────────────────────
        ax.annotate(
            "", xy=(xc, card_y + card_h), xytext=(xc, 6.1),
            arrowprops=dict(arrowstyle="-|>", color="#718096", lw=1.2),
        )

        # ── card background ────────────────────────────────────────────────────
        card = FancyBboxPatch(
            (xl, card_y), card_w, card_h,
            boxstyle="round,pad=0.15", linewidth=1.8,
            edgecolor=cand["color"], facecolor="#FFFFFF",
        )
        ax.add_patch(card)

        # ── variable name banner ───────────────────────────────────────────────
        banner = FancyBboxPatch(
            (xl, card_y + card_h - 0.82), card_w, 0.82,
            boxstyle="round,pad=0.12", linewidth=0,
            facecolor=cand["color"] + "22",   # very transparent tint
        )
        ax.add_patch(banner)
        ax.text(
            xc, card_y + card_h - 0.38,
            cand["label"],
            ha="center", va="center", fontsize=8.5, fontweight="bold",
            color=cand["color"],
        )

        # ── description ────────────────────────────────────────────────────────
        ax.text(
            xc, card_y + card_h - 1.28,
            cand["desc"],
            ha="center", va="center", fontsize=8,
            color=C_NEUTRAL, style="italic",
        )

        # ── divider ────────────────────────────────────────────────────────────
        ax.plot(
            [xl + 0.18, xl + card_w - 0.18],
            [card_y + card_h - 1.72, card_y + card_h - 1.72],
            color="#CBD5E0", lw=0.8,
        )

        # ── issue / note ───────────────────────────────────────────────────────
        ax.text(
            xc, card_y + 1.72,
            cand["issue"],
            ha="center", va="center", fontsize=7.6,
            color="#555555",
        )

        # ── outcome badge ──────────────────────────────────────────────────────
        badge = FancyBboxPatch(
            (xl + 0.5, card_y + 0.12), card_w - 1.0, 0.50,
            boxstyle="round,pad=0.10", linewidth=1.2,
            edgecolor=cand["color"], facecolor=cand["color"] + "33",
        )
        ax.add_patch(badge)
        ax.text(
            xc, card_y + 0.37,
            cand["outcome"],
            ha="center", va="center", fontsize=9, fontweight="bold",
            color=cand["color"],
        )

    # ── bottom annotation ──────────────────────────────────────────────────────
    ax.text(
        7, 0.55,
        "Definition of main target: country's percentage contribution to worldwide "
        "environment-related inventions — country rows sum ≈ 100 per year "
        "(aggregate areas such as OECD, EU27 excluded).",
        ha="center", va="center", fontsize=8, color="#718096",
        style="italic",
    )

    plt.tight_layout(pad=0)
    paths: dict[str, str] = {}
    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for ext in ("png", "pdf"):
            p = out_dir / f"{stem}.{ext}"
            fig.savefig(p, dpi=200, bbox_inches="tight", facecolor=C_BG)
            paths[ext] = str(p)
    return paths


# ---- fig2_predictor_funnel ----


C_NEUTRAL_f2   = "#4A5568"
C_LIGHT     = "#F7FAFC"
C_BG_f2        = "#FAFAFA"
C_ACCENT    = "#2D6A9F"
C_DROPPED   = "#B94040"
C_MERGED    = "#C87D2A"
C_FINAL     = "#2F6B4E"
C_INTERP    = "#5F7FA5"

PHASES = [
    {
        "code": "P0",
        "label": "Initial candidates",
        "count": 35,
        "action": "Literature synthesis\n+ database scan",
        "note": "28 domains screened;\nenergy prices excluded\n(data unavailable)",
        "color": C_INTERP,
        "width": 5.6,
    },
    {
        "code": "P1",
        "label": "Literature & availability filter",
        "count": 22,
        "action": "Drop: no literature support\nor unavailable series",
        "note": "−13 variables:\npoor data availability\nor weak theory link",
        "color": C_INTERP,
        "width": 4.8,
    },
    {
        "code": "P2",
        "label": "EDA quality / coverage filter",
        "count": 18,
        "action": "Drop: high missingness or\nambiguous interpretation",
        "note": "−4 variables:\nfossil_energy_share (worst coverage)\ntertiary_enrollment (broad proxy)\n+ 2 others",
        "color": C_INTERP,
        "width": 4.0,
    },
    {
        "code": "P3",
        "label": "Statistical screening",
        "count": 17,
        "action": "Merge collinear pair:\nGDP + Scientific articles\n→ size_factor (VIF 14→2.6)",
        "note": "−1 feature slot:\nGDP & scientific output\nmerged (Spearman r=0.97)",
        "color": C_MERGED,
        "width": 3.3,
    },
    {
        "code": "Model",
        "label": "Prediction & Interpretation",
        "count": 17,
        "action": "No further deletion.\nModel selection via\nvalidation-MAE (ElasticNet)",
        "note": "Main (8) · SubA (3)\nSubB (5) · SubC (1)\nEmbedded feature selection only",
        "color": C_FINAL,
        "width": 2.8,
    },
]


def make_predictor_funnel_figure(
    out_dir: str | Path | None = None,
    stem: str = "fig2_predictor_funnel",
) -> dict[str, str]:
    fig = plt.figure(figsize=(14, 8.5))
    fig.patch.set_facecolor(C_BG_f2)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8.5)
    ax.axis("off")

    # ── title ──────────────────────────────────────────────────────────────────
    ax.text(
        7, 8.2, "Predictor Screening Funnel: P0 → P3 → Prediction Model",
        ha="center", va="center", fontsize=13, fontweight="bold", color=C_NEUTRAL_f2,
    )

    # ── funnel parameters ──────────────────────────────────────────────────────
    n = len(PHASES)
    lane_h = 1.28          # height of each phase band
    gap = 0.10
    top_y = 7.7

    for i, ph in enumerate(PHASES):
        y_top = top_y - i * (lane_h + gap)
        y_bot = y_top - lane_h
        cx = 7.0
        hw = ph["width"] / 2  # half-width of funnel at this level
        y_mid = (y_top + y_bot) / 2

        # ── trapezoid funnel shape ─────────────────────────────────────────────
        if i < n - 1:
            next_hw = PHASES[i + 1]["width"] / 2
        else:
            next_hw = ph["width"] / 2

        trap_x = [
            cx - hw, cx + hw,          # top edge
            cx + next_hw, cx - next_hw, # bottom edge (narrowed)
        ]
        trap_y = [y_top, y_top, y_bot, y_bot]
        ax.fill(trap_x, trap_y, color=ph["color"], alpha=0.18, zorder=1)
        ax.plot(
            [trap_x[0], trap_x[1]], [y_top, y_top],
            color=ph["color"], lw=1.5, alpha=0.6, zorder=2,
        )
        ax.plot(
            [trap_x[3], trap_x[2]], [y_bot, y_bot],
            color=ph["color"], lw=1.5, alpha=0.6, zorder=2,
        )
        ax.plot(
            [trap_x[0], trap_x[3]], [y_top, y_bot],
            color=ph["color"], lw=1.5, alpha=0.6, zorder=2,
        )
        ax.plot(
            [trap_x[1], trap_x[2]], [y_top, y_bot],
            color=ph["color"], lw=1.5, alpha=0.6, zorder=2,
        )

        # ── phase code badge ───────────────────────────────────────────────────
        ax.text(
            cx - hw + 0.18, y_mid + 0.22,
            ph["code"],
            ha="left", va="center", fontsize=11, fontweight="bold",
            color=ph["color"], zorder=3,
        )

        # ── predictor count ────────────────────────────────────────────────────
        ax.text(
            cx, y_mid + 0.18,
            str(ph["count"]),
            ha="center", va="center", fontsize=22, fontweight="bold",
            color=ph["color"], alpha=0.55, zorder=3,
        )

        # ── phase label ────────────────────────────────────────────────────────
        ax.text(
            cx, y_mid - 0.18,
            ph["label"],
            ha="center", va="center", fontsize=8.5,
            color=C_NEUTRAL_f2, zorder=3,
        )

        # ── right-side annotation box ──────────────────────────────────────────
        note_x = cx + hw + 0.35
        note_bx = FancyBboxPatch(
            (note_x, y_mid - 0.50), 3.8, 1.0,
            boxstyle="round,pad=0.10", linewidth=0.8,
            edgecolor="#CBD5E0", facecolor="#FFFFFF", zorder=3,
        )
        ax.add_patch(note_bx)
        ax.text(
            note_x + 0.12, y_mid + 0.26,
            ph["action"],
            ha="left", va="top", fontsize=7.5,
            color=ph["color"], fontweight="semibold", zorder=4,
        )
        ax.text(
            note_x + 0.12, y_mid - 0.08,
            ph["note"],
            ha="left", va="top", fontsize=7,
            color="#718096", zorder=4,
        )

        # ── connector arrow from annotation to funnel ──────────────────────────
        ax.annotate(
            "", xy=(cx + hw + 0.02, y_mid),
            xytext=(note_x + 0.02, y_mid),
            arrowprops=dict(arrowstyle="<-", color="#CBD5E0", lw=1.2),
            zorder=3,
        )

    # ── legend: count badge meaning ───────────────────────────────────────────
    ax.text(
        0.3, 0.25,
        "Number = active model features entering next phase",
        ha="left", va="center", fontsize=8, color="#718096", style="italic",
    )

    paths: dict[str, str] = {}
    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for ext in ("png", "pdf"):
            p = out_dir / f"{stem}.{ext}"
            fig.savefig(p, dpi=200, bbox_inches="tight", facecolor=C_BG_f2)
            paths[ext] = str(p)
    return paths


# ---- fig3_predictor_coverage ----

import numpy as np

# ── palette (by model group) ──────────────────────────────────────────────────
COLOR_MAIN  = "#2D6A9F"
COLOR_SUBA  = "#5F9C6B"
COLOR_SUBB  = "#C87D2A"
COLOR_SUBC  = "#9E4F3F"
C_BG_f3        = "#FAFAFA"
C_NEUTRAL_f3   = "#4A5568"

# ── 17 predictors in display order (main first, then subA/B/C) ────────────────
PREDICTORS = [
    # (variable, display_label, coverage_share, model_group)
    # ── Main model (8) ─────────────────────────────────────────────────────────
    ("size_factor",          "Size Factor\n(GDP + Scientific articles)",  0.986, "Main (8)"),
    ("co2_per_capita_ar5",   "CO2 per capita",                            0.988, "Main (8)"),
    ("fdi_net_inflows",      "FDI net inflows",                           0.976, "Main (8)"),
    ("renewable_energy_share","Renewable energy share",                   0.961, "Main (8)"),
    ("trade_openness",       "Trade openness",                            0.959, "Main (8)"),
    ("inflation",            "Inflation",                                 0.943, "Main (8)"),
    ("wgi_regulatory_quality","WGI Regulatory Quality",                   0.930, "Main (8)"),
    ("manufacturing_share",  "Manufacturing share",                       0.943, "Main (8)"),
    # ── Sub A (3) ──────────────────────────────────────────────────────────────
    ("rise_energy_efficiency","RISE Energy Efficiency",                   0.932, "Sub A (3)"),
    ("rise_renewable_energy", "RISE Renewable Energy",                    0.932, "Sub A (3)"),
    ("high_tech_exports",    "High-tech exports",                         0.911, "Sub A (3)"),
    # ── Sub B (5) ──────────────────────────────────────────────────────────────
    ("energy_imports_net",   "Net energy imports",                        0.930, "Sub B (5)"),
    ("environmental_tax_revenue","Environmental tax revenue",             0.722, "Sub B (5)"),
    ("env_co_invention_share","Env. co-invention share",                  0.780, "Sub B (5)"),
    ("rd_expenditure_gdp",   "R&D expenditure (% GDP)",                   0.625, "Sub B (5)"),
    ("researchers_per_million","Researchers per million",                 0.597, "Sub B (5)"),
    # ── Sub C (1) ──────────────────────────────────────────────────────────────
    ("eps_index",            "EPS index",                                 1.000, "Sub C (1)"),
]

GROUP_COLORS = {
    "Main (8)": COLOR_MAIN,
    "Sub A (3)": COLOR_SUBA,
    "Sub B (5)": COLOR_SUBB,
    "Sub C (1)": COLOR_SUBC,
}


def make_predictor_coverage_bar_figure(
    out_dir: str | Path | None = None,
    stem: str = "fig3_predictor_coverage",
) -> dict[str, str]:
    labels  = [p[1] for p in PREDICTORS]
    values  = [p[2] for p in PREDICTORS]
    groups  = [p[3] for p in PREDICTORS]
    colors  = [GROUP_COLORS[g] for g in groups]

    n = len(PREDICTORS)
    fig, ax = plt.subplots(figsize=(11, 7.8), facecolor=C_BG_f3)
    ax.set_facecolor(C_BG_f3)

    y_pos = np.arange(n)
    bars = ax.barh(y_pos, values, color=colors, edgecolor="white", linewidth=0.4, height=0.72)

    # ── coverage threshold lines ──────────────────────────────────────────────
    for thresh, ls, lbl in [
        (0.80, "--", "80 %"),
        (0.90, ":",  "90 %"),
    ]:
        ax.axvline(thresh, color="#A0AEC0", lw=1.0, ls=ls, zorder=0)
        ax.text(thresh + 0.002, n - 0.3, lbl, fontsize=7.5, color="#A0AEC0", va="top")

    # ── value labels on bars ───────────────────────────────────────────────────
    for bar, val in zip(bars, values):
        ax.text(
            min(val + 0.008, 1.01), bar.get_y() + bar.get_height() / 2,
            f"{val:.0%}",
            va="center", ha="left", fontsize=7.5, color=C_NEUTRAL_f3,
        )

    # ── group separator lines ──────────────────────────────────────────────────
    # ── group separator lines and labels (must set before invert_yaxis) ──────────
    # group_bounds: bar index boundaries between groups
    # groups: Main(0-7), SubA(8-10), SubB(11-15), SubC(16)
    group_bounds = [8, 11, 16]   # separator positions between groups
    for b in group_bounds:
        ax.axhline(b - 0.5, color="#CBD5E0", lw=0.8, ls="-")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.set_xlim(0, 1.10)
    ax.set_xlabel("Non-missing share (lag1 specification, target-observed rows)", fontsize=9)
    ax.set_title(
        "Predictor Data Coverage — 17 Model Features\n"
        "(size_factor = GDP + Scientific articles, merged into one PCA component)",
        loc="left", fontsize=10, fontweight="bold", pad=8,
    )
    ax.invert_yaxis()

    # ── group labels on right (placed AFTER invert so data coords are stable) ──
    # Use blended transform: x in axes fraction, y in data coordinates.
    # After invert_yaxis: y=0 → visual top, y=16 → visual bottom.
    import matplotlib.transforms as mtransforms
    blend = mtransforms.blended_transform_factory(ax.transAxes, ax.transData)
    for g_label, (lo, hi) in zip(
        ["Main (8)", "Sub A (3)", "Sub B (5)", "Sub C (1)"],
        [(0, 8),     (8, 11),     (11, 16),    (16, 17)],
    ):
        mid = (lo + hi) / 2
        ax.text(
            1.01, mid, g_label,
            transform=blend,
            va="center", ha="left", fontsize=8.5,
            color=GROUP_COLORS[g_label], fontweight="bold",
        )

    # ── legend ────────────────────────────────────────────────────────────────
    handles = [
        mpatches.Patch(facecolor=v, label=k)
        for k, v in GROUP_COLORS.items()
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=8, frameon=True,
              edgecolor="#CBD5E0", facecolor="white")

    plt.tight_layout(pad=0.8)
    paths: dict[str, str] = {}
    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for ext in ("png", "pdf"):
            p = out_dir / f"{stem}.{ext}"
            fig.savefig(p, dpi=200, bbox_inches="tight", facecolor=C_BG_f3)
            paths[ext] = str(p)
    return paths


# ---- fig4_predictor_domains ----


# ── colour palette ─────────────────────────────────────────────────────────────
DOMAIN_COLORS = {
    "Macroeconomic / Structure": "#2D6A9F",
    "Environmental Policy":      "#9E4F3F",
    "R&D / Knowledge":           "#5F9C6B",
    "Energy / Environment":      "#C87D2A",
}
C_BG_f4      = "#FAFAFA"
C_NEUTRAL_f4 = "#4A5568"
C_LIGHT_f4   = "#F0F4F8"

# ── predictor → domain mapping ────────────────────────────────────────────────
# (display_label, domain, model_group, special_note)
PREDICTORS_f4 = [
    # ── Macroeconomic / Structure ──────────────────────────────────────────────
    ("Size Factor\n(GDP + Scientific articles)",
     "Macroeconomic / Structure", "Main", "Combined; VIF 2.6"),
    ("Manufacturing share",
     "Macroeconomic / Structure", "Main", ""),
    ("Trade openness",
     "Macroeconomic / Structure", "Main", ""),
    ("FDI net inflows",
     "Macroeconomic / Structure", "Main", ""),
    ("Inflation",
     "Macroeconomic / Structure", "Main", "Control"),
    ("High-tech exports",
     "Macroeconomic / Structure", "Sub A", ""),
    # ── Environmental Policy ───────────────────────────────────────────────────
    ("WGI Regulatory Quality",
     "Environmental Policy", "Main", ""),
    ("Env. tax revenue",
     "Environmental Policy", "Sub B", ""),
    ("EPS index",
     "Environmental Policy", "Sub C", "Narrow coverage"),
    ("RISE Energy Efficiency",
     "Environmental Policy", "Sub A", ""),
    ("RISE Renewable Energy",
     "Environmental Policy", "Sub A", ""),
    # ── R&D / Knowledge ───────────────────────────────────────────────────────
    ("R&D expenditure (% GDP)",
     "R&D / Knowledge", "Sub B", ""),
    ("Researchers per million",
     "R&D / Knowledge", "Sub B", ""),
    ("Env. co-invention share",
     "R&D / Knowledge", "Sub B", "Intl. collaboration"),
    # ── Energy / Environment ──────────────────────────────────────────────────
    ("Renewable energy share",
     "Energy / Environment", "Main", ""),
    ("CO2 per capita",
     "Energy / Environment", "Main", ""),
    ("Net energy imports",
     "Energy / Environment", "Sub B", ""),
]

DOMAIN_ORDER = list(DOMAIN_COLORS.keys())

MODEL_GROUP_HATCHES = {
    "Main":  "",
    "Sub A": "///",
    "Sub B": "...",
    "Sub C": "xxx",
}


def make_predictor_domain_figure(
    out_dir: str | Path | None = None,
    stem: str = "fig4_predictor_domains",
) -> dict[str, str]:
    # ── group predictors by domain ─────────────────────────────────────────────
    by_domain: dict[str, list] = {d: [] for d in DOMAIN_ORDER}
    for p in PREDICTORS_f4:
        by_domain[p[1]].append(p)

    # ── layout: 2 columns × 2 rows of domain panels ───────────────────────────
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), facecolor=C_BG_f4)
    fig.suptitle(
        "Predictor Domain Classification — 17 Model Features",
        fontsize=13, fontweight="bold", color=C_NEUTRAL_f4, y=0.98,
    )

    domain_list = DOMAIN_ORDER
    ax_map = {
        "Macroeconomic / Structure": axes[0, 0],
        "Environmental Policy":      axes[0, 1],
        "R&D / Knowledge":           axes[1, 0],
        "Energy / Environment":      axes[1, 1],
    }

    for domain, ax in ax_map.items():
        preds = by_domain[domain]
        color = DOMAIN_COLORS[domain]
        ax.set_facecolor(C_BG_f4)
        ax.axis("off")

        # ── domain header ──────────────────────────────────────────────────────
        header = FancyBboxPatch(
            (0.01, 0.88), 0.98, 0.11,
            boxstyle="round,pad=0.01", linewidth=1.5,
            edgecolor=color, facecolor=color + "22",
            transform=ax.transAxes, clip_on=False,
        )
        ax.add_patch(header)
        ax.text(
            0.50, 0.935, domain,
            transform=ax.transAxes,
            ha="center", va="center", fontsize=10.5, fontweight="bold",
            color=color,
        )
        ax.text(
            0.97, 0.935, f"n={len(preds)}",
            transform=ax.transAxes,
            ha="right", va="center", fontsize=9, color=color,
        )

        # ── predictor cards ────────────────────────────────────────────────────
        n_rows = len(preds)
        row_h = min(0.80 / max(n_rows, 1), 0.135)
        row_gap = 0.01
        y_start = 0.85

        for j, (label, dom, grp, note) in enumerate(preds):
            y = y_start - j * (row_h + row_gap)
            # card box
            box = FancyBboxPatch(
                (0.01, y - row_h), 0.98, row_h,
                boxstyle="round,pad=0.01", linewidth=0.8,
                edgecolor=color + "60", facecolor=color + "10",
                transform=ax.transAxes, clip_on=False,
                hatch=MODEL_GROUP_HATCHES.get(grp, ""),
            )
            ax.add_patch(box)

            # label
            ax.text(
                0.04, y - row_h / 2,
                label.replace("\n", " "),
                transform=ax.transAxes,
                ha="left", va="center", fontsize=8.5, color=C_NEUTRAL_f4,
            )

            # group badge
            badge_colors = {
                "Main": "#2D6A9F", "Sub A": "#5F9C6B",
                "Sub B": "#C87D2A", "Sub C": "#9E4F3F",
            }
            bc = badge_colors.get(grp, "#718096")
            badge = FancyBboxPatch(
                (0.80, y - row_h + 0.008), 0.17, row_h - 0.016,
                boxstyle="round,pad=0.01", linewidth=0.6,
                edgecolor=bc, facecolor=bc + "22",
                transform=ax.transAxes, clip_on=False,
            )
            ax.add_patch(badge)
            ax.text(
                0.885, y - row_h / 2, grp,
                transform=ax.transAxes,
                ha="center", va="center", fontsize=7.5,
                color=bc, fontweight="bold",
            )

            # note
            if note:
                ax.text(
                    0.04, y - row_h + 0.006,
                    note,
                    transform=ax.transAxes,
                    ha="left", va="bottom", fontsize=6.5,
                    color="#718096", style="italic",
                )

    # ── global legend for model groups ────────────────────────────────────────
    badge_colors = {"Main": "#2D6A9F", "Sub A": "#5F9C6B",
                    "Sub B": "#C87D2A", "Sub C": "#9E4F3F"}
    legend_patches = [
        mpatches.Patch(facecolor=c + "33", edgecolor=c, label=k)
        for k, c in badge_colors.items()
    ]
    fig.legend(
        handles=legend_patches, loc="lower center", ncols=4,
        fontsize=8.5, frameon=True, edgecolor="#CBD5E0",
        facecolor="white", title="Model Group", title_fontsize=8.5,
        bbox_to_anchor=(0.5, 0.01),
    )

    plt.tight_layout(rect=[0, 0.06, 1, 0.96], pad=1.2)
    paths: dict[str, str] = {}
    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for ext in ("png", "pdf"):
            p = out_dir / f"{stem}.{ext}"
            fig.savefig(p, dpi=200, bbox_inches="tight", facecolor=C_BG_f4)
            paths[ext] = str(p)
    return paths


# ---- fig5_main_vs_submodel ----


C_MAIN_f5    = "#2D6A9F"
C_SUBA    = "#5F9C6B"
C_SUBB    = "#C87D2A"
C_SUBC    = "#9E4F3F"
C_SIZE    = "#7B2F8E"  # special purple highlight for size_factor
C_BG_f5      = "#FAFAFA"
C_NEUTRAL_f5 = "#4A5568"

# ── 4 model panels ─────────────────────────────────────────────────────────────
PANELS = [
    {
        "id": "Main",
        "label": "Main Model",
        "n": 8,
        "color": C_MAIN_f5,
        "coverage": "191 countries · 1999–2023",
        "predictors": [
            ("Size Factor\n(GDP + Scientific articles)", True, "Scale"),
            ("Manufacturing share",                    False, "Structure"),
            ("Trade openness",                         False, "Structure"),
            ("FDI net inflows",                        False, "Capital"),
            ("WGI Regulatory Quality",                 False, "Policy"),
            ("Renewable energy share",                 False, "Energy"),
            ("CO2 per capita",                         False, "Energy"),
            ("Inflation",                              False, "Macro-ctrl"),
        ],
    },
    {
        "id": "Sub A",
        "label": "Sub Model A\n(RISE-EE · RISE-RE · Hi-Tech Exp.)",
        "n": 3,
        "color": C_SUBA,
        "coverage": "128 countries · 2013–2023",
        "predictors": [
            ("RISE Energy Efficiency",  False, "Policy"),
            ("RISE Renewable Energy",   False, "Policy"),
            ("High-tech exports",       False, "Structure"),
        ],
    },
    {
        "id": "Sub B",
        "label": "Sub Model B\n(R&D · Co-Inv. · Energy · Researchers · Tax)",
        "n": 5,
        "color": C_SUBB,
        "coverage": "119 countries · 1999–2023",
        "predictors": [
            ("R&D expenditure (% GDP)",  False, "R&D"),
            ("Env. co-invention share",  False, "R&D"),
            ("Net energy imports",       False, "Energy"),
            ("Researchers per million",  False, "R&D"),
            ("Env. tax revenue",         False, "Policy"),
        ],
    },
    {
        "id": "Sub C",
        "label": "Sub Model C\n(EPS index)",
        "n": 1,
        "color": C_SUBC,
        "coverage": "40 countries · 1993–2021",
        "predictors": [
            ("EPS index", False, "Policy"),
        ],
    },
]

ROLE_COLORS = {
    "Scale":     C_SIZE,
    "Structure": "#3182CE",
    "Capital":   "#5A7FB5",
    "Policy":    "#C53030",
    "Energy":    "#D97706",
    "Macro-ctrl":"#718096",
    "R&D":       "#276749",
}


def make_main_vs_submodel_figure(
    out_dir: str | Path | None = None,
    stem: str = "fig5_main_vs_submodel",
) -> dict[str, str]:
    fig = plt.figure(figsize=(14.5, 9.5), facecolor=C_BG_f5)

    # ── top: size_factor explanation banner ────────────────────────────────────
    top_ax = fig.add_axes([0.03, 0.88, 0.94, 0.08])
    top_ax.set_xlim(0, 1)
    top_ax.set_ylim(0, 1)
    top_ax.axis("off")

    banner = FancyBboxPatch(
        (0.0, 0.0), 1.0, 1.0,
        boxstyle="round,pad=0.01", linewidth=2,
        edgecolor=C_SIZE, facecolor=C_SIZE + "18",
        transform=top_ax.transAxes, clip_on=False,
    )
    top_ax.add_patch(banner)
    top_ax.text(
        0.5, 0.65,
        "size_factor  =  GDP (constant 2015 USD)  +  Scientific journal articles  "
        "→  merged via PCA (1st PC)  →  VIF: 14.0 + 13.4  →  2.6",
        ha="center", va="center", fontsize=10, fontweight="bold",
        color=C_SIZE,
    )
    top_ax.text(
        0.5, 0.22,
        "Represents national economic scale & research capacity. "
        "Permutation importance rank #1 (RF, 0.88). "
        "Sign oriented: increases with GDP.",
        ha="center", va="center", fontsize=8.5, color="#4A5568",
    )

    # ── main title ─────────────────────────────────────────────────────────────
    fig.text(
        0.5, 0.965,
        "Main Model vs. Sub-Model Predictor Distribution — 17 Features",
        ha="center", va="top", fontsize=13, fontweight="bold", color=C_NEUTRAL_f5,
    )

    # ── 4 panel columns ────────────────────────────────────────────────────────
    col_lefts  = [0.03, 0.295, 0.54, 0.78]
    col_widths = [0.245, 0.225, 0.220, 0.195]
    ax_height  = 0.78
    ax_bottom  = 0.06

    for pi, (panel, xl, cw) in enumerate(zip(PANELS, col_lefts, col_widths)):
        pax = fig.add_axes([xl, ax_bottom, cw, ax_height])
        pax.set_xlim(0, 1)
        pax.set_ylim(0, 1)
        pax.axis("off")
        pax.set_facecolor(C_BG_f5)

        c = panel["color"]

        # ── panel header ───────────────────────────────────────────────────────
        hdr = FancyBboxPatch(
            (0.0, 0.90), 1.0, 0.10,
            boxstyle="round,pad=0.01", linewidth=2,
            edgecolor=c, facecolor=c + "28",
            transform=pax.transAxes, clip_on=False,
        )
        pax.add_patch(hdr)
        pax.text(
            0.5, 0.95, panel["label"],
            transform=pax.transAxes,
            ha="center", va="center", fontsize=9, fontweight="bold",
            color=c,
        )

        # ── n & coverage ──────────────────────────────────────────────────────
        pax.text(
            0.5, 0.875,
            f"n = {panel['n']} predictors\n{panel['coverage']}",
            transform=pax.transAxes,
            ha="center", va="top", fontsize=7.8, color="#718096",
        )

        # ── predictor rows ────────────────────────────────────────────────────
        n_pred = len(panel["predictors"])
        row_h = min(0.76 / max(n_pred, 1), 0.115)
        row_gap = 0.01
        y_start = 0.82

        for j, (label, is_size, role) in enumerate(panel["predictors"]):
            y_top = y_start - j * (row_h + row_gap)
            y_bot = y_top - row_h

            rc = C_SIZE if is_size else ROLE_COLORS.get(role, "#718096")
            lw = 2.2 if is_size else 0.9
            fc = (C_SIZE + "25") if is_size else (rc + "15")

            card = FancyBboxPatch(
                (0.02, y_bot), 0.96, row_h,
                boxstyle="round,pad=0.01", linewidth=lw,
                edgecolor=rc, facecolor=fc,
                transform=pax.transAxes, clip_on=False,
            )
            pax.add_patch(card)

            pax.text(
                0.50, (y_top + y_bot) / 2,
                label.replace("\n", " "),
                transform=pax.transAxes,
                ha="center", va="center", fontsize=7.5,
                color=C_SIZE if is_size else C_NEUTRAL_f5,
                fontweight="bold" if is_size else "normal",
            )

            # role tag
            pax.text(
                0.96, y_bot + 0.006,
                role,
                transform=pax.transAxes,
                ha="right", va="bottom", fontsize=6.3,
                color=rc, style="italic",
            )

        # ── "added on top of Main" note for Sub panels ────────────────────────
        if panel["id"] != "Main":
            pax.text(
                0.5, 0.03,
                "+ Main (8) = nested comparison",
                transform=pax.transAxes,
                ha="center", va="bottom", fontsize=7, color="#A0AEC0",
                style="italic",
            )

    # ── role legend ────────────────────────────────────────────────────────────
    legend_items = [
        (C_SIZE,      "SIZE (size_factor; merged GDP + Scientific articles)"),
        ("#3182CE",   "Structure"),
        ("#C53030",   "Policy"),
        ("#D97706",   "Energy"),
        ("#276749",   "R&D"),
        ("#5A7FB5",   "Capital"),
        ("#718096",   "Macro control"),
    ]
    handles = [mpatches.Patch(facecolor=c + "40", edgecolor=c, label=l)
               for c, l in legend_items]
    fig.legend(
        handles=handles, loc="lower center", ncols=4,
        fontsize=8, frameon=True, edgecolor="#CBD5E0", facecolor="white",
        title="Predictor role", title_fontsize=8,
        bbox_to_anchor=(0.5, 0.002),
    )

    paths: dict[str, str] = {}
    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for ext in ("png", "pdf"):
            p = out_dir / f"{stem}.{ext}"
            fig.savefig(p, dpi=200, bbox_inches="tight", facecolor=C_BG_f5)
            paths[ext] = str(p)
    return paths
