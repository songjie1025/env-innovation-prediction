"""RMSE-benchmark versions of the two family-comparison figures.

Read-only companion to `model_family_comparison.py` (fig11) and the corrected-
level comparison in `persistence_adjusted_modeling.py` (fig12). Those figures
benchmark feature models against a persistence baseline in MAE; this script asks
whether the same "no feature model beats persistence" story survives when the
benchmark metric is RMSE instead.

Nothing here trains a model. It only reads existing committed CSV outputs and
renders two small-multiple figures matching the paper visual style (seaborn
whitegrid, grouped/coloured bars, dashed baseline line, value labels).

Figure A -- LEVEL-space family comparison, Test RMSE (analogue of fig11).
    Source: 3_models/outputs/model_family_comparison.csv (lag1_3_mean rows).
    Baseline: national-persistence Test RMSE. Available for the MAIN panel only
    (linear_model_historical_baselines.csv / tree historical baselines, rule
    `country_last_pretest_holdconstant`, rmse = 1.5534). No committed CSV holds a
    per-panel persistence RMSE for suba/subb/subc, so those panels are drawn
    without a baseline line and annotated "persistence RMSE n/a".

Figure B -- CORRECTED-LEVEL family comparison, RMSE (analogue of fig12).
    Source: persistence_adjusted_level_correction_summary.csv (lag1_3_mean,
    forecast_block == test). Bars = corrected_level_rmse per family; dashed
    baseline = that panel's history_only_rmse (a per-panel persistence baseline).

Run: python 3_models/scripts/rmse_baseline_figures.py
Writes fig_rmse_level_family.{png,pdf} and fig_rmse_corrected_family.{png,pdf}
to 4_analysis/figures/paper/ and copies both PNGs to ~/Desktop/figures/.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pandas as pd

# --- Paths (resolved relative to the repo root; this script is read-only) ------
REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "3_models" / "outputs"
TREE_DIR = OUTPUT_DIR / "tree"
FIG_DIR = REPO_ROOT / "4_analysis" / "figures" / "paper"
DESKTOP_FIG_DIR = Path.home() / "Desktop" / "figures"

FAMILY_COMPARISON_CSV = OUTPUT_DIR / "model_family_comparison.csv"
LINEAR_BASELINES_CSV = OUTPUT_DIR / "linear_model_historical_baselines.csv"
TREE_BASELINES_CSV = TREE_DIR / "tree_model_historical_baselines.csv"
TREE_ROBUSTNESS_BASELINES_CSV = TREE_DIR / "tree_model_robustness_historical_baselines.csv"
CORRECTION_SUMMARY_CSV = OUTPUT_DIR / "persistence_adjusted_level_correction_summary.csv"

# --- Style constants (kept consistent with fig11/fig12) ------------------------
LAG = "lag1_3_mean"
FAMILIES = ["Linear", "RandomForest", "XGBoost"]
FAMILY_COLORS = {"Linear": "#2F6DB5", "RandomForest": "#D9822B", "XGBoost": "#2E8B6F"}
C_BASELINE = "#1F2937"
PANEL_ORDER = ["main", "suba", "subb", "subc"]
PANEL_SHORT = {"main": "Main", "suba": "SubA", "subb": "SubB", "subc": "SubC"}
# Persistence rule shared by the linear and tree historical-baseline tables.
PERSISTENCE_RULE = "country_last_pretest_holdconstant"


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"required input not found: {path}")
    return pd.read_csv(path)


def _persistence_rmse_for_panel(panel_id: str) -> float | None:
    """Return the persistence Test RMSE for a panel, or None if not committed.

    Only the MAIN panel has a national-persistence RMSE in any committed CSV
    (linear or tree historical baselines, `country_last_pretest_holdconstant`).
    Submodels A/B/C have no such row, so this returns None for them and the
    caller draws the panel without a baseline line.
    """
    if panel_id != "main":
        return None
    for path in (LINEAR_BASELINES_CSV, TREE_BASELINES_CSV):
        if not path.exists():
            continue
        table = pd.read_csv(path)
        match = table[table["model"].eq(PERSISTENCE_RULE)]
        if not match.empty:
            return float(match.iloc[0]["rmse"])
    return None


def _value_labels(ax, bars, values) -> None:
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value:.3f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )


def _finish_axes(ax, values, baseline) -> None:
    ceiling = max([*values, baseline] if baseline is not None else values)
    ax.set_ylim(0, ceiling * 1.30 if ceiling > 0 else 1)
    ax.set_ylabel("Test RMSE")
    ax.set_xticks(range(len(FAMILIES)))
    ax.set_xticklabels(FAMILIES)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


def figure_level_family(comparison: pd.DataFrame):
    """Figure A: level-space Test RMSE per family, vs national persistence RMSE."""
    import matplotlib.pyplot as plt

    sub = comparison[comparison["lag_suffix"].eq(LAG)]
    panels = [p for p in PANEL_ORDER if p in set(sub["panel_id"])]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    fig.suptitle(
        "Level-space family comparison (Test RMSE, lag1-3 mean predictors)",
        fontsize=14,
        fontweight="bold",
    )
    for ax, panel_id in zip(axes.ravel(), panels):
        panel = sub[sub["panel_id"].eq(panel_id)]
        values = [float(panel[panel["family"].eq(fam)]["test_rmse"].iloc[0]) for fam in FAMILIES]
        baseline = _persistence_rmse_for_panel(panel_id)
        bars = ax.bar(
            range(len(FAMILIES)),
            values,
            color=[FAMILY_COLORS[fam] for fam in FAMILIES],
            edgecolor="white",
        )
        _value_labels(ax, bars, values)
        if baseline is not None:
            ax.axhline(baseline, color=C_BASELINE, linestyle="--", linewidth=1.6)
            ax.text(
                len(FAMILIES) - 0.5,
                baseline,
                f" persistence\n RMSE {baseline:.2f}",
                color=C_BASELINE,
                fontsize=9,
                va="center",
                ha="left",
            )
        else:
            ax.text(
                0.98,
                0.96,
                "persistence RMSE n/a",
                transform=ax.transAxes,
                ha="right",
                va="top",
                fontsize=8.5,
                style="italic",
                color=C_BASELINE,
            )
        label = panel["panel_label"].iloc[0]
        ax.set_title(f"{PANEL_SHORT.get(panel_id, panel_id)} — {label}", fontsize=11, loc="left")
        _finish_axes(ax, values, baseline)
    for ax in axes.ravel()[len(panels):]:
        ax.axis("off")
    return fig


def figure_corrected_family(correction: pd.DataFrame):
    """Figure B: corrected-level RMSE per family, vs per-panel history-only RMSE."""
    import matplotlib.pyplot as plt

    sub = correction[
        correction["lag_suffix"].eq(LAG) & correction["forecast_block"].eq("test")
    ]
    panels = [p for p in PANEL_ORDER if p in set(sub["panel_id"])]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    fig.suptitle(
        "Corrected-level family comparison (Test RMSE, lag1-3 mean predictors)",
        fontsize=14,
        fontweight="bold",
    )
    for ax, panel_id in zip(axes.ravel(), panels):
        panel = sub[sub["panel_id"].eq(panel_id)]
        values = [
            float(panel[panel["family"].eq(fam)]["corrected_level_rmse"].iloc[0]) for fam in FAMILIES
        ]
        baseline = float(panel["history_only_rmse"].iloc[0])
        bars = ax.bar(
            range(len(FAMILIES)),
            values,
            color=[FAMILY_COLORS[fam] for fam in FAMILIES],
            edgecolor="white",
        )
        _value_labels(ax, bars, values)
        ax.axhline(baseline, color=C_BASELINE, linestyle="--", linewidth=1.6)
        ax.text(
            len(FAMILIES) - 0.5,
            baseline,
            f" history-only\n RMSE {baseline:.2f}",
            color=C_BASELINE,
            fontsize=9,
            va="center",
            ha="left",
        )
        label = panel["panel_label"].iloc[0]
        ax.set_title(f"{PANEL_SHORT.get(panel_id, panel_id)} — {label}", fontsize=11, loc="left")
        _finish_axes(ax, values, baseline)
    for ax in axes.ravel()[len(panels):]:
        ax.axis("off")
    return fig


def _save(fig, stem: str) -> None:
    """Write <stem>.png and <stem>.pdf to FIG_DIR, and <stem>.png to Desktop."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    DESKTOP_FIG_DIR.mkdir(parents=True, exist_ok=True)
    png_path = FIG_DIR / f"{stem}.png"
    fig.savefig(png_path, bbox_inches="tight")
    fig.savefig(FIG_DIR / f"{stem}.pdf", bbox_inches="tight")
    shutil.copyfile(png_path, DESKTOP_FIG_DIR / f"{stem}.png")


def main() -> None:
    os.environ.setdefault(
        "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "env_innovation_matplotlib")
    )
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
    plt.rcParams.update(
        {"savefig.dpi": 300, "axes.titleweight": "bold", "font.family": "DejaVu Sans"}
    )

    comparison = _read_csv(FAMILY_COMPARISON_CSV)
    correction = _read_csv(CORRECTION_SUMMARY_CSV)

    fig_a = figure_level_family(comparison)
    _save(fig_a, "fig_rmse_level_family")
    plt.close(fig_a)

    fig_b = figure_corrected_family(correction)
    _save(fig_b, "fig_rmse_corrected_family")
    plt.close(fig_b)

    print(f"wrote fig_rmse_level_family.png/.pdf and fig_rmse_corrected_family.png/.pdf to {FIG_DIR}")
    print(f"copied both PNGs to {DESKTOP_FIG_DIR}")


if __name__ == "__main__":
    main()
