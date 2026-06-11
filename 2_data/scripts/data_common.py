from __future__ import annotations

from pathlib import Path
import re
from xml.etree import ElementTree
from zipfile import ZipFile

import pandas as pd
import requests


ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "2_data" / "raw"
RAW_PREDICTORS_V1_DIR = RAW_DIR / "predictorsv1"
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
    "E_O",
    "FCS",
    "G20",
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
    "ODA",
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
    "W_X",
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


def read_xlsx_sheet(path: Path, sheet_name: str | None = None) -> pd.DataFrame:
    with ZipFile(path) as workbook:
        shared_strings = _read_xlsx_shared_strings(workbook)
        sheet_path = _resolve_xlsx_sheet_path(workbook, sheet_name)
        root = ElementTree.fromstring(workbook.read(sheet_path))

    rows = []
    max_col = 0
    namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    for row_node in root.findall(".//x:sheetData/x:row", namespace):
        values: list[object] = []
        for cell in row_node.findall("x:c", namespace):
            cell_ref = cell.attrib.get("r", "")
            column_index = _xlsx_column_index(cell_ref)
            if column_index is None:
                column_index = len(values)
            while len(values) <= column_index:
                values.append(None)
            values[column_index] = _xlsx_cell_value(cell, shared_strings, namespace)
        max_col = max(max_col, len(values))
        rows.append(values)

    if not rows:
        return pd.DataFrame()

    normalized_rows = [row + [None] * (max_col - len(row)) for row in rows]
    headers = ["" if value is None else str(value) for value in normalized_rows[0]]
    frame = pd.DataFrame(normalized_rows[1:], columns=headers)
    non_empty_columns = [column for column in frame.columns if str(column).strip()]
    return frame.loc[:, non_empty_columns]


def _read_xlsx_shared_strings(workbook: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in workbook.namelist():
        return []
    root = ElementTree.fromstring(workbook.read("xl/sharedStrings.xml"))
    namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    strings = []
    for item in root.findall("x:si", namespace):
        strings.append("".join(text_node.text or "" for text_node in item.findall(".//x:t", namespace)))
    return strings


def _resolve_xlsx_sheet_path(workbook: ZipFile, sheet_name: str | None) -> str:
    workbook_root = ElementTree.fromstring(workbook.read("xl/workbook.xml"))
    relationships_root = ElementTree.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
    workbook_namespace = {
        "x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }
    relationship_namespace = {"rel": "http://schemas.openxmlformats.org/package/2006/relationships"}

    sheets = workbook_root.findall(".//x:sheets/x:sheet", workbook_namespace)
    selected_sheet = None
    for sheet in sheets:
        if sheet_name is None or sheet.attrib.get("name") == sheet_name:
            selected_sheet = sheet
            break
    if selected_sheet is None:
        available = ", ".join(sheet.attrib.get("name", "") for sheet in sheets)
        raise ValueError(f"Sheet {sheet_name!r} not found in {available}")

    relationship_id = selected_sheet.attrib[
        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    ]
    for relationship in relationships_root.findall("rel:Relationship", relationship_namespace):
        if relationship.attrib.get("Id") == relationship_id:
            target = relationship.attrib["Target"].lstrip("/")
            return target if target.startswith("xl/") else f"xl/{target}"
    raise ValueError(f"Workbook relationship {relationship_id!r} not found")


def _xlsx_cell_value(cell: ElementTree.Element, shared_strings: list[str], namespace: dict[str, str]) -> object:
    cell_type = cell.attrib.get("t", "")
    if cell_type == "inlineStr":
        return "".join(text_node.text or "" for text_node in cell.findall(".//x:t", namespace))

    value_node = cell.find("x:v", namespace)
    if value_node is None or value_node.text is None:
        return None

    raw_value = value_node.text
    if cell_type == "s":
        index = int(raw_value)
        return shared_strings[index] if index < len(shared_strings) else ""
    if cell_type in {"str", "e"}:
        return raw_value
    if cell_type == "b":
        return raw_value == "1"
    return _coerce_xlsx_number(raw_value)


def _coerce_xlsx_number(value: str) -> object:
    try:
        number = float(value)
    except ValueError:
        return value
    return int(number) if number.is_integer() else number


def _xlsx_column_index(cell_ref: str) -> int | None:
    match = re.match(r"([A-Z]+)", cell_ref)
    if match is None:
        return None
    column_index = 0
    for character in match.group(1):
        column_index = column_index * 26 + ord(character) - ord("A") + 1
    return column_index - 1
