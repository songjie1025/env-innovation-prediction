"""Robustness checks for the nonlinear (tree) findings.

These are heavier, occasional validations, so they live in their own script
instead of the main `run_modeling.py` path. They REUSE the same panels, nested
construction, and split protocol as the tree pipeline.

(1) MULTI-SEED NESTED CHECK
    Question: is the "submodel predictors help in trees" result (Section 8.5)
    real, or just a lucky random seed on a small validation window?
    Design: hold the model FIXED (one RandomForest config) for both the
    main-controls baseline and the main+submodel augmented model, and only vary
    the random seed. This isolates the FEATURE effect from model-selection noise
    (the headline pipeline picked different models for baseline vs augmented).
    Delta = augmented_test_MAE - baseline_test_MAE  (negative => predictors help).

(2) PERMUTATION IMPORTANCE
    Question: is the impurity-based importance ranking (GDP dominating) an
    artifact? Impurity importance over-credits high-variance continuous features.
    Permutation importance on the held-out test block is less biased.

Run:
    python 3_models/scripts/tree_robustness_checks.py
Writes CSVs to 3_models/outputs/tree/ and figures to 4_analysis/figures/paper/.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.pipeline import Pipeline

from model_config import (
    PANEL_CONFIGS,
    PRIMARY_LAG_SUFFIX,
    PRIMARY_PANEL_PATH,
    PRIMARY_TARGET,
    TRAIN_SHARE,
    TREE_OUTPUT_DIR,
    VALIDATION_SHARE,
)
from model_data import (
    chronological_train_validation_test_split,
    load_model_panel,
    matrix_from_panel,
    select_lag_features,
)
from model_experiments import PanelSpec, build_nested_submodel_panel, run_panel_tree_experiment

FIG_DIR = Path(__file__).resolve().parents[2] / "4_analysis" / "figures" / "paper"

# Fixed RF for the multi-seed check (isolates the feature effect from selection)
FIXED_RF = {"n_estimators": 300, "max_depth": None}
SEEDS = list(range(25))
PERM_REPEATS = 30

SUB_LABELS = {
    "suba": "SubA (RISE, high-tech exports)",
    "subb": "SubB (R&D, co-invention, tax)",
    "subc": "SubC (EPS policy)",
}


def _setup_mpl():
    cache = Path(tempfile.gettempdir()) / "env_innovation_matplotlib"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="whitegrid", context="paper", font_scale=1.25)
    plt.rcParams.update({"savefig.dpi": 300, "axes.titleweight": "bold",
                         "axes.spines.top": False, "axes.spines.right": False,
                         "font.family": "DejaVu Sans"})
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    return plt, sns


def _fixed_rf_test_mae(split, feature_columns: list[str], seed: int) -> float:
    """Fit a fixed RandomForest on train+validation, return test MAE."""
    train_validation = pd.concat([split.train, split.validation], ignore_index=True)
    x_tv, y_tv = matrix_from_panel(train_validation, feature_columns, PRIMARY_TARGET)
    x_te, y_te = matrix_from_panel(split.test, feature_columns, PRIMARY_TARGET)
    pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("model", RandomForestRegressor(random_state=seed, **FIXED_RF)),
        ]
    )
    pipe.fit(x_tv, y_tv)
    pred = pipe.predict(x_te)
    return float(np.mean(np.abs(y_te.to_numpy(dtype=float) - pred)))


def multi_seed_nested() -> tuple[pd.DataFrame, pd.DataFrame]:
    """For each submodel and seed, compute baseline / augmented / delta test MAE."""
    main_panel = load_model_panel(PRIMARY_PANEL_PATH, PRIMARY_TARGET)
    main_feats = select_lag_features(main_panel, PRIMARY_LAG_SUFFIX)

    per_seed_rows: list[dict] = []
    for cfg in PANEL_CONFIGS:
        if cfg["role"] != "mechanism_submodel":
            continue
        sub_id = cfg["panel_id"]
        sub_panel = load_model_panel(cfg["panel_path"], PRIMARY_TARGET)
        sub_feats = select_lag_features(sub_panel, PRIMARY_LAG_SUFFIX)
        nested = build_nested_submodel_panel(
            main_panel=main_panel,
            sub_panel=sub_panel,
            main_feature_columns=main_feats,
            submodel_feature_columns=sub_feats,
            target_column=PRIMARY_TARGET,
        )
        split = chronological_train_validation_test_split(
            nested, train_share=TRAIN_SHARE, validation_share=VALIDATION_SHARE
        )
        for seed in SEEDS:
            base = _fixed_rf_test_mae(split, main_feats, seed)
            aug = _fixed_rf_test_mae(split, main_feats + sub_feats, seed)
            per_seed_rows.append(
                {"submodel": sub_id, "seed": seed, "baseline_test_mae": base,
                 "augmented_test_mae": aug, "delta_test_mae": aug - base}
            )
        print(f"  multi-seed done: {sub_id} ({len(SEEDS)} seeds)")

    per_seed = pd.DataFrame(per_seed_rows)
    summary_rows = []
    for sub_id, g in per_seed.groupby("submodel"):
        d = g["delta_test_mae"]
        summary_rows.append(
            {
                "submodel": sub_id,
                "submodel_label": SUB_LABELS.get(sub_id, sub_id),
                "n_seeds": int(len(d)),
                "mean_delta_mae": float(d.mean()),
                "std_delta_mae": float(d.std(ddof=1)),
                "median_delta_mae": float(d.median()),
                "min_delta_mae": float(d.min()),
                "max_delta_mae": float(d.max()),
                "share_seeds_predictors_help": float((d < 0).mean()),
                "robust_help": bool((d < 0).mean() >= 0.90),
            }
        )
    summary = pd.DataFrame(summary_rows).sort_values("mean_delta_mae").reset_index(drop=True)
    return per_seed, summary


def permutation_importance_main() -> pd.DataFrame:
    """Permutation importance for the selected main tree model on the test block."""
    spec = PanelSpec(
        panel_id="main_tree", panel_label="Main v2 — tree models",
        panel_path=PRIMARY_PANEL_PATH, target_column=PRIMARY_TARGET,
        lag_suffix=PRIMARY_LAG_SUFFIX, role="main_tree",
        comparison_group="tree", feature_set_role="primary_specification",
    )
    exp = run_panel_tree_experiment(spec, random_state=42,
                                    train_share=TRAIN_SHARE, validation_share=VALIDATION_SHARE)
    feats = exp["feature_columns"]
    model = exp["fitted_model"]
    x_te, y_te = matrix_from_panel(exp["split"].test, feats, PRIMARY_TARGET)
    result = permutation_importance(
        model, x_te, y_te, n_repeats=PERM_REPEATS, random_state=42,
        scoring="neg_mean_absolute_error",
    )
    impurity = exp["importance"].set_index("feature")["importance"]
    table = pd.DataFrame(
        {
            "feature": feats,
            "permutation_importance_mean": result.importances_mean,
            "permutation_importance_std": result.importances_std,
            "impurity_importance": [float(impurity.get(f, np.nan)) for f in feats],
        }
    ).sort_values("permutation_importance_mean", ascending=False).reset_index(drop=True)
    return table


def _clean(label: str) -> str:
    names = {
        "size_factor": "Economic scale / research capacity",
        "gdp_constant_2015_usd": "GDP (constant USD)", "co2_per_capita_ar5": "CO2 per capita",
        "wgi_regulatory_quality": "Regulatory quality", "env_technology_rta": "Env. tech RTA",
        "scientific_journal_articles": "Scientific articles", "fdi_net_inflows": "FDI net inflows",
        "renewable_energy_share": "Renewable share", "trade_openness": "Trade openness",
        "inflation": "Inflation",
    }
    return names.get(str(label).replace("_lag1_3_mean", ""), str(label).replace("_lag1_3_mean", ""))


def figure_multiseed(per_seed: pd.DataFrame, summary: pd.DataFrame, plt, sns) -> None:
    order = list(summary["submodel"])
    per_seed = per_seed.copy()
    per_seed["label"] = per_seed["submodel"].map(SUB_LABELS)
    order_labels = [SUB_LABELS[s] for s in order]
    fig, ax = plt.subplots(figsize=(8.6, 5.0), constrained_layout=True)
    sns.boxplot(data=per_seed, x="label", y="delta_test_mae", order=order_labels,
                color="#D9822B", width=0.5, fliersize=0, ax=ax)
    sns.stripplot(data=per_seed, x="label", y="delta_test_mae", order=order_labels,
                  color="#1F2937", alpha=0.5, size=4, ax=ax)
    ax.axhline(0, color="#B5482F", lw=1.3, ls="--")
    for i, s in enumerate(order):
        pct = float(summary.loc[summary["submodel"].eq(s), "share_seeds_predictors_help"].iloc[0])
        ax.text(i, ax.get_ylim()[1], f"{pct:.0%} of seeds <0", ha="center", va="top", fontsize=9, color="#2E8B6F")
    ax.set_xlabel("")
    ax.set_ylabel("Δ test MAE across seeds  (negative = predictors help)")
    ax.set_title(f"Submodel improvement across {len(SEEDS)} random seeds (fixed RandomForest)")
    fig.savefig(FIG_DIR / "fig6_multiseed_nested.png", bbox_inches="tight")
    fig.savefig(FIG_DIR / "fig6_multiseed_nested.pdf", bbox_inches="tight")
    plt.close(fig)
    print("  wrote fig6_multiseed_nested.png / .pdf")


def figure_permutation(table: pd.DataFrame, plt, sns) -> None:
    t = table.copy()
    t["feat"] = t["feature"].map(_clean)
    t = t.sort_values("permutation_importance_mean")
    fig, ax = plt.subplots(figsize=(8.6, 5.2), constrained_layout=True)
    ax.barh(t["feat"], t["permutation_importance_mean"],
            xerr=t["permutation_importance_std"], color="#2F6DB5",
            error_kw={"ecolor": "#888", "elinewidth": 1})
    ax.set_xlabel("Permutation importance (MAE increase when feature is shuffled)")
    ax.set_title("Permutation importance — main tree model (less biased than impurity)")
    fig.savefig(FIG_DIR / "fig7_permutation_importance.png", bbox_inches="tight")
    fig.savefig(FIG_DIR / "fig7_permutation_importance.pdf", bbox_inches="tight")
    plt.close(fig)
    print("  wrote fig7_permutation_importance.png / .pdf")


def main() -> None:
    TREE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plt, sns = _setup_mpl()

    print(f"(1) Multi-seed nested check ({len(SEEDS)} seeds, fixed RF {FIXED_RF}) ...")
    per_seed, summary = multi_seed_nested()
    per_seed.to_csv(TREE_OUTPUT_DIR / "tree_model_multiseed_nested.csv", index=False)
    summary.to_csv(TREE_OUTPUT_DIR / "tree_model_multiseed_nested_summary.csv", index=False)
    print(summary.to_string(index=False))

    print(f"\n(2) Permutation importance (main tree model, n_repeats={PERM_REPEATS}) ...")
    perm = permutation_importance_main()
    perm.to_csv(TREE_OUTPUT_DIR / "tree_model_permutation_importance.csv", index=False)
    print(perm.to_string(index=False))

    figure_multiseed(per_seed, summary, plt, sns)
    figure_permutation(perm, plt, sns)
    print("\nDone.")


if __name__ == "__main__":
    main()
