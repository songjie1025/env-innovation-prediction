"""Head-to-head model-family comparison (v2 panels).

Linear vs RandomForest vs XGBoost, run on ALL four v2 panels (main, SubA, SubB,
SubC) and BOTH lag specifications (lag1_3_mean, lag1), each compared to its own
prediction-safe national persistence baseline.

Why this exists: the per-panel "best model" table in the tree notebook picks
whichever family happened to win validation on each panel, so it mixes RF and
XGB across panels (e.g. main->RF, SubB->XGB). That is not a family comparison.
Here we instead select the best model WITHIN each family on each panel x lag, so
Linear / RF / XGBoost are directly comparable on identical chronological splits.

Logic lives here; the tree notebook only displays the resulting table + figure.

Run: python 3_models/scripts/model_family_comparison.py
Writes 3_models/outputs/model_family_comparison.csv and an overview figure to
4_analysis/figures/paper/ (and a copy to the user's Desktop).
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from model_config import (
    OUTPUT_DIR,
    PANEL_CONFIGS,
    TRAIN_SHARE,
    VALIDATION_SHARE,
)
from model_data import (
    chronological_train_validation_test_split,
    load_model_panel,
    matrix_from_panel,
    select_lag_features,
)
from model_estimators import build_linear_model_candidates, build_tree_model_candidates
from model_evaluation import (
    evaluate_candidates_on_validation,
    evaluate_selected_model,
    select_best_validation_model,
)

FIG_DIR = Path(__file__).resolve().parents[2] / "4_analysis" / "figures" / "paper"
DESKTOP = Path.home() / "Desktop"
LAGS = ["lag1_3_mean", "lag1"]
PANEL_SHORT = {"main": "Main", "suba": "SubA", "subb": "SubB", "subc": "SubC"}
LAG_SHORT = {"lag1_3_mean": "3yr-mean", "lag1": "t-1"}
FAMILY_COLORS = {"Linear": "#2F6DB5", "RandomForest": "#D9822B", "XGBoost": "#2E8B6F"}
C_BASELINE = "#1F2937"


def _persistence_baseline_mae(split, target: str) -> float:
    """country_last: predict each country's latest train+validation target, held constant."""
    tv = pd.concat([split.train, split.validation], ignore_index=True)
    latest = (tv.sort_values(["country_code", "year"]).groupby("country_code").tail(1)
              .set_index("country_code")[target])
    global_mean = float(tv[target].mean())
    test = split.test
    pred = test["country_code"].map(latest).fillna(global_mean).to_numpy(dtype=float)
    return float(np.mean(np.abs(test[target].to_numpy(dtype=float) - pred)))


def run_family_comparison() -> pd.DataFrame:
    """Best-in-family (Linear/RF/XGBoost) test MAE for every panel x lag, vs baseline."""
    lin = build_linear_model_candidates(random_state=42)
    tree = build_tree_model_candidates(random_state=42)
    families = {
        "Linear": lin,
        "RandomForest": {k: v for k, v in tree.items() if k.startswith("rf")},
        "XGBoost": {k: v for k, v in tree.items() if k.startswith("xgb")},
    }

    rows = []
    for cfg in PANEL_CONFIGS:
        target = cfg["target_column"]
        for lag in LAGS:
            panel = load_model_panel(cfg["panel_path"], target)
            feats = select_lag_features(panel, lag)
            split = chronological_train_validation_test_split(
                panel, train_share=TRAIN_SHARE, validation_share=VALIDATION_SHARE
            )
            x_tr, y_tr = matrix_from_panel(split.train, feats, target)
            x_va, y_va = matrix_from_panel(split.validation, feats, target)
            x_te, y_te = matrix_from_panel(split.test, feats, target)
            tv = pd.concat([split.train, split.validation], ignore_index=True)
            x_tv, y_tv = matrix_from_panel(tv, feats, target)
            base_mae = _persistence_baseline_mae(split, target)

            for fam, cands in families.items():
                vm, _ = evaluate_candidates_on_validation(cands, x_tr, y_tr, x_va, y_va)
                best = select_best_validation_model(vm)
                val_mae = float(vm[vm["model"].eq(best)].iloc[0]["mae"])
                tm, _, _ = evaluate_selected_model(
                    cands[best], best, x_tv, y_tv, x_te, y_te, score_baseline_mean=float(y_tr.mean())
                )
                r = tm.iloc[0]
                rows.append({
                    "panel_id": cfg["panel_id"], "panel_label": cfg["panel_label"],
                    "lag_suffix": lag, "family": fam, "best_model": best,
                    "n_features": len(feats), "n_test": int(r["n_test"]),
                    "validation_mae": round(val_mae, 4), "test_mae": round(float(r["mae"]), 4),
                    "test_rmse": round(float(r["rmse"]), 4),
                    "test_oos_r2_vs_train_mean": round(float(r["oos_r2_vs_train_mean"]), 4),
                    "test_spearman": round(float(r["spearman"]), 4) if pd.notna(r["spearman"]) else np.nan,
                    "persistence_baseline_mae": round(base_mae, 4),
                    "delta_test_mae_vs_baseline": round(float(r["mae"]) - base_mae, 4),
                    "beats_baseline": bool(float(r["mae"]) < base_mae),
                })
            print(f"  done: {cfg['panel_id']} / {lag}")
    return pd.DataFrame(rows)


def figure_family_overview(df: pd.DataFrame, lag: str = "lag1_3_mean"):
    """2x2 small-multiples: per panel, Linear/RF/XGB test MAE vs its persistence baseline."""
    import matplotlib.pyplot as plt

    sub = df[df["lag_suffix"].eq(lag)]
    panels = [p for p in ["main", "suba", "subb", "subc"] if p in sub["panel_id"].unique()]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    fig.suptitle(
        f"No feature model beats national persistence — v2 panels (test MAE & RMSE, {LAG_SHORT[lag]} lag)",
        fontsize=14, fontweight="bold",
    )
    import numpy as np

    for ax, pid in zip(axes.ravel(), panels):
        d = sub[sub["panel_id"].eq(pid)]
        fams = ["Linear", "RandomForest", "XGBoost"]
        mae_vals = [float(d[d["family"].eq(f)]["test_mae"].iloc[0]) for f in fams]
        rmse_vals = [float(d[d["family"].eq(f)]["test_rmse"].iloc[0]) for f in fams]
        base = float(d["persistence_baseline_mae"].iloc[0])
        x = np.arange(len(fams))
        w = 0.4
        bars_mae = ax.bar(x - w / 2, mae_vals, w, color=[FAMILY_COLORS[f] for f in fams],
                          edgecolor="white", label="MAE")
        bars_rmse = ax.bar(x + w / 2, rmse_vals, w, color=[FAMILY_COLORS[f] for f in fams],
                           edgecolor="white", alpha=0.5, hatch="///", label="RMSE")
        for bars, vals in ((bars_mae, mae_vals), (bars_rmse, rmse_vals)):
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}", ha="center", va="bottom", fontsize=8.5)
        ax.set_xticks(x)
        ax.set_xticklabels(fams)
        ax.axhline(base, color=C_BASELINE, ls="--", lw=1.6)
        ax.text(2.5, base, f" persistence\n MAE {base:.2f}", color=C_BASELINE, fontsize=9, va="center", ha="left")
        label = d["panel_label"].iloc[0]
        ax.set_title(f"{PANEL_SHORT.get(pid, pid)} — {label}", fontsize=11, loc="left")
        ax.set_ylabel("Test MAE / RMSE")
        ax.legend(frameon=False, fontsize=8, loc="upper left")
        ax.set_ylim(0, max(max(rmse_vals), base) * 1.35)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    return fig


def main() -> None:
    os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "env_innovation_matplotlib"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
    plt.rcParams.update({"savefig.dpi": 300, "axes.titleweight": "bold", "font.family": "DejaVu Sans"})
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    df = run_family_comparison()
    df.to_csv(OUTPUT_DIR / "model_family_comparison.csv", index=False)
    print("\n=== Family comparison (test MAE, lower is better; baseline = persistence) ===")
    show = df[["panel_id", "lag_suffix", "family", "best_model", "test_mae",
               "persistence_baseline_mae", "delta_test_mae_vs_baseline", "beats_baseline"]]
    print(show.to_string(index=False))

    fig = figure_family_overview(df, "lag1_3_mean")
    for target_dir in (FIG_DIR, DESKTOP):
        fig.savefig(target_dir / "fig11_model_family_overview.png", bbox_inches="tight")
    fig.savefig(FIG_DIR / "fig11_model_family_overview.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"\nwrote fig11_model_family_overview.png/.pdf to {FIG_DIR} and Desktop")
    print(f"wrote model_family_comparison.csv to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
