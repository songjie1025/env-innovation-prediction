import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "3_models" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from model_experiments import (  # noqa: E402
    PanelSpec,
    build_missingness_indicator_panel,
    build_block_safe_target_history_feature,
    build_persistence_augmented_comparison_table,
    build_robustness_summary_table,
    build_skew_transformed_panel,
    build_nested_comparison_table,
    build_nested_submodel_panel,
    run_rolling_origin_linear_evaluation,
    combine_experiment_tables,
    run_panel_linear_experiment,
    run_panel_linear_experiment_from_panel,
)


class ModelExperimentTests(unittest.TestCase):
    def test_panel_linear_experiment_returns_complete_outputs(self):
        panel = _toy_panel(years=range(2000, 2010), countries=("AAA", "BBB", "CCC"))

        with tempfile.TemporaryDirectory() as tmp:
            panel_path = Path(tmp) / "toy_panel.csv"
            panel.to_csv(panel_path, index=False)
            spec = PanelSpec(
                panel_id="toy",
                panel_label="Toy mechanism panel",
                panel_path=panel_path,
                target_column="target",
                lag_suffix="lag1_3_mean",
                role="test",
            )

            result = run_panel_linear_experiment(spec, random_state=42)

        self.assertEqual(result["panel_id"], "toy")
        self.assertEqual(result["panel_label"], "Toy mechanism panel")
        self.assertIn("best_model", result)
        self.assertEqual(result["feature_columns"], ["x_lag1_3_mean", "z_lag1_3_mean"])
        self.assertEqual(result["split_years"]["train"], list(range(2000, 2008)))
        self.assertEqual(result["split_years"]["validation"], [2008])
        self.assertEqual(result["split_years"]["test"], [2009])

        for table_name in ["sample_summary", "validation_metrics", "test_metrics", "predictions", "coefficients"]:
            self.assertIn(table_name, result)
            self.assertIsInstance(result[table_name], pd.DataFrame)
            self.assertFalse(result[table_name].empty)
            self.assertIn("panel_id", result[table_name].columns)
            self.assertIn("panel_label", result[table_name].columns)

        self.assertTrue(result["validation_metrics"]["model"].notna().all())
        self.assertEqual(
            set(result["validation_metrics"]["comparison_scope"]),
            {"own_sample_not_direct_ranking"},
        )
        self.assertIn("panel_rows", result["validation_metrics"].columns)
        self.assertIn("panel_countries", result["validation_metrics"].columns)
        self.assertTrue(np.isfinite(result["test_metrics"].iloc[0]["mae"]))
        self.assertEqual(
            set(result["test_metrics"]["comparison_scope"]),
            {"own_sample_not_direct_ranking"},
        )
        self.assertIn("test_countries", result["test_metrics"].columns)
        self.assertIn("prediction", result["predictions"].columns)
        self.assertIn("observed", result["predictions"].columns)
        self.assertIn("error", result["predictions"].columns)
        self.assertTrue(result["predictions"]["observed"].equals(result["predictions"]["target"]))

    def test_skew_transformed_panel_preserves_missingness_and_feature_order(self):
        panel = pd.DataFrame(
            {
                "country_code": ["AAA", "AAA", "BBB"],
                "country_name": ["A", "A", "B"],
                "year": [2000, 2001, 2000],
                "target": [1.0, 2.0, 3.0],
                "gdp_lag1_3_mean": [0.0, 99.0, np.nan],
                "fdi_lag1_3_mean": [-10.0, 0.0, 10.0],
                "wgi_lag1_3_mean": [-1.0, 0.0, 1.0],
            }
        )

        transformed, features, plan = build_skew_transformed_panel(
            panel=panel,
            feature_columns=["gdp_lag1_3_mean", "fdi_lag1_3_mean", "wgi_lag1_3_mean"],
            transform_methods={
                "gdp_lag1_3_mean": "log1p",
                "fdi_lag1_3_mean": "asinh",
            },
        )

        self.assertEqual(
            features,
            [
                "skew_log1p__gdp_lag1_3_mean",
                "skew_asinh__fdi_lag1_3_mean",
                "wgi_lag1_3_mean",
            ],
        )
        self.assertAlmostEqual(transformed.loc[1, "skew_log1p__gdp_lag1_3_mean"], np.log1p(99.0))
        self.assertTrue(pd.isna(transformed.loc[2, "skew_log1p__gdp_lag1_3_mean"]))
        self.assertAlmostEqual(transformed.loc[0, "skew_asinh__fdi_lag1_3_mean"], np.arcsinh(-10.0))
        self.assertEqual(transformed.loc[2, "wgi_lag1_3_mean"], 1.0)
        self.assertEqual(
            list(plan["transformation"]),
            ["log1p", "asinh", "identity"],
        )
        self.assertTrue(plan["missing_values_preserved"].all())

    def test_combine_experiment_tables_preserves_panel_sample_context(self):
        panel = _toy_panel(years=range(2000, 2010), countries=("AAA", "BBB"))

        with tempfile.TemporaryDirectory() as tmp:
            specs = []
            for panel_id, label in [("main", "Main model"), ("suba", "RISE submodel")]:
                panel_path = Path(tmp) / f"{panel_id}.csv"
                panel.to_csv(panel_path, index=False)
                specs.append(
                    PanelSpec(
                        panel_id=panel_id,
                        panel_label=label,
                        panel_path=panel_path,
                        target_column="target",
                        lag_suffix="lag1_3_mean",
                        role="main" if panel_id == "main" else "submodel",
                    )
                )

            experiments = [run_panel_linear_experiment(spec, random_state=42) for spec in specs]
            combined = combine_experiment_tables(experiments)

        self.assertEqual(
            set(combined),
            {
                "sample_summary",
                "validation_metrics",
                "test_metrics",
                "predictions",
                "coefficients",
                "panel_comparison",
            },
        )
        comparison = combined["panel_comparison"]
        self.assertEqual(set(comparison["panel_id"]), {"main", "suba"})
        self.assertIn("test_year_start", comparison.columns)
        self.assertIn("test_year_end", comparison.columns)
        self.assertIn("feature_columns", comparison.columns)
        self.assertIn("test_mae", comparison.columns)

    def test_nested_submodel_comparison_uses_same_rows_for_main_and_augmented_models(self):
        main_panel = _toy_panel(years=range(2000, 2010), countries=("AAA", "BBB", "CCC"))
        sub_panel = main_panel.loc[main_panel["country_code"].isin(["AAA", "BBB"])].copy()
        sub_panel["policy_lag1_3_mean"] = sub_panel["x_lag1_3_mean"] * 0.2
        main_features = ["x_lag1_3_mean", "z_lag1_3_mean"]
        sub_features = ["policy_lag1_3_mean"]

        nested_panel = build_nested_submodel_panel(
            main_panel=main_panel,
            sub_panel=sub_panel,
            main_feature_columns=main_features,
            submodel_feature_columns=sub_features,
            target_column="target",
        )

        baseline_spec = PanelSpec(
            panel_id="main_on_suba",
            panel_label="Main controls on SubA sample",
            panel_path=None,
            target_column="target",
            lag_suffix="lag1_3_mean",
            role="nested_baseline",
            comparison_group="suba",
            feature_set_role="main_controls",
        )
        augmented_spec = PanelSpec(
            panel_id="main_plus_suba",
            panel_label="Main controls plus SubA predictors",
            panel_path=None,
            target_column="target",
            lag_suffix="lag1_3_mean",
            role="nested_augmented",
            comparison_group="suba",
            feature_set_role="main_plus_submodel",
        )

        baseline = run_panel_linear_experiment_from_panel(
            baseline_spec,
            nested_panel,
            feature_columns=main_features,
            random_state=42,
        )
        augmented = run_panel_linear_experiment_from_panel(
            augmented_spec,
            nested_panel,
            feature_columns=main_features + sub_features,
            random_state=42,
        )
        nested_comparison = build_nested_comparison_table([baseline, augmented])

        self.assertEqual(len(nested_panel), len(sub_panel))
        self.assertEqual(baseline["split_years"], augmented["split_years"])
        self.assertEqual(baseline["test_metrics"].iloc[0]["n_test"], augmented["test_metrics"].iloc[0]["n_test"])
        self.assertEqual(baseline["sample_summary"].query("split == 'all'")["rows"].iloc[0], len(nested_panel))
        self.assertEqual(augmented["sample_summary"].query("split == 'all'")["rows"].iloc[0], len(nested_panel))

        self.assertEqual(nested_comparison.iloc[0]["comparison_group"], "suba")
        self.assertEqual(nested_comparison.iloc[0]["comparison_scope"], "same_sample_nested")
        self.assertIn("delta_test_mae_augmented_minus_baseline", nested_comparison.columns)
        self.assertIn("improves_primary_test_mae", nested_comparison.columns)
        self.assertIsInstance(bool(nested_comparison.iloc[0]["improves_primary_test_mae"]), bool)

    def test_nested_submodel_panel_rejects_overlapping_feature_names(self):
        main_panel = _toy_panel(years=range(2000, 2010), countries=("AAA", "BBB"))
        sub_panel = main_panel.copy()

        with self.assertRaisesRegex(ValueError, "feature columns overlap"):
            build_nested_submodel_panel(
                main_panel=main_panel,
                sub_panel=sub_panel,
                main_feature_columns=["x_lag1_3_mean"],
                submodel_feature_columns=["x_lag1_3_mean"],
                target_column="target",
            )

    def test_panel_linear_experiment_from_panel_can_reuse_fixed_split_years(self):
        panel = _toy_panel(years=range(2000, 2010), countries=("AAA", "BBB", "CCC"))
        spec = PanelSpec(
            panel_id="complete_case",
            panel_label="Complete-case sensitivity",
            panel_path=None,
            target_column="target",
            lag_suffix="lag1_3_mean",
            role="missingness_sensitivity",
        )

        result = run_panel_linear_experiment_from_panel(
            spec,
            panel,
            feature_columns=["x_lag1_3_mean", "z_lag1_3_mean"],
            random_state=42,
            split_years={
                "train": [2000, 2001, 2002, 2003, 2004],
                "validation": [2005, 2006],
                "test": [2007, 2008, 2009],
            },
        )

        self.assertEqual(result["split_years"]["train"], [2000, 2001, 2002, 2003, 2004])
        self.assertEqual(result["split_years"]["validation"], [2005, 2006])
        self.assertEqual(result["split_years"]["test"], [2007, 2008, 2009])
        self.assertEqual(result["test_metrics"].iloc[0]["test_year_start"], 2007)
        self.assertEqual(result["test_metrics"].iloc[0]["test_year_end"], 2009)

    def test_rolling_origin_linear_evaluation_covers_distributed_test_periods(self):
        panel = _toy_panel(years=range(2000, 2012), countries=("AAA", "BBB", "CCC"))
        spec = PanelSpec(
            panel_id="main",
            panel_label="Main model",
            panel_path=None,
            target_column="target",
            lag_suffix="lag1_3_mean",
            role="rolling_origin_confirmatory",
        )

        result = run_rolling_origin_linear_evaluation(
            spec,
            panel=panel,
            feature_columns=["x_lag1_3_mean", "z_lag1_3_mean"],
            random_state=42,
            initial_pretest_years=4,
            validation_years=2,
            test_window_years=2,
        )

        fold_summary = result["fold_summary"]
        self.assertEqual(list(fold_summary["fold_id"]), ["fold_1", "fold_2", "fold_3", "fold_4"])
        self.assertEqual(list(fold_summary["test_year_start"]), [2004, 2006, 2008, 2010])
        self.assertEqual(list(fold_summary["test_year_end"]), [2005, 2007, 2009, 2011])
        self.assertTrue((fold_summary["validation_year_end"] < fold_summary["test_year_start"]).all())
        self.assertIn("delta_mae_selected_minus_best_history", fold_summary.columns)
        self.assertIn("best_historical_baseline_model", fold_summary.columns)
        self.assertFalse(result["fold_predictions"].empty)
        self.assertEqual(
            set(result["fold_predictions"]["fold_id"]),
            {"fold_1", "fold_2", "fold_3", "fold_4"},
        )

    def test_missingness_indicator_panel_adds_binary_features_without_imputing_values(self):
        panel = pd.DataFrame(
            {
                "country_code": ["AAA", "AAA", "BBB"],
                "country_name": ["Alpha", "Alpha", "Beta"],
                "year": [2000, 2001, 2000],
                "target": [1.0, 2.0, 3.0],
                "x_lag1_3_mean": [1.0, np.nan, 3.0],
                "z_lag1_3_mean": [np.nan, 2.0, 3.0],
            }
        )

        augmented_panel, augmented_features, indicator_plan = build_missingness_indicator_panel(
            panel=panel,
            feature_columns=["x_lag1_3_mean", "z_lag1_3_mean"],
        )

        self.assertEqual(
            augmented_features,
            [
                "x_lag1_3_mean",
                "z_lag1_3_mean",
                "missing__x_lag1_3_mean",
                "missing__z_lag1_3_mean",
            ],
        )
        self.assertTrue(pd.isna(augmented_panel.loc[1, "x_lag1_3_mean"]))
        self.assertEqual(list(augmented_panel["missing__x_lag1_3_mean"]), [0, 1, 0])
        self.assertEqual(list(augmented_panel["missing__z_lag1_3_mean"]), [1, 0, 0])
        self.assertEqual(set(indicator_plan["indicator_feature"]), {"missing__x_lag1_3_mean", "missing__z_lag1_3_mean"})

    def test_block_safe_target_history_feature_does_not_use_validation_or_test_labels_inside_block(self):
        panel = pd.DataFrame(
            {
                "country_code": ["AAA"] * 6,
                "country_name": ["Alpha"] * 6,
                "year": [2000, 2001, 2002, 2003, 2004, 2005],
                "target": [1.0, 2.0, 30.0, 40.0, 500.0, 600.0],
                "x_lag1_3_mean": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
            }
        )
        split_result = run_panel_linear_experiment_from_panel(
            PanelSpec(
                panel_id="toy",
                panel_label="Toy",
                panel_path=None,
                target_column="target",
                lag_suffix="lag1_3_mean",
                role="test",
            ),
            panel,
            feature_columns=["x_lag1_3_mean"],
            random_state=42,
            split_years={
                "train": [2000, 2001],
                "validation": [2002, 2003],
                "test": [2004, 2005],
            },
        )

        augmented_panel = build_block_safe_target_history_feature(
            panel=panel,
            split=split_result["split"],
            target_column="target",
            feature_name="target_history_preblock",
        )

        history_by_year = dict(zip(augmented_panel["year"], augmented_panel["target_history_preblock"]))
        self.assertEqual(history_by_year[2001], 1.0)
        self.assertEqual(history_by_year[2002], 2.0)
        self.assertEqual(history_by_year[2003], 2.0)
        self.assertEqual(history_by_year[2004], 40.0)
        self.assertEqual(history_by_year[2005], 40.0)

    def test_persistence_augmented_comparison_table_keeps_feature_history_and_augmented_rows(self):
        feature_experiment = {
            "best_model": "elastic_net_feature_only",
            "validation_metrics": pd.DataFrame(
                [{"model": "elastic_net_feature_only", "mae": 1.2, "rmse": 1.4}]
            ),
            "test_metrics": pd.DataFrame(
                [
                    {
                        "model": "elastic_net_feature_only",
                        "mae": 1.5,
                        "rmse": 2.0,
                        "oos_r2_vs_train_mean": 0.1,
                        "spearman": 0.7,
                        "n_test": 10,
                        "test_year_start": 2021,
                        "test_year_end": 2023,
                    }
                ]
            ),
        }
        augmented_experiment = {
            "best_model": "ridge_augmented",
            "validation_metrics": pd.DataFrame(
                [{"model": "ridge_augmented", "mae": 0.8, "rmse": 1.1}]
            ),
            "test_metrics": pd.DataFrame(
                [
                    {
                        "model": "ridge_augmented",
                        "mae": 0.9,
                        "rmse": 1.3,
                        "oos_r2_vs_train_mean": 0.5,
                        "spearman": 0.9,
                        "n_test": 10,
                        "test_year_start": 2021,
                        "test_year_end": 2023,
                    }
                ]
            ),
        }
        historical_baselines = pd.DataFrame(
            [
                {
                    "model": "elastic_net_feature_only",
                    "prediction_rule": "selected_linear_model",
                    "mae": 1.5,
                    "rmse": 2.0,
                    "oos_r2_vs_train_mean": 0.1,
                    "spearman": 0.7,
                    "n_test": 10,
                    "uses_test_labels": False,
                },
                {
                    "model": "oracle_test_period_mean",
                    "prediction_rule": "uses test-period target mean",
                    "mae": 0.1,
                    "rmse": 0.2,
                    "oos_r2_vs_train_mean": 0.95,
                    "spearman": 0.99,
                    "n_test": 10,
                    "uses_test_labels": True,
                },
                {
                    "model": "country_last_pretest_holdconstant",
                    "prediction_rule": "country latest observed train+validation target held constant",
                    "mae": 0.7,
                    "rmse": 1.0,
                    "oos_r2_vs_train_mean": 0.6,
                    "spearman": 0.95,
                    "n_test": 10,
                    "uses_test_labels": False,
                },
            ]
        )

        comparison = build_persistence_augmented_comparison_table(
            feature_experiment=feature_experiment,
            augmented_experiment=augmented_experiment,
            historical_baselines=historical_baselines,
        )

        self.assertEqual(
            list(comparison["model_stage"]),
            ["history_only_baseline", "persistence_augmented_linear", "feature_only_linear"],
        )
        self.assertEqual(
            list(comparison["includes_target_history"]),
            [True, True, False],
        )
        self.assertEqual(comparison.iloc[0]["model"], "country_last_pretest_holdconstant")
        self.assertEqual(comparison.iloc[1]["validation_mae"], 0.8)
        self.assertEqual(comparison.iloc[2]["validation_mae"], 1.2)

    def test_robustness_summary_tracks_model_choice_and_history_delta(self):
        panel = _toy_panel(years=range(2000, 2010), countries=("AAA", "BBB", "CCC"))
        panel["x_lag1"] = panel["x_lag1_3_mean"] + 0.1
        panel["z_lag1"] = panel["z_lag1_3_mean"]
        spec = PanelSpec(
            panel_id="robust_share_lag1",
            panel_label="Target share with lag1 predictors",
            panel_path=None,
            target_column="target",
            lag_suffix="lag1",
            role="robustness",
            comparison_group="target_share",
            feature_set_role="lag1",
        )
        experiment = run_panel_linear_experiment_from_panel(
            spec,
            panel,
            feature_columns=None,
            random_state=42,
        )
        historical_baselines = {
            "robust_share_lag1": pd.DataFrame(
                [
                    {
                        "model": experiment["best_model"],
                        "mae": 0.9,
                        "rmse": 1.2,
                        "uses_test_labels": False,
                    },
                    {
                        "model": "country_last_pretest_holdconstant",
                        "mae": 0.0,
                        "rmse": 0.0,
                        "uses_test_labels": False,
                    },
                ]
            )
        }

        summary = build_robustness_summary_table([experiment], historical_baselines)

        self.assertEqual(len(summary), 1)
        row = summary.iloc[0]
        self.assertEqual(row["robustness_id"], "robust_share_lag1")
        self.assertEqual(row["target_column"], "target")
        self.assertEqual(row["lag_suffix"], "lag1")
        self.assertEqual(row["comparison_role"], "lag1")
        self.assertIn("best_model", summary.columns)
        self.assertIn("validation_mae", summary.columns)
        self.assertIn("test_mae", summary.columns)
        self.assertIn("best_historical_baseline_model", summary.columns)
        self.assertEqual(row["best_historical_baseline_model"], "country_last_pretest_holdconstant")
        self.assertGreater(row["delta_test_mae_selected_minus_best_history"], 0)
        self.assertFalse(bool(row["beats_best_historical_baseline"]))


def _toy_panel(years, countries) -> pd.DataFrame:
    rows = []
    for year in years:
        for country_index, country_code in enumerate(countries):
            base = year - 1999 + country_index
            rows.append(
                {
                    "country_code": country_code,
                    "country_name": f"Country {country_code}",
                    "year": year,
                    "target": 0.4 * base + 0.2 * country_index,
                    "x_lag1_3_mean": float(base),
                    "z_lag1_3_mean": np.nan if year == 2002 and country_code == "BBB" else float(base % 5),
                }
            )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    unittest.main()
