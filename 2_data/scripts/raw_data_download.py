from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from data_common import RAW_DIR
from data_exploration import (
    OECD_EPS_URL,
    fetch_world_bank_indicator,
    oecd_patent_url,
    read_oecd_csv,
    world_bank_indicator_url,
)

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
        "variable": "gdp_per_capita",
        "source_variable": "NY.GDP.PCAP.KD",
        "source": "World Bank WDI",
        "role": "main_predictor",
        "description": "GDP per capita, constant 2015 US dollars.",
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


def build_raw_download_plan(start_year: int, end_year: int) -> list[dict[str, Any]]:
    entries = []
    for target in RAW_TARGETS:
        source_end_year = min(end_year, 2023)
        entries.append(
            {
                **target,
                "start_year": start_year,
                "end_year": source_end_year,
                "url": oecd_patent_url(target["unit_measure"], start_year, source_end_year),
                "file_name": _raw_file_name(target, start_year, source_end_year),
            }
        )

    for predictor in SELECTED_PREDICTORS:
        source_end_year = min(end_year, 2020) if predictor["dataset_id"] == "oecd_eps" else end_year
        url = _predictor_url(predictor, start_year, source_end_year)
        entries.append(
            {
                **predictor,
                "start_year": start_year,
                "end_year": source_end_year,
                "url": url,
                "file_name": _raw_file_name(predictor, start_year, source_end_year),
            }
        )
    return entries


def run_raw_download(
    start_year: int = 1990,
    end_year: int = 2024,
    raw_dir: Path = RAW_DIR,
    fetcher: Callable[[dict[str, Any]], pd.DataFrame] | None = None,
) -> pd.DataFrame:
    raw_dir.mkdir(parents=True, exist_ok=True)
    fetch = fetcher or fetch_raw_entry

    rows = []
    for entry in build_raw_download_plan(start_year, end_year):
        data = fetch(entry)
        output_path = raw_dir / entry["file_name"]
        data.to_csv(output_path, index=False)
        rows.append(
            {
                "dataset_id": entry["dataset_id"],
                "variable": entry["variable"],
                "source_variable": entry["source_variable"],
                "role": entry["role"],
                "source": entry["source"],
                "start_year": entry["start_year"],
                "end_year": entry["end_year"],
                "rows": int(len(data)),
                "columns": int(len(data.columns)),
                "status": "downloaded",
                "source_url": entry["url"],
                "file_path": str(output_path),
            }
        )

    manifest = pd.DataFrame(rows)
    manifest.to_csv(raw_dir / "raw_download_manifest.csv", index=False)
    return manifest


def fetch_raw_entry(entry: dict[str, Any]) -> pd.DataFrame:
    if entry["dataset_id"] == "oecd_patents_environment":
        return read_oecd_csv(entry["url"])
    if entry["dataset_id"] == "oecd_eps":
        return read_oecd_csv(entry["url"])
    if entry["dataset_id"] == "world_bank_wdi":
        source_id = entry.get("source_id")
        data, _ = fetch_world_bank_indicator(
            entry["variable"],
            entry["source_variable"],
            entry["start_year"],
            entry["end_year"],
            source_id,
        )
        return data
    raise ValueError(f"Unsupported dataset_id: {entry['dataset_id']}")


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


def _raw_file_name(entry: dict[str, Any], start_year: int, end_year: int) -> str:
    source_name = safe_source_name(entry["source_variable"])
    return f"{entry['dataset_id']}_{entry['variable']}_{source_name}_{start_year}_{end_year}.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download raw data for selected target and predictors.")
    parser.add_argument("--start-year", type=int, default=1990)
    parser.add_argument("--end-year", type=int, default=2024)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = run_raw_download(args.start_year, args.end_year, args.raw_dir)
    print(manifest.to_string(index=False))


if __name__ == "__main__":
    main()
