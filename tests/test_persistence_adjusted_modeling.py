import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "3_models" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from model_data import select_lag_features  # noqa: E402
from persistence_adjusted_modeling import (  # noqa: E402
    TARGET_VARIANTS,
    build_family_candidates,
    build_native_importance_table,
    build_persistence_adjusted_panel,
    summarize_persistence_adjusted_results,
)


class PersistenceAdjustedModelingTests(unittest.TestCase):
    def test_delta_target_uses_previous_calendar_year_and_drops_gaps(self):
        panel = pd.DataFrame(
            {
                "country_code": ["AAA", "AAA", "AAA", "BBB", "BBB"],
                "country_name": ["Alpha", "Alpha", "Alpha", "Beta", "Beta"],
                "year": [2000, 2001, 2002, 2000, 2002],
                "target": [1.0, 1.4, 1.1, 5.0, 6.5],
                "x_lag1": [10, 11, 12, 20, 22],
                "x_lag1_3_mean": [8, 9, 10, 18, 20],
            }
        )

        adjusted, target_column, metadata = build_persistence_adjusted_panel(
            panel,
            target_column="target",
            variant="delta_lag1",
        )

        self.assertEqual(target_column, "target_delta_from_previous_year")
        self.assertEqual(metadata["target_role"], "main_supplement")
        self.assertEqual(adjusted[["country_code", "year"]].values.tolist(), [["AAA", 2001], ["AAA", 2002]])
        self.assertTrue(np.allclose(adjusted[target_column].to_numpy(), [0.4, -0.3]))
        self.assertIn("previous_target_value", adjusted.columns)
        self.assertIn("previous_target_year", adjusted.columns)
        self.assertIn("target_year_gap", adjusted.columns)
        self.assertEqual(adjusted["target_year_gap"].tolist(), [1, 1])
        self.assertEqual(metadata["dropped_non_annual_pairs"], "1")
        self.assertEqual(adjusted["x_lag1"].tolist(), [11, 12])

    def test_log_ratio_target_uses_true_log_ratio_and_drops_nonpositive_pairs(self):
        panel = pd.DataFrame(
            {
                "country_code": ["AAA", "AAA", "AAA", "AAA"],
                "country_name": ["Alpha", "Alpha", "Alpha", "Alpha"],
                "year": [2000, 2001, 2002, 2003],
                "target": [0.0, 1.0, 3.0, 6.0],
                "x_lag1": [10, 11, 12, 13],
            }
        )

        adjusted, target_column, metadata = build_persistence_adjusted_panel(
            panel,
            target_column="target",
            variant="log_ratio_lag1",
        )

        self.assertEqual(target_column, "target_log_ratio_from_previous_year")
        self.assertEqual(metadata["target_role"], "robustness")
        expected = [np.log(3.0 / 1.0), np.log(6.0 / 3.0)]
        self.assertEqual(adjusted["year"].tolist(), [2002, 2003])
        self.assertTrue(np.allclose(adjusted[target_column].to_numpy(), expected))
        self.assertEqual(metadata["dropped_nonpositive_pairs"], "1")

    def test_family_candidates_are_split_into_three_separate_families(self):
        families = build_family_candidates(random_state=7)

        self.assertEqual(set(families), {"Linear", "RandomForest", "XGBoost"})
        self.assertGreater(len(families["Linear"]), 0)
        self.assertGreater(len(families["RandomForest"]), 0)
        self.assertGreater(len(families["XGBoost"]), 0)
        self.assertTrue(all(name.startswith("rf") for name in families["RandomForest"]))
        self.assertTrue(all(name.startswith("xgb") for name in families["XGBoost"]))
        self.assertIn("elastic_net_alpha_1_l1_0.2", families["Linear"])

    def test_target_variant_contract_marks_delta_primary_and_ratio_robustness(self):
        variants = {item["variant"]: item["target_role"] for item in TARGET_VARIANTS}

        self.assertEqual(variants["delta_lag1"], "main_supplement")
        self.assertEqual(variants["log_ratio_lag1"], "robustness")

    def test_helper_target_columns_do_not_enter_lag_feature_set(self):
        panel = pd.DataFrame(
            {
                "country_code": ["AAA", "AAA", "AAA"],
                "country_name": ["Alpha", "Alpha", "Alpha"],
                "year": [2000, 2001, 2002],
                "target": [1.0, 1.4, 1.1],
                "x_lag1": [10, 11, 12],
                "x_lag1_3_mean": [8, 9, 10],
            }
        )
        adjusted, target_column, _ = build_persistence_adjusted_panel(
            panel,
            target_column="target",
            variant="delta_lag1",
        )

        features = select_lag_features(adjusted, "lag1")

        self.assertEqual(features, ["x_lag1"])
        self.assertNotIn("target", features)
        self.assertNotIn(target_column, features)
        self.assertNotIn("previous_target_value", features)
        self.assertNotIn("target_year_gap", features)

    def test_summary_selects_family_by_validation_not_test_mae(self):
        results = pd.DataFrame(
            [
                {
                    "target_variant": "delta_lag1",
                    "target_role": "main_supplement",
                    "panel_id": "main",
                    "panel_label": "Main v2 model",
                    "lag_suffix": "lag1",
                    "family": "Linear",
                    "best_model": "elastic_net_alpha_1_l1_0.2",
                    "validation_mae": 0.10,
                    "test_mae": 0.50,
                    "test_minus_validation_mae": 0.40,
                    "zero_change_baseline_mae": 0.30,
                    "delta_test_mae_vs_zero_change": 0.20,
                    "beats_zero_change_baseline": False,
                    "test_spearman": 0.0,
                    "n_test": 10,
                    "dropped_non_annual_pairs": 1,
                    "dropped_nonpositive_pairs": 0,
                },
                {
                    "target_variant": "delta_lag1",
                    "target_role": "main_supplement",
                    "panel_id": "main",
                    "panel_label": "Main v2 model",
                    "lag_suffix": "lag1",
                    "family": "RandomForest",
                    "best_model": "rf_n100",
                    "validation_mae": 0.20,
                    "test_mae": 0.05,
                    "test_minus_validation_mae": -0.15,
                    "zero_change_baseline_mae": 0.30,
                    "delta_test_mae_vs_zero_change": -0.25,
                    "beats_zero_change_baseline": True,
                    "test_spearman": 0.1,
                    "n_test": 10,
                    "dropped_non_annual_pairs": 1,
                    "dropped_nonpositive_pairs": 0,
                },
            ]
        )

        summary = summarize_persistence_adjusted_results(results)

        self.assertEqual(summary["family"].tolist(), ["Linear"])
        self.assertEqual(summary["test_mae"].tolist(), [0.50])

    def test_native_importance_table_normalizes_linear_coefficients(self):
        x = pd.DataFrame(
            {
                "signal_lag1": [0.0, 1.0, 2.0, 3.0],
                "flat_lag1": [1.0, 1.0, 1.0, 1.0],
            }
        )
        y = pd.Series([0.0, 2.0, 4.0, 6.0])
        fitted = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
                ("scaler", StandardScaler()),
                ("model", LinearRegression()),
            ]
        ).fit(x, y)

        table = build_native_importance_table(
            fitted,
            ["signal_lag1", "flat_lag1"],
            model_name="linear_regression",
            family="Linear",
        )

        self.assertEqual(table.iloc[0]["feature"], "signal_lag1")
        self.assertEqual(table.iloc[0]["importance_kind"], "standardized_coefficient")
        self.assertAlmostEqual(float(table["normalized_importance"].sum()), 1.0)
        self.assertTrue(table["signed_importance"].notna().all())

    def test_native_importance_table_normalizes_tree_importances(self):
        class FakePipeline:
            named_steps = {"model": type("FakeTree", (), {"feature_importances_": np.array([0.75, 0.25])})()}

        table = build_native_importance_table(
            FakePipeline(),
            ["policy_lag1", "scale_lag1"],
            model_name="rf_n100",
            family="RandomForest",
        )

        self.assertEqual(table["feature"].tolist(), ["policy_lag1", "scale_lag1"])
        self.assertEqual(table["importance_kind"].unique().tolist(), ["tree_feature_importance"])
        self.assertAlmostEqual(float(table["normalized_importance"].sum()), 1.0)
        self.assertTrue(table["signed_importance"].isna().all())


if __name__ == "__main__":
    unittest.main()
