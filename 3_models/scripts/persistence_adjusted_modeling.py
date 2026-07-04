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
PERSISTENCE_FIGURE_OUTPUT = FIG_DIR / "fig12_persistence_adjusted_family_comparison.png"
PERSISTENCE_FIGURE_PDF_OUTPUT = FIG_DIR / "fig12_persistence_adjusted_family_comparison.pdf"
PERSISTENCE_IMPORTANCE_FIGURE_OUTPUT = FIG_DIR / "fig13_persistence_adjusted_delta_feature_roles.png"
PERSISTENCE_IMPORTANCE_FIGURE_PDF_OUTPUT = FIG_DIR / "fig13_persistence_adjusted_delta_feature_roles.pdf"

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
    results, _ = _run_persistence_adjusted_family_artifacts(random_state=random_state)
    return results


def _run_persistence_adjusted_family_artifacts(random_state: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run family-separated model comparisons and collect native importance tables."""
    families = build_family_candidates(random_state=random_state)
    rows = []
    importance_frames = []
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

                for family, candidates in families.items():
                    validation_metrics, _ = evaluate_candidates_on_validation(
                        candidates,
                        x_train,
                        y_train,
                        x_validation,
                        y_validation,
                    )
                    best_model = select_best_validation_model(validation_metrics)
                    best_validation = validation_metrics[validation_metrics["model"].eq(best_model)].iloc[0]
                    test_metrics, fitted_model, _ = evaluate_selected_model(
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
    return pd.DataFrame(rows), importance_output


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


def write_run_summary(results: pd.DataFrame, summary: pd.DataFrame) -> None:
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


def run_and_write_outputs(random_state: int = 42) -> dict[str, pd.DataFrame]:
    """Run the experiment and write CSV, markdown, and figure outputs."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results, importance = _run_persistence_adjusted_family_artifacts(random_state=random_state)
    summary = summarize_persistence_adjusted_results(results)
    top_importance = summarize_top_interpretation_features(importance, summary)
    results.to_csv(PERSISTENCE_OUTPUT, index=False)
    summary.to_csv(PERSISTENCE_SUMMARY_OUTPUT, index=False)
    importance.to_csv(PERSISTENCE_IMPORTANCE_OUTPUT, index=False)
    top_importance.to_csv(PERSISTENCE_TOP_IMPORTANCE_OUTPUT, index=False)
    write_run_summary(results, summary)
    make_persistence_adjusted_figure(results)
    make_persistence_adjusted_importance_figure(top_importance)
    return {"results": results, "summary": summary, "importance": importance, "top_importance": top_importance}


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
    print(f"wrote {PERSISTENCE_FIGURE_OUTPUT}")
    print(f"wrote {PERSISTENCE_IMPORTANCE_FIGURE_OUTPUT}")


if __name__ == "__main__":
    main()
