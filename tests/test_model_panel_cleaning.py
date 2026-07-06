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
    build_main_predictor_reassessment,
    choose_anchor_variable,
    default_panel_definitions,
    load_selected_raw_series,
    run_model_panel_cleaning,
    run_robustness_target_panel_cleaning,
    run_model_panel_cleaning_versions,
    v2_panel_definitions,
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

        panel, metadata = build_model_panel(
            definition=definition,
            predictor_long=predictors,
            target_wide=target,
            imputation="none",
            target_first_year=1990,
            target_last_year=2023,
        )

        self.assertEqual(list(panel["country_code"]), ["USA"])
        self.assertEqual(metadata["anchor_countries"], 2)
        self.assertEqual(metadata["anchor_year_grid_rows"], 2)
        self.assertEqual(metadata["target_missing_rows_dropped"], 1)
        self.assertEqual(metadata["rows"], 1)
        self.assertEqual(metadata["target_non_missing"], 1)
        self.assertEqual(metadata["lag1_3_mean_complete_rows"], 1)
        self.assertEqual(metadata["target_lag1_3_mean_complete_rows"], 1)
        self.assertEqual(metadata["target_lag1_3_mean_complete_countries"], 1)
        self.assertEqual(metadata["lag1_3_mean_complete_target_missing_rows"], 0)

    def test_build_model_panel_drops_rows_with_missing_target(self):
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

        panel, metadata = build_model_panel(
            definition=definition,
            predictor_long=predictors,
            target_wide=target,
            imputation="none",
            target_first_year=1990,
            target_last_year=2023,
        )

        self.assertEqual(list(panel["country_code"]), ["USA"])
        self.assertFalse(panel["env_patent_share_inventions"].isna().any())
        self.assertEqual(metadata["anchor_countries"], 2)
        self.assertEqual(metadata["anchor_year_grid_rows"], 2)
        self.assertEqual(metadata["target_missing_rows_dropped"], 1)
        self.assertEqual(metadata["rows"], 1)
        self.assertEqual(metadata["target_non_missing"], 1)

    def test_default_main_panel_uses_manufacturing_share_predictor(self):
        main_definition = next(definition for definition in default_panel_definitions() if definition.panel_id == "main")
        main_predictors = [spec.variable for spec in main_definition.predictors]

        self.assertIn("manufacturing_share", main_predictors)
        self.assertNotIn("env_technology_rta", main_predictors)

    def test_v2_main_panel_excludes_reassessed_fossil_and_tertiary_predictors(self):
        main_definition = next(definition for definition in v2_panel_definitions() if definition.panel_id == "main")
        main_predictors = [spec.variable for spec in main_definition.predictors]

        self.assertEqual(len(main_predictors), 9)
        self.assertNotIn("fossil_energy_share", main_predictors)
        self.assertNotIn("tertiary_enrollment", main_predictors)
        self.assertIn("manufacturing_share", main_predictors)
        self.assertIsNone(main_definition.anchor_variable)
        self.assertEqual(main_definition.raw_start_year, 1996)
        self.assertEqual(main_definition.raw_end_year, 2022)

    def test_main_predictor_reassessment_flags_v2_exclusions_with_sample_gain(self):
        panel = pd.DataFrame(
            {
                "country_code": ["USA", "CAN", "MEX"],
                "country_name": ["United States", "Canada", "Mexico"],
                "year": [2000, 2000, 2000],
                "env_patent_share_inventions": [1.0, 2.0, 3.0],
                "gdp_constant_2015_usd_lag1": [10.0, 20.0, 30.0],
                "gdp_constant_2015_usd_lag1_3_mean": [10.0, 20.0, 30.0],
                "fossil_energy_share_lag1": [1.0, None, None],
                "fossil_energy_share_lag1_3_mean": [1.0, None, None],
                "tertiary_enrollment_lag1": [1.0, 2.0, None],
                "tertiary_enrollment_lag1_3_mean": [1.0, 2.0, None],
            }
        )
        definition = PanelDefinition(
            panel_id="main",
            predictors=[
                PredictorSpec("gdp_constant_2015_usd", "GDP"),
                PredictorSpec("fossil_energy_share", "Fossil energy share"),
                PredictorSpec("tertiary_enrollment", "Tertiary enrollment"),
            ],
            anchor_variable="fossil_energy_share",
            raw_start_year=1996,
            raw_end_year=1999,
        )

        reassessment = build_main_predictor_reassessment(panel, definition)
        lag1 = reassessment.loc[reassessment["lag_scheme"].eq("lag1")].set_index("variable")

        self.assertEqual(lag1.loc["fossil_energy_share", "v2_decision"], "move_to_robustness_exploratory")
        self.assertEqual(lag1.loc["tertiary_enrollment", "v2_decision"], "move_to_robustness_exploratory")
        self.assertEqual(lag1.loc["gdp_constant_2015_usd", "v2_decision"], "retain_main_v2")
        self.assertEqual(int(lag1.loc["fossil_energy_share", "gain_if_removed"]), 1)
        self.assertEqual(int(lag1.loc["tertiary_enrollment", "gain_if_removed"]), 0)
        self.assertIn("sign-ambiguous", lag1.loc["fossil_energy_share", "decision_reason"])
        self.assertIn("broad human-capital proxy", lag1.loc["tertiary_enrollment", "decision_reason"])

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

    def test_fossil_energy_quality_rules_mark_invalid_values_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp)
            fossil_path = raw_dir / "fossil.csv"
            pd.DataFrame(
                {
                    "dataset_id": ["world_bank_wdi"] * 5,
                    "variable": ["fossil_energy_share"] * 5,
                    "source_variable": ["EG.USE.COMM.FO.ZS"] * 5,
                    "country_code": ["USA"] * 5,
                    "country_name": ["United States"] * 5,
                    "year": [2013, 2014, 2015, 2016, 2017],
                    "value": [0.0, 82.0, -1.0, 0.0, 10.0],
                }
            ).to_csv(fossil_path, index=False)
            manifest = pd.DataFrame(
                [
                    {
                        "dataset_id": "world_bank_wdi",
                        "variable": "fossil_energy_share",
                        "source_variable": "EG.USE.COMM.FO.ZS",
                        "source": "World Bank WDI",
                        "status": "downloaded",
                        "file_path": str(fossil_path),
                        "file_format": "csv",
                    }
                ]
            )

            loaded, _ = load_selected_raw_series(
                raw_dir=raw_dir,
                manifest=manifest,
                variables=["fossil_energy_share"],
            )

        values = dict(zip(loaded["year"], loaded["value"]))
        self.assertTrue(pd.isna(values[2013]))
        self.assertEqual(values[2014], 82.0)
        self.assertTrue(pd.isna(values[2015]))
        self.assertTrue(pd.isna(values[2016]))
        self.assertEqual(values[2017], 10.0)

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

            panel_dir = processed_dir / "model_panels"
            self.assertTrue((panel_dir / "model_panel_main_no_imputation.csv").exists())
            self.assertTrue((panel_dir / "model_panel_main_linear_interpolated.csv").exists())
            self.assertTrue((panel_dir / "model_panel_coverage_summary.csv").exists())
            self.assertTrue((panel_dir / "model_panel_imputation_summary.csv").exists())
            self.assertTrue((panel_dir / "model_panel_quality_summary.csv").exists())
            self.assertTrue((panel_dir / "model_panel_variable_map.csv").exists())
            self.assertFalse((processed_dir / "model_panel_main_no_imputation.csv").exists())
            self.assertEqual(outputs["panel_dir_path"], str(panel_dir))
            self.assertIn("model_panels/model_panel_main_no_imputation.csv", outputs["panel_paths"])
            self.assertIn("target_lag1_3_mean_complete_rows", outputs["coverage_summary"].columns)
            self.assertIn("imputation_summary", outputs)
            self.assertIn("quality_summary", outputs)

    def test_run_model_panel_cleaning_versions_writes_v2_outputs_in_version_subfolder(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp) / "raw"
            processed_dir = Path(tmp) / "processed"
            raw_dir.mkdir()
            target_path = raw_dir / "target.csv"
            gdp_path = raw_dir / "gdp.csv"
            fossil_path = raw_dir / "fossil.csv"
            tertiary_path = raw_dir / "tertiary.csv"
            pd.DataFrame(
                {
                    "REF_AREA": ["USA", "CAN"],
                    "Reference area": ["United States", "Canada"],
                    "TIME_PERIOD": [1999, 1999],
                    "OBS_VALUE": [1.0, 2.0],
                }
            ).to_csv(target_path, index=False)
            for path, variable, values in [
                (gdp_path, "gdp_constant_2015_usd", [100.0, 110.0, 120.0, 200.0, 210.0, 220.0]),
                (fossil_path, "fossil_energy_share", [10.0, 11.0, 12.0, None, None, None]),
                (tertiary_path, "tertiary_enrollment", [50.0, 51.0, 52.0, 60.0, None, 62.0]),
            ]:
                pd.DataFrame(
                    {
                        "dataset_id": ["world_bank_wdi"] * 6,
                        "variable": [variable] * 6,
                        "source_variable": [variable] * 6,
                        "country_code": ["USA", "USA", "USA", "CAN", "CAN", "CAN"],
                        "country_name": ["United States", "United States", "United States", "Canada", "Canada", "Canada"],
                        "year": [1996, 1997, 1998, 1996, 1997, 1998],
                        "value": values,
                    }
                ).to_csv(path, index=False)
            pd.DataFrame(
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
                        "variable": "gdp_constant_2015_usd",
                        "source_variable": "NY.GDP.MKTP.KD",
                        "source": "World Bank WDI",
                        "status": "downloaded",
                        "file_path": str(gdp_path),
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
                        "variable": "tertiary_enrollment",
                        "source_variable": "SE.TER.ENRR",
                        "source": "World Bank WDI",
                        "status": "downloaded",
                        "file_path": str(tertiary_path),
                        "file_format": "csv",
                    },
                ]
            ).to_csv(raw_dir / "raw_download_manifest.csv", index=False)

            outputs = run_model_panel_cleaning_versions(
                raw_dir=raw_dir,
                processed_dir=processed_dir,
                versioned_panel_definitions={
                    "v1": [
                        PanelDefinition(
                            panel_id="main",
                            predictors=[
                                PredictorSpec("gdp_constant_2015_usd", "GDP"),
                                PredictorSpec("fossil_energy_share", "Fossil energy share"),
                                PredictorSpec("tertiary_enrollment", "Tertiary enrollment"),
                            ],
                            anchor_variable="fossil_energy_share",
                            raw_start_year=1996,
                            raw_end_year=1998,
                        )
                    ],
                    "v2": [
                        PanelDefinition(
                            panel_id="main",
                            predictors=[PredictorSpec("gdp_constant_2015_usd", "GDP")],
                            anchor_variable="gdp_constant_2015_usd",
                            raw_start_year=1996,
                            raw_end_year=1998,
                        )
                    ],
                },
            )

            v2_dir = processed_dir / "model_panels" / "v2"
            v2_variable_map = pd.read_csv(v2_dir / "model_panel_variable_map.csv")
            v2_reassessment = pd.read_csv(v2_dir / "model_panel_predictor_reassessment.csv")
            v2_panel_exists = (v2_dir / "model_panel_main_no_imputation.csv").exists()

            self.assertEqual(outputs["active_version"], "v2")
            self.assertTrue(v2_panel_exists)
            self.assertIn("model_panels/v2/model_panel_main_no_imputation.csv", outputs["v2"]["panel_paths"])
            self.assertNotIn("fossil_energy_share", set(v2_variable_map["variable"]))
            self.assertNotIn("tertiary_enrollment", set(v2_variable_map["variable"]))
            self.assertIn("fossil_energy_share", set(v2_reassessment["variable"]))
            self.assertIn("tertiary_enrollment", set(v2_reassessment["variable"]))

    def test_run_robustness_target_panel_cleaning_writes_second_target_v2_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp) / "raw"
            processed_dir = Path(tmp) / "processed"
            raw_dir.mkdir()
            main_target_path = raw_dir / "main_target.csv"
            robustness_target_path = raw_dir / "robustness_target.csv"
            gdp_path = raw_dir / "gdp.csv"
            pd.DataFrame(
                {
                    "REF_AREA": ["USA", "CAN"],
                    "Reference area": ["United States", "Canada"],
                    "TIME_PERIOD": [1999, 1999],
                    "OBS_VALUE": [1.0, 2.0],
                }
            ).to_csv(main_target_path, index=False)
            pd.DataFrame(
                {
                    "REF_AREA": ["USA", "CAN"],
                    "Reference area": ["United States", "Canada"],
                    "TIME_PERIOD": [1999, 1999],
                    "OBS_VALUE": [10.0, None],
                }
            ).to_csv(robustness_target_path, index=False)
            pd.DataFrame(
                {
                    "dataset_id": ["world_bank_wdi"] * 6,
                    "variable": ["gdp_constant_2015_usd"] * 6,
                    "source_variable": ["NY.GDP.MKTP.KD"] * 6,
                    "country_code": ["USA", "USA", "USA", "CAN", "CAN", "CAN"],
                    "country_name": ["United States", "United States", "United States", "Canada", "Canada", "Canada"],
                    "year": [1996, 1997, 1998, 1996, 1997, 1998],
                    "value": [100.0, 110.0, 120.0, 200.0, 210.0, 220.0],
                }
            ).to_csv(gdp_path, index=False)
            pd.DataFrame(
                [
                    {
                        "dataset_id": "oecd_patents_environment",
                        "variable": "env_patent_share_inventions",
                        "source_variable": "PT_INV.DEV.ENV_PAT._Z",
                        "source": "OECD Patents - indicators",
                        "status": "downloaded",
                        "file_path": str(main_target_path),
                        "file_format": "csv",
                    },
                    {
                        "dataset_id": "oecd_patents_environment",
                        "variable": "env_patents_per_million",
                        "source_variable": "INV_PS.DEV.ENV_PAT._Z",
                        "source": "OECD Patents - indicators",
                        "status": "downloaded",
                        "file_path": str(robustness_target_path),
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
            ).to_csv(raw_dir / "raw_download_manifest.csv", index=False)

            outputs = run_robustness_target_panel_cleaning(
                raw_dir=raw_dir,
                processed_dir=processed_dir,
                panel_definitions=[
                    PanelDefinition(
                        panel_id="main",
                        predictors=[PredictorSpec("gdp_constant_2015_usd", "GDP")],
                        anchor_variable="gdp_constant_2015_usd",
                        raw_start_year=1996,
                        raw_end_year=1998,
                    )
                ],
            )

            panel_dir = processed_dir / "model_panels" / "robustness" / "env_patents_per_million" / "v2"
            panel = pd.read_csv(panel_dir / "model_panel_main_no_imputation.csv")
            variable_map = pd.read_csv(panel_dir / "model_panel_variable_map.csv")
            coverage = pd.read_csv(panel_dir / "model_panel_coverage_summary.csv")

        self.assertEqual(outputs["target_variable"], "env_patents_per_million")
        self.assertEqual(outputs["panel_dir_path"], str(panel_dir))
        self.assertIn("model_panels/robustness/env_patents_per_million/v2/model_panel_main_no_imputation.csv", outputs["panel_paths"])
        self.assertIn("env_patents_per_million", panel.columns)
        self.assertNotIn("env_patent_share_inventions", panel.columns)
        self.assertEqual(list(panel["country_code"]), ["USA"])
        self.assertEqual(variable_map.loc[variable_map["role"].eq("target"), "variable"].iloc[0], "env_patents_per_million")
        self.assertEqual(int(coverage.loc[0, "target_missing_rows_dropped"]), 1)

    def test_run_model_panel_cleaning_writes_nan_literal_for_missing_predictors(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp) / "raw"
            processed_dir = Path(tmp) / "processed"
            raw_dir.mkdir()
            target_path = raw_dir / "target.csv"
            fossil_path = raw_dir / "fossil.csv"
            gdp_path = raw_dir / "gdp.csv"
            pd.DataFrame(
                {
                    "REF_AREA": ["USA"],
                    "Reference area": ["United States"],
                    "TIME_PERIOD": [1999],
                    "OBS_VALUE": [1.0],
                }
            ).to_csv(target_path, index=False)
            for path, variable, values in [
                (fossil_path, "fossil_energy_share", [10.0, 11.0, 12.0]),
                (gdp_path, "gdp_constant_2015_usd", [100.0, None, 120.0]),
            ]:
                pd.DataFrame(
                    {
                        "dataset_id": ["world_bank_wdi"] * 3,
                        "variable": [variable] * 3,
                        "source_variable": [variable] * 3,
                        "country_code": ["USA"] * 3,
                        "country_name": ["United States"] * 3,
                        "year": [1996, 1997, 1998],
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

            run_model_panel_cleaning(
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
                        raw_end_year=1998,
                    )
                ],
            )

            panel_text = (processed_dir / "model_panels" / "model_panel_main_no_imputation.csv").read_text()
            variable_map_text = (processed_dir / "model_panels" / "model_panel_variable_map.csv").read_text()

        self.assertIn("NaN", panel_text)
        self.assertNotIn(",,", panel_text)
        self.assertIn("NaN", variable_map_text)
        self.assertNotIn(",,", variable_map_text)


if __name__ == "__main__":
    unittest.main()
