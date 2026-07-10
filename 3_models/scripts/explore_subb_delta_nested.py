"""EXPLORATORY (branch explore/subb-delta-nested): does SubB (R&D) add value in delta space?

Level-space nested checks showed no submodel adds incremental value. The delta
corrected-level result, however, showed SubB beating the history-only benchmark.
That could come from the main controls alone. This script isolates the SubB
feature contribution in delta space with a same-sample, fixed-RF, multi-seed
nested comparison:

  baseline  = main controls only            (delta target)
  augmented = main controls + SubB features  (delta target)
  Delta = augmented_test_MAE - baseline_test_MAE   (negative => SubB helps)

25 seeds, identical rows. If the mean delta is negative across seeds, the delta
increment is attributable to the SubB (R&D / co-invention / tax) features, not
only to the main size/structure controls.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline

from model_config import PANEL_CONFIGS, TRAIN_SHARE, VALIDATION_SHARE
from model_data import (
    chronological_train_validation_test_split,
    load_model_panel,
    matrix_from_panel,
    select_lag_features,
)
from model_experiments import build_nested_submodel_panel
from persistence_adjusted_modeling import build_persistence_adjusted_panel

LAG = "lag1_3_mean"
SEEDS = list(range(25))
SUB_FEATURES = [
    "rd_expenditure_gdp",
    "env_co_invention_share",
    "energy_imports_net",
    "researchers_per_million",
    "environmental_tax_revenue",
]


def _fixed_rf_delta_mae(split, feature_columns: list[str], adjusted_target: str, seed: int) -> float:
    pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("model", RandomForestRegressor(n_estimators=300, random_state=seed, n_jobs=-1)),
        ]
    )
    x_train, y_train = matrix_from_panel(split.train, feature_columns, adjusted_target)
    x_test, y_test = matrix_from_panel(split.test, feature_columns, adjusted_target)
    pipe.fit(x_train, y_train)
    return float(mean_absolute_error(y_test, pipe.predict(x_test)))


def main() -> None:
    main_cfg = next(c for c in PANEL_CONFIGS if c["panel_id"] == "main")
    subb_cfg = next(c for c in PANEL_CONFIGS if c["panel_id"] == "subb")
    target = main_cfg["target_column"]

    main_panel = load_model_panel(main_cfg["panel_path"], target)
    subb_panel = load_model_panel(subb_cfg["panel_path"], target)

    main_feats = select_lag_features(main_panel, LAG)
    sub_feats = [f"{name}_{LAG}" for name in SUB_FEATURES]

    nested = build_nested_submodel_panel(
        main_panel=main_panel,
        sub_panel=subb_panel,
        main_feature_columns=main_feats,
        submodel_feature_columns=sub_feats,
        target_column=target,
    )
    adjusted, adjusted_target, meta = build_persistence_adjusted_panel(
        nested, target_column=target, variant="delta_lag1"
    )
    split = chronological_train_validation_test_split(
        adjusted, train_share=TRAIN_SHARE, validation_share=VALIDATION_SHARE
    )
    print(f"SubB delta nested: rows={len(adjusted)} countries={adjusted.country_code.nunique()} "
          f"train/val/test={len(split.train)}/{len(split.validation)}/{len(split.test)}")

    deltas = []
    for seed in SEEDS:
        base = _fixed_rf_delta_mae(split, main_feats, adjusted_target, seed)
        aug = _fixed_rf_delta_mae(split, main_feats + sub_feats, adjusted_target, seed)
        deltas.append(aug - base)
    deltas = np.array(deltas)
    print("\n=== SubB delta-space nested (fixed RF n=300, 25 seeds) ===")
    print(f"mean delta MAE      = {deltas.mean():+.4f}")
    print(f"median delta MAE    = {np.median(deltas):+.4f}")
    print(f"std                 = {deltas.std():.4f}")
    print(f"share seeds delta<0 = {(deltas < 0).mean():.2f}  ({int((deltas < 0).sum())}/25)")
    print("Interpretation: delta<0 means SubB (R&D) features reduce delta-space error "
          "beyond the main controls.")


if __name__ == "__main__":
    main()
