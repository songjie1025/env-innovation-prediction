import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.pipeline import Pipeline


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "3_models" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from model_estimators import build_linear_model_candidates  # noqa: E402
from model_evaluation import (  # noqa: E402
    build_error_decomposition_tables,
    build_historical_baseline_delta_summary,
    build_historical_baseline_comparison,
    build_top_prediction_errors,
    compute_regression_metrics,
    evaluate_selected_model,
    select_best_validation_model,
    write_markdown_summary,
)


class ModelEvaluationTests(unittest.TestCase):
    def test_linear_model_candidates_handle_missing_predictors_inside_pipeline(self):
        candidates = build_linear_model_candidates(random_state=42)
        x_train = pd.DataFrame(
            {
                "x1_lag1_3_mean": [1.0, 2.0, np.nan, 4.0, 5.0],
                "x2_lag1_3_mean": [5.0, np.nan, 3.0, 2.0, 1.0],
            }
        )
        y_train = pd.Series([1.0, 2.0, 2.5, 4.0, 5.0])

        self.assertIn("ridge_alpha_1", candidates)
        self.assertIn("lasso_alpha_0.1", candidates)
        self.assertIn("elastic_net_alpha_1_l1_0.2", candidates)
        for estimator in candidates.values():
            self.assertIsInstance(estimator, Pipeline)
            self.assertIn("imputer", estimator.named_steps)
            self.assertIn("scaler", estimator.named_steps)
            self.assertTrue(estimator.named_steps["imputer"].keep_empty_features)
            estimator.fit(x_train, y_train)
            predictions = estimator.predict(x_train)
            self.assertFalse(np.isnan(predictions).any())

    def test_compute_regression_metrics_reports_mae_rmse_and_oos_r2(self):
        metrics = compute_regression_metrics(
            y_true=pd.Series([1.0, 3.0, 5.0]),
            y_pred=np.array([1.5, 2.5, 6.0]),
            train_mean=2.0,
        )

        self.assertAlmostEqual(metrics["mae"], (0.5 + 0.5 + 1.0) / 3)
        self.assertAlmostEqual(metrics["rmse"], np.sqrt((0.25 + 0.25 + 1.0) / 3))
        expected_oos_r2 = 1 - 1.5 / ((1.0 - 2.0) ** 2 + (3.0 - 2.0) ** 2 + (5.0 - 2.0) ** 2)
        self.assertAlmostEqual(metrics["oos_r2_vs_train_mean"], expected_oos_r2)

    def test_select_best_validation_model_prefers_lowest_validation_mae(self):
        validation_metrics = pd.DataFrame(
            [
                {"model": "linear_regression", "split": "validation", "mae": 3.0},
                {"model": "ridge_alpha_1", "split": "validation", "mae": 1.5},
                {"model": "elastic_net_alpha_0.01_l1_0.5", "split": "validation", "mae": 2.0},
            ]
        )

        self.assertEqual(select_best_validation_model(validation_metrics), "ridge_alpha_1")

    def test_evaluate_selected_model_uses_training_mean_for_oos_r2_baseline(self):
        estimator = DummyRegressor(strategy="constant", constant=0.0)
        x_train_validation = pd.DataFrame({"x": [0.0, 1.0]})
        y_train_validation = pd.Series([100.0, 100.0])
        x_test = pd.DataFrame({"x": [2.0]})
        y_test = pd.Series([10.0])

        metrics, _, _ = evaluate_selected_model(
            estimator,
            "dummy",
            x_train_validation,
            y_train_validation,
            x_test,
            y_test,
            score_baseline_mean=0.0,
        )

        self.assertAlmostEqual(metrics.iloc[0]["oos_r2_vs_train_mean"], 0.0)

    def test_markdown_summary_does_not_require_pandas_to_markdown_optional_dependency(self):
        validation_metrics = pd.DataFrame(
            [{"model": "dummy", "split": "validation", "mae": 1.0, "rmse": 2.0}]
        )
        test_metrics = pd.DataFrame(
            [{"model": "dummy", "split": "test", "mae": 1.5, "rmse": 2.5}]
        )

        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "summary.md"
            with patch.object(pd.DataFrame, "to_markdown", side_effect=ImportError("tabulate missing")):
                write_markdown_summary(
                    output_path,
                    best_model="dummy",
                    split_years={
                        "train": [2000, 2001],
                        "validation": [2002],
                        "test": [2003],
                    },
                    validation_metrics=validation_metrics,
                    test_metrics=test_metrics,
                )

            text = output_path.read_text(encoding="utf-8")

        self.assertIn("Best validation model: `dummy`", text)
        self.assertIn("| model | split |", text)

    def test_historical_baseline_comparison_includes_country_persistence(self):
        train = pd.DataFrame(
            {
                "country_code": ["AAA", "BBB"],
                "country_name": ["Alpha", "Beta"],
                "year": [2000, 2000],
                "target": [1.0, 5.0],
            }
        )
        validation = pd.DataFrame(
            {
                "country_code": ["AAA", "BBB"],
                "country_name": ["Alpha", "Beta"],
                "year": [2001, 2001],
                "target": [2.0, 6.0],
            }
        )
        test = pd.DataFrame(
            {
                "country_code": ["AAA", "BBB"],
                "country_name": ["Alpha", "Beta"],
                "year": [2002, 2002],
                "target": [2.2, 5.7],
            }
        )
        model_predictions = test.copy()
        model_predictions["prediction"] = [1.8, 6.5]
        split = type("Split", (), {"train": train, "validation": validation, "test": test})()

        comparison = build_historical_baseline_comparison(
            split=split,
            target_column="target",
            model_predictions=model_predictions,
            model_name="elastic_net_alpha_1_l1_0.2",
        )

        self.assertEqual(
            set(comparison["model"]),
            {
                "elastic_net_alpha_1_l1_0.2",
                "global_train_validation_mean",
                "country_train_validation_mean",
                "country_last_pretest_holdconstant",
            },
        )
        persistence = comparison[comparison["model"].eq("country_last_pretest_holdconstant")].iloc[0]
        self.assertFalse(bool(persistence["uses_test_labels"]))
        self.assertAlmostEqual(persistence["mae"], 0.25)

    def test_historical_baseline_delta_summary_centers_persistence_delta(self):
        historical_baselines = pd.DataFrame(
            [
                {
                    "model": "elastic_net_alpha_1_l1_0.2",
                    "prediction_rule": "selected_model",
                    "uses_test_labels": False,
                    "mae": 1.0,
                    "rmse": 2.0,
                    "oos_r2_vs_train_mean": 0.5,
                    "spearman": 0.7,
                },
                {
                    "model": "country_last_pretest_holdconstant",
                    "prediction_rule": "country latest observed train+validation target held constant",
                    "uses_test_labels": False,
                    "mae": 0.4,
                    "rmse": 1.5,
                    "oos_r2_vs_train_mean": 0.8,
                    "spearman": 0.9,
                },
                {
                    "model": "leaky_oracle",
                    "prediction_rule": "uses test labels",
                    "uses_test_labels": True,
                    "mae": 0.0,
                    "rmse": 0.0,
                    "oos_r2_vs_train_mean": 1.0,
                    "spearman": 1.0,
                },
            ]
        )

        delta_summary = build_historical_baseline_delta_summary(historical_baselines)

        self.assertEqual(len(delta_summary), 1)
        row = delta_summary.iloc[0]
        self.assertEqual(row["selected_model"], "elastic_net_alpha_1_l1_0.2")
        self.assertEqual(row["baseline_model"], "country_last_pretest_holdconstant")
        self.assertAlmostEqual(row["delta_mae_selected_minus_baseline"], 0.6)
        self.assertFalse(bool(row["selected_beats_baseline"]))
        self.assertIn("feature-only model trails", row["professor_interpretation"])

    def test_error_decomposition_tables_report_year_and_target_quantile_errors(self):
        predictions = pd.DataFrame(
            {
                "country_code": ["AAA", "BBB", "CCC", "DDD"],
                "country_name": ["Alpha", "Beta", "Gamma", "Delta"],
                "year": [2021, 2021, 2022, 2022],
                "target": [1.0, 2.0, 10.0, 20.0],
                "prediction": [1.5, 1.0, 7.0, 16.0],
            }
        )

        tables = build_error_decomposition_tables(predictions, target_column="target", quantiles=2)

        self.assertEqual(set(tables), {"by_year", "by_target_quantile"})
        by_year = tables["by_year"]
        self.assertEqual(list(by_year["year"]), [2021, 2022])
        self.assertAlmostEqual(by_year.loc[by_year["year"].eq(2021), "mae"].iloc[0], 0.75)
        self.assertAlmostEqual(by_year.loc[by_year["year"].eq(2022), "mae"].iloc[0], 3.5)
        by_quantile = tables["by_target_quantile"]
        self.assertEqual(len(by_quantile), 2)
        self.assertIn("target_quantile", by_quantile.columns)
        self.assertIn("target_min", by_quantile.columns)
        self.assertIn("target_max", by_quantile.columns)
        self.assertGreater(
            by_quantile.loc[by_quantile["target_quantile"].eq("Q2"), "mae"].iloc[0],
            by_quantile.loc[by_quantile["target_quantile"].eq("Q1"), "mae"].iloc[0],
        )

    def test_top_prediction_errors_orders_largest_errors_first(self):
        predictions = pd.DataFrame(
            {
                "country_code": ["AAA", "BBB", "CCC"],
                "country_name": ["Alpha", "Beta", "Gamma"],
                "year": [2021, 2021, 2021],
                "target": [1.0, 10.0, 2.0],
                "prediction": [1.2, 6.0, 0.0],
            }
        )

        top_errors = build_top_prediction_errors(
            predictions,
            target_column="target",
            limit=2,
        )

        self.assertEqual(list(top_errors["country_code"]), ["BBB", "CCC"])
        self.assertEqual(list(top_errors["rank"]), [1, 2])
        self.assertAlmostEqual(top_errors.iloc[0]["absolute_error"], 4.0)


if __name__ == "__main__":
    unittest.main()
