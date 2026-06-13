import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "2_data" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from raw_data_download import (  # noqa: E402
    RAW_PREDICTORS_V1_DIR,
    build_literature_predictor_download_plan,
    build_raw_download_plan,
    run_raw_download,
)


class RawDataDownloadTests(unittest.TestCase):
    def test_default_raw_download_directory_is_versioned_subfolder(self):
        self.assertEqual(RAW_PREDICTORS_V1_DIR.name, "predictorsv1")
        self.assertEqual(RAW_PREDICTORS_V1_DIR.parent.name, "raw")

    def test_literature_plan_extracts_downloadable_and_unsupported_predictors(self):
        with tempfile.TemporaryDirectory() as tmp:
            literature_csv = Path(tmp) / "literature.csv"
            pd.DataFrame(
                [
                    {
                        "paper name ": "R&D paper",
                        "predictors used": "R&D expenditure / GDP",
                        "Indicator Data Code": "(WDI) GB.XPD.RSDV.GD.ZS",
                        "comments": "",
                    },
                    {
                        "paper name ": "Policy paper",
                        "predictors used": "RISE_Score",
                        "Indicator Data Code": "https://data360.worldbank.org/en/dataset/WB_RISE",
                        "comments": "",
                    },
                    {
                        "paper name ": "Patent paper",
                        "predictors used": "Lagged Env Tech RTA",
                        "Indicator Data Code": "(OECD) calculate through ENV_TECH",
                        "comments": "",
                    },
                    {
                        "paper name ": "Tax paper",
                        "predictors used": "carbon tax",
                        "Indicator Data Code": (
                            "https://www.oecd.org/en/data/datasets/"
                            "carbon-pricing-and-energy-taxation-database.html"
                        ),
                        "comments": "",
                    },
                ]
            ).to_csv(literature_csv, index=False)

            plan = build_literature_predictor_download_plan(literature_csv, 1990, 2024)

        by_variable = {entry["variable"]: entry for entry in plan}
        self.assertEqual(by_variable["rd_expenditure_gdp"]["dataset_id"], "world_bank_wdi")
        self.assertEqual(by_variable["rd_expenditure_gdp"]["source_variable"], "GB.XPD.RSDV.GD.ZS")
        self.assertEqual(by_variable["rd_expenditure_gdp"]["source_id"], 2)
        self.assertEqual(by_variable["rise_renewable_energy"]["dataset_id"], "world_bank_data360")
        self.assertEqual(by_variable["rise_renewable_energy"]["indicator_prefix"], "WB_RISE_RE_")
        self.assertEqual(by_variable["rise_energy_efficiency"]["dataset_id"], "world_bank_data360")
        self.assertEqual(by_variable["rise_energy_efficiency"]["indicator_prefix"], "WB_RISE_EE_")
        self.assertEqual(
            by_variable["env_technology_rta"]["source_variable"],
            "IX.DEV.ENV_PAT._Z",
        )
        self.assertEqual(by_variable["carbon_tax"]["dataset_id"], "oecd_carbon_pricing")
        self.assertEqual(by_variable["carbon_tax"]["status"], "planned")
        self.assertTrue(by_variable["carbon_tax"]["source_variable"].startswith("OECD.CTP.TPS,"))

    def test_raw_plan_excludes_removed_predictors_and_keeps_regulatory_quality(self):
        plan = build_raw_download_plan(1990, 2024)
        variables = {entry["variable"] for entry in plan}

        self.assertIn("gdp_constant_2015_usd", variables)
        self.assertNotIn("gdp_per_capita_current_usd", variables)
        gdp_entries = [entry for entry in plan if entry["variable"] == "gdp_constant_2015_usd"]
        self.assertEqual(len(gdp_entries), 1)
        self.assertEqual(gdp_entries[0]["source_variable"], "NY.GDP.MKTP.KD")
        self.assertIn("total economic scale", gdp_entries[0]["notes"])

        self.assertNotIn("resident_patent_applications", variables)
        self.assertNotIn("energy_intensity", variables)
        self.assertNotIn("carbon_energy_prices", variables)
        self.assertNotIn("population", variables)
        self.assertIn("wgi_regulatory_quality", variables)
        self.assertIn("rise_renewable_energy", variables)
        self.assertIn("rise_energy_efficiency", variables)

        wgi_entries = [entry for entry in plan if entry["dataset_id"] == "world_bank_wgi"]
        self.assertEqual([entry["variable"] for entry in wgi_entries], ["wgi_regulatory_quality"])
        self.assertEqual(wgi_entries[0]["literature_predictors"], "Regulatory Quality")

    def test_run_raw_download_records_unsupported_entries_without_fetching(self):
        entries = [
            {
                "dataset_id": "unsupported_source",
                "variable": "carbon_tax",
                "source_variable": "",
                "source": "OECD carbon pricing and energy taxation data page",
                "role": "literature_predictor_unresolved_source",
                "description": "Carbon tax",
                "start_year": 1990,
                "end_year": 2024,
                "url": "https://example.test/carbon-tax",
                "file_name": "",
                "status": "not_downloaded",
                "notes": "unsupported source page",
                "literature_rows": "20",
                "literature_predictors": "carbon tax",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            manifest = run_raw_download(
                raw_dir=Path(tmp),
                plan_builder=lambda _start, _end: entries,
                fetcher=lambda _entry: self.fail("unsupported entries should not be fetched"),
            )

        self.assertEqual(len(manifest), 1)
        row = manifest.iloc[0]
        self.assertEqual(row["status"], "not_downloaded")
        self.assertEqual(row["rows"], 0)
        self.assertEqual(row["file_path"], "")

    def test_run_raw_download_records_supported_fetch_errors(self):
        entries = [
            {
                "dataset_id": "world_bank_wdi",
                "variable": "resident_patent_applications",
                "source_variable": "IP.PAT.RESD",
                "source": "World Bank WDI",
                "role": "literature_predictor",
                "description": "Patent applications by residents.",
                "start_year": 1990,
                "end_year": 2024,
                "url": "https://api.worldbank.org/v2/country/all/indicator/IP.PAT.RESD",
                "file_name": "resident_patent_applications.csv",
                "status": "planned",
                "download_method": "tabular",
                "file_format": "csv",
                "notes": "",
                "literature_rows": "8",
                "literature_predictors": "Patent applications (total)",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            manifest = run_raw_download(
                raw_dir=Path(tmp),
                plan_builder=lambda _start, _end: entries,
                fetcher=lambda _entry: (_ for _ in ()).throw(TimeoutError("temporary timeout")),
            )

        row = manifest.iloc[0]
        self.assertEqual(row["status"], "error")
        self.assertIn("temporary timeout", row["notes"])
        self.assertEqual(row["file_path"], "")

    def test_run_raw_download_records_existing_xlsx_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp)
            workbook_path = raw_dir / "epu.xlsx"
            pd.DataFrame(
                {
                    "Year": [2020, 2020],
                    "Month": [1, 2],
                    "US": [100.0, 110.0],
                }
            ).to_excel(workbook_path, index=False)

            entries = [
                {
                    "dataset_id": "policy_uncertainty",
                    "variable": "economic_policy_uncertainty",
                    "source_variable": "All_Country_Data",
                    "source": "Economic Policy Uncertainty Index",
                    "role": "literature_predictor_raw_source",
                    "description": "All-country Economic Policy Uncertainty workbook.",
                    "start_year": 1990,
                    "end_year": 2024,
                    "url": "https://example.test/epu.xlsx",
                    "file_name": workbook_path.name,
                    "status": "planned",
                    "download_method": "binary",
                    "file_format": "xlsx",
                    "literature_rows": "12",
                    "literature_predictors": "Economic Policy Uncertainty Index",
                    "notes": "",
                }
            ]

            manifest = run_raw_download(
                raw_dir=raw_dir,
                plan_builder=lambda _start, _end: entries,
                fetcher=lambda _entry: self.fail("existing xlsx should not be fetched"),
            )

        row = manifest.iloc[0]
        self.assertEqual(row["status"], "downloaded")
        self.assertEqual(row["rows"], 2)
        self.assertEqual(row["columns"], 3)

    def test_run_raw_download_keeps_existing_xlsx_downloaded_without_openpyxl(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp)
            workbook_path = raw_dir / "epu.xlsx"
            pd.DataFrame(
                {
                    "Year": [2020, 2020],
                    "Month": [1, 2],
                    "US": [100.0, 110.0],
                }
            ).to_excel(workbook_path, index=False)

            entries = [
                {
                    "dataset_id": "policy_uncertainty",
                    "variable": "economic_policy_uncertainty",
                    "source_variable": "All_Country_Data",
                    "source": "Economic Policy Uncertainty Index",
                    "role": "literature_predictor_raw_source",
                    "description": "All-country Economic Policy Uncertainty workbook.",
                    "start_year": 1990,
                    "end_year": 2024,
                    "url": "https://example.test/epu.xlsx",
                    "file_name": workbook_path.name,
                    "status": "planned",
                    "download_method": "binary",
                    "file_format": "xlsx",
                    "literature_rows": "12",
                    "literature_predictors": "Economic Policy Uncertainty Index",
                    "notes": "",
                }
            ]

            with patch("raw_data_download.pd.read_excel", side_effect=ImportError("missing openpyxl")):
                manifest = run_raw_download(
                    raw_dir=raw_dir,
                    plan_builder=lambda _start, _end: entries,
                    fetcher=lambda _entry: self.fail("existing xlsx should not be fetched"),
                )

        row = manifest.iloc[0]
        self.assertEqual(row["status"], "downloaded")
        self.assertEqual(row["rows"], 2)
        self.assertEqual(row["columns"], 3)
        self.assertEqual(Path(row["file_path"]).name, "epu.xlsx")


if __name__ == "__main__":
    unittest.main()
