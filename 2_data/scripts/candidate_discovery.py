from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

from data_common import (
    OECD_PATENT_AVAILABLE_DIMENSION_FALLBACK,
    OECD_PATENT_BROAD_TECH_DOMAINS,
    OECD_PATENT_DIMENSION_LABELS,
    OECD_PATENT_LABEL_FALLBACK,
    PROCESSED_DIR,
    RAW_DIR,
    dataframe_to_markdown,
    select_existing_columns,
    value_counts_frame,
)

TARGET_CATALOG_NAME = "target_candidate_catalog.csv"
PREDICTOR_CATALOG_NAME = "predictor_candidate_catalog.csv"
SUMMARY_NAME = "candidate_discovery_summary.md"

WORLD_BANK_SOURCE_INDICATOR_METADATA_URL = "https://api.worldbank.org/v2/source/{source_id}/indicator"
WORLD_BANK_METADATA_SOURCE_IDS = [2, 75]
METADATA_STOP_WORDS = {
    "a",
    "all",
    "and",
    "as",
    "constant",
    "for",
    "gross",
    "in",
    "of",
    "or",
    "per",
    "the",
    "total",
}
GENERIC_SINGLE_KEYWORDS = {
    "capita",
    "carbon",
    "constant",
    "development",
    "energy",
    "gdp",
    "income",
    "market",
    "population",
    "policy",
    "rise",
}

BROAD_ENVIRONMENT_TECH_DOMAINS = set(OECD_PATENT_BROAD_TECH_DOMAINS)

PREDICTOR_COLUMNS = [
    "variable_concept",
    "candidate_indicator",
    "source",
    "source_variable",
    "why_relevant",
    "literature_support",
    "expected_direction",
    "coverage_checked",
    "coverage_summary",
    "already_downloaded",
    "include_decision",
    "decision_reason",
    "measurement_caveat",
    "lag_recommendation",
    "metadata_match_keywords",
    "metadata_matches",
]

PREDICTOR_CONCEPTS = [
    {
        "variable_concept": "GDP per capita",
        "candidate_indicator": "gdp_per_capita",
        "source": "World Bank WDI",
        "source_variable": "NY.GDP.PCAP.KD",
        "why_relevant": "Captures development level and general innovation capacity.",
        "literature_support": "Moderate; used as a development and innovation-capacity control.",
        "expected_direction": "Positive",
        "include_decision": "candidate",
        "decision_reason": "Strong coverage and clear interpretation, but may absorb several mechanisms.",
        "measurement_caveat": "Consider log transform; avoid over-interpreting as a causal income effect.",
        "lag_recommendation": "Use t-1; test t-2 in robustness if coverage allows.",
        "metadata_match_keywords": "gdp per capita; constant; income per capita",
    },
    {
        "variable_concept": "GDP/population/market size",
        "candidate_indicator": "gdp; population",
        "source": "World Bank WDI",
        "source_variable": "NY.GDP.MKTP.KD; SP.POP.TOTL",
        "why_relevant": "Measures market size and scale of the national innovation system.",
        "literature_support": "Moderate; patent studies often control for market size or total demand.",
        "expected_direction": "Positive",
        "include_decision": "candidate_control",
        "decision_reason": "Useful control if the target is not fully size-normalized.",
        "measurement_caveat": "Can duplicate country-size information; use sparingly with normalized targets.",
        "lag_recommendation": "Use t-1.",
        "metadata_match_keywords": "gdp; gross domestic product; population; market size",
    },
    {
        "variable_concept": "Manufacturing share",
        "candidate_indicator": "manufacturing_share",
        "source": "World Bank WDI",
        "source_variable": "NV.IND.MANF.ZS",
        "why_relevant": "Rough proxy for industrial structure and potential demand for cleaner production.",
        "literature_support": "Moderate to weak; sectoral structure matters, but country-level share is coarse.",
        "expected_direction": "Ambiguous",
        "include_decision": "optional",
        "decision_reason": "Keep as an optional structural control after checking collinearity and coverage.",
        "measurement_caveat": "Does not identify pollution-intensive sectors or green manufacturing directly.",
        "lag_recommendation": "Use t-1.",
        "metadata_match_keywords": "manufacturing; value added; industry share",
    },
    {
        "variable_concept": "R&D expenditure",
        "candidate_indicator": "rd_expenditure_gdp",
        "source": "World Bank WDI",
        "source_variable": "GB.XPD.RSDV.GD.ZS",
        "why_relevant": "Measures national innovation capacity and knowledge investment.",
        "literature_support": "Strong; repeatedly linked to patenting and environmental innovation capacity.",
        "expected_direction": "Positive",
        "include_decision": "candidate",
        "decision_reason": "High conceptual fit; coverage is the main constraint.",
        "measurement_caveat": "General R&D, not green R&D.",
        "lag_recommendation": "Use t-1; test t-2 or t-3 if feasible.",
        "metadata_match_keywords": "research and development; r&d expenditure; gross domestic expenditure",
    },
    {
        "variable_concept": "Researchers",
        "candidate_indicator": "researchers_per_million",
        "source": "World Bank WDI",
        "source_variable": "SP.POP.SCIE.RD.P6",
        "why_relevant": "Captures human capital available for invention.",
        "literature_support": "Moderate; conceptually aligned with innovation capacity.",
        "expected_direction": "Positive",
        "include_decision": "secondary_candidate",
        "decision_reason": "Useful capacity proxy if R&D expenditure is missing or as a robustness check.",
        "measurement_caveat": "Coverage is thinner and the variable is not specific to environmental research.",
        "lag_recommendation": "Use t-1; test longer lags only if coverage remains usable.",
        "metadata_match_keywords": "researchers; research and development; per million",
    },
    {
        "variable_concept": "Tertiary education",
        "candidate_indicator": "tertiary_enrollment",
        "source": "World Bank WDI or OECD education data",
        "source_variable": "",
        "why_relevant": "Measures broad human-capital conditions for innovation.",
        "literature_support": "Moderate to weak for this specific country-level patent design.",
        "expected_direction": "Positive",
        "include_decision": "optional",
        "decision_reason": "Keep as a fallback human-capital proxy if researcher coverage is too sparse.",
        "measurement_caveat": "Enrollment is not the same as research workforce or technical skills.",
        "lag_recommendation": "Use t-1 or t-2.",
        "metadata_match_keywords": "tertiary education; school enrollment tertiary; educational attainment",
    },
    {
        "variable_concept": "Renewable energy share",
        "candidate_indicator": "renewable_energy_share",
        "source": "World Bank WDI",
        "source_variable": "EG.FEC.RNEW.ZS",
        "why_relevant": "Captures energy-transition demand and deployment context.",
        "literature_support": "Moderate; related literature often uses renewable policies, prices, or capacity.",
        "expected_direction": "Positive",
        "include_decision": "candidate_energy_variable",
        "decision_reason": "Prefer at most one energy-system variable in the first small model.",
        "measurement_caveat": "Final-energy share may reflect resource endowments as much as innovation demand.",
        "lag_recommendation": "Use t-1; test t-2 in robustness.",
        "metadata_match_keywords": "renewable energy; final energy consumption; renewables share",
    },
    {
        "variable_concept": "Fossil energy share",
        "candidate_indicator": "fossil_energy_share",
        "source": "World Bank WDI",
        "source_variable": "EG.USE.COMM.FO.ZS",
        "why_relevant": "Captures fossil dependence, possible transition pressure, and lock-in.",
        "literature_support": "Weak to cautionary; sign is theoretically ambiguous.",
        "expected_direction": "Ambiguous",
        "include_decision": "optional_energy_variable",
        "decision_reason": "Use only if it adds interpretable information beyond renewable share or energy intensity.",
        "measurement_caveat": "Can indicate both high transition need and fossil lock-in.",
        "lag_recommendation": "Use t-1.",
        "metadata_match_keywords": "fossil fuel; energy consumption; total energy use",
    },
    {
        "variable_concept": "Energy intensity",
        "candidate_indicator": "energy_intensity",
        "source": "World Bank WDI",
        "source_variable": "EG.EGY.PRIM.PP.KD",
        "why_relevant": "Measures energy efficiency pressure and production structure.",
        "literature_support": "Weak to cautionary; related evidence more often uses energy prices.",
        "expected_direction": "Ambiguous",
        "include_decision": "optional_energy_variable",
        "decision_reason": "Potential robustness variable, not a first-choice predictor.",
        "measurement_caveat": "Not equivalent to energy price incentives or regulation.",
        "lag_recommendation": "Use t-1.",
        "metadata_match_keywords": "energy intensity; primary energy; purchasing power parity",
    },
    {
        "variable_concept": "CO2 per capita",
        "candidate_indicator": "co2_per_capita",
        "source": "World Bank WDI",
        "source_variable": "EN.ATM.CO2E.PC",
        "why_relevant": "Captures emissions pressure and carbon-intensive structure.",
        "literature_support": "Weak to cautionary; emissions can be pressure, outcome, or structural proxy.",
        "expected_direction": "Ambiguous",
        "include_decision": "optional_energy_variable",
        "decision_reason": "Consider only with careful interpretation and lagging.",
        "measurement_caveat": "May proxy economic structure and fossil dependence rather than policy pressure.",
        "lag_recommendation": "Use t-1 or t-2.",
        "metadata_match_keywords": "co2 emissions; carbon dioxide; per capita",
    },
    {
        "variable_concept": "Environmental policy stringency",
        "candidate_indicator": "eps_index",
        "source": "OECD EPS",
        "source_variable": "POL_STRINGENCY.EPS",
        "why_relevant": "Measures policy incentives for cleaner technologies.",
        "literature_support": "Strong; central policy predictor in environmental innovation literature.",
        "expected_direction": "Positive",
        "include_decision": "candidate",
        "decision_reason": "Best policy candidate if narrower OECD-style coverage is acceptable.",
        "measurement_caveat": "Coverage narrows the panel and predictive association is not causal proof.",
        "lag_recommendation": "Use t-1; test t-2 or t-3 if feasible.",
        "metadata_match_keywords": "environmental policy stringency; eps; policy stringency",
    },
    {
        "variable_concept": "RISE sustainable energy regulation",
        "candidate_indicator": "rise_score",
        "source": "RISE",
        "source_variable": "",
        "why_relevant": "Captures sustainable-energy policy and regulatory environment.",
        "literature_support": "Optional; useful policy proxy but less directly tied to patent evidence.",
        "expected_direction": "Positive",
        "include_decision": "optional_policy_variable",
        "decision_reason": "Keep until country-year coverage and exact measure are verified.",
        "measurement_caveat": "May have limited years and may not align with OECD patent panel.",
        "lag_recommendation": "Use t-1 or nearest prior observation.",
        "metadata_match_keywords": "rise; sustainable energy; regulatory indicators",
    },
    {
        "variable_concept": "Carbon pricing/ETS",
        "candidate_indicator": "carbon_pricing_ets",
        "source": "OECD, World Bank, or other public policy source",
        "source_variable": "",
        "why_relevant": "Measures direct price incentives for low-carbon innovation.",
        "literature_support": "Optional; mechanism is strong but harmonized coverage must be checked.",
        "expected_direction": "Positive",
        "include_decision": "optional_policy_variable",
        "decision_reason": "Add only if a clean public panel source is available without excess complexity.",
        "measurement_caveat": "Policy design and sector coverage vary; binary ETS measures may be coarse.",
        "lag_recommendation": "Use t-1; test longer policy lags if coverage allows.",
        "metadata_match_keywords": "carbon pricing; carbon tax; emissions trading; ets",
    },
]


def source_variable(unit_measure: str, patent_type: str, tech: str, pat: str) -> str:
    return f"{unit_measure}.{patent_type}.{tech}.{pat}"


def load_dimension_values(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    metadata_path = processed_dir / "oecd_patent_dimension_values.csv"
    if metadata_path.exists():
        return pd.read_csv(metadata_path)

    rows = []
    for dimension, codes in OECD_PATENT_AVAILABLE_DIMENSION_FALLBACK.items():
        for position, code in enumerate(codes, start=1):
            rows.append(
                {
                    "dimension": dimension,
                    "dimension_label": OECD_PATENT_DIMENSION_LABELS[dimension],
                    "code": code,
                    "label": OECD_PATENT_LABEL_FALLBACK[dimension].get(code, code),
                    "position": position,
                }
            )
    return pd.DataFrame(rows)


def build_target_candidate_catalog(processed_dir: Path = PROCESSED_DIR) -> pd.DataFrame:
    dimension_values = load_dimension_values(processed_dir)
    lookups = _dimension_lookups(dimension_values)
    coverage = _load_coverage(processed_dir)

    rows = []
    for unit_measure in lookups["UNIT_MEASURE"]:
        for patent_type in lookups["TYPE"]:
            for tech in lookups["TECH"]:
                for pat in lookups["PAT"]:
                    variable = source_variable(unit_measure, patent_type, tech, pat)
                    role, include, reason = classify_target_candidate(unit_measure, patent_type, tech, pat)
                    row = {
                        "source_variable": variable,
                        "unit_measure": unit_measure,
                        "unit_measure_label": lookups["UNIT_MEASURE"][unit_measure],
                        "type": patent_type,
                        "type_label": lookups["TYPE"][patent_type],
                        "technology_domain": tech,
                        "technology_domain_label": lookups["TECH"][tech],
                        "regional_patent_office": pat,
                        "regional_patent_office_label": lookups["PAT"][pat],
                        "candidate_role": role,
                        "recommended_use": recommended_target_use(
                            unit_measure, patent_type, tech, pat, role, include
                        ),
                        "include": include,
                        "reason": reason,
                    }
                    row.update(_coverage_fields(variable, coverage))
                    rows.append(row)

    data = pd.DataFrame(rows)
    role_order = {
        "main_target_candidate": 0,
        "secondary_target": 1,
        "mechanism_candidate": 2,
        "breakdown_candidate": 3,
        "context_only": 4,
        "not_suitable": 5,
    }
    data["_role_order"] = data["candidate_role"].map(role_order).fillna(99).astype(int)
    return (
        data.sort_values(["_role_order", "include", "source_variable"], ascending=[True, False, True])
        .drop(columns="_role_order")
        .reset_index(drop=True)
    )


def classify_target_candidate(
    unit_measure: str, patent_type: str, tech: str, pat: str
) -> tuple[str, bool, str]:
    variable = source_variable(unit_measure, patent_type, tech, pat)

    if tech == "TOT":
        return (
            "context_only",
            False,
            "All-technologies denominator; useful context for normalization but not an environment-related innovation outcome.",
        )
    if pat != "_Z":
        return (
            "breakdown_candidate",
            False,
            (
                "Patent-office breakdown may help diagnose regional patenting routes, "
                "but it is too narrow for the main country-year outcome."
            ),
        )
    if patent_type == "COL" or "COL" in unit_measure:
        return (
            "mechanism_candidate",
            False,
            (
                "International collaboration is relevant for mechanisms and descriptive analysis, "
                "but it is not the broad country-year innovation outcome for the main target."
            ),
        )
    if patent_type == "DIFF":
        return (
            "mechanism_candidate",
            False,
            (
                "Diffusion is relevant for adoption and international spread of environmental technologies, "
                "but it is analytically different from domestic technology development."
            ),
        )
    if patent_type == "RENEW":
        return (
            "secondary_target",
            False,
            "Renewable-energy patenting is substantively important but narrower than the broad environmental-innovation target.",
        )
    if unit_measure in {"INV_RD_S13", "INV_RD_S1ZS"} and patent_type == "DEV" and tech == "ENV_PAT":
        return (
            "secondary_target",
            False,
            "R&D-normalized patent intensity may be useful for robustness, but the denominator is harder to compare broadly.",
        )
    if unit_measure == "IX":
        return (
            "not_suitable",
            False,
            "Index measure is less directly interpretable as a target for country-year innovation levels.",
        )
    if variable == "PT_INV.DEV.ENV_PAT._Z":
        return (
            "main_target_candidate",
            True,
            "Preferred normalized target: environment-related technologies as a share of inventions.",
        )
    if variable == "INV_PS.DEV.ENV_PAT._Z":
        return (
            "secondary_target",
            True,
            "Size-normalized patent intensity candidate; useful robustness target.",
        )
    if variable == "PT_TECH.DEV.ENV_PAT._Z":
        return (
            "secondary_target",
            False,
            "Technology-share candidate kept for robustness only because values can be hard to interpret.",
        )
    if patent_type == "DEV" and tech in BROAD_ENVIRONMENT_TECH_DOMAINS and pat == "_Z":
        return (
            "secondary_target",
            False,
            "Broad environmental subdomain; useful for descriptive checks but too narrow for the main target.",
        )

    return (
        "not_suitable",
        False,
        "Does not match the conservative broad country-year target definition for this project.",
    )


def recommended_target_use(
    unit_measure: str,
    patent_type: str,
    tech: str,
    pat: str,
    candidate_role: str,
    include: bool,
) -> str:
    variable = source_variable(unit_measure, patent_type, tech, pat)
    if candidate_role == "main_target_candidate" and include:
        return "main outcome candidate"
    if variable == "INV_PS.DEV.ENV_PAT._Z":
        return "robustness outcome candidate"
    if candidate_role == "secondary_target":
        return "robustness or thematic outcome candidate"
    if candidate_role == "mechanism_candidate":
        return "mechanism or descriptive candidate"
    if candidate_role == "breakdown_candidate":
        return "diagnostic breakdown candidate"
    if candidate_role == "context_only":
        return "denominator or context variable"
    return "do not use without separate justification"


def keyword_matches(text: str, keywords: Iterable[str]) -> bool:
    return bool(_matched_keywords(text, keywords))


def filter_world_bank_metadata(records: Iterable[dict], keywords: Iterable[str]) -> list[dict]:
    matches = []
    for record in records:
        searchable_parts = [
            record.get("id"),
            record.get("name"),
            record.get("indicator", {}).get("id") if isinstance(record.get("indicator"), dict) else None,
            record.get("indicator", {}).get("value") if isinstance(record.get("indicator"), dict) else None,
            record.get("sourceNote"),
            record.get("sourceOrganization"),
        ]
        matched_keywords = _matched_keywords(" ".join(str(part or "") for part in searchable_parts), keywords)
        if matched_keywords:
            matched_record = dict(record)
            matched_record["matched_keywords"] = "; ".join(matched_keywords)
            matches.append(matched_record)
    return matches


def build_predictor_candidate_catalog(
    processed_dir: Path = PROCESSED_DIR, scan_world_bank: bool = False
) -> pd.DataFrame:
    coverage = _load_coverage(processed_dir)
    metadata_records = _world_bank_metadata_records(scan_world_bank)

    rows = []
    for concept in PREDICTOR_CONCEPTS:
        row = dict(concept)
        row["metadata_matches"] = ""
        source_variables = _split_source_variables(row["source_variable"])
        coverage_summaries = [
            _coverage_summary_for_source_variable(source_var, coverage) for source_var in source_variables
        ]
        checked = bool(source_variables) and all(summary != "not checked" for summary in coverage_summaries)
        row["coverage_checked"] = checked
        row["coverage_summary"] = "; ".join(coverage_summaries) if coverage_summaries else "not checked"
        row["already_downloaded"] = any(
            coverage.get(source_var, {}).get("source_variable") == source_var for source_var in source_variables
        )
        keywords = _split_keywords(row["metadata_match_keywords"])
        matches = _exact_metadata_matches(metadata_records, source_variables)
        if not matches and metadata_records and _should_keyword_scan_world_bank(row, source_variables):
            matches = filter_world_bank_metadata(metadata_records, keywords)
        if matches:
            row["metadata_matches"] = _format_metadata_matches(matches)
        rows.append(row)

    return pd.DataFrame(rows, columns=PREDICTOR_COLUMNS)


def write_outputs(
    target_catalog: pd.DataFrame,
    predictor_catalog: pd.DataFrame,
    output_dir: Path = PROCESSED_DIR,
    metadata_scan_used: bool = False,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    target_path = output_dir / TARGET_CATALOG_NAME
    predictor_path = output_dir / PREDICTOR_CATALOG_NAME
    summary_path = output_dir / SUMMARY_NAME

    target_catalog.to_csv(target_path, index=False)
    predictor_catalog.to_csv(predictor_path, index=False)
    write_markdown_summary(
        target_catalog,
        predictor_catalog,
        summary_path,
        metadata_scan_used=metadata_scan_used,
    )
    return {"target": target_path, "predictor": predictor_path, "summary": summary_path}


def write_markdown_summary(
    target_catalog: pd.DataFrame,
    predictor_catalog: pd.DataFrame,
    output_path: Path,
    metadata_scan_used: bool = False,
) -> None:
    target_counts = value_counts_frame(target_catalog, ["candidate_role", "include"])
    target_use_counts = value_counts_frame(
        target_catalog, ["candidate_role", "recommended_use", "include"]
    )
    predictor_counts = value_counts_frame(predictor_catalog, ["include_decision"])
    included_targets = (
        target_catalog[target_catalog["include"]].copy()
        if "include" in target_catalog.columns
        else target_catalog.head(0).copy()
    )
    included_predictors = (
        predictor_catalog[
            predictor_catalog["include_decision"].isin(
                ["candidate", "candidate_control", "candidate_energy_variable"]
            )
        ].copy()
        if "include_decision" in predictor_catalog.columns
        else predictor_catalog.head(0).copy()
    )
    mechanism_targets = (
        target_catalog[target_catalog["candidate_role"].eq("mechanism_candidate")]
        .drop_duplicates("reason")
        .head(8)
        .copy()
        if "candidate_role" in target_catalog.columns
        else target_catalog.head(0).copy()
    )

    text = [
        "# Candidate Discovery Summary",
        "",
        "This file is generated by `2_data/scripts/candidate_discovery.py`.",
        "",
        "The catalogs are reviewer-facing discovery artifacts, not final modeling decisions.",
        "",
        "## Target Candidate Counts",
        "",
        dataframe_to_markdown(target_counts),
        "",
        "## Target Candidate Uses",
        "",
        dataframe_to_markdown(target_use_counts),
        "",
        "## Included Or Leading Target Candidates",
        "",
        dataframe_to_markdown(
            select_existing_columns(
                included_targets,
                [
                    "source_variable",
                    "candidate_role",
                    "recommended_use",
                    "include",
                    "coverage_checked",
                    "countries_with_data",
                    "first_year",
                    "last_year",
                    "reason",
                ],
            )
        ),
        "",
        "## Mechanism Or Descriptive Target Candidates",
        "",
        dataframe_to_markdown(
            select_existing_columns(
                mechanism_targets,
                [
                    "source_variable",
                    "unit_measure_label",
                    "type_label",
                    "technology_domain_label",
                    "recommended_use",
                    "reason",
                ],
            )
        ),
        "",
        "## Predictor Decision Counts",
        "",
        dataframe_to_markdown(predictor_counts),
        "",
        "## Leading Predictor Candidates",
        "",
        dataframe_to_markdown(
            select_existing_columns(
                included_predictors,
                [
                    "variable_concept",
                    "source",
                    "source_variable",
                    "include_decision",
                    "coverage_summary",
                    "decision_reason",
                ],
            )
        ),
        "",
        "## Notes",
        "",
        "1. `coverage_checked` only reflects variables present in `data_availability.csv`.",
        (
            "2. Optional World Bank metadata scanning was enabled for this run; it searches "
            "indicator metadata only, not time series."
            if metadata_scan_used
            else "2. Optional World Bank metadata scanning was not enabled for this run."
        ),
        "3. The predictor catalog is provisional because the literature review is still in progress.",
        "4. Final target and predictor choices should be recorded in `0_organization/decision_log.md`.",
        "",
    ]
    output_path.write_text("\n".join(text), encoding="utf-8")


def run_candidate_discovery(
    scan_world_bank: bool = False,
    output_dir: Path = PROCESSED_DIR,
    processed_dir: Path = PROCESSED_DIR,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    target_catalog = build_target_candidate_catalog(processed_dir)
    predictor_catalog = build_predictor_candidate_catalog(processed_dir, scan_world_bank=scan_world_bank)
    write_outputs(target_catalog, predictor_catalog, output_dir, metadata_scan_used=scan_world_bank)
    return target_catalog, predictor_catalog


def fetch_world_bank_indicator_metadata(timeout: int = 90) -> list[dict]:
    records: list[dict] = []
    for source_id in WORLD_BANK_METADATA_SOURCE_IDS:
        page = 1
        pages = 1
        while page <= pages:
            response = requests.get(
                WORLD_BANK_SOURCE_INDICATOR_METADATA_URL.format(source_id=source_id),
                params={"format": "json", "per_page": 20000, "page": page},
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list) or len(payload) < 2:
                raise ValueError("Unexpected World Bank metadata response")
            metadata = payload[0]
            records.extend(payload[1])
            pages = int(metadata.get("pages", page))
            page += 1
    return records


def _dimension_lookups(dimension_values: pd.DataFrame) -> dict[str, dict[str, str]]:
    lookups = {}
    for dimension in OECD_PATENT_AVAILABLE_DIMENSION_FALLBACK:
        subset = dimension_values[dimension_values["dimension"].eq(dimension)].copy()
        if subset.empty:
            lookups[dimension] = dict(OECD_PATENT_LABEL_FALLBACK[dimension])
            continue
        subset = subset.sort_values("position") if "position" in subset.columns else subset
        lookups[dimension] = dict(zip(subset["code"], subset["label"]))
    return lookups


def _load_coverage(processed_dir: Path) -> dict[str, dict]:
    availability_path = processed_dir / "data_availability.csv"
    if not availability_path.exists():
        return {}
    data = pd.read_csv(availability_path)
    if "source_variable" not in data.columns:
        return {}
    return {
        row["source_variable"]: row.to_dict()
        for _, row in data.iterrows()
        if pd.notna(row.get("source_variable"))
    }


def _coverage_fields(source_var: str, coverage: dict[str, dict]) -> dict:
    coverage_row = coverage.get(source_var, {})
    fields = {"coverage_checked": bool(coverage_row)}
    for column in [
        "dataset_id",
        "variable",
        "total_rows",
        "non_missing_observations",
        "missing_observations",
        "countries_total",
        "countries_with_data",
        "years_total",
        "years_with_data",
        "first_year",
        "last_year",
    ]:
        fields[column] = coverage_row.get(column, pd.NA)
    return fields


def _coverage_summary_for_source_variable(source_var: str, coverage: dict[str, dict]) -> str:
    coverage_row = coverage.get(source_var)
    if not coverage_row:
        return "not checked"
    countries = _format_number(coverage_row.get("countries_with_data"))
    years = _format_number(coverage_row.get("years_with_data"))
    first_year = _format_number(coverage_row.get("first_year"))
    last_year = _format_number(coverage_row.get("last_year"))
    variable = coverage_row.get("variable", source_var)
    return f"{variable}: {countries} countries, {years} years, {first_year}-{last_year}"


def _format_number(value) -> str:
    if pd.isna(value):
        return ""
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return str(value)


def _split_source_variables(value: str) -> list[str]:
    return [part.strip() for part in str(value or "").split(";") if part.strip()]


def _split_keywords(value: str) -> list[str]:
    return [part.strip() for part in str(value or "").replace(",", ";").split(";") if part.strip()]


def _format_metadata_matches(matches: list[dict], limit: int = 5) -> str:
    formatted = []
    for match in matches[:limit]:
        indicator = match.get("indicator")
        indicator_id = match.get("id") or (indicator.get("id", "") if isinstance(indicator, dict) else "")
        name = match.get("name") or (indicator.get("value", "") if isinstance(indicator, dict) else "")
        formatted.append(f"{indicator_id}: {name}".strip(": "))
    suffix = f"; +{len(matches) - limit} more" if len(matches) > limit else ""
    return "; ".join(formatted) + suffix


def _exact_metadata_matches(records: Iterable[dict], source_variables: list[str]) -> list[dict]:
    if not source_variables:
        return []
    wanted = set(source_variables)
    matches = []
    for record in records:
        indicator = record.get("indicator")
        indicator_id = indicator.get("id", "") if isinstance(indicator, dict) else ""
        if (record.get("id") or indicator_id) in wanted:
            matches.append(record)
    return matches


def _should_keyword_scan_world_bank(row: dict, source_variables: list[str]) -> bool:
    source = str(row.get("source", ""))
    return not source_variables and "World Bank WDI" in source


def _matched_keywords(text: str, keywords: Iterable[str]) -> list[str]:
    normalized_text = _normalize_for_matching(text)
    text_tokens = set(normalized_text.split())
    matches = []
    for keyword in keywords:
        keyword_text = str(keyword).strip()
        if not keyword_text:
            continue
        tokens = _keyword_tokens(keyword_text)
        if not tokens:
            continue
        if len(tokens) == 1:
            token = tokens[0]
            if len(token) < 6 or token in GENERIC_SINGLE_KEYWORDS:
                continue
            if token in text_tokens:
                matches.append(keyword_text)
            continue
        if all(token in text_tokens for token in tokens):
            matches.append(keyword_text)
    return matches


def _keyword_tokens(keyword: str) -> list[str]:
    normalized = _normalize_for_matching(keyword)
    return [
        token
        for token in normalized.split()
        if token not in METADATA_STOP_WORDS and token not in GENERIC_SINGLE_KEYWORDS
    ]


def _normalize_for_matching(text: str) -> str:
    normalized = str(text or "").lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


def _world_bank_metadata_records(scan_world_bank: bool) -> list[dict]:
    local_path = RAW_DIR / "world_bank_metadata.json"
    records = _local_world_bank_metadata_records(local_path)
    if scan_world_bank:
        records.extend(fetch_world_bank_indicator_metadata())
    return records


def _local_world_bank_metadata_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for variable, metadata in raw.items():
        records.append(
            {
                "id": metadata.get("indicator"),
                "name": variable,
                "sourceNote": metadata.get("description", ""),
                "sourceOrganization": "World Bank WDI",
            }
        )
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover target and predictor candidates for the project.")
    parser.add_argument(
        "--scan-world-bank-metadata",
        action="store_true",
        help="Optionally query World Bank indicator metadata catalogs without downloading time series.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target_catalog, predictor_catalog = run_candidate_discovery(
        scan_world_bank=args.scan_world_bank_metadata
    )
    print(
        f"Wrote {len(target_catalog)} target candidates and "
        f"{len(predictor_catalog)} predictor candidates to {PROCESSED_DIR}"
    )


if __name__ == "__main__":
    main()
