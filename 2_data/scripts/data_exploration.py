from __future__ import annotations

import argparse
import json
from io import StringIO
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests


ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "2_data" / "raw"
PROCESSED_DIR = ROOT_DIR / "2_data" / "processed"

OECD_PAT_IND_BASE_URL = "https://sdmx.oecd.org/public/rest/data/OECD.ENV.EPI,DSD_PAT_IND@DF_PAT_IND,1.0"
OECD_EPS_URL = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.ECO.MAD,DSD_EPS@DF_EPS,1.0/.A..EPS"
    "?startPeriod=1990&endPeriod=2020&dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
)
WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2/country/all/indicator"

AGGREGATE_AREA_CODES = {
    "",
    "_Z",
    "AFE",
    "AFW",
    "ARB",
    "CEB",
    "CSS",
    "EAP",
    "EAR",
    "EAS",
    "ECA",
    "ECS",
    "EMU",
    "EU27",
    "EU27_2020",
    "EUU",
    "FCS",
    "HIC",
    "HPC",
    "IBD",
    "IBT",
    "IDA",
    "IDB",
    "IDX",
    "INX",
    "LAC",
    "LCN",
    "LDC",
    "LIC",
    "LMC",
    "LMY",
    "LTE",
    "MEA",
    "MIC",
    "MNA",
    "NAC",
    "OED",
    "OECD",
    "OECDA",
    "OECDE",
    "OECDSO",
    "OSS",
    "PRE",
    "PSS",
    "PST",
    "SAS",
    "SSA",
    "SSF",
    "SST",
    "TEA",
    "TEC",
    "TLA",
    "TMN",
    "TSA",
    "TSS",
    "UMC",
    "W",
    "WLD",
}

OECD_PATENT_TARGET_CANDIDATES = [
    {
        "variable": "env_patent_share_tech",
        "source_variable": "PT_TECH.DEV.ENV_PAT._Z",
        "unit_measure": "PT_TECH",
        "description": "Environment-related technologies as a percentage of all technologies.",
    },
    {
        "variable": "env_patent_share_inventions",
        "source_variable": "PT_INV.DEV.ENV_PAT._Z",
        "unit_measure": "PT_INV",
        "description": "Environment-related technologies as a percentage of inventions.",
    },
    {
        "variable": "env_patents_per_million",
        "source_variable": "INV_PS.DEV.ENV_PAT._Z",
        "unit_measure": "INV_PS",
        "description": "Environment-related inventions per million people.",
    },
]

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


def filter_country_rows(data: pd.DataFrame) -> pd.DataFrame:
    filtered = data.copy()
    filtered["country_code"] = filtered["country_code"].fillna("").astype(str).str.strip()
    is_country_like = filtered["country_code"].str.len().eq(3)
    is_aggregate = filtered["country_code"].isin(AGGREGATE_AREA_CODES)
    return filtered[is_country_like & ~is_aggregate].reset_index(drop=True)


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


def fetch_text(url: str, timeout: int = 90) -> str:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


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
    ]
    output_path.write_text("\n".join(text), encoding="utf-8")


def dataframe_to_markdown(data: pd.DataFrame) -> str:
    columns = list(data.columns)
    rows = []
    rows.append("| " + " | ".join(columns) + " |")
    rows.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for _, row in data.iterrows():
        values = ["" if pd.isna(row[column]) else str(row[column]) for column in columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def run_exploration(start_year: int, end_year: int) -> pd.DataFrame:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

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
