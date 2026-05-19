from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests


ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "2_data" / "raw"
PROCESSED_DIR = ROOT_DIR / "2_data" / "processed"

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

OECD_PATENT_DIMENSION_CODELISTS = {
    "UNIT_MEASURE": "CL_UNIT_MEASURE",
    "TYPE": "CL_TYPE_PAT_IND",
    "TECH": "CL_TECH_PAT",
    "PAT": "CL_PAT_PAT_DIFF",
}

OECD_PATENT_DIMENSION_LABELS = {
    "UNIT_MEASURE": "Indicator measure",
    "TYPE": "Patent counting type",
    "TECH": "Technological domain",
    "PAT": "Regional patent office",
}

OECD_PATENT_AVAILABLE_DIMENSION_FALLBACK = {
    "UNIT_MEASURE": [
        "INV_PS",
        "INV_RD_S13",
        "INV_RD_S1ZS",
        "IX",
        "PT_INV",
        "PT_TECH",
        "PT_TECH_COL",
        "PT_TECH_ENV",
    ],
    "TYPE": ["COL", "DEV", "DIFF", "RENEW"],
    "TECH": [
        "ADAPT",
        "BUILD",
        "ENE",
        "ENV_PAT",
        "GHG",
        "GOODS",
        "ICT",
        "MAN",
        "OCEAN",
        "TOT",
        "TRA",
        "WAT_WASTE",
    ],
    "PAT": ["_Z", "ARIPO", "EAPO", "EPO", "GCC", "OAPI", "PCT"],
}

OECD_PATENT_LABEL_FALLBACK = {
    "UNIT_MEASURE": {
        "INV_PS": "Inventions per person",
        "INV_RD_S13": "Inventions per unit of government R&D",
        "INV_RD_S1ZS": "Inventions per unit of public R&D",
        "IX": "Index",
        "PT_INV": "Percentage of inventions",
        "PT_TECH": "Percentage of technologies",
        "PT_TECH_COL": "Percentage of collaborations in all technologies",
        "PT_TECH_ENV": "Percentage of environment related technologies",
    },
    "TYPE": {
        "COL": "International collaboration in development of environment-related technologies",
        "DEV": "Development of environment-related technologies",
        "DIFF": "Diffusion of environment-related technologies",
        "RENEW": "Development of renewable energy technologies",
    },
    "TECH": {
        "ADAPT": "Climate change adaptation technologies",
        "BUILD": "Climate change mitigation technologies related to buildings",
        "ENE": "Climate change mitigation technologies related to energy generation, transmission or distribution",
        "ENV_PAT": "Environment-related technologies",
        "GHG": "Capture, storage, sequestration or disposal of greenhouse gases",
        "GOODS": "Climate change mitigation technologies in the production or processing of goods",
        "ICT": "Climate change mitigation in information and communication technologies (ICT)",
        "MAN": "Environmental management",
        "OCEAN": "Sustainable ocean economy",
        "TOT": "All technologies (total patents)",
        "TRA": "Climate change mitigation technologies related to transportation",
        "WAT_WASTE": "Climate change mitigation technologies related to wastewater treatment or waste management",
    },
    "PAT": {
        "_Z": "Not applicable",
        "ARIPO": "African Regional Industrial Property Organisation",
        "EAPO": "Eurasian Patent Organization",
        "EPO": "European Patent Office",
        "GCC": "Patent Office of the Cooperation Council for the Arab States of the Gulf",
        "OAPI": "African Intellectual Property Organization",
        "PCT": "Patent Cooperation Treaty",
    },
}

OECD_PATENT_BROAD_TECH_DOMAINS = [
    "ADAPT",
    "BUILD",
    "ENE",
    "GHG",
    "GOODS",
    "ICT",
    "MAN",
    "OCEAN",
    "TRA",
    "WAT_WASTE",
]


def filter_country_rows(data: pd.DataFrame) -> pd.DataFrame:
    filtered = data.copy()
    filtered["country_code"] = filtered["country_code"].fillna("").astype(str).str.strip()
    is_country_like = filtered["country_code"].str.len().eq(3)
    is_aggregate = filtered["country_code"].isin(AGGREGATE_AREA_CODES)
    return filtered[is_country_like & ~is_aggregate].reset_index(drop=True)


def fetch_text(url: str, timeout: int = 90) -> str:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def dataframe_to_markdown(data: pd.DataFrame) -> str:
    if data.empty:
        return "_No rows._"
    columns = list(data.columns)
    rows = []
    rows.append("| " + " | ".join(columns) + " |")
    rows.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for _, row in data.iterrows():
        values = ["" if pd.isna(row[column]) else str(row[column]) for column in columns]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def value_counts_frame(data: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    if data.empty or any(column not in data.columns for column in columns):
        return pd.DataFrame(columns=[*columns, "candidate_count"])
    return (
        data.groupby(columns, dropna=False)
        .size()
        .reset_index(name="candidate_count")
        .sort_values(columns)
    )


def select_existing_columns(data: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    existing = [column for column in columns if column in data.columns]
    return data.loc[:, existing] if existing else data.head(0).copy()
