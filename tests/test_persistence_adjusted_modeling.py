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
from model_data import ChronologicalSplit  # noqa: E402
from persistence_adjusted_modeling import (  # noqa: E402
    TARGET_VARIANTS,
    build_validation_block_level_correction_predictions,
    build_family_candidates,
    build_block_safe_level_correction_predictions,
    build_native_importance_table,
    build_persistence_adjusted_panel,
    select_validation_level_models,
    summarize_level_correction_predictions,
    summarize_persistence_adjusted_results,
    _validation_artifact_schema,
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

    def test_level_correction_recurses_from_pretest_anchor_without_test_labels(self):
        split = ChronologicalSplit(
            train=pd.DataFrame(
                {
                    "country_code": ["AAA", "AAA"],
                    "country_name": ["Alpha", "Alpha"],
                    "year": [2000, 2001],
                    "target": [1.0, 2.0],
                }
            ),
            validation=pd.DataFrame(
                {
                    "country_code": ["AAA"],
                    "country_name": ["Alpha"],
                    "year": [2002],
                    "target": [10.0],
                }
            ),
            test=pd.DataFrame(
                {
                    "country_code": ["AAA", "AAA", "BBB"],
                    "country_name": ["Alpha", "Alpha", "Beta"],
                    "year": [2003, 2004, 2003],
                    "target": [100.0, 200.0, 50.0],
                    "previous_target_value": [10.0, 100.0, np.nan],
                }
            ),
            train_years=[2000, 2001],
            validation_years=[2002],
            test_years=[2003, 2004],
        )

        predictions = build_block_safe_level_correction_predictions(
            split=split,
            source_target_column="target",
            delta_predictions=np.array([1.0, 1.0, 2.0]),
            metadata={
                "target_variant": "delta_lag1",
                "panel_id": "toy",
                "lag_suffix": "lag1",
                "family": "Linear",
                "best_model": "linear_regression",
            },
        )

        alpha = predictions[predictions["country_code"].eq("AAA")].sort_values("year")
        self.assertEqual(alpha["history_anchor_value"].tolist(), [10.0, 10.0])
        self.assertEqual(alpha["history_only_prediction"].tolist(), [10.0, 10.0])
        self.assertEqual(alpha["corrected_level_prediction"].tolist(), [11.0, 12.0])
        self.assertTrue(alpha["forecast_path_eligible"].all())
        self.assertTrue((alpha["uses_test_label_for_anchor"] == False).all())  # noqa: E712
        beta = predictions[predictions["country_code"].eq("BBB")].iloc[0]
        self.assertFalse(bool(beta["forecast_path_eligible"]))
        self.assertTrue(pd.isna(beta["corrected_level_prediction"]))
        self.assertAlmostEqual(float(beta["history_anchor_value"]), (1.0 + 2.0 + 10.0) / 3.0)
        self.assertEqual(beta["history_anchor_source"], "global_train_validation_mean")

    def test_level_correction_flags_nonconsecutive_anchor_paths(self):
        split = ChronologicalSplit(
            train=pd.DataFrame(
                {
                    "country_code": ["AAA"],
                    "country_name": ["Alpha"],
                    "year": [2000],
                    "target": [1.0],
                }
            ),
            validation=pd.DataFrame(
                {
                    "country_code": ["BBB"],
                    "country_name": ["Beta"],
                    "year": [2001],
                    "target": [5.0],
                }
            ),
            test=pd.DataFrame(
                {
                    "country_code": ["AAA"],
                    "country_name": ["Alpha"],
                    "year": [2003],
                    "target": [10.0],
                }
            ),
            train_years=[2000],
            validation_years=[2001],
            test_years=[2003],
        )

        predictions = build_block_safe_level_correction_predictions(
            split=split,
            source_target_column="target",
            delta_predictions=np.array([1.0]),
            metadata={
                "target_variant": "delta_lag1",
                "panel_id": "toy",
                "lag_suffix": "lag1",
                "family": "Linear",
                "best_model": "linear_regression",
            },
        )

        row = predictions.iloc[0]
        self.assertFalse(bool(row["forecast_path_eligible"]))
        self.assertEqual(int(row["anchor_to_first_test_gap_years"]), 3)
        self.assertTrue(pd.isna(row["corrected_level_prediction"]))

    def test_level_correction_summary_reports_signed_delta_against_history(self):
        predictions = pd.DataFrame(
            {
                "target_variant": ["delta_lag1", "delta_lag1"],
                "panel_id": ["main", "main"],
                "lag_suffix": ["lag1", "lag1"],
                "family": ["RandomForest", "RandomForest"],
                "best_model": ["rf_n100", "rf_n100"],
                "observed_level": [2.0, 4.0],
                "history_only_prediction": [1.0, 1.0],
                "corrected_level_prediction": [2.5, 3.5],
                "forecast_path_eligible": [True, True],
            }
        )

        summary = summarize_level_correction_predictions(predictions)

        row = summary.iloc[0]
        self.assertAlmostEqual(float(row["history_only_mae"]), 2.0)
        self.assertAlmostEqual(float(row["corrected_level_mae"]), 0.5)
        self.assertAlmostEqual(float(row["delta_corrected_mae_minus_history"]), -1.5)
        self.assertTrue(bool(row["beats_history_only"]))

    def test_level_correction_summary_excludes_ineligible_paths(self):
        predictions = pd.DataFrame(
            {
                "target_variant": ["delta_lag1", "delta_lag1"],
                "panel_id": ["main", "main"],
                "lag_suffix": ["lag1", "lag1"],
                "family": ["RandomForest", "RandomForest"],
                "best_model": ["rf_n100", "rf_n100"],
                "observed_level": [2.0, 100.0],
                "history_only_prediction": [1.0, 1.0],
                "corrected_level_prediction": [2.5, np.nan],
                "forecast_path_eligible": [True, False],
            }
        )

        summary = summarize_level_correction_predictions(predictions)

        row = summary.iloc[0]
        self.assertEqual(int(row["n_forecast"]), 1)
        self.assertEqual(int(row["n_test"]), 1)
        self.assertEqual(int(row["n_forecast_total"]), 2)
        self.assertEqual(int(row["n_test_total"]), 2)
        self.assertEqual(int(row["n_forecast_excluded_anchor_gap"]), 1)
        self.assertEqual(int(row["n_test_excluded_anchor_gap"]), 1)
        self.assertAlmostEqual(float(row["history_only_mae"]), 1.0)
        self.assertAlmostEqual(float(row["corrected_level_mae"]), 0.5)

    def test_level_correction_summary_excludes_global_fallback_anchors(self):
        predictions = pd.DataFrame(
            {
                "target_variant": ["delta_lag1", "delta_lag1"],
                "panel_id": ["main", "main"],
                "lag_suffix": ["lag1", "lag1"],
                "family": ["RandomForest", "RandomForest"],
                "best_model": ["rf_n100", "rf_n100"],
                "observed_level": [2.0, 100.0],
                "history_only_prediction": [1.0, 1.0],
                "corrected_level_prediction": [2.5, np.nan],
                "forecast_path_eligible": [True, False],
                "history_anchor_source": [
                    "country_latest_train_validation_target",
                    "global_train_validation_mean",
                ],
            }
        )

        summary = summarize_level_correction_predictions(predictions)

        row = summary.iloc[0]
        self.assertEqual(int(row["n_test"]), 1)
        self.assertEqual(int(row["n_test_total"]), 2)
        self.assertEqual(int(row["n_test_excluded_anchor_gap"]), 1)
        self.assertEqual(int(row["global_fallback_anchor_rows"]), 1)

    def test_validation_block_correction_anchors_on_train_only(self):
        split = ChronologicalSplit(
            train=pd.DataFrame(
                {
                    "country_code": ["AAA"],
                    "country_name": ["Alpha"],
                    "year": [2000],
                    "target": [1.0],
                }
            ),
            validation=pd.DataFrame(
                {
                    "country_code": ["AAA", "AAA"],
                    "country_name": ["Alpha", "Alpha"],
                    "year": [2001, 2002],
                    "target": [10.0, 100.0],
                    "previous_target_value": [1.0, 10.0],
                }
            ),
            test=pd.DataFrame(
                {
                    "country_code": ["AAA"],
                    "country_name": ["Alpha"],
                    "year": [2003],
                    "target": [1000.0],
                }
            ),
            train_years=[2000],
            validation_years=[2001, 2002],
            test_years=[2003],
        )

        predictions = build_validation_block_level_correction_predictions(
            split=split,
            source_target_column="target",
            delta_predictions=np.array([2.0, 3.0]),
            metadata={
                "target_variant": "delta_lag1",
                "panel_id": "toy",
                "lag_suffix": "lag1",
                "family": "Linear",
                "best_model": "linear_regression",
            },
        )

        self.assertEqual(predictions["forecast_block"].unique().tolist(), ["validation"])
        self.assertEqual(predictions["history_anchor_source"].unique().tolist(), ["country_latest_train_target"])
        self.assertEqual(predictions["history_anchor_value"].tolist(), [1.0, 1.0])
        self.assertEqual(predictions["corrected_level_prediction"].tolist(), [3.0, 6.0])
        self.assertTrue((predictions["uses_test_label_for_anchor"] == False).all())  # noqa: E712

    def test_validation_selection_uses_validation_corrected_level_mae(self):
        validation_summary = pd.DataFrame(
            [
                {
                    "target_variant": "delta_lag1",
                    "forecast_block": "validation",
                    "panel_id": "main",
                    "panel_label": "Main panel",
                    "lag_suffix": "lag1",
                    "family": "RandomForest",
                    "best_model": "rf_test_winner",
                    "n_test": 10,
                    "corrected_level_mae": 0.40,
                    "history_only_mae": 0.50,
                    "delta_corrected_mae_minus_history": -0.10,
                    "corrected_level_rmse": 0.45,
                },
                {
                    "target_variant": "delta_lag1",
                    "forecast_block": "validation",
                    "panel_id": "main",
                    "panel_label": "Main panel",
                    "lag_suffix": "lag1_3_mean",
                    "family": "XGBoost",
                    "best_model": "xgb_validation_winner",
                    "n_test": 10,
                    "corrected_level_mae": 0.30,
                    "history_only_mae": 0.50,
                    "delta_corrected_mae_minus_history": -0.20,
                    "corrected_level_rmse": 0.36,
                },
                {
                    "target_variant": "delta_lag1",
                    "forecast_block": "test",
                    "panel_id": "main",
                    "panel_label": "Main panel",
                    "lag_suffix": "lag1",
                    "family": "RandomForest",
                    "best_model": "rf_test_winner",
                    "n_test": 10,
                    "corrected_level_mae": 0.01,
                    "history_only_mae": 0.50,
                    "delta_corrected_mae_minus_history": -0.49,
                    "corrected_level_rmse": 0.02,
                },
            ]
        )

        selected = select_validation_level_models(validation_summary)

        self.assertEqual(len(selected), 1)
        row = selected.iloc[0]
        self.assertEqual(row["family"], "XGBoost")
        self.assertEqual(row["best_model"], "xgb_validation_winner")
        self.assertEqual(int(row["n_forecast"]), 10)
        self.assertEqual(row["selection_metric"], "validation_corrected_level_mae")
        self.assertEqual(row["selection_scope"], "target_variant_panel")

    def test_validation_artifact_schema_drops_test_named_legacy_aliases(self):
        frame = pd.DataFrame(
            {
                "forecast_block": ["validation"],
                "n_forecast": [1],
                "n_test": [1],
                "n_forecast_total": [2],
                "n_test_total": [2],
                "n_forecast_excluded_anchor_gap": [1],
                "n_test_excluded_anchor_gap": [1],
                "anchor_to_first_forecast_gap_years": [1],
                "anchor_to_first_test_gap_years": [1],
                "forecast_path_is_consecutive": [True],
                "test_path_is_consecutive": [True],
            }
        )

        output = _validation_artifact_schema(frame)

        self.assertIn("n_forecast", output.columns)
        self.assertIn("anchor_to_first_forecast_gap_years", output.columns)
        self.assertIn("forecast_path_is_consecutive", output.columns)
        self.assertNotIn("n_test", output.columns)
        self.assertNotIn("n_test_total", output.columns)
        self.assertNotIn("n_test_excluded_anchor_gap", output.columns)
        self.assertNotIn("anchor_to_first_test_gap_years", output.columns)
        self.assertNotIn("test_path_is_consecutive", output.columns)


if __name__ == "__main__":
    unittest.main()
