import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "2_data" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from model_panel_visualizations import make_model_panel_figures  # noqa: E402


class ModelPanelVisualizationTests(unittest.TestCase):
    def test_make_model_panel_figures_writes_expected_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel_dir = root / "model_panels"
            figures_dir = root / "figures"
            panel_dir.mkdir()

            coverage_rows = []
            for panel_id in ["main", "suba", "subb", "subc"]:
                for imputation, prediction_safe, rows in [
                    ("no_imputation", True, 10),
                    ("linear_interpolated", False, 12),
                ]:
                    coverage_rows.append(
                        {
                            "panel_id": panel_id,
                            "imputation": imputation,
                            "prediction_safe": prediction_safe,
                            "anchor_year_grid_rows": rows + 2,
                            "rows": rows,
                            "target_non_missing": rows - 1,
                            "target_lag1_complete_rows": rows - 2,
                            "target_lag1_3_mean_complete_rows": rows - 3,
                        }
                    )
            pd.DataFrame(coverage_rows).to_csv(panel_dir / "model_panel_coverage_summary.csv", index=False)

            pd.DataFrame(
                [
                    {
                        "panel_id": "main",
                        "imputation": "linear_interpolated",
                        "variable": "tertiary_enrollment",
                        "imputed_values": 5,
                    },
                    {
                        "panel_id": "subb",
                        "imputation": "linear_interpolated",
                        "variable": "researchers_per_million",
                        "imputed_values": 3,
                    },
                ]
            ).to_csv(panel_dir / "model_panel_imputation_summary.csv", index=False)

            pd.DataFrame(
                {
                    "country_code": ["USA", "USA", "CAN", "CAN"],
                    "country_name": ["United States", "United States", "Canada", "Canada"],
                    "year": [2000, 2001, 2000, 2001],
                    "env_patent_share_inventions": [1.0, 1.1, 2.0, None],
                    "env_technology_rta_lag1": [0.8, 1.2, 1.5, 2.0],
                    "env_technology_rta_lag1_3_mean": [0.9, 1.1, None, 1.8],
                    "gdp_constant_2015_usd_lag1": [100.0, 101.0, 80.0, 81.0],
                    "gdp_constant_2015_usd_lag1_3_mean": [99.0, 100.0, 79.0, None],
                }
            ).to_csv(panel_dir / "model_panel_main_no_imputation.csv", index=False)
            for panel_id, variable in [
                ("suba", "rise_energy_efficiency"),
                ("subb", "rd_expenditure_gdp"),
                ("subc", "eps_index"),
            ]:
                pd.DataFrame(
                    {
                        "country_code": ["USA", "USA", "CAN", "CAN"],
                        "country_name": ["United States", "United States", "Canada", "Canada"],
                        "year": [2000, 2001, 2000, 2001],
                        "env_patent_share_inventions": [1.0, 1.1, 2.0, 2.1],
                        f"{variable}_lag1": [1.0, 1.2, None, 1.5],
                        f"{variable}_lag1_3_mean": [0.9, 1.1, None, None],
                    }
                ).to_csv(panel_dir / f"model_panel_{panel_id}_no_imputation.csv", index=False)

            figure_paths = make_model_panel_figures(panel_dir=panel_dir, figures_dir=figures_dir)

            self.assertEqual(
                set(figure_paths),
                {
                    "sample_funnel",
                    "prediction_safe_comparison",
                    "feature_availability_heatmap",
                    "missingness_burden",
                },
            )
            for png_path in figure_paths.values():
                path = Path(png_path)
                self.assertTrue(path.exists())
                self.assertTrue(path.with_suffix(".pdf").exists())


if __name__ == "__main__":
    unittest.main()
