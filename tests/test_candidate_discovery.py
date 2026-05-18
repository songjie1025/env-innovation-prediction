import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "2_data" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from candidate_discovery import (  # noqa: E402
    build_predictor_candidate_catalog,
    build_target_candidate_catalog,
    filter_world_bank_metadata,
    run_candidate_discovery,
    source_variable,
    write_outputs,
)


class CandidateDiscoveryTests(unittest.TestCase):
    def test_source_variable_uses_oecd_dimension_order(self):
        self.assertEqual(
            source_variable("PT_INV", "DEV", "ENV_PAT", "_Z"),
            "PT_INV.DEV.ENV_PAT._Z",
        )

    def test_build_target_candidate_catalog_classifies_main_and_secondary_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            processed_dir = Path(tmp)
            pd.DataFrame(
                [
                    ["UNIT_MEASURE", "Indicator measure", "PT_INV", "Percentage of inventions", 1],
                    ["UNIT_MEASURE", "Indicator measure", "PT_TECH", "Percentage of technologies", 2],
                    ["UNIT_MEASURE", "Indicator measure", "INV_PS", "Inventions per person", 3],
                    ["UNIT_MEASURE", "Indicator measure", "PT_TECH_COL", "Percentage of collaborations", 4],
                    ["TYPE", "Patent counting type", "DEV", "Development", 1],
                    ["TYPE", "Patent counting type", "COL", "Collaboration", 2],
                    ["TECH", "Technological domain", "ENV_PAT", "Environment-related technologies", 1],
                    ["TECH", "Technological domain", "ENE", "Energy technology", 2],
                    ["TECH", "Technological domain", "TOT", "All technologies", 3],
                    ["PAT", "Regional patent office", "_Z", "Not applicable", 1],
                    ["PAT", "Regional patent office", "EPO", "European Patent Office", 2],
                ],
                columns=["dimension", "dimension_label", "code", "label", "position"],
            ).to_csv(processed_dir / "oecd_patent_dimension_values.csv", index=False)
            pd.DataFrame(
                [
                    {
                        "dataset_id": "oecd_patents_environment",
                        "variable": "env_patent_share_inventions",
                        "source_variable": "PT_INV.DEV.ENV_PAT._Z",
                        "non_missing_observations": 100,
                        "countries_with_data": 10,
                        "first_year": 1990,
                        "last_year": 2023,
                    }
                ]
            ).to_csv(processed_dir / "data_availability.csv", index=False)

            catalog = build_target_candidate_catalog(processed_dir)

        main = catalog[catalog["source_variable"].eq("PT_INV.DEV.ENV_PAT._Z")].iloc[0]
        intensity = catalog[catalog["source_variable"].eq("INV_PS.DEV.ENV_PAT._Z")].iloc[0]
        office_breakdown = catalog[catalog["source_variable"].eq("PT_INV.DEV.ENV_PAT.EPO")].iloc[0]
        collaboration = catalog[catalog["source_variable"].eq("PT_TECH_COL.COL.ENV_PAT._Z")].iloc[0]

        self.assertEqual(main["candidate_role"], "main_target_candidate")
        self.assertTrue(bool(main["include"]))
        self.assertTrue(bool(main["coverage_checked"]))
        self.assertEqual(main["non_missing_observations"], 100)
        self.assertEqual(intensity["candidate_role"], "secondary_target")
        self.assertFalse(bool(office_breakdown["include"]))
        self.assertEqual(collaboration["candidate_role"], "not_suitable")

    def test_filter_world_bank_metadata_matches_keywords_without_network(self):
        records = [
            {
                "id": "GB.XPD.RSDV.GD.ZS",
                "name": "Research and development expenditure (% of GDP)",
                "sourceNote": "Gross domestic expenditures on research and development.",
            },
            {
                "id": "SP.POP.TOTL",
                "name": "Population, total",
                "sourceNote": "Total population is based on the de facto definition.",
            },
        ]

        matches = filter_world_bank_metadata(records, ["research", "development"])

        self.assertEqual([match["id"] for match in matches], ["GB.XPD.RSDV.GD.ZS"])
        self.assertIn("Research and development", matches[0]["name"])

    def test_build_predictor_candidate_catalog_includes_reviewer_fields_and_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            processed_dir = Path(tmp)
            pd.DataFrame(
                [
                    {
                        "dataset_id": "world_bank_wdi",
                        "variable": "rd_expenditure_gdp",
                        "source_variable": "GB.XPD.RSDV.GD.ZS",
                        "non_missing_observations": 2467,
                        "countries_with_data": 156,
                        "first_year": 1996,
                        "last_year": 2024,
                    },
                    {
                        "dataset_id": "oecd_eps",
                        "variable": "eps_index",
                        "source_variable": "POL_STRINGENCY.EPS",
                        "non_missing_observations": 1240,
                        "countries_with_data": 40,
                        "first_year": 1990,
                        "last_year": 2020,
                    },
                ]
            ).to_csv(processed_dir / "data_availability.csv", index=False)

            catalog = build_predictor_candidate_catalog(processed_dir)

        required_columns = {
            "variable_concept",
            "candidate_indicator",
            "source",
            "source_variable",
            "why_relevant",
            "literature_support",
            "coverage_checked",
            "coverage_summary",
            "already_downloaded",
            "include_decision",
            "decision_reason",
            "measurement_caveat",
            "lag_recommendation",
        }
        self.assertTrue(required_columns.issubset(catalog.columns))
        rd = catalog[catalog["candidate_indicator"].eq("rd_expenditure_gdp")].iloc[0]
        eps = catalog[catalog["candidate_indicator"].eq("eps_index")].iloc[0]
        self.assertTrue(bool(rd["already_downloaded"]))
        self.assertIn("156 countries", rd["coverage_summary"])
        self.assertTrue(bool(eps["coverage_checked"]))

    def test_write_outputs_creates_expected_catalog_files(self):
        target_catalog = pd.DataFrame(
            [{"source_variable": "PT_INV.DEV.ENV_PAT._Z", "candidate_role": "main_target_candidate"}]
        )
        predictor_catalog = pd.DataFrame(
            [{"candidate_indicator": "rd_expenditure_gdp", "include_decision": "include_main"}]
        )

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            write_outputs(target_catalog, predictor_catalog, output_dir)

            self.assertTrue((output_dir / "target_candidate_catalog.csv").exists())
            self.assertTrue((output_dir / "predictor_candidate_catalog.csv").exists())
            self.assertTrue((output_dir / "candidate_discovery_summary.md").exists())

    def test_run_candidate_discovery_can_read_from_explicit_processed_dir(self):
        with tempfile.TemporaryDirectory() as input_tmp, tempfile.TemporaryDirectory() as output_tmp:
            processed_dir = Path(input_tmp)
            output_dir = Path(output_tmp)
            pd.DataFrame(
                [
                    ["UNIT_MEASURE", "Indicator measure", "PT_INV", "Percentage of inventions", 1],
                    ["TYPE", "Patent counting type", "DEV", "Development", 1],
                    ["TECH", "Technological domain", "ENV_PAT", "Environment-related technologies", 1],
                    ["PAT", "Regional patent office", "_Z", "Not applicable", 1],
                ],
                columns=["dimension", "dimension_label", "code", "label", "position"],
            ).to_csv(processed_dir / "oecd_patent_dimension_values.csv", index=False)
            pd.DataFrame(
                [
                    {
                        "dataset_id": "oecd_patents_environment",
                        "variable": "env_patent_share_inventions",
                        "source_variable": "PT_INV.DEV.ENV_PAT._Z",
                        "non_missing_observations": 12,
                        "countries_with_data": 3,
                        "years_with_data": 4,
                        "first_year": 2000,
                        "last_year": 2003,
                    }
                ]
            ).to_csv(processed_dir / "data_availability.csv", index=False)

            target_catalog, _ = run_candidate_discovery(
                output_dir=output_dir,
                processed_dir=processed_dir,
            )

            main = target_catalog[target_catalog["source_variable"].eq("PT_INV.DEV.ENV_PAT._Z")].iloc[0]
            self.assertEqual(main["countries_with_data"], 3)
            self.assertTrue((output_dir / "target_candidate_catalog.csv").exists())


if __name__ == "__main__":
    unittest.main()
