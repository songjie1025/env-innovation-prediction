import unittest

import pandas as pd

from raw_data_download import build_literature_predictor_download_plan
from data_exploration import (
    build_oecd_patent_catalog,
    filter_country_rows,
    summarize_panel_coverage,
    world_bank_indicator_url,
    world_bank_records_to_frame,
)


class DataExplorationTests(unittest.TestCase):
    def test_literature_oecd_tax_sources_are_machine_downloadable_without_carbon_energy_prices(self):
        data = pd.DataFrame(
            [
                {
                    "paper name ": "Energy prices paper",
                    "predictors used": "Carbon / Energy Prices",
                    "Indicator Data Code": "no WDI-Data",
                    "comments": "Poor data coverage and high collection costs",
                },
                {
                    "paper name ": "Carbon tax paper",
                    "predictors used": "carbon tax",
                    "Indicator Data Code": (
                        "https://www.oecd.org/en/data/datasets/"
                        "carbon-pricing-and-energy-taxation-database.html"
                    ),
                    "comments": "",
                },
                {
                    "paper name ": "Environmental tax paper",
                    "predictors used": "Environmental tax revenue",
                    "Indicator Data Code": "https://www.oecd.org/en/data/indicators/environmental-tax.html",
                    "comments": "",
                },
            ]
        )

        with pd.option_context("mode.copy_on_write", True):
            from tempfile import TemporaryDirectory
            from pathlib import Path

            with TemporaryDirectory() as tmp:
                path = Path(tmp) / "literature.csv"
                data.to_csv(path, index=False)
                plan = build_literature_predictor_download_plan(path, 1990, 2024)

        by_variable = {entry["variable"]: entry for entry in plan}
        self.assertNotIn("carbon_energy_prices", by_variable)
        self.assertEqual(by_variable["carbon_tax"]["dataset_id"], "oecd_carbon_pricing")
        self.assertEqual(by_variable["environmental_tax_revenue"]["dataset_id"], "oecd_environment_tax")
        self.assertTrue(by_variable["carbon_tax"]["source_variable"].startswith("OECD.CTP.TPS,"))
        self.assertTrue(by_variable["environmental_tax_revenue"]["source_variable"].startswith("OECD.ENV.EPI,"))
        self.assertNotIn("unsupported_source", {entry["dataset_id"] for entry in plan})

    def test_summarize_panel_coverage_counts_non_missing_values(self):
        data = pd.DataFrame(
            {
                "dataset_id": ["demo"] * 5,
                "variable": ["x"] * 5,
                "country_code": ["AAA", "AAA", "BBB", "BBB", "CCC"],
                "year": [2000, 2001, 2000, 2001, 2001],
                "value": [1.0, None, 2.0, 3.0, None],
            }
        )

        summary = summarize_panel_coverage(data)

        self.assertEqual(len(summary), 1)
        row = summary.iloc[0]
        self.assertEqual(row["dataset_id"], "demo")
        self.assertEqual(row["variable"], "x")
        self.assertEqual(row["non_missing_observations"], 3)
        self.assertEqual(row["countries_with_data"], 2)
        self.assertEqual(row["first_year"], 2000)
        self.assertEqual(row["last_year"], 2001)

    def test_world_bank_records_to_frame_extracts_country_year_values(self):
        records = [
            {
                "countryiso3code": "DEU",
                "country": {"value": "Germany"},
                "date": "2020",
                "value": 123.4,
            },
            {
                "countryiso3code": "USA",
                "country": {"value": "United States"},
                "date": "2020",
                "value": None,
            },
        ]

        frame = world_bank_records_to_frame(records, "gdp_per_capita", "NY.GDP.PCAP.KD")

        self.assertEqual(list(frame["country_code"]), ["DEU", "USA"])
        self.assertEqual(list(frame["country_name"]), ["Germany", "United States"])
        self.assertEqual(list(frame["year"]), [2020, 2020])
        self.assertEqual(list(frame["variable"]), ["gdp_per_capita", "gdp_per_capita"])
        self.assertEqual(list(frame["source_variable"]), ["NY.GDP.PCAP.KD", "NY.GDP.PCAP.KD"])

    def test_filter_country_rows_removes_world_bank_aggregates(self):
        data = pd.DataFrame(
            {
                "country_code": ["DEU", "USA", "WLD", "AFE", ""],
                "country_name": ["Germany", "United States", "World", "Africa Eastern and Southern", "Unknown"],
                "year": [2020, 2020, 2020, 2020, 2020],
                "value": [1, 2, 3, 4, 5],
            }
        )

        filtered = filter_country_rows(data)

        self.assertEqual(list(filtered["country_code"]), ["DEU", "USA"])

    def test_world_bank_indicator_url_can_pin_source(self):
        url = world_bank_indicator_url("EN.ATM.CO2E.PC", 1990, 2024, source_id=75)

        self.assertIn("source=75", url)
        self.assertIn("EN.ATM.CO2E.PC", url)
        self.assertIn("date=1990:2024", url)

    def test_build_oecd_patent_catalog_extracts_available_dimensions(self):
        xml_text = """<?xml version="1.0" encoding="utf-8"?>
        <message:Structure
            xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
            xmlns:structure="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"
            xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
          <message:Structures>
            <structure:Codelists>
              <structure:Codelist id="CL_UNIT_MEASURE">
                <structure:Code id="PT_TECH"><common:Name xml:lang="en">Percentage of technologies</common:Name></structure:Code>
                <structure:Code id="PT_INV"><common:Name xml:lang="en">Percentage of inventions</common:Name></structure:Code>
              </structure:Codelist>
              <structure:Codelist id="CL_TYPE_PAT_IND">
                <structure:Code id="DEV"><common:Name xml:lang="en">Development of environment-related technologies</common:Name></structure:Code>
              </structure:Codelist>
              <structure:Codelist id="CL_TECH_PAT">
                <structure:Code id="ENV_PAT"><common:Name xml:lang="en">Environment-related technologies</common:Name></structure:Code>
                <structure:Code id="ENE"><common:Name xml:lang="en">Energy generation, transmission or distribution</common:Name></structure:Code>
                <structure:Code id="ENE_RE"><common:Name xml:lang="en">Renewable energy generation</common:Name></structure:Code>
              </structure:Codelist>
              <structure:Codelist id="CL_PAT_PAT_DIFF">
                <structure:Code id="_Z"><common:Name xml:lang="en">Not applicable</common:Name></structure:Code>
              </structure:Codelist>
            </structure:Codelists>
            <structure:Constraints>
              <structure:ContentConstraint id="CR_A_DSD_PAT_IND@DF_PAT_IND" type="Actual">
                <structure:CubeRegion include="true">
                  <common:KeyValue id="UNIT_MEASURE">
                    <common:Value>PT_TECH</common:Value>
                    <common:Value>PT_INV</common:Value>
                  </common:KeyValue>
                  <common:KeyValue id="TYPE"><common:Value>DEV</common:Value></common:KeyValue>
                  <common:KeyValue id="TECH">
                    <common:Value>ENV_PAT</common:Value>
                    <common:Value>ENE</common:Value>
                  </common:KeyValue>
                  <common:KeyValue id="PAT"><common:Value>_Z</common:Value></common:KeyValue>
                </structure:CubeRegion>
              </structure:ContentConstraint>
            </structure:Constraints>
          </message:Structures>
        </message:Structure>
        """

        catalog = build_oecd_patent_catalog(xml_text)

        dimension_values = catalog["dimension_values"]
        unit_rows = dimension_values[dimension_values["dimension"].eq("UNIT_MEASURE")]
        self.assertEqual(set(unit_rows["code"]), {"PT_TECH", "PT_INV"})
        self.assertIn("Percentage of technologies", set(unit_rows["label"]))

        technology_domains = catalog["technology_domains"]
        env_total = technology_domains[technology_domains["code"].eq("ENV_PAT")].iloc[0]
        renewable = technology_domains[technology_domains["code"].eq("ENE_RE")].iloc[0]
        self.assertEqual(env_total["domain_role"], "overall environment-related total")
        self.assertEqual(renewable["broad_domain_code"], "ENE")
        self.assertFalse(bool(renewable["available_in_indicator_data"]))

    def test_build_oecd_patent_catalog_describes_target_candidates(self):
        catalog = build_oecd_patent_catalog()
        candidates = catalog["target_candidates"]

        self.assertEqual(
            set(candidates["source_variable"]),
            {
                "PT_TECH.DEV.ENV_PAT._Z",
                "PT_INV.DEV.ENV_PAT._Z",
                "INV_PS.DEV.ENV_PAT._Z",
            },
        )
        rationale_by_source = candidates.set_index("source_variable")["selection_rationale"]
        self.assertIn(
            "worldwide environment-related invention pool",
            rationale_by_source["PT_INV.DEV.ENV_PAT._Z"],
        )
        self.assertIn("diagnostic domestic portfolio-share", rationale_by_source["PT_TECH.DEV.ENV_PAT._Z"])
        self.assertIn("size-normalized", rationale_by_source["INV_PS.DEV.ENV_PAT._Z"])


if __name__ == "__main__":
    unittest.main()
