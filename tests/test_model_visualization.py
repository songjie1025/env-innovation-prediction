import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "3_models" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from model_visualization import (  # noqa: E402
    make_correlation_diagnostic_figures,
    make_linear_model_figures,
    make_missingness_pattern_figures,
    make_model_comparison_figures,
    make_nested_comparison_figures,
    make_review_diagnostic_figures,
    make_robustness_figures,
)


class ModelVisualizationTests(unittest.TestCase):
    def test_make_linear_model_figures_writes_expected_png_and_pdf_files(self):
        panel = pd.DataFrame(
            {
                "country_code": ["AAA", "BBB", "AAA", "BBB", "AAA", "BBB"],
                "country_name": ["Alpha", "Beta", "Alpha", "Beta", "Alpha", "Beta"],
                "year": [2000, 2000, 2001, 2001, 2002, 2002],
                "target": [0.1, 1.5, 0.2, 1.7, 0.3, 2.0],
                "x_lag1_3_mean": [1.0, 2.0, 1.1, None, 1.2, 2.2],
                "z_lag1_3_mean": [3.0, 1.0, None, 1.1, 3.2, 1.2],
            }
        )
        sample_summary = pd.DataFrame(
            [
                {"split": "train", "year_start": 2000, "year_end": 2000, "rows": 2},
                {"split": "validation", "year_start": 2001, "year_end": 2001, "rows": 2},
                {"split": "test", "year_start": 2002, "year_end": 2002, "rows": 2},
            ]
        )
        validation_metrics = pd.DataFrame(
            [
                {"model": "linear_regression", "mae": 0.5, "rmse": 0.8},
                {"model": "ridge_alpha_1", "mae": 0.3, "rmse": 0.6},
            ]
        )
        predictions = pd.DataFrame(
            {
                "country_code": ["AAA", "BBB"],
                "country_name": ["Alpha", "Beta"],
                "year": [2002, 2002],
                "target": [0.3, 2.0],
                "prediction": [0.4, 1.8],
                "error": [-0.1, 0.2],
                "absolute_error": [0.1, 0.2],
            }
        )
        coefficients = pd.DataFrame(
            {
                "feature": ["x_lag1_3_mean", "z_lag1_3_mean"],
                "coefficient": [0.4, -0.2],
                "abs_coefficient": [0.4, 0.2],
            }
        )

        with tempfile.TemporaryDirectory() as tmp:
            figure_paths = make_linear_model_figures(
                panel=panel,
                feature_columns=["x_lag1_3_mean", "z_lag1_3_mean"],
                target_column="target",
                sample_summary=sample_summary,
                validation_metrics=validation_metrics,
                predictions=predictions,
                coefficients=coefficients,
                figures_dir=Path(tmp),
            )

            self.assertEqual(
                set(figure_paths),
                {
                    "split_rows",
                    "target_distribution",
                    "feature_missingness",
                    "validation_mae",
                    "actual_vs_predicted",
                    "error_by_year",
                    "coefficients",
                },
            )
            for png_path in figure_paths.values():
                path = Path(png_path)
                self.assertTrue(path.exists())
                self.assertTrue(path.with_suffix(".pdf").exists())

    def test_make_model_comparison_figures_writes_expected_png_and_pdf_files(self):
        sample_summary = pd.DataFrame(
            [
                {"panel_id": "main", "panel_label": "Main model", "split": "all", "rows": 100, "countries": 20},
                {"panel_id": "suba", "panel_label": "RISE submodel", "split": "all", "rows": 60, "countries": 12},
            ]
        )
        test_metrics = pd.DataFrame(
            [
                {"panel_id": "main", "panel_label": "Main model", "mae": 1.0, "rmse": 2.0, "oos_r2_vs_train_mean": 0.4},
                {"panel_id": "suba", "panel_label": "RISE submodel", "mae": 1.7, "rmse": 3.0, "oos_r2_vs_train_mean": 0.1},
            ]
        )
        validation_metrics = pd.DataFrame(
            [
                {"panel_id": "main", "panel_label": "Main model", "model": "elastic_net_alpha_1_l1_0.2", "mae": 1.0},
                {"panel_id": "suba", "panel_label": "RISE submodel", "model": "elastic_net_alpha_1_l1_0.8", "mae": 1.5},
            ]
        )
        coefficients = pd.DataFrame(
            [
                {"panel_id": "main", "panel_label": "Main model", "feature": "gdp_lag1_3_mean", "coefficient": 0.6, "abs_coefficient": 0.6},
                {"panel_id": "suba", "panel_label": "RISE submodel", "feature": "rise_lag1_3_mean", "coefficient": 0.2, "abs_coefficient": 0.2},
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            figure_paths = make_model_comparison_figures(
                sample_summary=sample_summary,
                test_metrics=test_metrics,
                validation_metrics=validation_metrics,
                coefficients=coefficients,
                figures_dir=Path(tmp),
            )

            self.assertEqual(
                set(figure_paths),
                {
                    "panel_sample_comparison",
                    "test_metric_comparison",
                    "submodel_coefficients",
                    "panel_validation_mae",
                },
            )
            for png_path in figure_paths.values():
                path = Path(png_path)
                self.assertTrue(path.exists())
                self.assertTrue(path.with_suffix(".pdf").exists())

    def test_make_correlation_diagnostic_figures_writes_expected_png_and_pdf_files(self):
        spearman_feature_correlations = pd.DataFrame(
            [[1.0, 0.8], [0.8, 1.0]],
            index=["gdp_lag1_3_mean", "science_lag1_3_mean"],
            columns=["gdp_lag1_3_mean", "science_lag1_3_mean"],
        )
        target_correlations = pd.DataFrame(
            [
                {"feature": "gdp_lag1_3_mean", "correlation": 0.7, "abs_correlation": 0.7},
                {"feature": "science_lag1_3_mean", "correlation": 0.6, "abs_correlation": 0.6},
            ]
        )
        coefficient_alignment = pd.DataFrame(
            [
                {"feature": "gdp_lag1_3_mean", "coefficient": 0.5, "target_correlation": 0.7},
                {"feature": "science_lag1_3_mean", "coefficient": 0.3, "target_correlation": 0.6},
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            figure_paths = make_correlation_diagnostic_figures(
                spearman_feature_correlations=spearman_feature_correlations,
                target_correlations=target_correlations,
                coefficient_alignment=coefficient_alignment,
                figures_dir=Path(tmp),
            )

            self.assertEqual(
                set(figure_paths),
                {
                    "main_feature_correlation_heatmap",
                    "main_target_correlations",
                    "main_coefficient_correlation_alignment",
                },
            )
            for png_path in figure_paths.values():
                path = Path(png_path)
                self.assertTrue(path.exists())
                self.assertTrue(path.with_suffix(".pdf").exists())

    def test_make_nested_comparison_figures_writes_expected_png_and_pdf_files(self):
        nested_comparison = pd.DataFrame(
            [
                {
                    "comparison_group": "suba",
                    "baseline_label": "Main controls on SubA sample",
                    "augmented_label": "Main + SubA predictors",
                    "baseline_test_mae": 1.6,
                    "augmented_test_mae": 1.4,
                    "delta_test_mae_augmented_minus_baseline": -0.2,
                    "comparison_scope": "same_sample_nested",
                },
                {
                    "comparison_group": "subb",
                    "baseline_label": "Main controls on SubB sample",
                    "augmented_label": "Main + SubB predictors",
                    "baseline_test_mae": 1.8,
                    "augmented_test_mae": 1.9,
                    "delta_test_mae_augmented_minus_baseline": 0.1,
                    "comparison_scope": "same_sample_nested",
                },
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            figure_paths = make_nested_comparison_figures(
                nested_comparison=nested_comparison,
                figures_dir=Path(tmp),
            )

            self.assertEqual(
                set(figure_paths),
                {
                    "nested_test_mae_comparison",
                    "nested_test_mae_delta",
                },
            )
            for png_path in figure_paths.values():
                path = Path(png_path)
                self.assertTrue(path.exists())
                self.assertTrue(path.with_suffix(".pdf").exists())

    def test_make_review_diagnostic_figures_writes_expected_png_and_pdf_files(self):
        historical_baselines = pd.DataFrame(
            [
                {"model": "elastic_net", "mae": 1.0, "uses_test_labels": False},
                {"model": "country_last_pretest_holdconstant", "mae": 0.4, "uses_test_labels": False},
            ]
        )
        top_errors = pd.DataFrame(
            [
                {
                    "rank": 1,
                    "country_code": "CHN",
                    "country_name": "China",
                    "year": 2023,
                    "observed": 38.0,
                    "prediction": 22.0,
                    "absolute_error": 16.0,
                },
                {
                    "rank": 2,
                    "country_code": "KOR",
                    "country_name": "Korea, Rep.",
                    "year": 2023,
                    "observed": 17.0,
                    "prediction": 3.0,
                    "absolute_error": 14.0,
                },
            ]
        )
        missingness_sensitivity = pd.DataFrame(
            [
                {"analysis": "primary_median_imputed_all_rows", "test_mae": 1.0, "test_rows": 100},
                {"analysis": "complete_case_refit", "test_mae": 1.2, "test_rows": 50},
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            figure_paths = make_review_diagnostic_figures(
                historical_baselines=historical_baselines,
                top_errors=top_errors,
                missingness_sensitivity=missingness_sensitivity,
                figures_dir=Path(tmp),
            )

            self.assertEqual(
                set(figure_paths),
                {
                    "historical_baseline_mae",
                    "top_absolute_errors",
                    "missingness_sensitivity_mae",
                },
            )
            for png_path in figure_paths.values():
                path = Path(png_path)
                self.assertTrue(path.exists())
                self.assertTrue(path.with_suffix(".pdf").exists())

    def test_make_robustness_figures_writes_expected_png_and_pdf_files(self):
        robustness_summary = pd.DataFrame(
            [
                {
                    "robustness_id": "share_lag1_3_mean",
                    "robustness_label": "Share target, lag1-3 mean",
                    "target_column": "env_patent_share_inventions",
                    "lag_suffix": "lag1_3_mean",
                    "validation_mae": 0.8,
                    "test_mae": 1.0,
                    "best_historical_baseline_mae": 0.4,
                    "delta_test_mae_selected_minus_best_history": 0.6,
                    "beats_best_historical_baseline": False,
                },
                {
                    "robustness_id": "per_million_lag1",
                    "robustness_label": "Per-million target, lag1",
                    "target_column": "env_patents_per_million",
                    "lag_suffix": "lag1",
                    "validation_mae": 0.5,
                    "test_mae": 0.7,
                    "best_historical_baseline_mae": 0.9,
                    "delta_test_mae_selected_minus_best_history": -0.2,
                    "beats_best_historical_baseline": True,
                },
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            figure_paths = make_robustness_figures(
                robustness_summary=robustness_summary,
                figures_dir=Path(tmp),
            )

            self.assertEqual(
                set(figure_paths),
                {
                    "robustness_validation_test_mae",
                    "robustness_history_delta",
                },
            )
            for png_path in figure_paths.values():
                path = Path(png_path)
                self.assertTrue(path.exists())
                self.assertTrue(path.with_suffix(".pdf").exists())

    def test_make_missingness_pattern_figures_writes_expected_png_and_pdf_files(self):
        missingness_pattern_summary = pd.DataFrame(
            [
                {
                    "feature": "gdp_lag1_3_mean",
                    "complete_countries": 8,
                    "late_start_countries": 1,
                    "early_end_countries": 0,
                    "bounded_coverage_window_countries": 0,
                    "intermittent_gaps_countries": 0,
                    "all_missing_countries": 0,
                },
                {
                    "feature": "policy_lag1_3_mean",
                    "complete_countries": 2,
                    "late_start_countries": 4,
                    "early_end_countries": 1,
                    "bounded_coverage_window_countries": 1,
                    "intermittent_gaps_countries": 3,
                    "all_missing_countries": 2,
                },
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            figure_paths = make_missingness_pattern_figures(
                missingness_pattern_summary=missingness_pattern_summary,
                figures_dir=Path(tmp),
            )

            self.assertEqual(set(figure_paths), {"missingness_pattern_counts"})
            for png_path in figure_paths.values():
                path = Path(png_path)
                self.assertTrue(path.exists())
                self.assertTrue(path.with_suffix(".pdf").exists())

    def test_make_missingness_pattern_figures_rejects_missing_pattern_columns(self):
        missingness_pattern_summary = pd.DataFrame(
            [
                {
                    "feature": "gdp_lag1_3_mean",
                    "complete_countries": 8,
                }
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "missing pattern columns"):
                make_missingness_pattern_figures(
                    missingness_pattern_summary=missingness_pattern_summary,
                    figures_dir=Path(tmp),
                )


if __name__ == "__main__":
    unittest.main()
