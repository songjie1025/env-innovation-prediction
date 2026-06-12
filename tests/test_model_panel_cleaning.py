import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "2_data" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from model_panel_cleaning import (  # noqa: E402
    PanelDefinition,
    PredictorSpec,
    build_model_panel,
    choose_anchor_variable,
    default_panel_definitions,
    load_selected_raw_series,
    run_model_panel_cleaning,
)


class ModelPanelCleaningTests(unittest.TestCase):
    def test_lagged_mean_requires_complete_window_without_imputation(self):
        predictors = pd.DataFrame(
            {
                "variable": ["toy"] * 3,
                "country_code": ["USA"] * 3,
                "country_name": ["United States"] * 3,
                "year": [1996, 1997, 1998],
                "value": [1.0, None, 3.0],
            }
        )
        target = pd.DataFrame(
            {
                "country_code": ["USA"],
                "country_name": ["United States"],
                "year": [1999],
                "env_patent_share_inventions": [5.0],
            }
        )
        definition = PanelDefinition(
            panel_id="toy",
            predictors=[PredictorSpec("toy", "Toy variable", "toy.csv")],
            anchor_variable="toy",
            raw_start_year=1996,
            raw_end_year=1998,
        )

        panel, metadata = build_model_panel(
            definition=definition,
            predictor_long=predictors,
            target_wide=target,
            imputation="none",
            target_first_year=1990,
            target_last_year=2023,
        )

        row = panel.iloc[0]
        self.assertEqual(row["toy_lag1"], 3.0)
        self.assertTrue(pd.isna(row["toy_lag1_3_mean"]))
        self.assertEqual(metadata["imputed_values_total"], 0)

    def test_linear_interpolation_fills_internal_predictor_gaps_before_lagging(self):
        predictors = pd.DataFrame(
            {
                "variable": ["toy"] * 3,
                "country_code": ["USA"] * 3,
                "country_name": ["United States"] * 3,
                "year": [1996, 1997, 1998],
                "value": [1.0, None, 3.0],
            }
        )
        target = pd.DataFrame(
            {
                "country_code": ["USA"],
                "country_name": ["United States"],
                "year": [1999],
                "env_patent_share_inventions": [5.0],
            }
        )
        definition = PanelDefinition(
            panel_id="toy",
            predictors=[PredictorSpec("toy", "Toy variable", "toy.csv")],
            anchor_variable="toy",
            raw_start_year=1996,
            raw_end_year=1998,
        )

        panel, metadata = build_model_panel(
            definition=definition,
            predictor_long=predictors,
            target_wide=target,
            imputation="linear_interpolated",
            target_first_year=1990,
            target_last_year=2023,
        )

        row = panel.iloc[0]
        self.assertEqual(row["toy_lag1"], 3.0)
        self.assertEqual(row["toy_lag1_3_mean"], 2.0)
        self.assertEqual(metadata["imputed_values_total"], 1)

    def test_main_panel_uses_anchor_country_set_and_lagged_target_years(self):
        predictors = pd.DataFrame(
            {
                "variable": ["fossil_energy_share"] * 6 + ["gdp_constant_2015_usd"] * 6,
                "country_code": ["USA", "USA", "USA", "CAN", "CAN", "CAN"] * 2,
                "country_name": ["United States", "United States", "United States", "Canada", "Canada", "Canada"] * 2,
                "year": [1996, 1997, 1998, 1996, 1997, 1998] * 2,
                "value": [10.0, 11.0, 12.0, None, None, None, 100.0, 110.0, 120.0, 200.0, 210.0, 220.0],
            }
        )
        target = pd.DataFrame(
            {
                "country_code": ["USA", "CAN"],
                "country_name": ["United States", "Canada"],
                "year": [1999, 1999],
                "env_patent_share_inventions": [1.5, 2.5],
            }
        )
        definition = PanelDefinition(
            panel_id="main",
            predictors=[
                PredictorSpec("gdp_constant_2015_usd", "GDP", "gdp.csv"),
                PredictorSpec("fossil_energy_share", "Fossil energy share", "fossil.csv"),
            ],
            anchor_variable="fossil_energy_share",
            raw_start_year=1996,
            raw_end_year=1998,
        )

        panel, metadata = build_model_panel(
            definition=definition,
            predictor_long=predictors,
            target_wide=target,
            imputation="none",
            target_first_year=1990,
            target_last_year=2023,
        )

        self.assertEqual(list(panel["country_code"]), ["USA"])
        self.assertEqual(list(panel["year"]), [1999])
        self.assertEqual(panel.iloc[0]["fossil_energy_share_lag1_3_mean"], 11.0)
        self.assertEqual(metadata["countries"], 1)
        self.assertEqual(metadata["target_year_start"], 1999)
        self.assertEqual(metadata["target_year_end"], 1999)

    def test_metadata_reports_analysis_ready_target_and_feature_rows(self):
        predictors = pd.DataFrame(
            {
                "variable": ["toy"] * 6,
                "country_code": ["USA", "USA", "USA", "CAN", "CAN", "CAN"],
                "country_name": ["United States", "United States", "United States", "Canada", "Canada", "Canada"],
                "year": [1996, 1997, 1998, 1996, 1997, 1998],
                "value": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            }
        )
        target = pd.DataFrame(
            {
                "country_code": ["USA", "CAN"],
                "country_name": ["United States", "Canada"],
                "year": [1999, 1999],
                "env_patent_share_inventions": [10.0, None],
            }
        )
        definition = PanelDefinition(
            panel_id="toy",
            predictors=[PredictorSpec("toy", "Toy variable", "toy.csv")],
            anchor_variable="toy",
            raw_start_year=1996,
            raw_end_year=1998,
        )

        _, metadata = build_model_panel(
            definition=definition,
            predictor_long=predictors,
            target_wide=target,
            imputation="none",
            target_first_year=1990,
            target_last_year=2023,
        )

        self.assertEqual(metadata["lag1_3_mean_complete_rows"], 2)
        self.assertEqual(metadata["target_lag1_3_mean_complete_rows"], 1)
        self.assertEqual(metadata["target_lag1_3_mean_complete_countries"], 1)
        self.assertEqual(metadata["lag1_3_mean_complete_target_missing_rows"], 1)

    def test_default_main_panel_uses_oecd_rta_index_predictor(self):
        main_definition = next(definition for definition in default_panel_definitions() if definition.panel_id == "main")
        main_predictors = [spec.variable for spec in main_definition.predictors]

        self.assertIn("env_technology_rta", main_predictors)
        self.assertNotIn("env_technology_share_for_rta", main_predictors)

    def test_rise_loader_uses_all_score_when_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp)
            rise_path = raw_dir / "rise.csv"
            pd.DataFrame(
                {
                    "REF_AREA": ["USA", "USA", "USA", "USA"],
                    "REF_AREA_LABEL": ["United States"] * 4,
                    "INDICATOR": ["WB_RISE_RE_ALL", "WB_RISE_RE_ELEC", "WB_RISE_RE_ALL", "WB_RISE_RE_ELEC"],
                    "INDICATOR_LABEL": ["Renewable Energy Score", "Electricity", "Renewable Energy Score", "Electricity"],
                    "TIME_PERIOD": [2020, 2020, 2021, 2021],
                    "OBS_VALUE": [50.0, 99.0, 60.0, 88.0],
                }
            ).to_csv(rise_path, index=False)
            manifest = pd.DataFrame(
                [
                    {
                        "dataset_id": "world_bank_data360",
                        "variable": "rise_renewable_energy",
                        "source_variable": "WB_RISE_RE_*",
                        "source": "World Bank Data360 RISE",
                        "status": "downloaded",
                        "file_path": str(rise_path),
                        "file_format": "csv",
                        "indicator_prefix": "WB_RISE_RE_",
                    }
                ]
            )

            loaded, variable_map = load_selected_raw_series(
                raw_dir=raw_dir,
                manifest=manifest,
                variables=["rise_renewable_energy"],
            )

        self.assertEqual(list(loaded["value"]), [50.0, 60.0])
        self.assertEqual(variable_map.iloc[0]["rise_selection_rule"], "WB_RISE_RE_ALL")
        self.assertEqual(variable_map.iloc[0]["source_series_count"], 1)

    def test_choose_anchor_variable_uses_fewest_countries_then_observations(self):
        predictor_long = pd.DataFrame(
            {
                "variable": ["wide", "wide", "wide", "narrow", "narrow"],
                "country_code": ["USA", "CAN", "MEX", "USA", "USA"],
                "year": [2020, 2020, 2020, 2020, 2021],
                "value": [1.0, 1.0, 1.0, 2.0, 3.0],
            }
        )

        anchor, diagnostics = choose_anchor_variable(
            predictor_long=predictor_long,
            candidate_variables=["wide", "narrow"],
            raw_start_year=2020,
            raw_end_year=2021,
        )

        self.assertEqual(anchor, "narrow")
        self.assertEqual(diagnostics.loc[0, "variable"], "narrow")
        self.assertEqual(int(diagnostics.loc[0, "countries_with_data"]), 1)

    def test_run_model_panel_cleaning_writes_expected_panel_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp) / "raw"
            processed_dir = Path(tmp) / "processed"
            raw_dir.mkdir()
            target_path = raw_dir / "target.csv"
            fossil_path = raw_dir / "fossil.csv"
            gdp_path = raw_dir / "gdp.csv"
            pd.DataFrame(
                {
                    "REF_AREA": ["USA", "USA"],
                    "Reference area": ["United States", "United States"],
                    "TIME_PERIOD": [1999, 2000],
                    "OBS_VALUE": [1.0, 2.0],
                }
            ).to_csv(target_path, index=False)
            for path, variable, values in [
                (fossil_path, "fossil_energy_share", [10.0, 11.0, 12.0, 13.0]),
                (gdp_path, "gdp_constant_2015_usd", [100.0, 110.0, 120.0, 130.0]),
            ]:
                pd.DataFrame(
                    {
                        "dataset_id": ["world_bank_wdi"] * 4,
                        "variable": [variable] * 4,
                        "source_variable": [variable] * 4,
                        "country_code": ["USA"] * 4,
                        "country_name": ["United States"] * 4,
                        "year": [1996, 1997, 1998, 1999],
                        "value": values,
                    }
                ).to_csv(path, index=False)
            manifest = pd.DataFrame(
                [
                    {
                        "dataset_id": "oecd_patents_environment",
                        "variable": "env_patent_share_inventions",
                        "source_variable": "PT_INV.DEV.ENV_PAT._Z",
                        "source": "OECD Patents - indicators",
                        "status": "downloaded",
                        "file_path": str(target_path),
                        "file_format": "csv",
                    },
                    {
                        "dataset_id": "world_bank_wdi",
                        "variable": "fossil_energy_share",
                        "source_variable": "EG.USE.COMM.FO.ZS",
                        "source": "World Bank WDI",
                        "status": "downloaded",
                        "file_path": str(fossil_path),
                        "file_format": "csv",
                    },
                    {
                        "dataset_id": "world_bank_wdi",
                        "variable": "gdp_constant_2015_usd",
                        "source_variable": "NY.GDP.MKTP.KD",
                        "source": "World Bank WDI",
                        "status": "downloaded",
                        "file_path": str(gdp_path),
                        "file_format": "csv",
                    },
                ]
            )
            manifest.to_csv(raw_dir / "raw_download_manifest.csv", index=False)

            outputs = run_model_panel_cleaning(
                raw_dir=raw_dir,
                processed_dir=processed_dir,
                panel_definitions=[
                    PanelDefinition(
                        panel_id="main",
                        predictors=[
                            PredictorSpec("gdp_constant_2015_usd", "GDP", "gdp.csv"),
                            PredictorSpec("fossil_energy_share", "Fossil energy share", "fossil.csv"),
                        ],
                        anchor_variable="fossil_energy_share",
                        raw_start_year=1996,
                        raw_end_year=1999,
                    )
                ],
            )

            self.assertTrue((processed_dir / "model_panel_main_no_imputation.csv").exists())
            self.assertTrue((processed_dir / "model_panel_main_linear_interpolated.csv").exists())
            self.assertTrue((processed_dir / "model_panel_coverage_summary.csv").exists())
            self.assertTrue((processed_dir / "model_panel_imputation_summary.csv").exists())
            self.assertTrue((processed_dir / "model_panel_variable_map.csv").exists())
            self.assertIn("model_panel_main_no_imputation.csv", outputs["panel_paths"])
            self.assertIn("target_lag1_3_mean_complete_rows", outputs["coverage_summary"].columns)
            self.assertIn("imputation_summary", outputs)


if __name__ == "__main__":
    unittest.main()
