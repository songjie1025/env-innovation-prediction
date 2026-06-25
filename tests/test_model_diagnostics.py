import sys
import unittest
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "3_models" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from model_data import ChronologicalSplit  # noqa: E402
from model_diagnostics import (  # noqa: E402
    build_correlation_diagnostics,
    build_missingness_pattern_diagnostics,
    top_feature_correlations,
)


class ModelDiagnosticTests(unittest.TestCase):
    def test_correlation_diagnostics_use_train_and_validation_only(self):
        train = pd.DataFrame(
            {
                "country_code": ["AAA", "BBB"],
                "country_name": ["Alpha", "Beta"],
                "year": [2000, 2000],
                "target": [1.0, 2.0],
                "x_lag1_3_mean": [1.0, 2.0],
                "z_lag1_3_mean": [4.0, 3.0],
            }
        )
        validation = pd.DataFrame(
            {
                "country_code": ["AAA", "BBB"],
                "country_name": ["Alpha", "Beta"],
                "year": [2001, 2001],
                "target": [3.0, 4.0],
                "x_lag1_3_mean": [3.0, 4.0],
                "z_lag1_3_mean": [2.0, 1.0],
            }
        )
        test = pd.DataFrame(
            {
                "country_code": ["AAA", "BBB"],
                "country_name": ["Alpha", "Beta"],
                "year": [2002, 2002],
                "target": [100.0, 100.0],
                "x_lag1_3_mean": [4.0, 1.0],
                "z_lag1_3_mean": [1.0, 4.0],
            }
        )
        split = ChronologicalSplit(
            train=train,
            validation=validation,
            test=test,
            train_years=[2000],
            validation_years=[2001],
            test_years=[2002],
        )
        coefficients = pd.DataFrame(
            {
                "model": ["elastic_net", "elastic_net"],
                "feature": ["x_lag1_3_mean", "z_lag1_3_mean"],
                "coefficient": [0.5, -0.25],
                "abs_coefficient": [0.5, 0.25],
            }
        )

        diagnostics = build_correlation_diagnostics(
            split=split,
            feature_columns=["x_lag1_3_mean", "z_lag1_3_mean"],
            target_column="target",
            coefficients=coefficients,
            panel_id="main",
            panel_label="Main model",
        )

        target_correlations = diagnostics["target_correlations"]
        x_corr = target_correlations.loc[
            target_correlations["feature"].eq("x_lag1_3_mean"), "correlation"
        ].iloc[0]
        z_corr = target_correlations.loc[
            target_correlations["feature"].eq("z_lag1_3_mean"), "correlation"
        ].iloc[0]

        self.assertAlmostEqual(x_corr, 1.0)
        self.assertAlmostEqual(z_corr, -1.0)
        self.assertEqual(diagnostics["analysis_year_start"], 2000)
        self.assertEqual(diagnostics["analysis_year_end"], 2001)
        self.assertEqual(diagnostics["analysis_rows"], 4)
        self.assertNotEqual(diagnostics["analysis_rows"], len(pd.concat([train, validation, test])))

        self.assertIn("spearman_feature_correlations", diagnostics)
        self.assertIn("pearson_feature_correlations", diagnostics)
        self.assertIn("top_correlated_pairs", diagnostics)
        self.assertIn("coefficient_correlation_alignment", diagnostics)

        alignment = diagnostics["coefficient_correlation_alignment"]
        self.assertTrue(alignment["sign_aligned"].all())
        self.assertIn("panel_id", alignment.columns)
        self.assertIn("panel_label", alignment.columns)

    def test_correlation_alignment_marks_zero_coefficients_as_shrunk_not_aligned(self):
        coefficients = pd.DataFrame(
            {
                "model": ["elastic_net", "elastic_net"],
                "feature": ["x_lag1_3_mean", "z_lag1_3_mean"],
                "coefficient": [0.0, -0.25],
                "abs_coefficient": [0.0, 0.25],
            }
        )
        target_correlations = pd.DataFrame(
            {
                "feature": ["x_lag1_3_mean", "z_lag1_3_mean"],
                "correlation": [0.8, -0.5],
                "abs_correlation": [0.8, 0.5],
                "non_missing_rows": [10, 10],
            }
        )

        diagnostics = build_correlation_diagnostics(
            split=ChronologicalSplit(
                train=pd.DataFrame(
                    {
                        "country_code": ["AAA", "BBB"],
                        "country_name": ["Alpha", "Beta"],
                        "year": [2000, 2000],
                        "target": [1.0, 2.0],
                        "x_lag1_3_mean": [1.0, 2.0],
                        "z_lag1_3_mean": [4.0, 3.0],
                    }
                ),
                validation=pd.DataFrame(
                    {
                        "country_code": ["AAA", "BBB"],
                        "country_name": ["Alpha", "Beta"],
                        "year": [2001, 2001],
                        "target": [3.0, 4.0],
                        "x_lag1_3_mean": [3.0, 4.0],
                        "z_lag1_3_mean": [2.0, 1.0],
                    }
                ),
                test=pd.DataFrame(
                    {
                        "country_code": ["AAA", "BBB"],
                        "country_name": ["Alpha", "Beta"],
                        "year": [2002, 2002],
                        "target": [5.0, 6.0],
                        "x_lag1_3_mean": [5.0, 6.0],
                        "z_lag1_3_mean": [0.0, -1.0],
                    }
                ),
                train_years=[2000],
                validation_years=[2001],
                test_years=[2002],
            ),
            feature_columns=["x_lag1_3_mean", "z_lag1_3_mean"],
            target_column="target",
            coefficients=coefficients,
            panel_id="main",
            panel_label="Main model",
        )
        alignment = diagnostics["coefficient_correlation_alignment"]
        zero_row = alignment[alignment["feature"].eq("x_lag1_3_mean")].iloc[0]
        nonzero_row = alignment[alignment["feature"].eq("z_lag1_3_mean")].iloc[0]

        self.assertEqual(zero_row["coefficient_status"], "shrunk_to_zero")
        self.assertFalse(bool(zero_row["sign_aligned"]))
        self.assertEqual(nonzero_row["coefficient_status"], "nonzero")
        self.assertTrue(bool(nonzero_row["sign_aligned"]))

    def test_top_feature_correlations_handles_one_feature_matrix(self):
        matrix = pd.DataFrame([[1.0]], index=["eps_index_lag1_3_mean"], columns=["eps_index_lag1_3_mean"])

        top_pairs = top_feature_correlations(
            matrix,
            method="spearman",
            panel_id="subc",
            panel_label="Submodel C: OECD EPS",
        )

        self.assertTrue(top_pairs.empty)
        self.assertEqual(
            list(top_pairs.columns),
            [
                "panel_id",
                "panel_label",
                "method",
                "feature_a",
                "feature_b",
                "correlation",
                "abs_correlation",
            ],
        )

    def test_missingness_pattern_diagnostics_classifies_country_feature_sequences(self):
        years = [2000, 2001, 2002, 2003]
        sequences = {
            ("AAA", "Alpha"): [1.0, 2.0, 3.0, 4.0],
            ("BBB", "Beta"): [None, None, 3.0, 4.0],
            ("CCC", "Gamma"): [1.0, 2.0, None, None],
            ("DDD", "Delta"): [None, 2.0, 3.0, None],
            ("EEE", "Epsilon"): [1.0, None, 3.0, 4.0],
            ("FFF", "Zeta"): [None, None, None, None],
        }
        rows = []
        for (country_code, country_name), values in sequences.items():
            for year, value in zip(years, values):
                rows.append(
                    {
                        "country_code": country_code,
                        "country_name": country_name,
                        "year": year,
                        "target": 1.0,
                        "feature_lag1_3_mean": value,
                    }
                )
        panel = pd.DataFrame(rows)

        summary, detail = build_missingness_pattern_diagnostics(
            panel=panel,
            feature_columns=["feature_lag1_3_mean"],
        )

        pattern_by_country = dict(zip(detail["country_code"], detail["missingness_pattern"]))
        self.assertEqual(pattern_by_country["AAA"], "complete")
        self.assertEqual(pattern_by_country["BBB"], "late_start")
        self.assertEqual(pattern_by_country["CCC"], "early_end")
        self.assertEqual(pattern_by_country["DDD"], "bounded_coverage_window")
        self.assertEqual(pattern_by_country["EEE"], "intermittent_gaps")
        self.assertEqual(pattern_by_country["FFF"], "all_missing")

        all_missing = detail[detail["country_code"].eq("FFF")].iloc[0]
        self.assertTrue(pd.isna(all_missing["first_observed_year"]))
        self.assertTrue(pd.isna(all_missing["last_observed_year"]))
        self.assertEqual(all_missing["missing_years"], 4)

        summary_row = summary.iloc[0]
        self.assertEqual(summary_row["countries"], 6)
        self.assertEqual(summary_row["country_year_rows"], 24)
        self.assertEqual(summary_row["missing_country_year_rows"], 11)
        self.assertAlmostEqual(summary_row["missing_share"], 11 / 24)
        self.assertEqual(summary_row["complete_countries"], 1)
        self.assertEqual(summary_row["late_start_countries"], 1)
        self.assertEqual(summary_row["early_end_countries"], 1)
        self.assertEqual(summary_row["bounded_coverage_window_countries"], 1)
        self.assertEqual(summary_row["intermittent_gaps_countries"], 1)
        self.assertEqual(summary_row["all_missing_countries"], 1)

    def test_missingness_pattern_diagnostics_reports_calendar_span_for_non_contiguous_panel_rows(self):
        panel = pd.DataFrame(
            {
                "country_code": ["AAA", "AAA", "AAA"],
                "country_name": ["Alpha", "Alpha", "Alpha"],
                "year": [2000, 2002, 2004],
                "feature_lag1_3_mean": [1.0, None, 3.0],
            }
        )

        _, detail = build_missingness_pattern_diagnostics(
            panel=panel,
            feature_columns=["feature_lag1_3_mean"],
        )

        row = detail.iloc[0]
        self.assertEqual(row["year_start"], 2000)
        self.assertEqual(row["year_end"], 2004)
        self.assertEqual(row["total_years"], 3)
        self.assertEqual(row["calendar_year_span"], 5)
        self.assertEqual(row["internal_missing_years"], 1)
        self.assertEqual(row["missingness_pattern"], "intermittent_gaps")

    def test_missingness_pattern_diagnostics_groups_by_country_code_when_names_change(self):
        panel = pd.DataFrame(
            {
                "country_code": ["AAA", "AAA"],
                "country_name": ["Alpha", "Alpha, renamed"],
                "year": [2000, 2001],
                "feature_lag1_3_mean": [1.0, None],
            }
        )

        summary, detail = build_missingness_pattern_diagnostics(
            panel=panel,
            feature_columns=["feature_lag1_3_mean"],
        )

        self.assertEqual(len(detail), 1)
        self.assertEqual(detail.iloc[0]["country_code"], "AAA")
        self.assertEqual(detail.iloc[0]["country_name"], "Alpha")
        self.assertEqual(detail.iloc[0]["missingness_pattern"], "early_end")
        self.assertEqual(summary.iloc[0]["countries"], 1)
        self.assertEqual(summary.iloc[0]["early_end_countries"], 1)


if __name__ == "__main__":
    unittest.main()
