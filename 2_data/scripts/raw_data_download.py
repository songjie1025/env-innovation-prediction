from __future__ import annotations

import argparse
from collections.abc import Callable
from datetime import date
from io import StringIO
from pathlib import Path
import re
from time import sleep
from typing import Any

import pandas as pd
import requests

from data_common import RAW_PREDICTORS_V1_DIR, ROOT_DIR, read_xlsx_sheet
from data_exploration import (
    OECD_EPS_URL,
    OECD_PAT_IND_BASE_URL,
    fetch_world_bank_indicator,
    world_bank_indicator_url,
)

LITERATURE_CSV_PATH = ROOT_DIR / "1_literature_review" / "Managerial AI- literature review - List 1.csv"
RISE_DATA360_CSV_URL = "https://data360files.worldbank.org/data360-data/data/WB_RISE/WB_RISE.csv"
EPU_ALL_COUNTRY_XLSX_URL = "https://www.policyuncertainty.com/media/All_Country_Data.xlsx"
WORLD_BANK_WDI_SOURCE_ID = 2
WORLD_BANK_WGI_SOURCE_ID = 3
OECD_SDMX_CSV_QUERY = "dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
OECD_RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
OECD_REQUEST_ATTEMPTS = 6
OECD_REQUEST_BACKOFF_SECONDS = 5
OECD_SUCCESS_PAUSE_SECONDS = 2

WORLD_BANK_CODE_PATTERN = re.compile(r"(?:\(WDI\)\s*|data\.worldbank\.org/indicator/)([A-Z0-9][A-Z0-9.]+)")
EXCLUDED_WORLD_BANK_CODES = {
    "IP.PAT.RESD",
    "EG.EGY.PRIM.PP.KD",
    "SP.POP.TOTL",
}

WORLD_BANK_LITERATURE_INDICATORS = {
    "GB.XPD.RSDV.GD.ZS": {
        "variable": "rd_expenditure_gdp",
        "description": "Research and development expenditure as percent of GDP.",
    },
    "SP.POP.SCIE.RD.P6": {
        "variable": "researchers_per_million",
        "description": "Researchers in R&D per million people.",
    },
    "SE.TER.ENRR": {
        "variable": "tertiary_enrollment",
        "description": "Gross tertiary school enrollment ratio.",
    },
    "IP.JRN.ARTC.SC": {
        "variable": "scientific_journal_articles",
        "description": "Scientific and technical journal articles.",
    },
    "TX.VAL.TECH.MF.ZS": {
        "variable": "high_tech_exports",
        "description": "High-technology exports as percent of manufactured exports.",
    },
    "EG.FEC.RNEW.ZS": {
        "variable": "renewable_energy_share",
        "description": "Renewable energy consumption as percent of final energy consumption.",
    },
    "EN.GHG.CO2.PC.CE.AR5": {
        "variable": "co2_per_capita_ar5",
        "description": "CO2 emissions per capita using AR5 climate source.",
    },
    "EG.USE.COMM.FO.ZS": {
        "variable": "fossil_energy_share",
        "description": "Fossil fuel energy consumption as percent of total energy use.",
    },
    "EG.IMP.CONS.ZS": {
        "variable": "energy_imports_net",
        "description": "Net energy imports as percent of energy use.",
    },
    "NE.TRD.GNFS.ZS": {
        "variable": "trade_openness",
        "description": "Trade as percent of GDP.",
    },
    "FP.CPI.TOTL.ZG": {
        "variable": "inflation",
        "description": "Inflation, consumer prices, annual percent.",
    },
    "NY.GDP.MKTP.KD": {
        "variable": "gdp_constant_2015_usd",
        "description": "GDP, constant 2015 US dollars.",
    },
    "BX.KLT.DINV.CD.WD": {
        "variable": "fdi_net_inflows",
        "description": "Foreign direct investment, net inflows, current US dollars.",
    },
}

WGI_REGULATORY_QUALITY = {
    "dataset_id": "world_bank_wgi",
    "variable": "wgi_regulatory_quality",
    "source_variable": "GOV_WGI_RQ.EST",
    "source": "World Bank Worldwide Governance Indicators",
    "source_id": WORLD_BANK_WGI_SOURCE_ID,
    "role": "literature_predictor",
    "description": "Regulatory Quality governance estimate, approximately -2.5 to 2.5.",
    "notes": "Selected WGI Regulatory Quality predictor.",
}

RISE_SELECTED_INDICATOR_GROUPS = [
    {
        "variable": "rise_renewable_energy",
        "source_variable": "WB_RISE_RE_*",
        "indicator_prefix": "WB_RISE_RE_",
        "description": "RISE renewable energy score and sub-indicators.",
        "file_name": "world_bank_data360_rise_renewable_energy_WB_RISE_RE_2010_2023.csv",
    },
    {
        "variable": "rise_energy_efficiency",
        "source_variable": "WB_RISE_EE_*",
        "indicator_prefix": "WB_RISE_EE_",
        "description": "RISE energy efficiency score and sub-indicators.",
        "file_name": "world_bank_data360_rise_energy_efficiency_WB_RISE_EE_2010_2023.csv",
    },
]

RAW_TARGETS = [
    {
        "dataset_id": "oecd_patents_environment",
        "variable": "env_patent_share_inventions",
        "source_variable": "PT_INV.DEV.ENV_PAT._Z",
        "source": "OECD Patents - indicators",
        "role": "main_target",
        "unit_measure": "PT_INV",
        "description": "Environment-related technologies as a percentage of inventions.",
    },
    {
        "dataset_id": "oecd_patents_environment",
        "variable": "env_patents_per_million",
        "source_variable": "INV_PS.DEV.ENV_PAT._Z",
        "source": "OECD Patents - indicators",
        "role": "robustness_target",
        "unit_measure": "INV_PS",
        "description": "Environment-related inventions per million people.",
    },
]

SELECTED_PREDICTORS = [
    {
        "dataset_id": "world_bank_wdi",
        "variable": "gdp_constant_2015_usd",
        "source_variable": "NY.GDP.MKTP.KD",
        "source": "World Bank WDI",
        "role": "main_predictor",
        "description": "GDP, constant 2015 US dollars.",
    },
    {
        "dataset_id": "world_bank_wdi",
        "variable": "rd_expenditure_gdp",
        "source_variable": "GB.XPD.RSDV.GD.ZS",
        "source": "World Bank WDI",
        "role": "main_predictor",
        "description": "Research and development expenditure as percent of GDP.",
    },
    {
        "dataset_id": "world_bank_wdi",
        "variable": "renewable_energy_share",
        "source_variable": "EG.FEC.RNEW.ZS",
        "source": "World Bank WDI",
        "role": "main_predictor",
        "description": "Renewable energy consumption as percent of final energy consumption.",
    },
    {
        "dataset_id": "oecd_eps",
        "variable": "eps_index",
        "source_variable": "POL_STRINGENCY.EPS",
        "source": "OECD Environmental Policy Stringency index",
        "role": "policy_robustness_predictor",
        "description": "Environmental Policy Stringency index on a 0-6 scale.",
    },
]


def safe_source_name(source_variable: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in source_variable)


def build_raw_download_plan(
    start_year: int,
    end_year: int,
    literature_csv_path: Path = LITERATURE_CSV_PATH,
) -> list[dict[str, Any]]:
    entries = []
    for target in RAW_TARGETS:
        source_end_year = min(end_year, 2023)
        entries.append(
            {
                **target,
                "start_year": start_year,
                "end_year": source_end_year,
                "url": oecd_patent_source_url(target["source_variable"], start_year, source_end_year),
                "file_name": _raw_file_name(target, start_year, source_end_year),
                "status": "planned",
                "download_method": "tabular",
                "file_format": "csv",
                "notes": "",
            }
        )

    entries.extend(build_literature_predictor_download_plan(literature_csv_path, start_year, end_year))
    return _deduplicate_plan_entries(entries)


def build_literature_predictor_download_plan(
    literature_csv_path: Path = LITERATURE_CSV_PATH,
    start_year: int = 1990,
    end_year: int = 2024,
) -> list[dict[str, Any]]:
    literature = pd.read_csv(literature_csv_path).fillna("")
    entries: list[dict[str, Any]] = []

    for row_index, row in literature.iterrows():
        predictor_text = _clean_cell(row.get("predictors used", ""))
        code_text = _clean_cell(row.get("Indicator Data Code", ""))
        comments = _clean_cell(row.get("comments", ""))
        paper_name = _clean_cell(row.get("paper name ", ""))
        row_number = row_index + 2
        combined_text = " ".join([paper_name, predictor_text, code_text, comments])
        predictor_code_text = " ".join([predictor_text, code_text]).lower()

        if _is_non_predictor_row(predictor_text, code_text, comments):
            continue

        world_bank_codes = _extract_world_bank_codes(combined_text)
        for source_variable in world_bank_codes:
            if source_variable in EXCLUDED_WORLD_BANK_CODES:
                continue
            entries.append(
                _world_bank_literature_entry(
                    source_variable,
                    predictor_text,
                    row_number,
                    start_year,
                    end_year,
                    comments,
                )
            )

        lower_text = combined_text.lower()
        if _mentions_eps(predictor_code_text):
            entries.append(
                _oecd_eps_entry(
                    predictor_text or "Environmental Policy Stringency",
                    row_number,
                    start_year,
                    end_year,
                    comments,
                )
            )
        if "policy stability" in predictor_text.lower():
            entries.append(
                _oecd_eps_entry(
                    predictor_text or "Policy Stability",
                    row_number,
                    start_year,
                    end_year,
                    "Derived from rolling five-year EPS volatility. " + comments,
                )
            )
        if "rise" in lower_text:
            entries.extend(_rise_entries(predictor_text or "RISE score", row_number, comments))
        if "economic policy uncertainty" in predictor_code_text:
            entries.append(_epu_entry(predictor_text or "Economic Policy Uncertainty Index", row_number, comments))
        if "env tech rta" in lower_text or "env_tech" in lower_text:
            entries.append(
                _oecd_patent_literature_entry(
                    variable="env_technology_rta",
                    source_variable="IX.DEV.ENV_PAT._Z",
                    description=(
                        "OECD environment-related technology specialization index used as "
                        "the lagged environmental-technology RTA predictor."
                    ),
                    predictor_text=predictor_text or "Lagged Env Tech RTA",
                    row_number=row_number,
                    start_year=start_year,
                    end_year=end_year,
                    comments=comments,
                )
            )
        if "co-invention" in lower_text or "international collaboration" in lower_text:
            entries.append(
                _oecd_patent_literature_entry(
                    variable="env_co_invention_share",
                    source_variable="PT_TECH_COL.COL.ENV_PAT._Z",
                    description="OECD environment-related international collaboration share used as raw support for co-invention rates.",
                    predictor_text=predictor_text or "Co-invention rate",
                    row_number=row_number,
                    start_year=start_year,
                    end_year=end_year,
                    comments=comments,
                )
            )
        if "carbon tax" in predictor_code_text or "carbon-pricing-and-energy-taxation" in lower_text:
            entries.append(
                _oecd_sdmx_literature_entry(
                    dataset_id="oecd_carbon_pricing",
                    variable="carbon_tax",
                    source_variable="OECD.CTP.TPS,DSD_NECR@DF_NECRS,1.1/.ENE.FFUEL.CARBTAX._Z.EUR_TCO2.MEANW.V.A",
                    source="OECD Net Effective Carbon Rates",
                    role="literature_predictor",
                    description=(
                        "Carbon tax rate for energy-use sectors and fossil fuels, "
                        "weighted mean in EUR per tonne of CO2."
                    ),
                    predictor_text=predictor_text,
                    row_number=row_number,
                    start_year=start_year,
                    end_year=end_year,
                    comments=comments,
                )
            )
        if "environmental tax revenue" in predictor_code_text or "environmental-tax" in lower_text:
            entries.append(
                _oecd_sdmx_literature_entry(
                    dataset_id="oecd_environment_tax",
                    variable="environmental_tax_revenue",
                    source_variable="OECD.ENV.EPI,DSD_ERTR@DF_ERTR,1.0/A..TAXREV._T._T.PT_B1GQ._Z",
                    source="OECD Environmentally Related Tax Revenue",
                    role="literature_predictor",
                    description="Total environmentally related tax revenue as percent of GDP.",
                    predictor_text=predictor_text,
                    row_number=row_number,
                    start_year=start_year,
                    end_year=end_year,
                    comments=comments,
                )
            )
        if _requires_unsupported_manifest_row(lower_text, world_bank_codes):
            entries.append(_unsupported_literature_entry(predictor_text, code_text, row_number, comments))

    entries.append(_wgi_entry("Regulatory Quality", "", start_year, end_year, ""))
    return _deduplicate_plan_entries(entries)


def run_raw_download(
    start_year: int = 1990,
    end_year: int = 2024,
    raw_dir: Path = RAW_PREDICTORS_V1_DIR,
    fetcher: Callable[[dict[str, Any]], pd.DataFrame] | None = None,
    plan_builder: Callable[[int, int], list[dict[str, Any]]] | None = None,
    continue_on_error: bool = True,
    refresh: bool = False,
) -> pd.DataFrame:
    raw_dir.mkdir(parents=True, exist_ok=True)
    fetch = fetcher or fetch_raw_entry
    plan = plan_builder(start_year, end_year) if plan_builder else build_raw_download_plan(start_year, end_year)

    rows = []
    for entry in plan:
        output_path = raw_dir / entry["file_name"] if entry.get("file_name") else None
        status = entry.get("status", "planned")
        row_count = 0
        column_count = 0
        file_size = 0
        content_type = ""

        try:
            if status == "not_downloaded":
                file_path = ""
            elif output_path is not None and output_path.exists() and not refresh:
                file_path = str(output_path)
                file_size = output_path.stat().st_size
                row_count, column_count = _read_file_shape(output_path, entry.get("file_format", "csv"))
                status = "downloaded"
            elif entry.get("download_method") == "binary":
                if output_path is None:
                    raise ValueError(f"Binary entry missing file_name: {entry}")
                content_type, file_size = download_binary_entry(entry, output_path)
                row_count, column_count = _read_file_shape(output_path, entry.get("file_format", ""))
                file_path = str(output_path)
                status = "downloaded"
            else:
                if output_path is None:
                    raise ValueError(f"Tabular entry missing file_name: {entry}")
                data = fetch(entry)
                data.to_csv(output_path, index=False)
                row_count = int(len(data))
                column_count = int(len(data.columns))
                file_size = output_path.stat().st_size
                file_path = str(output_path)
                status = "downloaded"
                if entry["dataset_id"].startswith("oecd_"):
                    sleep(OECD_SUCCESS_PAUSE_SECONDS)
        except Exception as exc:
            if not continue_on_error:
                raise
            file_path = ""
            status = "error"
            entry["notes"] = _join_unique(entry.get("notes", ""), f"{type(exc).__name__}: {exc}")

        rows.append(
            {
                "dataset_id": entry["dataset_id"],
                "variable": entry["variable"],
                "source_variable": entry["source_variable"],
                "role": entry["role"],
                "source": entry["source"],
                "start_year": entry["start_year"],
                "end_year": entry["end_year"],
                "rows": row_count,
                "columns": column_count,
                "status": status,
                "source_url": entry["url"],
                "file_path": file_path,
                "download_date": date.today().isoformat(),
                "download_method": entry.get("download_method", "tabular"),
                "file_format": entry.get("file_format", "csv"),
                "file_size_bytes": file_size,
                "content_type": content_type,
                "indicator_prefix": entry.get("indicator_prefix", ""),
                "literature_rows": entry.get("literature_rows", ""),
                "literature_predictors": entry.get("literature_predictors", ""),
                "notes": entry.get("notes", ""),
            }
        )

    manifest = pd.DataFrame(rows)
    manifest.to_csv(raw_dir / "raw_download_manifest.csv", index=False)
    return manifest


def fetch_raw_entry(entry: dict[str, Any]) -> pd.DataFrame:
    if entry["dataset_id"] == "oecd_patents_environment":
        return read_oecd_csv_with_retries(entry["url"])
    if entry["dataset_id"] == "oecd_eps":
        return read_oecd_csv_with_retries(entry["url"])
    if entry["dataset_id"] in {"oecd_carbon_pricing", "oecd_environment_tax"}:
        return read_oecd_csv_with_retries(entry["url"])
    if entry["dataset_id"] in {"world_bank_wdi", "world_bank_wgi"}:
        source_id = entry.get("source_id")
        data, _ = fetch_world_bank_indicator_with_retries(
            entry["variable"],
            entry["source_variable"],
            entry["start_year"],
            entry["end_year"],
            source_id,
        )
        data["dataset_id"] = entry["dataset_id"]
        return data
    if entry["dataset_id"] == "world_bank_data360":
        data = pd.read_csv(entry["url"], low_memory=False)
        indicator_prefix = entry.get("indicator_prefix", "")
        if indicator_prefix:
            data = data[data["INDICATOR"].astype(str).str.startswith(indicator_prefix)].reset_index(drop=True)
        return data
    raise ValueError(f"Unsupported dataset_id: {entry['dataset_id']}")


def read_oecd_csv_with_retries(
    url: str,
    attempts: int = OECD_REQUEST_ATTEMPTS,
    backoff_seconds: int = OECD_REQUEST_BACKOFF_SECONDS,
) -> pd.DataFrame:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        response: requests.Response | None = None
        try:
            response = requests.get(url, timeout=90)
            response.raise_for_status()
            return pd.read_csv(StringIO(response.text))
        except requests.exceptions.HTTPError as exc:
            last_error = exc
            if response is not None and response.status_code not in OECD_RETRY_STATUS_CODES:
                raise
        except requests.exceptions.RequestException as exc:
            last_error = exc

        if attempt < attempts:
            sleep(_retry_delay_seconds(response, attempt, backoff_seconds))

    if last_error is not None:
        raise last_error
    raise RuntimeError("OECD request failed without an exception")


def fetch_world_bank_indicator_with_retries(
    variable: str,
    source_variable: str,
    start_year: int,
    end_year: int,
    source_id: int | None = None,
    attempts: int = 3,
) -> tuple[pd.DataFrame, dict]:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fetch_world_bank_indicator(variable, source_variable, start_year, end_year, source_id)
        except requests.exceptions.RequestException as exc:
            last_error = exc
            if attempt == attempts:
                break
            sleep(2 * attempt)
    if last_error is not None:
        raise last_error
    raise RuntimeError("World Bank request failed without an exception")


def download_binary_entry(entry: dict[str, Any], output_path: Path) -> tuple[str, int]:
    response = requests.get(entry["url"], timeout=90)
    response.raise_for_status()
    output_path.write_bytes(response.content)
    return response.headers.get("content-type", ""), len(response.content)


def _read_file_shape(path: Path, file_format: str) -> tuple[int, int]:
    if file_format == "csv":
        data = pd.read_csv(path, low_memory=False)
        return int(len(data)), int(len(data.columns))
    if file_format == "xlsx":
        data = read_xlsx_sheet(path)
        return int(len(data)), int(len(data.columns))
    return 0, 0


def _retry_delay_seconds(
    response: requests.Response | None,
    attempt: int,
    backoff_seconds: int,
) -> int:
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            return max(int(retry_after), backoff_seconds * attempt)
    return backoff_seconds * attempt


def _predictor_url(predictor: dict[str, Any], start_year: int, end_year: int) -> str:
    if predictor["dataset_id"] == "oecd_eps":
        return OECD_EPS_URL
    if predictor["dataset_id"] == "world_bank_wdi":
        return world_bank_indicator_url(
            predictor["source_variable"],
            start_year,
            end_year,
            predictor.get("source_id"),
        )
    raise ValueError(f"Unsupported predictor dataset_id: {predictor['dataset_id']}")


def oecd_patent_source_url(source_variable: str, start_year: int, end_year: int) -> str:
    return (
        f"{OECD_PAT_IND_BASE_URL}/.A.{source_variable}"
        f"?startPeriod={start_year}&endPeriod={end_year}"
        "&dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
    )


def oecd_sdmx_csv_url(source_variable: str, start_year: int, end_year: int) -> str:
    dataflow, key = source_variable.split("/", maxsplit=1)
    return (
        f"https://sdmx.oecd.org/public/rest/data/{dataflow}/{key}"
        f"?startPeriod={start_year}&endPeriod={end_year}&{OECD_SDMX_CSV_QUERY}"
    )


def _raw_file_name(entry: dict[str, Any], start_year: int, end_year: int) -> str:
    source_name = safe_source_name(entry["source_variable"])
    return f"{entry['dataset_id']}_{entry['variable']}_{source_name}_{start_year}_{end_year}.csv"


def _clean_cell(value: Any) -> str:
    return str(value).strip()


def _is_non_predictor_row(predictor_text: str, code_text: str, comments: str) -> bool:
    if not predictor_text and not code_text and not comments:
        return True
    section_headers = {"r&d", "energy", "environmental policy", "macroeconomic"}
    if predictor_text.strip().lower() in section_headers and not code_text:
        return True
    lower = predictor_text.strip().lower()
    return lower.startswith("excluded ") or lower.startswith("target ")


def _extract_world_bank_codes(text: str) -> list[str]:
    codes = []
    for code in WORLD_BANK_CODE_PATTERN.findall(text):
        if code not in codes:
            codes.append(code)
    return codes


def _world_bank_literature_entry(
    source_variable: str,
    predictor_text: str,
    row_number: int,
    start_year: int,
    end_year: int,
    comments: str,
) -> dict[str, Any]:
    config = WORLD_BANK_LITERATURE_INDICATORS.get(
        source_variable,
        {
            "variable": _slugify(predictor_text or source_variable),
            "description": predictor_text or source_variable,
        },
    )
    entry = {
        "dataset_id": "world_bank_wdi",
        "variable": config["variable"],
        "source_variable": source_variable,
        "source": "World Bank World Development Indicators",
        "source_id": WORLD_BANK_WDI_SOURCE_ID,
        "role": "literature_predictor",
        "description": config["description"],
        "start_year": start_year,
        "end_year": end_year,
        "url": world_bank_indicator_url(source_variable, start_year, end_year, WORLD_BANK_WDI_SOURCE_ID),
        "status": "planned",
        "download_method": "tabular",
        "file_format": "csv",
        "literature_rows": str(row_number),
        "literature_predictors": predictor_text,
        "notes": comments,
    }
    entry["file_name"] = _raw_file_name(entry, start_year, end_year)
    return entry


def _wgi_entry(
    predictor_text: str,
    row_number: int,
    start_year: int,
    end_year: int,
    comments: str,
) -> dict[str, Any]:
    entry = {
        **WGI_REGULATORY_QUALITY,
        "start_year": start_year,
        "end_year": end_year,
        "url": world_bank_indicator_url(
            WGI_REGULATORY_QUALITY["source_variable"],
            start_year,
            end_year,
            WORLD_BANK_WGI_SOURCE_ID,
        ),
        "status": "planned",
        "download_method": "tabular",
        "file_format": "csv",
        "literature_rows": str(row_number),
        "literature_predictors": predictor_text,
        "notes": (WGI_REGULATORY_QUALITY["notes"] + " " + comments).strip(),
    }
    entry["file_name"] = _raw_file_name(entry, start_year, end_year)
    return entry


def _oecd_eps_entry(
    predictor_text: str,
    row_number: int,
    start_year: int,
    end_year: int,
    comments: str,
) -> dict[str, Any]:
    source_end_year = min(end_year, 2020)
    entry = {
        "dataset_id": "oecd_eps",
        "variable": "eps_index",
        "source_variable": "POL_STRINGENCY.EPS",
        "source": "OECD Environmental Policy Stringency index",
        "role": "literature_predictor",
        "description": "Environmental Policy Stringency index on a 0-6 scale.",
        "start_year": start_year,
        "end_year": source_end_year,
        "url": OECD_EPS_URL,
        "status": "planned",
        "download_method": "tabular",
        "file_format": "csv",
        "literature_rows": str(row_number),
        "literature_predictors": predictor_text,
        "notes": comments,
    }
    entry["file_name"] = _raw_file_name(entry, start_year, source_end_year)
    return entry


def _rise_entries(predictor_text: str, row_number: int, comments: str) -> list[dict[str, Any]]:
    entries = []
    for group in RISE_SELECTED_INDICATOR_GROUPS:
        entries.append(
            {
                "dataset_id": "world_bank_data360",
                "variable": group["variable"],
                "source_variable": group["source_variable"],
                "source": "World Bank Data360 Regulatory Indicators for Sustainable Energy",
                "role": "literature_predictor_raw_source",
                "description": group["description"],
                "start_year": 2010,
                "end_year": 2023,
                "url": RISE_DATA360_CSV_URL,
                "file_name": group["file_name"],
                "indicator_prefix": group["indicator_prefix"],
                "status": "planned",
                "download_method": "tabular",
                "file_format": "csv",
                "literature_rows": str(row_number),
                "literature_predictors": predictor_text,
                "notes": comments,
            }
        )
    return entries


def _epu_entry(predictor_text: str, row_number: int, comments: str) -> dict[str, Any]:
    return {
        "dataset_id": "policy_uncertainty",
        "variable": "economic_policy_uncertainty",
        "source_variable": "All_Country_Data",
        "source": "Economic Policy Uncertainty Index",
        "role": "literature_predictor_raw_source",
        "description": "All-country Economic Policy Uncertainty workbook.",
        "start_year": 1990,
        "end_year": 2024,
        "url": EPU_ALL_COUNTRY_XLSX_URL,
        "file_name": "policy_uncertainty_economic_policy_uncertainty_All_Country_Data.xlsx",
        "status": "planned",
        "download_method": "binary",
        "file_format": "xlsx",
        "literature_rows": str(row_number),
        "literature_predictors": predictor_text,
        "notes": comments,
    }


def _oecd_patent_literature_entry(
    variable: str,
    source_variable: str,
    description: str,
    predictor_text: str,
    row_number: int,
    start_year: int,
    end_year: int,
    comments: str,
) -> dict[str, Any]:
    source_end_year = min(end_year, 2023)
    entry = {
        "dataset_id": "oecd_patents_environment",
        "variable": variable,
        "source_variable": source_variable,
        "source": "OECD Patents - indicators",
        "role": "literature_predictor_derived_source",
        "description": description,
        "start_year": start_year,
        "end_year": source_end_year,
        "url": oecd_patent_source_url(source_variable, start_year, source_end_year),
        "status": "planned",
        "download_method": "tabular",
        "file_format": "csv",
        "literature_rows": str(row_number),
        "literature_predictors": predictor_text,
        "notes": comments,
    }
    entry["file_name"] = _raw_file_name(entry, start_year, source_end_year)
    return entry


def _oecd_sdmx_literature_entry(
    dataset_id: str,
    variable: str,
    source_variable: str,
    source: str,
    role: str,
    description: str,
    predictor_text: str,
    row_number: int,
    start_year: int,
    end_year: int,
    comments: str,
) -> dict[str, Any]:
    entry = {
        "dataset_id": dataset_id,
        "variable": variable,
        "source_variable": source_variable,
        "source": source,
        "role": role,
        "description": description,
        "start_year": start_year,
        "end_year": end_year,
        "url": oecd_sdmx_csv_url(source_variable, start_year, end_year),
        "status": "planned",
        "download_method": "tabular",
        "file_format": "csv",
        "literature_rows": str(row_number),
        "literature_predictors": predictor_text,
        "notes": comments,
    }
    entry["file_name"] = _raw_file_name(entry, start_year, end_year)
    return entry


def _requires_unsupported_manifest_row(lower_text: str, world_bank_codes: list[str]) -> bool:
    if world_bank_codes:
        return False
    unsupported_terms: list[str] = []
    return any(term in lower_text for term in unsupported_terms)


def _unsupported_literature_entry(
    predictor_text: str,
    code_text: str,
    row_number: int,
    comments: str,
) -> dict[str, Any]:
    variable = _slugify(predictor_text or code_text or f"literature_row_{row_number}")
    return {
        "dataset_id": "unsupported_source",
        "variable": variable,
        "source_variable": "",
        "source": predictor_text or code_text,
        "role": "literature_predictor_unresolved_source",
        "description": predictor_text,
        "start_year": 1990,
        "end_year": 2024,
        "url": _first_url(code_text) or code_text,
        "file_name": "",
        "status": "not_downloaded",
        "download_method": "manual_or_unresolved",
        "file_format": "",
        "literature_rows": str(row_number),
        "literature_predictors": predictor_text,
        "notes": ("unsupported source page; " + comments).strip(),
    }


def _mentions_eps(lower_text: str) -> bool:
    return "pol_stringency.eps" in lower_text or "environmental policy stringency" in lower_text


def _first_url(text: str) -> str:
    match = re.search(r"https?://\S+", text)
    return match.group(0) if match else ""


def _slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "unnamed_predictor"


def _deduplicate_plan_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduplicated: dict[tuple[str, str, str], dict[str, Any]] = {}
    for entry in entries:
        key = (entry["dataset_id"], entry["variable"], entry.get("source_variable", ""))
        if key not in deduplicated:
            deduplicated[key] = entry.copy()
            continue

        existing = deduplicated[key]
        existing["literature_rows"] = _join_unique(existing.get("literature_rows", ""), entry.get("literature_rows", ""))
        existing["literature_predictors"] = _join_unique(
            existing.get("literature_predictors", ""),
            entry.get("literature_predictors", ""),
        )
        existing["notes"] = _join_unique(existing.get("notes", ""), entry.get("notes", ""))
    return list(deduplicated.values())


def _join_unique(left: str, right: str) -> str:
    values = []
    for part in [left, right]:
        for value in str(part).split(";"):
            value = value.strip()
            if value and value not in values:
                values.append(value)
    return "; ".join(values)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download raw data for selected target and predictors.")
    parser.add_argument("--start-year", type=int, default=1990)
    parser.add_argument("--end-year", type=int, default=2024)
    parser.add_argument("--raw-dir", type=Path, default=RAW_PREDICTORS_V1_DIR)
    parser.add_argument("--refresh", action="store_true", help="Redownload files even if they already exist.")
    parser.add_argument("--fail-fast", action="store_true", help="Raise on the first supported-source download error.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = run_raw_download(
        args.start_year,
        args.end_year,
        args.raw_dir,
        continue_on_error=not args.fail_fast,
        refresh=args.refresh,
    )
    print(manifest.to_string(index=False))


if __name__ == "__main__":
    main()
