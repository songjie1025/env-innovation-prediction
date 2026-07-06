"""Generate publication-quality figures for the paper.

This script does NOT retrain anything. It reads the CSV outputs produced by
`run_modeling.py --both` and renders a small set of clean, paper-reusable
figures (PNG at 300 dpi + vector PDF) into 4_analysis/figures/paper/.

Run:
    python 3_models/scripts/paper_figures.py
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "3_models" / "outputs"
TREE = OUT / "tree"
FIG_DIR = ROOT / "4_analysis" / "figures" / "paper"

# ---- palette (consistent across all figures) ----
C_BASELINE = "#6B7280"   # grey: naive baselines
C_PERSIST = "#1F2937"    # near-black: the persistence benchmark
C_LINEAR = "#2F6DB5"     # blue: linear feature model
C_TREE = "#D9822B"       # orange: tree feature model
C_POS = "#2F6DB5"        # blue
C_NEG = "#B5482F"        # red
C_GOOD = "#2E8B6F"       # green: improvement


def _setup():
    cache = Path(tempfile.gettempdir()) / "env_innovation_matplotlib"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="whitegrid", context="paper", font_scale=1.25)
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.family": "DejaVu Sans",
        }
    )
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    return plt


_DISPLAY_NAMES = {
    "size_factor": "Economic scale / research capacity",
    "gdp_constant_2015_usd": "GDP (constant USD)",
    "co2_per_capita_ar5": "CO2 per capita",
    "wgi_regulatory_quality": "Regulatory quality",
    "manufacturing_share": "Manufacturing share",
    "scientific_journal_articles": "Scientific articles",
    "fdi_net_inflows": "FDI net inflows",
    "renewable_energy_share": "Renewable share",
    "trade_openness": "Trade openness",
    "inflation": "Inflation",
}


def _clean(label: str) -> str:
    stem = str(label).replace("_lag1_3_mean", "").replace("_lag1", "")
    if stem in _DISPLAY_NAMES:
        return _DISPLAY_NAMES[stem]
    # fallback: title-case but keep short tokens (acronyms) upper-cased
    words = stem.replace("_", " ").split()
    return " ".join(w.upper() if len(w) <= 3 else w.capitalize() for w in words)


def _save(fig, name: str, plt) -> None:
    for ext in ("png", "pdf"):
        fig.savefig(FIG_DIR / f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {name}.png / .pdf")


def _bar_labels(ax, bars, fmt="{:.3f}", pad=0.01, horizontal=True):
    for b in bars:
        if horizontal:
            w = b.get_width()
            ax.text(w + pad, b.get_y() + b.get_height() / 2, fmt.format(w),
                    va="center", ha="left", fontsize=9)
        else:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, h + pad, fmt.format(h),
                    va="bottom", ha="center", fontsize=9)


# ---------------------------------------------------------------------------
# Figure 1: No feature model beats national persistence
# ---------------------------------------------------------------------------
def fig1_forecast_vs_persistence(plt) -> None:
    hb_all = pd.read_csv(OUT / "linear_model_historical_baselines.csv").set_index("model")
    hb = hb_all["mae"]
    hb_rmse = hb_all["rmse"]
    pa = pd.read_csv(OUT / "linear_model_persistence_augmented_comparison.csv")
    pa_row = pa.loc[pa["model_stage"].eq("persistence_augmented_linear")].iloc[0]
    pa_mae = float(pa_row["test_mae"])
    pa_rmse = float(pa_row["test_rmse"])
    tree_metrics = pd.read_csv(TREE / "tree_model_test_metrics.csv").iloc[0]
    tree_mae = float(tree_metrics["mae"])
    tree_rmse = float(tree_metrics["rmse"])
    # Reference the model actually selected by validation instead of a fixed name.
    selected_linear = str(pd.read_csv(OUT / "linear_model_test_metrics.csv")["model"].iloc[0])

    rows = [
        ("Persistence (last value)", float(hb["country_last_pretest_holdconstant"]),
         float(hb_rmse["country_last_pretest_holdconstant"]), C_PERSIST, "baseline"),
        ("Persistence-augmented linear", pa_mae, pa_rmse, C_GOOD, "feature+history"),
        ("Random Forest (features only)", tree_mae, tree_rmse, C_TREE, "feature model"),
        ("Country mean", float(hb["country_train_validation_mean"]),
         float(hb_rmse["country_train_validation_mean"]), C_BASELINE, "baseline"),
        ("Selected linear (features only)", float(hb[selected_linear]),
         float(hb_rmse[selected_linear]), C_LINEAR, "feature model"),
        ("Global mean", float(hb["global_train_validation_mean"]),
         float(hb_rmse["global_train_validation_mean"]), C_BASELINE, "baseline"),
    ]
    df = pd.DataFrame(rows, columns=["label", "mae", "rmse", "color", "kind"]).sort_values("mae")

    y = np.arange(len(df))
    h = 0.4
    fig, ax = plt.subplots(figsize=(8.6, 5.0), constrained_layout=True)
    bars_mae = ax.barh(y + h / 2, df["mae"], h, color=df["color"], edgecolor="white", label="MAE")
    bars_rmse = ax.barh(y - h / 2, df["rmse"], h, color=df["color"], edgecolor="white",
                        alpha=0.5, hatch="///", label="RMSE")
    _bar_labels(ax, bars_mae, pad=0.03)
    _bar_labels(ax, bars_rmse, pad=0.03)
    ax.set_yticks(y)
    ax.set_yticklabels(df["label"])
    bench = float(hb["country_last_pretest_holdconstant"])
    ax.axvline(bench, color=C_PERSIST, ls="--", lw=1.2, alpha=0.7)
    ax.text(bench, -0.9, "  persistence MAE benchmark", color=C_PERSIST, fontsize=9, va="top")
    ax.set_xlabel("Test error (lower is better) — main target, 2021–2023")
    ax.set_ylabel("")
    ax.set_title("No feature-based model beats simple national persistence")
    ax.set_xlim(0, df["rmse"].max() * 1.18)
    ax.legend(frameon=False, loc="lower right")
    _save(fig, "fig1_forecast_vs_persistence", plt)


# ---------------------------------------------------------------------------
# Figure 2: Which predictors are most associated (linear coef vs tree importance)
# ---------------------------------------------------------------------------
def fig2_drivers_linear_vs_tree(plt) -> None:
    coef = pd.read_csv(OUT / "linear_model_coefficients.csv").copy()
    coef["feat"] = coef["feature"].map(_clean)
    coef = coef.sort_values("coefficient")
    imp = pd.read_csv(TREE / "tree_model_feature_importance.csv").copy()
    imp["feat"] = imp["feature"].map(_clean)
    imp = imp.sort_values("importance")

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2), constrained_layout=True)

    colors = [C_POS if v >= 0 else C_NEG for v in coef["coefficient"]]
    b1 = axes[0].barh(coef["feat"], coef["coefficient"], color=colors, edgecolor="white")
    axes[0].axvline(0, color="#333", lw=1)
    axes[0].set_title("(a) Linear model — standardized coefficients")
    axes[0].set_xlabel("Linear coefficient (sign = direction)")
    for b, v in zip(b1, coef["coefficient"]):
        off = 0.02 if v >= 0 else -0.02
        axes[0].text(v + off, b.get_y() + b.get_height() / 2, f"{v:.2f}",
                     va="center", ha="left" if v >= 0 else "right", fontsize=8.5)

    b2 = axes[1].barh(imp["feat"], imp["importance"], color=C_TREE, edgecolor="white")
    axes[1].set_title("(b) Random Forest — feature importance")
    axes[1].set_xlabel("Impurity importance (magnitude only)")
    _bar_labels(axes[1], b2, fmt="{:.2f}", pad=0.005)
    axes[1].set_xlim(0, imp["importance"].max() * 1.18)

    fig.suptitle("Most associated predictors: GDP and scientific output dominate",
                 fontsize=14, fontweight="bold")
    _save(fig, "fig2_drivers_linear_vs_tree", plt)


# ---------------------------------------------------------------------------
# Figure 3: Submodel incremental value — linear vs tree (THE new finding)
# ---------------------------------------------------------------------------
def fig3_nested_incremental_value(plt) -> None:
    lin = pd.read_csv(OUT / "linear_model_nested_comparison.csv")
    tre = pd.read_csv(TREE / "tree_model_nested_comparison.csv")
    key = "delta_test_mae_augmented_minus_baseline"
    name = {"suba": "SubA\n(RISE, high-tech exp.)", "subb": "SubB\n(R&D, co-invention)", "subc": "SubC\n(EPS policy)"}
    groups = ["suba", "subb", "subc"]
    lin_d = [float(lin.loc[lin["comparison_group"].eq(g), key].iloc[0]) for g in groups]
    tre_d = [float(tre.loc[tre["comparison_group"].eq(g), key].iloc[0]) for g in groups]

    x = np.arange(len(groups))
    w = 0.38
    fig, ax = plt.subplots(figsize=(8.6, 5.0), constrained_layout=True)
    b1 = ax.bar(x - w / 2, lin_d, w, label="Linear", color=C_LINEAR, edgecolor="white")
    b2 = ax.bar(x + w / 2, tre_d, w, label="Tree (RF/XGB)", color=C_TREE, edgecolor="white")
    ax.axhline(0, color="#333", lw=1)
    for bars in (b1, b2):
        for b in bars:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, h + (0.006 if h >= 0 else -0.006),
                    f"{h:+.3f}", ha="center", va="bottom" if h >= 0 else "top", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels([name[g] for g in groups])
    ax.set_ylabel("Δ test MAE  (negative = predictors help)")
    ax.set_title("Submodel predictors add value only in nonlinear (tree) models")
    ax.legend(frameon=False, loc="upper left")
    ax.annotate("below 0 = the extra predictors improve accuracy",
                xy=(0.02, 0.02), xycoords="axes fraction", fontsize=8.5, color=C_GOOD)
    _save(fig, "fig3_nested_incremental_value", plt)


# ---------------------------------------------------------------------------
# Figure 4: Errors concentrate in the highest-innovation countries
# ---------------------------------------------------------------------------
def fig4_error_by_quantile(plt) -> None:
    q = pd.read_csv(OUT / "linear_model_error_by_target_quantile_summary.csv")
    fig, ax = plt.subplots(figsize=(7.6, 4.6), constrained_layout=True)
    colors = [C_LINEAR] * (len(q) - 1) + [C_NEG]
    bars = ax.bar(q["target_quantile"], q["mae"], color=colors, edgecolor="white")
    _bar_labels(ax, bars, fmt="{:.2f}", pad=0.03, horizontal=False)
    ax.set_xlabel("Target quantile (Q1 = lowest, Q4 = highest innovation)")
    ax.set_ylabel("Test MAE")
    ax.set_title("Prediction error concentrates in the highest-innovation countries")
    ax.set_ylim(0, q["mae"].max() * 1.18)
    _save(fig, "fig4_error_by_quantile", plt)


# ---------------------------------------------------------------------------
# Figure 5: Rolling-origin — persistence wins in every fold
# ---------------------------------------------------------------------------
def fig5_rolling_origin(plt) -> None:
    r = pd.read_csv(OUT / "linear_model_rolling_origin_summary.csv")
    folds = [f"F{int(i)}\n{int(s)}-{int(e)}" for i, s, e in
             zip(range(1, len(r) + 1), r["test_year_start"], r["test_year_end"])]
    x = np.arange(len(r))
    fig, ax = plt.subplots(figsize=(8.8, 4.8), constrained_layout=True)
    ax.plot(x, r["test_mae"], "-o", color=C_LINEAR, lw=2, label="Selected linear model")
    ax.plot(x, r["best_historical_baseline_mae"], "-s", color=C_PERSIST, lw=2, label="Best persistence baseline")
    ax.fill_between(x, r["best_historical_baseline_mae"], r["test_mae"],
                    color=C_NEG, alpha=0.12)
    ax.set_xticks(x)
    ax.set_xticklabels(folds, fontsize=9)
    ax.set_ylabel("Test MAE")
    ax.set_xlabel("Rolling-origin fold (test window)")
    ax.set_title("Across every rolling-origin fold, persistence wins")
    ax.legend(frameon=False, loc="upper left")
    _save(fig, "fig5_rolling_origin", plt)


# ---------------------------------------------------------------------------
# Combined paper summary table (CSV + Markdown)
# ---------------------------------------------------------------------------
def write_summary_table() -> None:
    hb = pd.read_csv(OUT / "linear_model_historical_baselines.csv").set_index("model")["mae"]
    pa = pd.read_csv(OUT / "linear_model_persistence_augmented_comparison.csv")
    pa_mae = float(pa.loc[pa["model_stage"].eq("persistence_augmented_linear"), "test_mae"].iloc[0])
    tree = pd.read_csv(TREE / "tree_model_test_metrics.csv").iloc[0]
    lin = pd.read_csv(OUT / "linear_model_test_metrics.csv").iloc[0]
    bench = float(hb["country_last_pretest_holdconstant"])

    table = pd.DataFrame(
        [
            ["Persistence (last value)", "baseline", "main", bench, np.nan, np.nan, 0.0],
            ["Country mean", "baseline", "main", float(hb["country_train_validation_mean"]), np.nan, np.nan,
             float(hb["country_train_validation_mean"]) - bench],
            ["Global mean", "baseline", "main", float(hb["global_train_validation_mean"]), np.nan, np.nan,
             float(hb["global_train_validation_mean"]) - bench],
            ["Selected linear (features only)", "linear", "main", float(lin["mae"]), float(lin["rmse"]),
             float(lin["oos_r2_vs_train_mean"]), float(lin["mae"]) - bench],
            ["Random Forest (features only)", "tree", "main", float(tree["mae"]), float(tree["rmse"]),
             float(tree["oos_r2_vs_train_mean"]), float(tree["mae"]) - bench],
            ["Persistence-augmented linear", "linear+history", "main", pa_mae, np.nan, np.nan, pa_mae - bench],
        ],
        columns=["model", "type", "target", "test_mae", "test_rmse", "test_oos_r2", "delta_vs_persistence"],
    ).sort_values("test_mae").reset_index(drop=True)

    table.to_csv(FIG_DIR / "paper_model_summary.csv", index=False)
    md = ["| Model | Type | Test MAE | Test RMSE | OOS-R2 | Δ vs persistence |",
          "| --- | --- | --- | --- | --- | --- |"]
    for _, r in table.iterrows():
        md.append(
            f"| {r['model']} | {r['type']} | {r['test_mae']:.3f} | "
            f"{'' if pd.isna(r['test_rmse']) else f'{r.test_rmse:.3f}'} | "
            f"{'' if pd.isna(r['test_oos_r2']) else f'{r.test_oos_r2:.3f}'} | "
            f"{r['delta_vs_persistence']:+.3f} |"
        )
    (FIG_DIR / "paper_model_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("  wrote paper_model_summary.csv / .md")


def main() -> None:
    plt = _setup()
    print(f"Writing paper figures to: {FIG_DIR}")
    fig1_forecast_vs_persistence(plt)
    fig2_drivers_linear_vs_tree(plt)
    fig3_nested_incremental_value(plt)
    fig4_error_by_quantile(plt)
    fig5_rolling_origin(plt)
    write_summary_table()
    print("Done.")


if __name__ == "__main__":
    main()
