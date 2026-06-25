import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "3_models" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from model_data import (  # noqa: E402
    chronological_train_validation_test_split,
    load_model_panel,
    select_lag_features,
)


class ModelDataTests(unittest.TestCase):
    def test_load_model_panel_rejects_missing_target_values(self):
        panel = pd.DataFrame(
            {
                "country_code": ["AAA", "AAA"],
                "country_name": ["Alpha", "Alpha"],
                "year": [2000, 2001],
                "target": [1.0, None],
                "x_lag1_3_mean": [2.0, 3.0],
            }
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "panel.csv"
            panel.to_csv(path, index=False)

            with self.assertRaisesRegex(ValueError, "missing target"):
                load_model_panel(path, target_column="target")

    def test_load_model_panel_rejects_duplicate_country_year_keys(self):
        panel = pd.DataFrame(
            {
                "country_code": ["AAA", "AAA"],
                "country_name": ["Alpha", "Alpha"],
                "year": [2000, 2000],
                "target": [1.0, 2.0],
                "x_lag1_3_mean": [2.0, 3.0],
            }
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "panel.csv"
            panel.to_csv(path, index=False)

            with self.assertRaisesRegex(ValueError, "Duplicate country-year"):
                load_model_panel(path, target_column="target")

    def test_select_lag_features_keeps_only_requested_lag_scheme(self):
        panel = pd.DataFrame(
            {
                "country_code": ["AAA"],
                "country_name": ["Alpha"],
                "year": [2000],
                "target": [1.0],
                "gdp_lag1": [2.0],
                "gdp_lag1_3_mean": [2.5],
                "inflation_lag1": [3.0],
                "inflation_lag1_3_mean": [3.5],
            }
        )

        lagged_mean_features = select_lag_features(panel, "lag1_3_mean")
        single_lag_features = select_lag_features(panel, "lag1")

        self.assertEqual(lagged_mean_features, ["gdp_lag1_3_mean", "inflation_lag1_3_mean"])
        self.assertEqual(single_lag_features, ["gdp_lag1", "inflation_lag1"])

    def test_chronological_split_uses_contiguous_80_10_10_year_blocks(self):
        panel = pd.DataFrame(
            {
                "country_code": ["AAA"] * 10,
                "country_name": ["Alpha"] * 10,
                "year": list(range(2000, 2010)),
                "target": list(range(10)),
                "x_lag1_3_mean": list(range(10)),
            }
        )

        split = chronological_train_validation_test_split(panel, year_column="year")

        self.assertEqual(split.train_years, list(range(2000, 2008)))
        self.assertEqual(split.validation_years, [2008])
        self.assertEqual(split.test_years, [2009])
        self.assertEqual(split.train["year"].tolist(), list(range(2000, 2008)))
        self.assertEqual(split.validation["year"].tolist(), [2008])
        self.assertEqual(split.test["year"].tolist(), [2009])

    def test_chronological_split_keeps_test_at_end_for_actual_25_year_panel(self):
        panel = pd.DataFrame(
            {
                "country_code": ["AAA"] * 25,
                "country_name": ["Alpha"] * 25,
                "year": list(range(1999, 2024)),
                "target": list(range(25)),
                "x_lag1_3_mean": list(range(25)),
            }
        )

        split = chronological_train_validation_test_split(panel, year_column="year")

        self.assertEqual(split.train_years[0], 1999)
        self.assertEqual(split.train_years[-1], 2018)
        self.assertEqual(split.validation_years, [2019, 2020])
        self.assertEqual(split.test_years, [2021, 2022, 2023])


if __name__ == "__main__":
    unittest.main()
