"""Tree persistence-augmented robustness check (advisor-requested).

Runs the same specification as the linear persistence-augmented comparison,
but with the tree families: main-panel features plus the block-safe
``target_history_preblock`` feature, evaluated against (a) the feature-only
tree specification and (b) the prediction-safe country-persistence baseline.

The advisor asked for "one additional specification with lagged target plus
features, to see whether the covariates add predictive value beyond
persistence", presented as a robustness check. The linear version already
exists (``linear_model_persistence_augmented_comparison.csv``); this script
adds the tree counterpart. Selection is validation-MAE only; the test block
is scored once per selected model.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.metrics import mean_absolute_error

from model_config import OUTPUT_DIR, PANEL_CONFIGS, TRAIN_SHARE, VALIDATION_SHARE
from model_data import (
    chronological_train_validation_test_split,
    load_model_panel,
    matrix_from_panel,
    select_lag_features,
)
from model_estimators import build_tree_model_candidates
from model_experiments import build_block_safe_target_history_feature

TREE_OUTPUT_DIR = OUTPUT_DIR / "tree"
COMPARISON_OUTPUT = TREE_OUTPUT_DIR / "tree_model_persistence_augmented_comparison.csv"
LINEAR_COMPARISON_PATH = OUTPUT_DIR / "linear_model_persistence_augmented_comparison.csv"
HISTORY_FEATURE = "target_history_preblock"
LAG_SUFFIX = "lag1_3_mean"


def _country_persistence_baseline(split, target_column: str) -> float:
    """Country-last baseline: latest pre-test target per country, held constant."""
    pretest = pd.concat([split.train, split.validation], ignore_index=True)
    latest = (
        pretest.sort_values("year").groupby("country_code")[target_column].last()
    )
    predictions = split.test["country_code"].map(latest)
    mask = predictions.notna()
    return float(
        mean_absolute_error(split.test.loc[mask, target_column], predictions[mask])
    )


def _select_and_score(split, feature_columns: list[str], target_column: str):
    """Validation-MAE selection over tree candidates; refit on train+validation,
    then a single test evaluation (same protocol as model_family_comparison)."""
    x_train, y_train = matrix_from_panel(split.train, feature_columns, target_column)
    x_validation, y_validation = matrix_from_panel(
        split.validation, feature_columns, target_column
    )
    x_test, y_test = matrix_from_panel(split.test, feature_columns, target_column)
    train_validation = pd.concat([split.train, split.validation], ignore_index=True)
    x_train_validation, y_train_validation = matrix_from_panel(
        train_validation, feature_columns, target_column
    )
    candidates = build_tree_model_candidates()
    best_name, best_validation_mae = None, None
    for name, pipeline in candidates.items():
        pipeline.fit(x_train, y_train)
        validation_mae = mean_absolute_error(y_validation, pipeline.predict(x_validation))
        if best_validation_mae is None or validation_mae < best_validation_mae:
            best_name, best_validation_mae = name, validation_mae
    refit_pipeline = build_tree_model_candidates()[best_name]
    refit_pipeline.fit(x_train_validation, y_train_validation)
    test_mae = float(mean_absolute_error(y_test, refit_pipeline.predict(x_test)))
    return best_name, float(best_validation_mae), test_mae


def main() -> None:
    main_cfg = next(cfg for cfg in PANEL_CONFIGS if cfg["panel_id"] == "main")
    target_column = main_cfg["target_column"]
    panel = load_model_panel(main_cfg["panel_path"], target_column)
    feature_columns = select_lag_features(panel, LAG_SUFFIX)
    split = chronological_train_validation_test_split(
        panel, train_share=TRAIN_SHARE, validation_share=VALIDATION_SHARE
    )

    baseline_mae = _country_persistence_baseline(split, target_column)

    feature_name, feature_val_mae, feature_test_mae = _select_and_score(
        split, feature_columns, target_column
    )

    augmented_panel = build_block_safe_target_history_feature(
        panel=panel, split=split, target_column=target_column,
        feature_name=HISTORY_FEATURE,
    )
    augmented_split = chronological_train_validation_test_split(
        augmented_panel, train_share=TRAIN_SHARE, validation_share=VALIDATION_SHARE
    )
    augmented_name, augmented_val_mae, augmented_test_mae = _select_and_score(
        augmented_split, feature_columns + [HISTORY_FEATURE], target_column
    )

    rows = [
        {
            "specification": "country_persistence_baseline",
            "family": "baseline",
            "selected_model": "country_last_pretest_holdconstant",
            "validation_mae": None,
            "test_mae": baseline_mae,
            "delta_test_mae_vs_baseline": 0.0,
            "beats_baseline": None,
        },
        {
            "specification": "tree_feature_only",
            "family": "tree",
            "selected_model": feature_name,
            "validation_mae": feature_val_mae,
            "test_mae": feature_test_mae,
            "delta_test_mae_vs_baseline": feature_test_mae - baseline_mae,
            "beats_baseline": feature_test_mae < baseline_mae,
        },
        {
            "specification": "tree_persistence_augmented",
            "family": "tree",
            "selected_model": augmented_name,
            "validation_mae": augmented_val_mae,
            "test_mae": augmented_test_mae,
            "delta_test_mae_vs_baseline": augmented_test_mae - baseline_mae,
            "beats_baseline": augmented_test_mae < baseline_mae,
        },
    ]
    if LINEAR_COMPARISON_PATH.exists():
        linear = pd.read_csv(LINEAR_COMPARISON_PATH)
        augmented_rows = linear[
            linear["model_stage"].astype(str).eq("persistence_augmented_linear")
        ]
        if not augmented_rows.empty:
            reference = augmented_rows.iloc[0]
            rows.append(
                {
                    "specification": "linear_persistence_augmented_reference",
                    "family": "linear",
                    "selected_model": str(reference["model"]),
                    "validation_mae": float(reference["validation_mae"]),
                    "test_mae": float(reference["test_mae"]),
                    "delta_test_mae_vs_baseline": float(reference["test_mae"]) - baseline_mae,
                    "beats_baseline": float(reference["test_mae"]) < baseline_mae,
                }
            )

    comparison = pd.DataFrame(rows)
    TREE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(COMPARISON_OUTPUT, index=False)
    print(f"wrote {COMPARISON_OUTPUT}")
    print(comparison.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
