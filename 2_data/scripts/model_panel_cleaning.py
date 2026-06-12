from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from data_common import PROCESSED_DIR, RAW_PREDICTORS_V1_DIR, filter_country_rows


TARGET_VARIABLE = "env_patent_share_inventions"
MANIFEST_FILE_NAME = "raw_download_manifest.csv"
MODEL_PANEL_SUBDIR_NAME = "model_panels"
IMPUTATION_MODES = ["none", "linear_interpolated"]
OUTPUT_FILE_NAMES = {
    "none": "model_panel_{panel_id}_no_imputation.csv",
    "linear_interpolated": "model_panel_{panel_id}_linear_interpolated.csv",
}
IMPUTATION_OUTPUT_LABELS = {
    "none": "no_imputation",
    "linear_interpolated": "linear_interpolated",
}
IMPUTATION_RECOMMENDED_USE = {
    "none": "primary_prediction_analysis_base",
    "linear_interpolated": "retrospective_sensitivity_not_for_prediction",
}


@dataclass(frozen=True)
class PredictorSpec:
    variable: str
    label: str
    raw_file: str = ""


@dataclass(frozen=True)
class PanelDefinition:
    panel_id: str
    predictors: list[PredictorSpec]
    anchor_variable: str | None = None
    raw_start_year: int | None = None
    raw_end_year: int | None = None


def default_panel_definitions() -> list[PanelDefinition]:
    """Return the four agreed model panels in a readable, edit-friendly form."""
    main_predictors = [
        PredictorSpec("gdp_constant_2015_usd", "GDP, constant 2015 US dollars"),
        PredictorSpec("renewable_energy_share", "Renewable energy share"),
        PredictorSpec("wgi_regulatory_quality", "WGI Regulatory Quality"),
        PredictorSpec("co2_per_capita_ar5", "CO2 per capita, AR5 source"),
        PredictorSpec("fdi_net_inflows", "FDI net inflows"),
        PredictorSpec("tertiary_enrollment", "Tertiary enrollment"),
        PredictorSpec("env_technology_rta", "Environmental technology RTA index"),
        PredictorSpec("scientific_journal_articles", "Scientific journal articles"),
        PredictorSpec("trade_openness", "Trade openness"),
        PredictorSpec("inflation", "Inflation"),
        PredictorSpec("fossil_energy_share", "Fossil energy share"),
    ]
    suba_predictors = [
        PredictorSpec("rise_energy_efficiency", "RISE Energy Efficiency score"),
        PredictorSpec("rise_renewable_energy", "RISE Renewable Energy score"),
        PredictorSpec("high_tech_exports", "High-tech exports"),
    ]
    subb_predictors = [
        PredictorSpec("rd_expenditure_gdp", "R&D expenditure as percent of GDP"),
        PredictorSpec("env_co_invention_share", "Environmental co-invention share"),
        PredictorSpec("energy_imports_net", "Net energy imports"),
        PredictorSpec("researchers_per_million", "Researchers per million people"),
        PredictorSpec("environmental_tax_revenue", "Environmental tax revenue"),
    ]
    subc_predictors = [
        PredictorSpec("eps_index", "Environmental Policy Stringency index"),
    ]
    return [
        PanelDefinition(
            panel_id="main",
            predictors=main_predictors,
            anchor_variable="fossil_energy_share",
            raw_start_year=1996,
            raw_end_year=2022,
        ),
        PanelDefinition(panel_id="suba", predictors=suba_predictors),
        PanelDefinition(panel_id="subb", predictors=subb_predictors),
        PanelDefinition(panel_id="subc", predictors=subc_predictors),
    ]


def run_model_panel_cleaning(
    raw_dir: Path = RAW_PREDICTORS_V1_DIR,
    processed_dir: Path = PROCESSED_DIR,
    panel_definitions: list[PanelDefinition] | None = None,
) -> dict[str, object]:
    """Build all requested lagged model panels under processed_dir/model_panels."""
    panel_definitions = panel_definitions or default_panel_definitions()
    manifest = load_manifest(raw_dir)
    all_predictors = sorted({spec.variable for definition in panel_definitions for spec in definition.predictors})

    predictor_long, base_variable_map = load_selected_raw_series(raw_dir, manifest, all_predictors)
    target_wide, target_first_year, target_last_year, target_map = load_target_series(raw_dir, manifest)

    panel_dir = processed_dir / MODEL_PANEL_SUBDIR_NAME
    panel_dir.mkdir(parents=True, exist_ok=True)
    panel_paths: list[str] = []
    summary_rows: list[dict[str, object]] = []
    imputation_rows: list[dict[str, object]] = []
    panel_variable_rows: list[dict[str, object]] = []

    for definition in panel_definitions:
        resolved = resolve_panel_definition(definition, predictor_long)
        predictor_names = [spec.variable for spec in resolved.predictors]
        panel_variable_rows.extend(_panel_variable_map_rows(resolved, base_variable_map, target_map))

        for imputation in IMPUTATION_MODES:
            panel, metadata = build_model_panel(
                definition=resolved,
                predictor_long=predictor_long[predictor_long["variable"].isin(predictor_names)],
                target_wide=target_wide,
                imputation=imputation,
                target_first_year=target_first_year,
                target_last_year=target_last_year,
            )
            file_name = OUTPUT_FILE_NAMES[imputation].format(panel_id=resolved.panel_id)
            output_path = panel_dir / file_name
            panel.to_csv(output_path, index=False)
            panel_paths.append(str(output_path.relative_to(processed_dir)))
            imputation_counts = metadata.pop("_imputation_counts_by_variable")
            for _, imputation_row in imputation_counts.iterrows():
                imputation_rows.append(
                    {
                        "panel_id": resolved.panel_id,
                        "imputation": _imputation_output_label(imputation),
                        "variable": imputation_row["variable"],
                        "imputed_values": int(imputation_row["imputed_values"]),
                        "file_name": file_name,
                    }
                )
            summary_rows.append({**metadata, "file_name": file_name})

    coverage_summary = pd.DataFrame(summary_rows)
    imputation_summary = pd.DataFrame(imputation_rows)
    variable_map = pd.DataFrame(panel_variable_rows).drop_duplicates().reset_index(drop=True)
    coverage_summary_path = panel_dir / "model_panel_coverage_summary.csv"
    imputation_summary_path = panel_dir / "model_panel_imputation_summary.csv"
    variable_map_path = panel_dir / "model_panel_variable_map.csv"
    coverage_summary.to_csv(coverage_summary_path, index=False)
    imputation_summary.to_csv(imputation_summary_path, index=False)
    variable_map.to_csv(variable_map_path, index=False)

    return {
        "panel_paths": panel_paths,
        "coverage_summary": coverage_summary,
        "imputation_summary": imputation_summary,
        "variable_map": variable_map,
        "panel_dir_path": str(panel_dir),
        "coverage_summary_path": str(coverage_summary_path),
        "imputation_summary_path": str(imputation_summary_path),
        "variable_map_path": str(variable_map_path),
    }


def load_manifest(raw_dir: Path = RAW_PREDICTORS_V1_DIR) -> pd.DataFrame:
    return pd.read_csv(raw_dir / MANIFEST_FILE_NAME)


def load_selected_raw_series(
    raw_dir: Path,
    manifest: pd.DataFrame,
    variables: Iterable[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read selected raw files into one long country-year table."""
    requested = set(variables)
    frames: list[pd.DataFrame] = []
    map_rows: list[dict[str, object]] = []

    for _, entry in manifest.iterrows():
        variable = str(entry.get("variable", ""))
        if variable not in requested or entry.get("status") != "downloaded":
            continue
        file_path = _resolve_raw_path(raw_dir, entry.get("file_path", ""))
        raw = pd.read_csv(file_path, low_memory=False)
        if entry.get("dataset_id") == "world_bank_data360":
            frame, rise_rule, series_count = _standardize_rise(raw, entry)
        elif _is_standard_country_year(raw):
            frame = _standardize_country_year(raw, entry)
            rise_rule = ""
            series_count = 1
        elif _is_sdmx_country_year(raw):
            frame = _standardize_sdmx(raw, entry)
            rise_rule = ""
            series_count = 1
        else:
            raise ValueError(f"Unsupported raw structure for {variable}: {file_path}")

        frames.append(frame)
        map_rows.append(
            {
                "variable": variable,
                "dataset_id": entry.get("dataset_id", ""),
                "source_variable": entry.get("source_variable", ""),
                "source": entry.get("source", ""),
                "raw_file": file_path.name,
                "source_series_count": series_count,
                "rise_selection_rule": rise_rule,
            }
        )

    missing = sorted(requested - set(row["variable"] for row in map_rows))
    if missing:
        raise ValueError(f"Missing downloaded raw files for variables: {', '.join(missing)}")

    long = pd.concat(frames, ignore_index=True) if frames else _empty_long_frame()
    long["year"] = pd.to_numeric(long["year"], errors="coerce")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long = long.dropna(subset=["year"]).copy()
    long["year"] = long["year"].astype(int)
    long = _deduplicate_long_series(long)
    return long.reset_index(drop=True), pd.DataFrame(map_rows)


def load_target_series(raw_dir: Path, manifest: pd.DataFrame) -> tuple[pd.DataFrame, int, int, pd.DataFrame]:
    target_long, target_map = load_selected_raw_series(raw_dir, manifest, [TARGET_VARIABLE])
    target_wide = target_long.rename(columns={"value": TARGET_VARIABLE})
    target_wide = target_wide.loc[:, ["country_code", "country_name", "year", TARGET_VARIABLE]]
    non_missing = target_wide.dropna(subset=[TARGET_VARIABLE])
    if non_missing.empty:
        raise ValueError(f"Target variable {TARGET_VARIABLE} has no non-missing observations.")
    return target_wide, int(non_missing["year"].min()), int(non_missing["year"].max()), target_map


def resolve_panel_definition(definition: PanelDefinition, predictor_long: pd.DataFrame) -> PanelDefinition:
    predictor_names = [spec.variable for spec in definition.predictors]
    raw_start_year = definition.raw_start_year
    raw_end_year = definition.raw_end_year
    if raw_start_year is None or raw_end_year is None:
        raw_start_year, raw_end_year = common_predictor_year_window(predictor_long, predictor_names)

    anchor_variable = definition.anchor_variable
    if anchor_variable is None:
        anchor_variable, _ = choose_anchor_variable(
            predictor_long,
            predictor_names,
            raw_start_year,
            raw_end_year,
        )

    return PanelDefinition(
        panel_id=definition.panel_id,
        predictors=definition.predictors,
        anchor_variable=anchor_variable,
        raw_start_year=raw_start_year,
        raw_end_year=raw_end_year,
    )


def common_predictor_year_window(
    predictor_long: pd.DataFrame,
    variables: list[str],
) -> tuple[int, int]:
    rows = []
    for variable in variables:
        data = predictor_long.loc[
            predictor_long["variable"].eq(variable) & predictor_long["value"].notna()
        ]
        if data.empty:
            raise ValueError(f"Variable {variable} has no non-missing raw data.")
        rows.append({"variable": variable, "first_year": int(data["year"].min()), "last_year": int(data["year"].max())})
    coverage = pd.DataFrame(rows)
    raw_start_year = int(coverage["first_year"].max())
    raw_end_year = int(coverage["last_year"].min())
    if raw_start_year > raw_end_year:
        raise ValueError(f"No overlapping raw predictor window for variables: {', '.join(variables)}")
    return raw_start_year, raw_end_year


def choose_anchor_variable(
    predictor_long: pd.DataFrame,
    candidate_variables: list[str],
    raw_start_year: int,
    raw_end_year: int,
) -> tuple[str, pd.DataFrame]:
    rows = []
    for variable in candidate_variables:
        data = predictor_long.loc[
            predictor_long["variable"].eq(variable)
            & predictor_long["year"].between(raw_start_year, raw_end_year)
            & predictor_long["value"].notna()
        ]
        rows.append(
            {
                "variable": variable,
                "countries_with_data": int(data["country_code"].nunique()),
                "non_missing_observations": int(len(data)),
                "first_year": int(data["year"].min()) if not data.empty else None,
                "last_year": int(data["year"].max()) if not data.empty else None,
            }
        )
    diagnostics = pd.DataFrame(rows).sort_values(
        ["countries_with_data", "non_missing_observations", "variable"],
        ascending=[True, True, True],
    ).reset_index(drop=True)
    if diagnostics.empty or int(diagnostics.loc[0, "countries_with_data"]) == 0:
        raise ValueError("Cannot choose an anchor variable because no candidate has country coverage.")
    return str(diagnostics.loc[0, "variable"]), diagnostics


def build_model_panel(
    definition: PanelDefinition,
    predictor_long: pd.DataFrame,
    target_wide: pd.DataFrame,
    imputation: str,
    target_first_year: int,
    target_last_year: int,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Create one lagged panel for one panel definition and imputation mode."""
    if imputation not in IMPUTATION_MODES:
        raise ValueError(f"Unsupported imputation mode: {imputation}")
    if definition.anchor_variable is None or definition.raw_start_year is None or definition.raw_end_year is None:
        raise ValueError("Panel definition must have an anchor variable and raw year window before building.")

    predictor_names = [spec.variable for spec in definition.predictors]
    target_year_start = max(definition.raw_start_year + 3, target_first_year)
    target_year_end = min(definition.raw_end_year + 1, target_last_year)
    if target_year_start > target_year_end:
        raise ValueError(f"Panel {definition.panel_id} has no usable target years after lagging.")

    anchor_countries = _anchor_countries(
        predictor_long,
        definition.anchor_variable,
        definition.raw_start_year,
        definition.raw_end_year,
    )
    country_names = _country_name_lookup(predictor_long, target_wide)
    predictor_grid = _predictor_grid(
        predictor_long,
        predictor_names,
        anchor_countries,
        definition.raw_start_year,
        definition.raw_end_year,
        country_names,
    )
    predictor_grid, imputation_counts = _apply_imputation(predictor_grid, imputation)
    panel = _target_grid(anchor_countries, country_names, target_year_start, target_year_end)
    target_values = target_wide.loc[:, ["country_code", "year", TARGET_VARIABLE]]
    panel = panel.merge(target_values, on=["country_code", "year"], how="left")

    for variable in predictor_names:
        panel = _add_lag_columns(panel, predictor_grid, variable)

    feature_columns = [f"{variable}_{suffix}" for variable in predictor_names for suffix in ["lag1", "lag1_3_mean"]]
    panel = panel.loc[:, ["country_code", "country_name", "year", TARGET_VARIABLE, *feature_columns]]
    metadata = _panel_metadata(
        panel,
        definition,
        imputation,
        feature_columns,
        imputation_counts,
        target_year_start,
        target_year_end,
    )
    return panel, metadata


def _resolve_raw_path(raw_dir: Path, value: object) -> Path:
    path = Path(str(value))
    if path.is_absolute():
        return path
    return raw_dir / path


def _is_standard_country_year(raw: pd.DataFrame) -> bool:
    return {"country_code", "country_name", "year", "value"}.issubset(raw.columns)


def _is_sdmx_country_year(raw: pd.DataFrame) -> bool:
    return {"REF_AREA", "TIME_PERIOD", "OBS_VALUE"}.issubset(raw.columns)


def _standardize_country_year(raw: pd.DataFrame, entry: pd.Series) -> pd.DataFrame:
    frame = raw.loc[:, ["country_code", "country_name", "year", "value"]].copy()
    frame["variable"] = entry.get("variable", "")
    return _filter_and_order_long_frame(frame)


def _standardize_sdmx(raw: pd.DataFrame, entry: pd.Series) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "variable": entry.get("variable", ""),
            "country_code": raw["REF_AREA"],
            "country_name": raw.get("Reference area", raw["REF_AREA"]),
            "year": raw["TIME_PERIOD"],
            "value": raw["OBS_VALUE"],
        }
    )
    return _filter_and_order_long_frame(frame)


def _standardize_rise(raw: pd.DataFrame, entry: pd.Series) -> tuple[pd.DataFrame, str, int]:
    variable = str(entry.get("variable", ""))
    prefix = str(entry.get("indicator_prefix", "") or "")
    all_indicator = f"{prefix}ALL"
    data = raw[raw["INDICATOR"].astype(str).str.startswith(prefix)].copy() if prefix else raw.copy()
    if all_indicator in set(data["INDICATOR"].astype(str)):
        selected = data[data["INDICATOR"].astype(str).eq(all_indicator)].copy()
        rise_rule = all_indicator
        source_series_count = 1
    else:
        selected = (
            data.groupby(["REF_AREA", "REF_AREA_LABEL", "TIME_PERIOD"], dropna=False)["OBS_VALUE"]
            .mean()
            .reset_index()
        )
        selected["INDICATOR"] = f"{prefix}MEAN"
        rise_rule = "country_year_mean_across_prefix"
        source_series_count = int(data["INDICATOR"].nunique())

    frame = pd.DataFrame(
        {
            "variable": variable,
            "country_code": selected["REF_AREA"],
            "country_name": selected["REF_AREA_LABEL"],
            "year": selected["TIME_PERIOD"],
            "value": selected["OBS_VALUE"],
        }
    )
    return _filter_and_order_long_frame(frame), rise_rule, source_series_count


def _filter_and_order_long_frame(frame: pd.DataFrame) -> pd.DataFrame:
    frame = filter_country_rows(frame)
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame.dropna(subset=["year"]).copy()
    frame["year"] = frame["year"].astype(int)
    return frame.loc[:, ["variable", "country_code", "country_name", "year", "value"]]


def _deduplicate_long_series(long: pd.DataFrame) -> pd.DataFrame:
    if not long.duplicated(["variable", "country_code", "year"]).any():
        return long
    return (
        long.groupby(["variable", "country_code", "year"], dropna=False)
        .agg(country_name=("country_name", "first"), value=("value", "mean"))
        .reset_index()
        .loc[:, ["variable", "country_code", "country_name", "year", "value"]]
    )


def _empty_long_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=["variable", "country_code", "country_name", "year", "value"])


def _anchor_countries(
    predictor_long: pd.DataFrame,
    anchor_variable: str,
    raw_start_year: int,
    raw_end_year: int,
) -> list[str]:
    anchor = predictor_long.loc[
        predictor_long["variable"].eq(anchor_variable)
        & predictor_long["year"].between(raw_start_year, raw_end_year)
        & predictor_long["value"].notna()
    ]
    countries = sorted(anchor["country_code"].dropna().astype(str).unique())
    if not countries:
        raise ValueError(f"Anchor variable {anchor_variable} has no countries with data.")
    return countries


def _country_name_lookup(predictor_long: pd.DataFrame, target_wide: pd.DataFrame) -> dict[str, str]:
    names = pd.concat(
        [
            predictor_long.loc[:, ["country_code", "country_name"]],
            target_wide.loc[:, ["country_code", "country_name"]],
        ],
        ignore_index=True,
    )
    names = names.dropna(subset=["country_code"]).drop_duplicates("country_code")
    return dict(zip(names["country_code"], names["country_name"]))


def _predictor_grid(
    predictor_long: pd.DataFrame,
    predictor_names: list[str],
    countries: list[str],
    raw_start_year: int,
    raw_end_year: int,
    country_names: dict[str, str],
) -> pd.DataFrame:
    grid = pd.MultiIndex.from_product(
        [predictor_names, countries, range(raw_start_year, raw_end_year + 1)],
        names=["variable", "country_code", "year"],
    ).to_frame(index=False)
    grid["country_name"] = grid["country_code"].map(country_names).fillna(grid["country_code"])
    values = predictor_long.loc[
        predictor_long["variable"].isin(predictor_names)
        & predictor_long["country_code"].isin(countries)
        & predictor_long["year"].between(raw_start_year, raw_end_year),
        ["variable", "country_code", "year", "value"],
    ]
    return grid.merge(values, on=["variable", "country_code", "year"], how="left")


def _apply_imputation(predictor_grid: pd.DataFrame, imputation: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    grid = predictor_grid.copy()
    grid["was_missing_before_imputation"] = grid["value"].isna()
    if imputation == "linear_interpolated":
        grid = grid.sort_values(["variable", "country_code", "year"]).copy()
        grid["value"] = (
            grid.groupby(["variable", "country_code"], group_keys=False)["value"]
            .apply(lambda values: values.interpolate(method="linear", limit_area="inside"))
        )
    grid["was_imputed"] = grid["was_missing_before_imputation"] & grid["value"].notna()
    counts = (
        grid.groupby("variable", dropna=False)["was_imputed"]
        .sum()
        .reset_index(name="imputed_values")
    )
    return grid.drop(columns=["was_missing_before_imputation", "was_imputed"]), counts


def _target_grid(
    countries: list[str],
    country_names: dict[str, str],
    target_year_start: int,
    target_year_end: int,
) -> pd.DataFrame:
    grid = pd.MultiIndex.from_product(
        [countries, range(target_year_start, target_year_end + 1)],
        names=["country_code", "year"],
    ).to_frame(index=False)
    grid["country_name"] = grid["country_code"].map(country_names).fillna(grid["country_code"])
    return grid.loc[:, ["country_code", "country_name", "year"]]


def _add_lag_columns(panel: pd.DataFrame, predictor_grid: pd.DataFrame, variable: str) -> pd.DataFrame:
    source = predictor_grid.loc[
        predictor_grid["variable"].eq(variable),
        ["country_code", "year", "value"],
    ]
    output = panel.copy()
    for lag in [1, 2, 3]:
        lag_frame = source.copy()
        lag_frame["year"] = lag_frame["year"] + lag
        lag_frame = lag_frame.rename(columns={"value": f"{variable}_lag{lag}"})
        output = output.merge(lag_frame, on=["country_code", "year"], how="left")
    lag_columns = [f"{variable}_lag{lag}" for lag in [1, 2, 3]]
    output[f"{variable}_lag1_3_mean"] = output[lag_columns].mean(axis=1, skipna=False)
    output = output.drop(columns=[f"{variable}_lag2", f"{variable}_lag3"])
    return output


def _panel_metadata(
    panel: pd.DataFrame,
    definition: PanelDefinition,
    imputation: str,
    feature_columns: list[str],
    imputation_counts: pd.DataFrame,
    target_year_start: int,
    target_year_end: int,
) -> dict[str, object]:
    lag1_columns = [column for column in feature_columns if column.endswith("_lag1")]
    lag_mean_columns = [column for column in feature_columns if column.endswith("_lag1_3_mean")]
    target_mask = panel[TARGET_VARIABLE].notna()
    lag1_complete_mask = panel[lag1_columns].notna().all(axis=1) if lag1_columns else pd.Series(False, index=panel.index)
    lag_mean_complete_mask = (
        panel[lag_mean_columns].notna().all(axis=1) if lag_mean_columns else pd.Series(False, index=panel.index)
    )
    target_lag1_complete_mask = target_mask & lag1_complete_mask
    target_lag_mean_complete_mask = target_mask & lag_mean_complete_mask
    return {
        "panel_id": definition.panel_id,
        "imputation": _imputation_output_label(imputation),
        "recommended_use": IMPUTATION_RECOMMENDED_USE[imputation],
        "prediction_safe": bool(imputation == "none"),
        "anchor_variable": definition.anchor_variable,
        "predictor_window_start": definition.raw_start_year,
        "predictor_window_end": definition.raw_end_year,
        "target_year_start": target_year_start,
        "target_year_end": target_year_end,
        "countries": int(panel["country_code"].nunique()),
        "rows": int(len(panel)),
        "target_non_missing": int(panel[TARGET_VARIABLE].notna().sum()),
        "lag1_complete_rows": int(lag1_complete_mask.sum()) if lag1_columns else 0,
        "lag1_3_mean_complete_rows": int(lag_mean_complete_mask.sum()) if lag_mean_columns else 0,
        "target_lag1_complete_rows": int(target_lag1_complete_mask.sum()),
        "target_lag1_complete_countries": _country_count(panel, target_lag1_complete_mask),
        "target_lag1_3_mean_complete_rows": int(target_lag_mean_complete_mask.sum()),
        "target_lag1_3_mean_complete_countries": _country_count(panel, target_lag_mean_complete_mask),
        "lag1_complete_target_missing_rows": int((~target_mask & lag1_complete_mask).sum()),
        "lag1_3_mean_complete_target_missing_rows": int((~target_mask & lag_mean_complete_mask).sum()),
        "lag1_feature_non_missing_min": int(panel[lag1_columns].notna().sum().min()) if lag1_columns else 0,
        "lag1_3_feature_non_missing_min": (
            int(panel[lag_mean_columns].notna().sum().min()) if lag_mean_columns else 0
        ),
        "imputed_values_total": int(imputation_counts["imputed_values"].sum()) if not imputation_counts.empty else 0,
        "_imputation_counts_by_variable": imputation_counts,
    }


def _imputation_output_label(imputation: str) -> str:
    return IMPUTATION_OUTPUT_LABELS[imputation]


def _country_count(panel: pd.DataFrame, mask: pd.Series) -> int:
    return int(panel.loc[mask, "country_code"].nunique())


def _panel_variable_map_rows(
    definition: PanelDefinition,
    base_variable_map: pd.DataFrame,
    target_map: pd.DataFrame,
) -> list[dict[str, object]]:
    rows = []
    combined_map = pd.concat([target_map, base_variable_map], ignore_index=True)
    variables = [TARGET_VARIABLE, *[spec.variable for spec in definition.predictors]]
    labels = {spec.variable: spec.label for spec in definition.predictors}
    labels[TARGET_VARIABLE] = "Environment-related patent share of inventions"
    for variable in variables:
        match = combined_map.loc[combined_map["variable"].eq(variable)]
        source_row = match.iloc[0].to_dict() if not match.empty else {}
        rows.append(
            {
                "panel_id": definition.panel_id,
                "variable": variable,
                "role": "target" if variable == TARGET_VARIABLE else "predictor",
                "label": labels.get(variable, variable),
                "is_anchor": bool(variable == definition.anchor_variable),
                "dataset_id": source_row.get("dataset_id", ""),
                "source_variable": source_row.get("source_variable", ""),
                "source": source_row.get("source", ""),
                "raw_file": source_row.get("raw_file", ""),
                "source_series_count": source_row.get("source_series_count", ""),
                "rise_selection_rule": source_row.get("rise_selection_rule", ""),
                "predictor_window_start": definition.raw_start_year,
                "predictor_window_end": definition.raw_end_year,
            }
        )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build lagged model panels from raw predictor files.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_PREDICTORS_V1_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs = run_model_panel_cleaning(args.raw_dir, args.processed_dir)
    print("Wrote model panel files:")
    for file_name in outputs["panel_paths"]:
        print(f"- {file_name}")
    print(f"Panel directory: {outputs['panel_dir_path']}")
    print(f"Coverage summary: {outputs['coverage_summary_path']}")
    print(f"Imputation summary: {outputs['imputation_summary_path']}")
    print(f"Variable map: {outputs['variable_map_path']}")


if __name__ == "__main__":
    main()
