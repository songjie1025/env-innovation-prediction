from __future__ import annotations

import argparse
import json
from io import StringIO
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

import pandas as pd
import requests

from data_common import (
    AGGREGATE_AREA_CODES,
    OECD_PATENT_AVAILABLE_DIMENSION_FALLBACK,
    OECD_PATENT_BROAD_TECH_DOMAINS,
    OECD_PATENT_DIMENSION_CODELISTS,
    OECD_PATENT_DIMENSION_LABELS,
    OECD_PATENT_LABEL_FALLBACK,
    PROCESSED_DIR,
    RAW_DIR,
    ROOT_DIR,
    dataframe_to_markdown,
    fetch_text,
    filter_country_rows,
)

OECD_PAT_IND_BASE_URL = "https://sdmx.oecd.org/public/rest/data/OECD.ENV.EPI,DSD_PAT_IND@DF_PAT_IND,1.0"
OECD_PAT_IND_METADATA_URL = (
    "https://sdmx.oecd.org/public/rest/dataflow/"
    "OECD.ENV.EPI/DSD_PAT_IND@DF_PAT_IND/1.0?references=all"
)
OECD_EPS_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.ECO.MAD,DSD_EPS@DF_EPS,1.0/.A..EPS"
    "?startPeriod=1990&endPeriod=2020&dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
)
WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2/country/all/indicator"

OECD_PATENT_TARGET_CANDIDATES = [
    {
        "variable": "env_patent_share_tech",
        "source_variable": "PT_TECH.DEV.ENV_PAT._Z",
        "unit_measure": "PT_TECH",
        "description": "Environment-related technologies as a percentage of all technologies.",
        "measurement_note": "Percent share; normalized by the country's overall technology portfolio.",
        "selection_rationale": (
            "broad normalized target candidate for comparing the environment-related share "
            "of each country's technology portfolio."
        ),
    },
    {
        "variable": "env_patent_share_inventions",
        "source_variable": "PT_INV.DEV.ENV_PAT._Z",
        "unit_measure": "PT_INV",
        "description": "Environment-related technologies as a percentage of inventions.",
        "measurement_note": "Percent share; normalized by the country's overall invention output.",
        "selection_rationale": (
            "broad normalized target candidate for comparing the environment-related share "
            "of each country's invention output."
        ),
    },
    {
        "variable": "env_patents_per_million",
        "source_variable": "INV_PS.DEV.ENV_PAT._Z",
        "unit_measure": "INV_PS",
        "description": "Environment-related inventions per million people.",
        "measurement_note": (
            "OECD labels the unit as inventions per person; the downloaded CSV uses unit multiplier 6, "
            "so project outputs interpret the value as inventions per million people."
        ),
        "selection_rationale": (
            "broad size-normalized target candidate that keeps patent intensity visible "
            "without letting population dominate mechanically."
        ),
    },
]

SDMX_NAMESPACES = {
    "structure": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
    "common": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common",
}

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

WORLD_BANK_INDICATORS = {
    "gdp_per_capita": {
        "indicator": "NY.GDP.PCAP.KD",
        "description": "GDP per capita, constant 2015 US dollars.",
    },
    "gdp": {
        "indicator": "NY.GDP.MKTP.KD",
        "description": "GDP, constant 2015 US dollars.",
    },
    "population": {
        "indicator": "SP.POP.TOTL",
        "description": "Total population.",
    },
    "manufacturing_share": {
        "indicator": "NV.IND.MANF.ZS",
        "description": "Manufacturing value added as percent of GDP.",
    },
    "rd_expenditure_gdp": {
        "indicator": "GB.XPD.RSDV.GD.ZS",
        "description": "Research and development expenditure as percent of GDP.",
    },
    "researchers_per_million": {
        "indicator": "SP.POP.SCIE.RD.P6",
        "description": "Researchers in R&D per million people.",
    },
    "renewable_energy_share": {
        "indicator": "EG.FEC.RNEW.ZS",
        "description": "Renewable energy consumption as percent of final energy consumption.",
    },
    "fossil_energy_share": {
        "indicator": "EG.USE.COMM.FO.ZS",
        "description": "Fossil fuel energy consumption as percent of total energy use.",
    },
    "energy_intensity": {
        "indicator": "EG.EGY.PRIM.PP.KD",
        "description": "Energy intensity level of primary energy.",
    },
    "co2_per_capita": {
        "indicator": "EN.ATM.CO2E.PC",
        "description": "CO2 emissions per capita.",
        "source_id": 75,
    },
}


def summarize_panel_coverage(data: pd.DataFrame) -> pd.DataFrame:
    group_columns = ["dataset_id", "variable"]
    if "source_variable" in data.columns:
        group_columns.append("source_variable")

    rows = []
    for keys, group in data.groupby(group_columns, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        key_values = dict(zip(group_columns, keys))
        non_missing = group[group["value"].notna()]
        rows.append(
            {
                **key_values,
                "total_rows": int(len(group)),
                "non_missing_observations": int(len(non_missing)),
                "missing_observations": int(group["value"].isna().sum()),
                "countries_total": int(group["country_code"].nunique()),
                "countries_with_data": int(non_missing["country_code"].nunique()),
                "years_total": int(group["year"].nunique()),
                "years_with_data": int(non_missing["year"].nunique()),
                "first_year": int(non_missing["year"].min()) if not non_missing.empty else None,
                "last_year": int(non_missing["year"].max()) if not non_missing.empty else None,
            }
        )
    return pd.DataFrame(rows).sort_values(group_columns).reset_index(drop=True)


def world_bank_records_to_frame(
    records: Iterable[dict], variable: str, source_variable: str
) -> pd.DataFrame:
    rows = []
    for record in records:
        rows.append(
            {
                "dataset_id": "world_bank_wdi",
                "variable": variable,
                "source_variable": source_variable,
                "country_code": record.get("countryiso3code"),
                "country_name": (record.get("country") or {}).get("value"),
                "year": int(record["date"]),
                "value": record.get("value"),
            }
        )
    frame = pd.DataFrame(rows)
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame


def fetch_oecd_patent_metadata() -> str:
    return fetch_text(OECD_PAT_IND_METADATA_URL)


def read_oecd_csv(url: str) -> pd.DataFrame:
    return pd.read_csv(StringIO(fetch_text(url)))


def oecd_patent_url(unit_measure: str, start_year: int, end_year: int) -> str:
    data_selection = f".A.{unit_measure}.DEV.ENV_PAT._Z"
    return (
        f"{OECD_PAT_IND_BASE_URL}/{data_selection}"
        f"?startPeriod={start_year}&endPeriod={end_year}"
        "&dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
    )


def oecd_patent_frame(raw: pd.DataFrame, candidate: dict) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "dataset_id": "oecd_patents_environment",
            "variable": candidate["variable"],
            "source_variable": candidate["source_variable"],
            "country_code": raw["REF_AREA"],
            "country_name": raw["Reference area"],
            "year": pd.to_numeric(raw["TIME_PERIOD"], errors="coerce").astype("Int64"),
            "value": pd.to_numeric(raw["OBS_VALUE"], errors="coerce"),
        }
    )
    return frame.dropna(subset=["year"]).astype({"year": int})


def build_oecd_patent_catalog(xml_text: str | None = None) -> dict[str, pd.DataFrame]:
    """Build reusable OECD patent indicator metadata tables for notebooks."""
    labels = {dimension: values.copy() for dimension, values in OECD_PATENT_LABEL_FALLBACK.items()}
    available_codes = {
        dimension: list(codes) for dimension, codes in OECD_PATENT_AVAILABLE_DIMENSION_FALLBACK.items()
    }

    if xml_text:
        root = ET.fromstring(xml_text)
        labels.update(_extract_oecd_patent_codelist_labels(root))
        available_codes.update(_extract_oecd_patent_available_codes(root))

    dimension_values = _build_oecd_patent_dimension_values(available_codes, labels)
    technology_domains = _build_oecd_patent_technology_domains(available_codes, labels)
    technology_summary = _summarize_oecd_patent_technology_domains(technology_domains, labels)
    target_candidates = _build_oecd_patent_target_candidate_catalog(labels)

    return {
        "dimension_values": dimension_values,
        "technology_domains": technology_domains,
        "technology_category_summary": technology_summary,
        "target_candidates": target_candidates,
    }


def write_oecd_patent_catalog(catalog: dict[str, pd.DataFrame], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in catalog.items():
        data.to_csv(output_dir / f"oecd_patent_{name}.csv", index=False)


def _extract_oecd_patent_codelist_labels(root: ET.Element) -> dict[str, dict[str, str]]:
    labels = {}
    for dimension, codelist_id in OECD_PATENT_DIMENSION_CODELISTS.items():
        codelist = root.find(f".//structure:Codelist[@id='{codelist_id}']", SDMX_NAMESPACES)
        if codelist is None:
            continue
        labels[dimension] = {}
        for code in codelist.findall("structure:Code", SDMX_NAMESPACES):
            code_id = code.attrib["id"]
            labels[dimension][code_id] = _english_sdmx_name(code) or code_id
    return labels


def _extract_oecd_patent_available_codes(root: ET.Element) -> dict[str, list[str]]:
    available_codes = {}
    constraint = root.find(".//structure:ContentConstraint[@type='Actual']", SDMX_NAMESPACES)
    if constraint is None:
        return available_codes
    for key_value in constraint.findall(".//common:KeyValue", SDMX_NAMESPACES):
        dimension = key_value.attrib.get("id")
        if dimension not in OECD_PATENT_DIMENSION_CODELISTS:
            continue
        available_codes[dimension] = [
            value.text for value in key_value.findall("common:Value", SDMX_NAMESPACES) if value.text
        ]
    return available_codes


def _english_sdmx_name(element: ET.Element) -> str | None:
    names = element.findall("common:Name", SDMX_NAMESPACES)
    for name in names:
        if name.attrib.get(XML_LANG) == "en":
            return name.text
    return names[0].text if names else None


def _build_oecd_patent_dimension_values(
    available_codes: dict[str, list[str]], labels: dict[str, dict[str, str]]
) -> pd.DataFrame:
    rows = []
    for dimension, codes in available_codes.items():
        for position, code in enumerate(codes, start=1):
            rows.append(
                {
                    "dimension": dimension,
                    "dimension_label": OECD_PATENT_DIMENSION_LABELS.get(dimension, dimension),
                    "code": code,
                    "label": labels.get(dimension, {}).get(code, code),
                    "position": position,
                }
            )
    return pd.DataFrame(rows)


def _build_oecd_patent_target_candidate_catalog(labels: dict[str, dict[str, str]]) -> pd.DataFrame:
    rows = []
    for candidate in OECD_PATENT_TARGET_CANDIDATES:
        unit_measure, patent_type, tech_domain, patent_office = candidate["source_variable"].split(".")
        rows.append(
            {
                "variable": candidate["variable"],
                "source_variable": candidate["source_variable"],
                "unit_measure": unit_measure,
                "unit_measure_label": labels["UNIT_MEASURE"].get(unit_measure, unit_measure),
                "type": patent_type,
                "type_label": labels["TYPE"].get(patent_type, patent_type),
                "technology_domain": tech_domain,
                "technology_domain_label": labels["TECH"].get(tech_domain, tech_domain),
                "regional_patent_office": patent_office,
                "regional_patent_office_label": labels["PAT"].get(patent_office, patent_office),
                "description": candidate["description"],
                "measurement_note": candidate["measurement_note"],
                "selection_rationale": candidate["selection_rationale"],
            }
        )
    return pd.DataFrame(rows)


def _build_oecd_patent_technology_domains(
    available_codes: dict[str, list[str]], labels: dict[str, dict[str, str]]
) -> pd.DataFrame:
    tech_labels = labels.get("TECH", {})
    available_tech_codes = set(available_codes.get("TECH", []))
    rows = []
    for code, label in tech_labels.items():
        broad_code = _infer_broad_oecd_patent_technology_domain(code, available_tech_codes)
        rows.append(
            {
                "code": code,
                "label": label,
                "broad_domain_code": broad_code,
                "broad_domain_label": tech_labels.get(broad_code, broad_code),
                "available_in_indicator_data": code in available_tech_codes,
                "domain_role": _technology_domain_role(code, broad_code, available_tech_codes),
            }
        )
    data = pd.DataFrame(rows)
    role_order = {
        "overall environment-related total": 0,
        "all technologies denominator": 1,
        "available broad environment subdomain": 2,
        "metadata subdomain under available broad domain": 3,
        "climate mitigation umbrella": 4,
        "metadata technology domain": 5,
    }
    data["role_order"] = data["domain_role"].map(role_order).fillna(99).astype(int)
    return data.sort_values(["role_order", "broad_domain_code", "code"]).drop(columns="role_order").reset_index(
        drop=True
    )


def _infer_broad_oecd_patent_technology_domain(code: str, available_tech_codes: set[str]) -> str:
    if code in {"NA", "TOT", "ENV_PAT", "CCM"}:
        return code
    candidate_broad_domains = [
        domain
        for domain in OECD_PATENT_BROAD_TECH_DOMAINS
        if domain in available_tech_codes or domain in OECD_PATENT_LABEL_FALLBACK["TECH"]
    ]
    for domain in sorted(candidate_broad_domains, key=len, reverse=True):
        if code == domain or code.startswith(f"{domain}_"):
            return domain
    return code


def _technology_domain_role(code: str, broad_code: str, available_tech_codes: set[str]) -> str:
    if code == "ENV_PAT":
        return "overall environment-related total"
    if code == "TOT":
        return "all technologies denominator"
    if code == "CCM":
        return "climate mitigation umbrella"
    if code in OECD_PATENT_BROAD_TECH_DOMAINS and code in available_tech_codes:
        return "available broad environment subdomain"
    if broad_code in OECD_PATENT_BROAD_TECH_DOMAINS and code != broad_code:
        return "metadata subdomain under available broad domain"
    return "metadata technology domain"


def _summarize_oecd_patent_technology_domains(
    technology_domains: pd.DataFrame, labels: dict[str, dict[str, str]]
) -> pd.DataFrame:
    rows = []
    for broad_code in OECD_PATENT_BROAD_TECH_DOMAINS:
        group = technology_domains[technology_domains["broad_domain_code"].eq(broad_code)]
        if group.empty:
            continue
        detailed = group[~group["code"].eq(broad_code)]
        rows.append(
            {
                "broad_domain_code": broad_code,
                "broad_domain_label": labels["TECH"].get(broad_code, broad_code),
                "available_in_indicator_data": bool(group["available_in_indicator_data"].any()),
                "metadata_subdomain_count": int(len(detailed)),
                "example_subdomains": "; ".join(detailed["label"].head(4).tolist()),
            }
        )
    return pd.DataFrame(rows)


def oecd_eps_frame(raw: pd.DataFrame) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "dataset_id": "oecd_eps",
            "variable": "eps_index",
            "source_variable": "POL_STRINGENCY.EPS",
            "country_code": raw["REF_AREA"],
            "country_name": raw["Reference area"],
            "year": pd.to_numeric(raw["TIME_PERIOD"], errors="coerce").astype("Int64"),
            "value": pd.to_numeric(raw["OBS_VALUE"], errors="coerce"),
        }
    )
    return frame.dropna(subset=["year"]).astype({"year": int})


def fetch_world_bank_indicator(
    variable: str, source_variable: str, start_year: int, end_year: int, source_id: int | None = None
) -> tuple[pd.DataFrame, dict]:
    url = world_bank_indicator_url(source_variable, start_year, end_year, source_id)
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError(f"Unexpected World Bank response for {source_variable}")
    metadata = payload[0]
    records = payload[1]
    return world_bank_records_to_frame(records, variable, source_variable), metadata


def world_bank_indicator_url(
    source_variable: str, start_year: int, end_year: int, source_id: int | None = None
) -> str:
    url = (
        f"{WORLD_BANK_BASE_URL}/{source_variable}"
        f"?format=json&per_page=20000&date={start_year}:{end_year}"
    )
    if source_id is not None:
        url += f"&source={source_id}"
    return url


def write_markdown_summary(summary: pd.DataFrame, output_path: Path) -> None:
    compact = summary[
        [
            "dataset_id",
            "variable",
            "source_variable",
            "non_missing_observations",
            "countries_with_data",
            "first_year",
            "last_year",
        ]
    ].copy()
    text = [
        "# Data Source Exploration Summary",
        "",
        "This file is generated by `2_data/scripts/data_exploration.py`.",
        "",
        "Raw downloads are stored in `2_data/raw/` and are not committed.",
        "",
        "## Coverage Summary",
        "",
        dataframe_to_markdown(compact),
        "",
        "## Notes",
        "",
        "1. Coverage counts exclude common aggregate areas such as `WLD`, `OECD`, and World Bank regional aggregates.",
        "2. The OECD target candidates are exploratory. The final target must be recorded in `0_organization/decision_log.md`.",
        "3. World Bank data are downloaded for candidate predictors only; inclusion in the final model is not decided here.",
        "",
        "## Related OECD Metadata Outputs",
        "",
        "The script also writes structured OECD patent indicator metadata tables:",
        "",
        "1. `2_data/processed/oecd_patent_dimension_values.csv`",
        "2. `2_data/processed/oecd_patent_target_candidates.csv`",
        "3. `2_data/processed/oecd_patent_technology_domains.csv`",
        "4. `2_data/processed/oecd_patent_technology_category_summary.csv`",
        "",
    ]
    output_path.write_text("\n".join(text), encoding="utf-8")


def run_exploration(start_year: int, end_year: int) -> pd.DataFrame:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    metadata_text = fetch_oecd_patent_metadata()
    (RAW_DIR / "oecd_patents_indicator_metadata.xml").write_text(metadata_text, encoding="utf-8")
    write_oecd_patent_catalog(build_oecd_patent_catalog(metadata_text), PROCESSED_DIR)

    frames = []

    for candidate in OECD_PATENT_TARGET_CANDIDATES:
        url = oecd_patent_url(candidate["unit_measure"], start_year, min(end_year, 2023))
        raw = read_oecd_csv(url)
        raw_path = RAW_DIR / f"oecd_patents_{candidate['variable']}_{start_year}_{min(end_year, 2023)}.csv"
        raw.to_csv(raw_path, index=False)
        frames.append(filter_country_rows(oecd_patent_frame(raw, candidate)))

    eps_raw = read_oecd_csv(OECD_EPS_URL)
    eps_raw.to_csv(RAW_DIR / "oecd_eps_1990_2020.csv", index=False)
    frames.append(filter_country_rows(oecd_eps_frame(eps_raw)))

    wb_metadata = {}
    for variable, config in WORLD_BANK_INDICATORS.items():
        frame, metadata = fetch_world_bank_indicator(
            variable, config["indicator"], start_year, end_year, config.get("source_id")
        )
        wb_metadata[variable] = {
            "indicator": config["indicator"],
            "description": config["description"],
            "source_id": config.get("source_id", 2),
            "lastupdated": metadata.get("lastupdated"),
            "total": metadata.get("total"),
        }
        raw_path = RAW_DIR / f"world_bank_{variable}_{config['indicator']}_{start_year}_{end_year}.csv"
        frame.to_csv(raw_path, index=False)
        frames.append(filter_country_rows(frame))

    (RAW_DIR / "world_bank_metadata.json").write_text(
        json.dumps(wb_metadata, indent=2, sort_keys=True), encoding="utf-8"
    )

    combined = pd.concat(frames, ignore_index=True)
    summary = summarize_panel_coverage(combined)
    summary_path = PROCESSED_DIR / "data_availability.csv"
    summary.to_csv(summary_path, index=False)
    write_markdown_summary(summary, PROCESSED_DIR / "data_exploration_summary.md")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Explore candidate project data sources.")
    parser.add_argument("--start-year", type=int, default=1990)
    parser.add_argument("--end-year", type=int, default=2024)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_exploration(args.start_year, args.end_year)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
