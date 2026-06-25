import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "2_data" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from raw_coverage_diagnostics import (  # noqa: E402
    FIGURES_DIR,
    build_coverage_panel,
    build_country_coverage_summary,
    build_reliability_audit,
    build_variable_country_rank,
    filter_rise_indicators,
    make_country_coverage_rank_figure,
    make_variable_country_rank_figure,
    run_coverage_diagnostics,
    summarize_coverage,
)


class RawCoverageDiagnosticsTests(unittest.TestCase):
    def test_default_figure_directory_is_predictors_v1_subfolder(self):
        self.assertEqual(FIGURES_DIR.name, "predictorsv1")
        self.assertEqual(FIGURES_DIR.parent.name, "figures")

    def test_world_bank_and_oecd_csvs_are_standardized_to_country_year_panel(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp)
            wb_path = raw_dir / "wb.csv"
            pd.DataFrame(
                {
                    "dataset_id": ["world_bank_wdi", "world_bank_wdi"],
                    "variable": ["rd_expenditure_gdp", "rd_expenditure_gdp"],
                    "source_variable": ["GB.XPD.RSDV.GD.ZS", "GB.XPD.RSDV.GD.ZS"],
                    "country_code": ["USA", "USA"],
                    "country_name": ["United States", "United States"],
                    "year": [2020, 2021],
                    "value": [2.8, None],
                }
            ).to_csv(wb_path, index=False)

            oecd_path = raw_dir / "oecd.csv"
            pd.DataFrame(
                {
                    "REF_AREA": ["USA", "USA"],
                    "Reference area": ["United States", "United States"],
                    "TIME_PERIOD": [2020, 2021],
                    "OBS_VALUE": [1.2, None],
                }
            ).to_csv(oecd_path, index=False)

            manifest = pd.DataFrame(
                [
                    {
                        "dataset_id": "world_bank_wdi",
                        "variable": "rd_expenditure_gdp",
                        "source_variable": "GB.XPD.RSDV.GD.ZS",
                        "status": "downloaded",
                        "file_format": "csv",
                        "file_path": str(wb_path),
                    },
                    {
                        "dataset_id": "oecd_eps",
                        "variable": "eps_index",
                        "source_variable": "POL_STRINGENCY.EPS",
                        "status": "downloaded",
                        "file_format": "csv",
                        "file_path": str(oecd_path),
                    },
                ]
            )

            panel = build_coverage_panel(manifest)
            summary = summarize_coverage(panel)

        self.assertEqual(set(panel["variable"]), {"rd_expenditure_gdp", "eps_index"})
        self.assertEqual(int(summary["non_missing_observations"].sum()), 2)
        self.assertEqual(int(summary["years_total"].max()), 2)

    def test_reliability_audit_flags_existing_nonempty_files_and_matching_shapes(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw_path = Path(tmp) / "source.csv"
            pd.DataFrame(
                {
                    "country_code": ["USA", "CAN"],
                    "country_name": ["United States", "Canada"],
                    "year": [2020, 2020],
                    "value": [1.0, 2.0],
                }
            ).to_csv(raw_path, index=False)
            manifest = pd.DataFrame(
                [
                    {
                        "dataset_id": "world_bank_wdi",
                        "variable": "toy",
                        "source_variable": "TOY",
                        "status": "downloaded",
                        "rows": 2,
                        "columns": 4,
                        "file_format": "csv",
                        "file_path": str(raw_path),
                    }
                ]
            )

            audit = build_reliability_audit(manifest)

        row = audit.iloc[0]
        self.assertTrue(bool(row["file_exists"]))
        self.assertTrue(bool(row["shape_matches_manifest"]))
        self.assertEqual(row["reliability_status"], "confirmed")

    def test_epu_xlsx_audit_and_coverage_do_not_require_openpyxl(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw_path = Path(tmp) / "epu.xlsx"
            pd.DataFrame(
                {
                    "Year": [2020, 2020, 2021],
                    "Month": [1, 2, 1],
                    "US": [100.0, 110.0, 120.0],
                    "Canada": [80.0, None, 90.0],
                    "GEPU_current": [1.0, 2.0, 3.0],
                }
            ).to_excel(raw_path, sheet_name="EPU", index=False)
            manifest = pd.DataFrame(
                [
                    {
                        "dataset_id": "policy_uncertainty",
                        "variable": "economic_policy_uncertainty",
                        "source_variable": "All_Country_Data",
                        "source": "Economic Policy Uncertainty Index",
                        "source_url": "https://www.policyuncertainty.com/media/All_Country_Data.xlsx",
                        "status": "downloaded",
                        "rows": 3,
                        "columns": 5,
                        "file_format": "xlsx",
                        "file_path": str(raw_path),
                        "start_year": 2020,
                        "end_year": 2021,
                    }
                ]
            )

            with (
                patch("raw_coverage_diagnostics.pd.ExcelFile", side_effect=ImportError("missing openpyxl")),
                patch("raw_coverage_diagnostics.pd.read_excel", side_effect=ImportError("missing openpyxl")),
            ):
                audit = build_reliability_audit(manifest)
                panel = build_coverage_panel(manifest)
                summary = summarize_coverage(panel)

        audit_row = audit.iloc[0]
        self.assertEqual(audit_row["reliability_status"], "confirmed")
        self.assertEqual(audit_row["actual_rows"], 3)
        self.assertEqual(audit_row["actual_columns"], 5)
        self.assertTrue(bool(audit_row["expected_columns_present"]))
        self.assertEqual(set(panel["country_name"]), {"US", "Canada"})
        self.assertNotIn("GEPU_current", set(panel["country_name"]))
        self.assertEqual(int(summary.iloc[0]["entities_with_data"]), 2)

    def test_filter_rise_indicators_keeps_only_requested_prefix(self):
        data = pd.DataFrame(
            {
                "INDICATOR": ["WB_RISE_RE_ALL", "WB_RISE_RE_GOV", "WB_RISE_EE_ALL"],
                "OBS_VALUE": [1.0, 2.0, 3.0],
            }
        )

        filtered = filter_rise_indicators(data, "WB_RISE_RE_")

        self.assertEqual(list(filtered["INDICATOR"]), ["WB_RISE_RE_ALL", "WB_RISE_RE_GOV"])

    def test_country_coverage_summary_ranks_iso_countries_descending(self):
        panel = pd.DataFrame(
            {
                "country_code": ["USA", "USA", "USA", "CAN", "CAN", "CAN", "", "G20", "ODA"],
                "country_name": [
                    "United States",
                    "United States",
                    "United States",
                    "Canada",
                    "Canada",
                    "Canada",
                    "US",
                    "G20",
                    "ODA recipient countries",
                ],
                "variable": ["gdp", "gdp", "rise", "gdp", "gdp", "rise", "epu", "gdp", "gdp"],
                "year": [2020, 2021, 2020, 2020, 2021, 2020, 2020, 2020, 2020],
                "has_value": [True, True, True, True, False, False, True, True, True],
            }
        )

        summary = build_country_coverage_summary(panel)

        self.assertEqual(list(summary["country_code"]), ["USA", "CAN"])
        self.assertEqual(float(summary.loc[summary["country_code"].eq("USA"), "coverage_share"].iloc[0]), 1.0)
        self.assertEqual(int(summary.loc[summary["country_code"].eq("CAN"), "non_missing_variable_years"].iloc[0]), 1)
        self.assertNotIn("", set(summary["country_code"]))
        self.assertNotIn("G20", set(summary["country_code"]))
        self.assertNotIn("ODA", set(summary["country_code"]))

    def test_variable_country_rank_sorts_variables_by_country_coverage_descending(self):
        summary = pd.DataFrame(
            {
                "variable": ["low_coverage", "high_coverage", "middle_coverage"],
                "variable_group": ["Energy system", "Environmental policy", "R&D and knowledge capacity"],
                "entities_with_data": [20, 120, 70],
                "entities_total": [140, 140, 140],
                "years_with_data": [10, 14, 12],
                "first_year": [2000, 2010, 1995],
                "last_year": [2009, 2023, 2006],
            }
        )

        rank = build_variable_country_rank(summary)

        self.assertEqual(list(rank["variable"]), ["high_coverage", "middle_coverage", "low_coverage"])
        self.assertEqual(list(rank["entities_with_data"]), [120, 70, 20])
        self.assertEqual(list(rank["coverage_year_label"]), ["2010-2023", "1995-2006", "2000-2009"])

    def test_variable_country_rank_figure_uses_single_panel_dual_axis_layout(self):
        rank = pd.DataFrame(
            {
                "variable": ["high_coverage", "low_coverage"],
                "variable_group": ["Environmental policy", "Energy system"],
                "entities_with_data": [120, 20],
                "years_with_data": [14, 10],
                "first_year": [2010, 2000],
                "last_year": [2023, 2009],
                "coverage_year_label": ["2010-2023", "2000-2009"],
            }
        )
        palette = {"Environmental policy": "#8E63A9", "Energy system": "#D79A3B"}

        fig, axes = make_variable_country_rank_figure(rank, palette)

        self.assertEqual(len(axes), 2)
        self.assertEqual(axes[0].get_position().bounds, axes[1].get_position().bounds)
        self.assertEqual(axes[0].get_xlabel(), "Countries/entities with non-missing data")
        self.assertEqual(axes[1].get_xlabel(), "Coverage years")
        self.assertAlmostEqual(fig._suptitle.get_position()[0], 0.5)
        self.assertEqual(fig._suptitle.get_ha(), "center")
        fig.clear()

    def test_country_coverage_rank_figure_title_is_centered(self):
        country_summary = pd.DataFrame(
            {
                "country_code": ["USA", "CAN"],
                "country_name": ["United States", "Canada"],
                "coverage_share": [1.0, 0.5],
                "non_missing_variable_years": [10, 5],
            }
        )

        fig, _ = make_country_coverage_rank_figure(country_summary)

        self.assertAlmostEqual(fig._suptitle.get_position()[0], 0.5)
        self.assertEqual(fig._suptitle.get_ha(), "center")
        fig.clear()

    def test_run_coverage_diagnostics_writes_one_combined_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            raw_dir = base / "raw"
            processed_dir = base / "processed"
            figures_dir = base / "figures"
            raw_dir.mkdir()

            data_path = raw_dir / "wb.csv"
            pd.DataFrame(
                {
                    "dataset_id": ["world_bank_wdi", "world_bank_wdi"],
                    "variable": ["rd_expenditure_gdp", "rd_expenditure_gdp"],
                    "source_variable": ["GB.XPD.RSDV.GD.ZS", "GB.XPD.RSDV.GD.ZS"],
                    "country_code": ["USA", "CAN"],
                    "country_name": ["United States", "Canada"],
                    "year": [2020, 2020],
                    "value": [2.8, None],
                }
            ).to_csv(data_path, index=False)
            pd.DataFrame(
                [
                    {
                        "dataset_id": "world_bank_wdi",
                        "variable": "rd_expenditure_gdp",
                        "source_variable": "GB.XPD.RSDV.GD.ZS",
                        "source": "World Bank WDI",
                        "source_url": "https://api.worldbank.org/example",
                        "status": "downloaded",
                        "rows": 2,
                        "columns": 7,
                        "file_format": "csv",
                        "file_path": str(data_path),
                        "start_year": 2020,
                        "end_year": 2020,
                    }
                ]
            ).to_csv(raw_dir / "raw_download_manifest.csv", index=False)
            for stale_name in [
                "raw_reliability_audit.csv",
                "raw_coverage_summary.csv",
                "raw_coverage_by_year.csv",
                "raw_coverage_panel.csv",
            ]:
                processed_dir.mkdir(exist_ok=True)
                (processed_dir / stale_name).write_text("stale\n")
            figures_dir.mkdir()
            for stale_figure in [
                "raw_coverage_heatmap.png",
                "raw_coverage_heatmap.pdf",
                "raw_coverage_summary.png",
                "raw_coverage_summary.pdf",
            ]:
                (figures_dir / stale_figure).write_text("stale\n")

            outputs = run_coverage_diagnostics(
                raw_dir=raw_dir,
                processed_dir=processed_dir,
                figures_dir=figures_dir,
            )

            audit_path = processed_dir / "raw_predictor_audit.csv"
            self.assertTrue(audit_path.exists())
            self.assertFalse((processed_dir / "raw_reliability_audit.csv").exists())
            self.assertFalse((processed_dir / "raw_coverage_summary.csv").exists())
            self.assertFalse((processed_dir / "raw_coverage_by_year.csv").exists())
            self.assertFalse((processed_dir / "raw_coverage_panel.csv").exists())

            saved = pd.read_csv(audit_path)
            self.assertIn("reliability_status", saved.columns)
            self.assertIn("entities_with_data", saved.columns)
            self.assertEqual(int(saved.loc[0, "non_missing_observations"]), 1)
            self.assertEqual(outputs["predictor_audit_path"], str(audit_path))
            self.assertIn("country_coverage_summary", outputs)
            self.assertIn("country_coverage_rank_png", outputs["figure_paths"])
            self.assertIn("variable_country_rank", outputs)
            self.assertIn("variable_country_rank_png", outputs["figure_paths"])
            self.assertNotIn("coverage_heatmap_png", outputs["figure_paths"])
            self.assertNotIn("coverage_summary_png", outputs["figure_paths"])
            self.assertFalse((figures_dir / "raw_coverage_heatmap.png").exists())
            self.assertFalse((figures_dir / "raw_coverage_summary.png").exists())


if __name__ == "__main__":
    unittest.main()
