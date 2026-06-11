from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
from urllib.parse import urlparse
import warnings

import pandas as pd

from data_common import AGGREGATE_AREA_CODES, PROCESSED_DIR, RAW_PREDICTORS_V1_DIR, ROOT_DIR, read_xlsx_sheet


FIGURES_ROOT_DIR = ROOT_DIR / "4_analysis" / "figures"
FIGURES_DIR = FIGURES_ROOT_DIR / "predictorsv1"
MANIFEST_FILE_NAME = "raw_download_manifest.csv"
MPLCONFIG_DIR = ROOT_DIR / ".cache" / "matplotlib"
PREDICTOR_AUDIT_FILE_NAME = "raw_predictor_audit.csv"
STALE_INTERMEDIATE_CSVS = [
    "raw_reliability_audit.csv",
    "raw_coverage_summary.csv",
    "raw_coverage_by_year.csv",
    "raw_coverage_panel.csv",
]
STALE_ROOT_FIGURES = [
    "raw_coverage_heatmap.png",
    "raw_coverage_heatmap.pdf",
    "raw_coverage_summary.png",
    "raw_coverage_summary.pdf",
    "raw_country_coverage_rank.png",
    "raw_country_coverage_rank.pdf",
    "raw_variable_country_rank.png",
    "raw_variable_country_rank.pdf",
]
STALE_PREDICTOR_FIGURES = [
    "raw_coverage_heatmap.png",
    "raw_coverage_heatmap.pdf",
    "raw_coverage_summary.png",
    "raw_coverage_summary.pdf",
]

EPU_NON_COUNTRY_SERIES = {"GEPU_current", "GEPU_ppp"}
REQUIRED_COLUMNS = {
    "world_bank_standard": {"country_code", "country_name", "year", "value"},
    "sdmx": {"REF_AREA", "TIME_PERIOD", "OBS_VALUE"},
    "data360": {"REF_AREA", "TIME_PERIOD", "OBS_VALUE", "INDICATOR"},
    "epu": {"Year", "Month"},
}

VARIABLE_GROUPS = {
    "env_patent_share_inventions": "Target and patent dynamics",
    "env_patents_per_million": "Target and patent dynamics",
    "env_technology_share_for_rta": "Target and patent dynamics",
    "env_co_invention_share": "Target and patent dynamics",
    "rd_expenditure_gdp": "R&D and knowledge capacity",
    "researchers_per_million": "R&D and knowledge capacity",
    "tertiary_enrollment": "R&D and knowledge capacity",
    "scientific_journal_articles": "R&D and knowledge capacity",
    "high_tech_exports": "R&D and knowledge capacity",
    "renewable_energy_share": "Energy system",
    "co2_per_capita_ar5": "Energy system",
    "fossil_energy_share": "Energy system",
    "energy_imports_net": "Energy system",
    "eps_index": "Environmental policy",
    "rise_renewable_energy": "Environmental policy",
    "rise_energy_efficiency": "Environmental policy",
    "carbon_tax": "Environmental policy",
    "environmental_tax_revenue": "Environmental policy",
    "economic_policy_uncertainty": "Policy and macro conditions",
    "trade_openness": "Policy and macro conditions",
    "inflation": "Policy and macro conditions",
    "gdp_per_capita_current_usd": "Policy and macro conditions",
    "fdi_net_inflows": "Policy and macro conditions",
    "wgi_regulatory_quality": "Policy and macro conditions",
}

GROUP_ORDER = [
    "Target and patent dynamics",
    "R&D and knowledge capacity",
    "Energy system",
    "Environmental policy",
    "Policy and macro conditions",
]


def load_manifest(raw_dir: Path = RAW_PREDICTORS_V1_DIR) -> pd.DataFrame:
    manifest_path = raw_dir / MANIFEST_FILE_NAME
    return pd.read_csv(manifest_path)


def build_reliability_audit(manifest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, entry in manifest.iterrows():
        file_path = Path(str(entry.get("file_path", ""))) if str(entry.get("file_path", "")) else None
        file_exists = file_path.exists() if file_path is not None else False
        file_size = file_path.stat().st_size if file_exists else 0
        actual_rows: int | None = None
        actual_columns: int | None = None
        shape_matches_manifest = False
        readable = False
        expected_columns_present = False
        observed_structure = ""
        notes = []

        if not file_exists:
            notes.append("file missing")
        elif file_size <= 0:
            notes.append("empty file")
        else:
            try:
                if entry.get("file_format") == "csv":
                    data = pd.read_csv(file_path, low_memory=False)
                    actual_rows = int(len(data))
                    actual_columns = int(len(data.columns))
                    readable = True
                    expected_columns_present = _has_expected_columns(data, entry)
                    observed_structure = _observed_structure(data)
                    shape_matches_manifest = (
                        int(entry.get("rows", -1)) == actual_rows
                        and int(entry.get("columns", -1)) == actual_columns
                    )
                elif entry.get("file_format") == "xlsx":
                    data = read_xlsx_sheet(file_path, sheet_name="EPU")
                    actual_rows = int(len(data))
                    actual_columns = int(len(data.columns))
                    readable = True
                    expected_columns_present = REQUIRED_COLUMNS["epu"].issubset(data.columns)
                    observed_structure = "xlsx:EPU"
                    shape_matches_manifest = True
            except Exception as exc:  # pragma: no cover - defensive audit path
                notes.append(f"{type(exc).__name__}: {exc}")

        reliability_status = "confirmed"
        if (
            entry.get("status") != "downloaded"
            or not file_exists
            or file_size <= 0
            or not readable
            or not expected_columns_present
            or not shape_matches_manifest
        ):
            reliability_status = "review"

        rows.append(
            {
                "dataset_id": entry.get("dataset_id", ""),
                "variable": entry.get("variable", ""),
                "source_variable": entry.get("source_variable", ""),
                "source": entry.get("source", ""),
                "source_url": entry.get("source_url", ""),
                "source_domain": urlparse(str(entry.get("source_url", ""))).netloc,
                "download_status": entry.get("status", ""),
                "file_format": entry.get("file_format", ""),
                "file_exists": bool(file_exists),
                "file_size_bytes_actual": int(file_size),
                "sha256": _sha256(file_path) if file_exists and file_size > 0 else "",
                "actual_rows": actual_rows,
                "actual_columns": actual_columns,
                "manifest_rows": entry.get("rows", None),
                "manifest_columns": entry.get("columns", None),
                "shape_matches_manifest": bool(shape_matches_manifest),
                "expected_columns_present": bool(expected_columns_present),
                "observed_structure": observed_structure,
                "reliability_status": reliability_status,
                "audit_notes": "; ".join(notes),
            }
        )

    return pd.DataFrame(rows)


def build_coverage_panel(manifest: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for _, entry in manifest.iterrows():
        if entry.get("status") != "downloaded":
            continue
        file_path = Path(str(entry.get("file_path", "")))
        if not file_path.exists():
            continue

        if entry.get("file_format") == "csv":
            raw = pd.read_csv(file_path, low_memory=False)
            if _is_world_bank_standard(raw):
                panel = _standardize_world_bank(raw, entry)
            elif entry.get("dataset_id") == "world_bank_data360":
                raw = filter_rise_indicators(raw, str(entry.get("indicator_prefix", "")))
                panel = _standardize_data360(raw, entry)
            elif REQUIRED_COLUMNS["sdmx"].issubset(raw.columns):
                panel = _standardize_sdmx(raw, entry)
            else:
                continue
        elif entry.get("file_format") == "xlsx" and entry.get("dataset_id") == "policy_uncertainty":
            panel = _standardize_epu_workbook(file_path, entry)
        else:
            continue

        if not panel.empty:
            panel = _filter_manifest_year_window(panel, entry)
            frames.append(panel)

    if not frames:
        return pd.DataFrame(columns=_coverage_columns())

    panel = pd.concat(frames, ignore_index=True)
    panel["year"] = pd.to_numeric(panel["year"], errors="coerce")
    panel = panel.dropna(subset=["year"]).copy()
    panel["year"] = panel["year"].astype(int)
    panel["value"] = pd.to_numeric(panel["value"], errors="coerce")
    panel["has_value"] = panel["value"].notna()
    panel["country_code"] = panel["country_code"].fillna("").astype(str).str.strip()
    panel["country_name"] = panel["country_name"].fillna("").astype(str).str.strip()
    panel["entity_key"] = panel["country_code"].where(panel["country_code"].ne(""), panel["country_name"])
    panel["is_country_like"] = panel.apply(_is_country_like_row, axis=1)
    return panel.loc[panel["is_country_like"]].reset_index(drop=True)


def summarize_coverage(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (dataset_id, variable), group in panel.groupby(["dataset_id", "variable"], dropna=False):
        non_missing = group[group["has_value"]]
        rows.append(
            {
                "dataset_id": dataset_id,
                "variable": variable,
                "variable_group": _variable_group(variable),
                "observations_total": int(len(group)),
                "non_missing_observations": int(len(non_missing)),
                "missing_observations": int(group["value"].isna().sum()),
                "entities_total": int(group["entity_key"].nunique()),
                "entities_with_data": int(non_missing["entity_key"].nunique()),
                "years_total": int(group["year"].nunique()),
                "years_with_data": int(non_missing["year"].nunique()),
                "first_year": int(non_missing["year"].min()) if not non_missing.empty else None,
                "last_year": int(non_missing["year"].max()) if not non_missing.empty else None,
                "source_series_count": int(group["series_id"].nunique()),
                "country_code_complete_share": _complete_share(non_missing["country_code"].ne("")),
            }
        )
    summary = pd.DataFrame(rows)
    if summary.empty:
        return summary
    summary["variable_group"] = pd.Categorical(summary["variable_group"], GROUP_ORDER, ordered=True)
    return summary.sort_values(["variable_group", "entities_with_data", "variable"], ascending=[True, False, True])


def build_variable_year_coverage(panel: pd.DataFrame) -> pd.DataFrame:
    non_missing = panel[panel["has_value"]]
    return (
        non_missing.groupby(["dataset_id", "variable", "year"], dropna=False)["entity_key"]
        .nunique()
        .reset_index(name="entities_with_data")
    )


def build_country_coverage_summary(panel: pd.DataFrame) -> pd.DataFrame:
    country_panel = panel.loc[panel["country_code"].astype(str).str.strip().ne("")].copy()
    country_panel["country_code"] = country_panel["country_code"].astype(str).str.strip()
    country_panel = country_panel.loc[
        country_panel["country_code"].str.fullmatch(r"[A-Z]{3}")
        & ~country_panel["country_code"].isin(AGGREGATE_AREA_CODES)
    ].copy()
    if country_panel.empty:
        return pd.DataFrame(
            columns=[
                "country_code",
                "country_name",
                "non_missing_variable_years",
                "total_variable_years",
                "coverage_share",
                "variables_with_data",
                "years_with_any_data",
                "first_year",
                "last_year",
            ]
        )

    country_panel["country_name"] = country_panel["country_name"].astype(str).str.strip()
    country_panel["has_value"] = country_panel["has_value"].astype(bool)

    country_names = (
        country_panel.sort_values(["country_code", "country_name"])
        .drop_duplicates("country_code")
        .loc[:, ["country_code", "country_name"]]
    )
    countries = country_names.loc[:, ["country_code"]].drop_duplicates()
    variable_years = country_panel.loc[:, ["variable", "year"]].drop_duplicates()
    grid = countries.merge(variable_years, how="cross")

    availability = (
        country_panel.groupby(["country_code", "variable", "year"], dropna=False)["has_value"]
        .max()
        .reset_index()
    )
    grid = grid.merge(availability, on=["country_code", "variable", "year"], how="left")
    grid["has_value"] = grid["has_value"].where(grid["has_value"].notna(), False).astype(bool)

    observed = grid.loc[grid["has_value"]]
    summary = (
        grid.groupby("country_code", dropna=False)
        .agg(
            non_missing_variable_years=("has_value", "sum"),
            total_variable_years=("has_value", "size"),
        )
        .reset_index()
    )
    summary["coverage_share"] = summary["non_missing_variable_years"] / summary["total_variable_years"]

    detail = (
        observed.groupby("country_code", dropna=False)
        .agg(
            variables_with_data=("variable", "nunique"),
            years_with_any_data=("year", "nunique"),
            first_year=("year", "min"),
            last_year=("year", "max"),
        )
        .reset_index()
    )
    summary = summary.merge(country_names, on="country_code", how="left")
    summary = summary.merge(detail, on="country_code", how="left")
    for column in ["variables_with_data", "years_with_any_data", "first_year", "last_year"]:
        summary[column] = summary[column].fillna(0).astype(int)

    return summary.sort_values(
        ["coverage_share", "non_missing_variable_years", "country_code"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def build_variable_country_rank(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame(
            columns=[
                "variable",
                "variable_group",
                "entities_with_data",
                "entities_total",
                "country_coverage_share",
                "years_with_data",
                "first_year",
                "last_year",
                "coverage_year_label",
            ]
        )

    rank = summary.copy()
    rank["entities_with_data"] = pd.to_numeric(rank["entities_with_data"], errors="coerce").fillna(0).astype(int)
    rank["entities_total"] = pd.to_numeric(rank["entities_total"], errors="coerce").fillna(0).astype(int)
    rank["years_with_data"] = pd.to_numeric(rank["years_with_data"], errors="coerce").fillna(0).astype(int)
    if "first_year" not in rank.columns:
        rank["first_year"] = pd.NA
    if "last_year" not in rank.columns:
        rank["last_year"] = pd.NA
    rank["first_year"] = pd.to_numeric(rank["first_year"], errors="coerce")
    rank["last_year"] = pd.to_numeric(rank["last_year"], errors="coerce")
    rank["coverage_year_label"] = rank.apply(_coverage_year_label, axis=1)
    rank["country_coverage_share"] = rank["entities_with_data"] / rank["entities_total"].where(
        rank["entities_total"].ne(0)
    )
    return rank.sort_values(
        ["entities_with_data", "years_with_data", "variable"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def build_predictor_audit(reliability_audit: pd.DataFrame, coverage_summary: pd.DataFrame) -> pd.DataFrame:
    if reliability_audit.empty:
        return reliability_audit.copy()

    coverage_columns = [
        "dataset_id",
        "variable",
        "variable_group",
        "observations_total",
        "non_missing_observations",
        "missing_observations",
        "entities_total",
        "entities_with_data",
        "years_total",
        "years_with_data",
        "first_year",
        "last_year",
        "source_series_count",
        "country_code_complete_share",
    ]
    available_coverage_columns = [column for column in coverage_columns if column in coverage_summary.columns]
    merged = reliability_audit.merge(
        coverage_summary.loc[:, available_coverage_columns],
        on=["dataset_id", "variable"],
        how="left",
    )
    return merged.sort_values(["reliability_status", "dataset_id", "variable"]).reset_index(drop=True)


def filter_rise_indicators(data: pd.DataFrame, indicator_prefix: str) -> pd.DataFrame:
    if not indicator_prefix:
        return data.copy()
    return data[data["INDICATOR"].astype(str).str.startswith(indicator_prefix)].reset_index(drop=True)


def run_coverage_diagnostics(
    raw_dir: Path = RAW_PREDICTORS_V1_DIR,
    processed_dir: Path = PROCESSED_DIR,
    figures_dir: Path = FIGURES_DIR,
) -> dict[str, object]:
    manifest = load_manifest(raw_dir)
    audit = build_reliability_audit(manifest)
    panel = build_coverage_panel(manifest)
    summary = summarize_coverage(panel)
    by_year = build_variable_year_coverage(panel)
    country_summary = build_country_coverage_summary(panel)
    variable_rank = build_variable_country_rank(summary)
    predictor_audit = build_predictor_audit(audit, summary)

    processed_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    _remove_stale_intermediate_csvs(processed_dir)
    _remove_stale_root_figures(figures_dir)
    _remove_stale_predictor_figures(figures_dir)
    predictor_audit_path = processed_dir / PREDICTOR_AUDIT_FILE_NAME
    predictor_audit.to_csv(predictor_audit_path, index=False)

    figure_paths = make_coverage_figures(summary, by_year, country_summary, variable_rank, figures_dir)
    return {
        "manifest": manifest,
        "reliability_audit": audit,
        "coverage_panel": panel,
        "coverage_summary": summary,
        "coverage_by_year": by_year,
        "country_coverage_summary": country_summary,
        "variable_country_rank": variable_rank,
        "predictor_audit": predictor_audit,
        "predictor_audit_path": str(predictor_audit_path),
        "figure_paths": figure_paths,
    }


def _remove_stale_intermediate_csvs(processed_dir: Path) -> None:
    for file_name in STALE_INTERMEDIATE_CSVS:
        path = processed_dir / file_name
        if path.exists():
            path.unlink()


def _remove_stale_root_figures(figures_dir: Path) -> None:
    if figures_dir != FIGURES_DIR:
        return
    for file_name in STALE_ROOT_FIGURES:
        path = FIGURES_ROOT_DIR / file_name
        if path.exists():
            path.unlink()


def _remove_stale_predictor_figures(figures_dir: Path) -> None:
    for file_name in STALE_PREDICTOR_FIGURES:
        path = figures_dir / file_name
        if path.exists():
            path.unlink()


def make_coverage_figures(
    summary: pd.DataFrame,
    by_year: pd.DataFrame,
    country_summary: pd.DataFrame,
    variable_rank: pd.DataFrame,
    figures_dir: Path = FIGURES_DIR,
) -> dict[str, str]:
    _configure_matplotlib()
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="whitegrid", context="paper")
    palette = {
        "Target and patent dynamics": "#3B6EA8",
        "R&D and knowledge capacity": "#5F9E6E",
        "Energy system": "#D79A3B",
        "Environmental policy": "#8E63A9",
        "Policy and macro conditions": "#4D4D4D",
    }

    variable_rank_png = figures_dir / "raw_variable_country_rank.png"
    variable_rank_pdf = figures_dir / "raw_variable_country_rank.pdf"
    fig, _ = make_variable_country_rank_figure(variable_rank, palette)
    _save_figure(fig, variable_rank_png, variable_rank_pdf)

    country_png = figures_dir / "raw_country_coverage_rank.png"
    country_pdf = figures_dir / "raw_country_coverage_rank.pdf"
    fig, _ = make_country_coverage_rank_figure(country_summary)
    _save_figure(fig, country_png, country_pdf)

    return {
        "variable_country_rank_png": str(variable_rank_png),
        "variable_country_rank_pdf": str(variable_rank_pdf),
        "country_coverage_rank_png": str(country_png),
        "country_coverage_rank_pdf": str(country_pdf),
    }


def make_variable_country_rank_figure(
    variable_rank: pd.DataFrame,
    palette: dict[str, str],
):
    _configure_matplotlib()
    import matplotlib.patheffects as path_effects
    import matplotlib.pyplot as plt

    variable_plot = variable_rank.sort_values(
        ["entities_with_data", "years_with_data", "variable"],
        ascending=[True, True, False],
    ).copy()
    variable_plot["variable_group"] = variable_plot["variable_group"].astype(str)
    colors = [palette.get(group, "#777777") for group in variable_plot["variable_group"]]
    fig_height = max(8, 0.36 * len(variable_plot) + 2.2)
    fig, ax_count = plt.subplots(figsize=(14.8, fig_height), constrained_layout=True)
    ax_year = ax_count.twiny()
    ax_year.patch.set_visible(False)
    ax_year.set_zorder(ax_count.get_zorder() + 1)

    y_positions = list(range(len(variable_plot)))
    bar_y = [position - 0.11 for position in y_positions]
    line_y = [position + 0.25 for position in y_positions]
    ax_count.barh(bar_y, variable_plot["entities_with_data"], color=colors, edgecolor="none", height=0.52, alpha=0.92)
    ax_count.set_yticks(y_positions)
    ax_count.set_yticklabels([_labelize(v) for v in variable_plot["variable"]], fontsize=8)
    ax_count.set_xlabel("Countries/entities with non-missing data")
    ax_count.set_ylabel("")
    ax_count.grid(axis="x", color="#E5E5E5", linewidth=0.7)
    ax_count.grid(axis="y", visible=False)
    ax_count.spines[["top", "right", "left"]].set_visible(False)
    ax_count.tick_params(axis="y", length=0)
    ax_count.set_ylim(-0.6, len(variable_plot) - 0.35)
    x_max = max(float(variable_plot["entities_with_data"].max()) if not variable_plot.empty else 0.0, 1.0)
    ax_count.set_xlim(0, x_max * 1.22)

    for index, row in enumerate(variable_plot.itertuples(index=False)):
        label_inside = row.entities_with_data > x_max * 0.18
        ax_count.text(
            row.entities_with_data - x_max * 0.018 if label_inside else row.entities_with_data + x_max * 0.014,
            bar_y[index],
            f"{row.entities_with_data}",
            va="center",
            ha="right" if label_inside else "left",
            fontsize=7.6,
            color="white" if label_inside else "#333333",
            fontweight="bold" if label_inside else "normal",
        )

    year_rows = variable_plot.dropna(subset=["first_year", "last_year"]).copy()
    if not year_rows.empty:
        min_year = int(year_rows["first_year"].min())
        max_year = int(year_rows["last_year"].max())
        axis_min = min_year - 1
        axis_max = max_year + 5
        ax_year.set_xlim(axis_min, axis_max)
        ax_year.set_ylim(ax_count.get_ylim())
        for index, row in enumerate(variable_plot.itertuples(index=False)):
            if pd.isna(row.first_year) or pd.isna(row.last_year):
                continue
            color = palette.get(row.variable_group, "#333333")
            line = ax_year.hlines(
                y=line_y[index],
                xmin=row.first_year,
                xmax=row.last_year,
                color=color,
                linewidth=2.0,
                linestyle=(0, (3.0, 2.0)),
                alpha=0.96,
                zorder=4,
            )
            line.set_path_effects([path_effects.Stroke(linewidth=3.8, foreground="white"), path_effects.Normal()])
            points = ax_year.scatter(
                [row.first_year, row.last_year],
                [line_y[index], line_y[index]],
                s=17,
                color=color,
                edgecolor="white",
                linewidth=0.45,
                zorder=5,
            )
            points.set_path_effects([path_effects.Stroke(linewidth=1.5, foreground="white"), path_effects.Normal()])
            ax_year.text(
                row.last_year + 0.45,
                line_y[index],
                row.coverage_year_label,
                va="center",
                ha="left",
                fontsize=6.7,
                color="#333333",
                zorder=6,
            )
        tick_start = min_year if min_year % 5 == 0 else min_year + (5 - min_year % 5)
        ticks = [min_year] + list(range(tick_start, max_year + 1, 5))
        if max_year not in ticks:
            ticks.append(max_year)
        ax_year.set_xticks(sorted(set(ticks)))
    ax_year.set_xlabel("Coverage years")
    ax_year.xaxis.set_label_position("top")
    ax_year.xaxis.tick_top()
    ax_year.grid(axis="x", color="#E9E9E9", linewidth=0.7)
    ax_year.grid(axis="y", visible=False)
    ax_year.spines[["right", "left", "bottom"]].set_visible(False)
    ax_year.tick_params(axis="y", length=0, labelleft=False)
    ax_year.tick_params(axis="x", labelsize=8)

    handles = [
        plt.Line2D([0], [0], marker="s", linestyle="", color=color, label=group, markersize=8)
        for group, color in palette.items()
        if group in set(variable_plot["variable_group"])
    ]
    fig.legend(handles=handles, loc="center left", ncol=1, frameon=False, bbox_to_anchor=(1.01, 0.5))
    fig.suptitle(
        "Variable Ranking by Country Coverage and Year Span",
        x=0.5,
        ha="center",
        fontsize=14,
        fontweight="bold",
    )
    return fig, (ax_count, ax_year)


def make_country_coverage_rank_figure(country_summary: pd.DataFrame):
    _configure_matplotlib()
    import matplotlib.pyplot as plt
    import seaborn as sns

    country_plot = country_summary.sort_values(
        ["coverage_share", "non_missing_variable_years", "country_code"],
        ascending=[True, True, False],
    ).copy()
    fig_height = max(10, 0.16 * len(country_plot) + 2.4)
    fig, ax = plt.subplots(figsize=(11.5, fig_height), constrained_layout=True)
    y_positions = range(len(country_plot))
    colors = sns.color_palette("crest", n_colors=max(len(country_plot), 1))
    ax.barh(
        y_positions,
        country_plot["coverage_share"] * 100,
        color=colors,
        edgecolor="none",
        height=0.72,
    )
    country_labels = [
        f"{row.country_code} - {row.country_name}" if row.country_name else row.country_code
        for row in country_plot.itertuples(index=False)
    ]
    ax.set_yticks(list(y_positions))
    ax.set_yticklabels(country_labels, fontsize=5.6)
    ax.set_xlabel("Coverage share of ISO-coded variable-year opportunities (%)")
    ax.set_ylabel("")
    ax.set_xlim(0, 100)
    ax.grid(axis="x", color="#E5E5E5", linewidth=0.7)
    ax.grid(axis="y", visible=False)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    for index, row in enumerate(country_plot.itertuples(index=False)):
        ax.text(
            min(row.coverage_share * 100 + 0.8, 99.2),
            index,
            f"{row.coverage_share * 100:.1f}",
            va="center",
            ha="left" if row.coverage_share < 0.985 else "right",
            fontsize=5.3,
            color="#333333",
        )
    fig.suptitle(
        "Country Coverage Ranking Across Raw Variables",
        x=0.5,
        ha="center",
        fontsize=14,
        fontweight="bold",
    )
    return fig, ax


def _standardize_world_bank(raw: pd.DataFrame, entry: pd.Series) -> pd.DataFrame:
    frame = raw[["country_code", "country_name", "year", "value"]].copy()
    return _add_common_columns(frame, entry, series_id=entry.get("source_variable", ""), series_label=entry.get("variable", ""))


def _standardize_sdmx(raw: pd.DataFrame, entry: pd.Series) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "country_code": raw["REF_AREA"],
            "country_name": raw.get("Reference area", raw["REF_AREA"]),
            "year": raw["TIME_PERIOD"],
            "value": raw["OBS_VALUE"],
        }
    )
    return _add_common_columns(frame, entry, series_id=entry.get("source_variable", ""), series_label=entry.get("variable", ""))


def _standardize_data360(raw: pd.DataFrame, entry: pd.Series) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "country_code": raw["REF_AREA"],
            "country_name": raw["REF_AREA_LABEL"],
            "year": raw["TIME_PERIOD"],
            "value": raw["OBS_VALUE"],
            "series_id": raw["INDICATOR"],
            "series_label": raw["INDICATOR_LABEL"],
        }
    )
    return _add_common_columns(frame, entry)


def _standardize_epu_workbook(file_path: Path, entry: pd.Series) -> pd.DataFrame:
    raw = read_xlsx_sheet(file_path, sheet_name="EPU")
    raw["year"] = pd.to_numeric(raw["Year"], errors="coerce")
    value_columns = [column for column in raw.columns if column not in {"Year", "Month", "year"}]
    value_columns = [column for column in value_columns if column not in EPU_NON_COUNTRY_SERIES]
    long = raw.melt(id_vars=["year"], value_vars=value_columns, var_name="country_name", value_name="value")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    annual = (
        long.groupby(["country_name", "year"], dropna=False)["value"]
        .mean()
        .reset_index()
        .dropna(subset=["year"])
    )
    annual["country_code"] = ""
    annual["series_id"] = annual["country_name"]
    annual["series_label"] = annual["country_name"]
    return _add_common_columns(annual, entry)


def _add_common_columns(
    frame: pd.DataFrame,
    entry: pd.Series,
    series_id: str | None = None,
    series_label: str | None = None,
) -> pd.DataFrame:
    frame = frame.copy()
    frame["dataset_id"] = entry.get("dataset_id", "")
    frame["variable"] = entry.get("variable", "")
    frame["source_variable"] = entry.get("source_variable", "")
    if "series_id" not in frame.columns:
        frame["series_id"] = series_id or entry.get("source_variable", "")
    if "series_label" not in frame.columns:
        frame["series_label"] = series_label or entry.get("variable", "")
    return frame.loc[:, _coverage_columns()]


def _filter_manifest_year_window(panel: pd.DataFrame, entry: pd.Series) -> pd.DataFrame:
    start_year = pd.to_numeric(entry.get("start_year", None), errors="coerce")
    end_year = pd.to_numeric(entry.get("end_year", None), errors="coerce")
    if pd.isna(start_year) or pd.isna(end_year):
        return panel
    years = pd.to_numeric(panel["year"], errors="coerce")
    return panel.loc[years.between(int(start_year), int(end_year))].copy()


def _coverage_columns() -> list[str]:
    return [
        "dataset_id",
        "variable",
        "source_variable",
        "series_id",
        "series_label",
        "country_code",
        "country_name",
        "year",
        "value",
    ]


def _has_expected_columns(data: pd.DataFrame, entry: pd.Series) -> bool:
    if _is_world_bank_standard(data):
        return True
    if entry.get("dataset_id") == "world_bank_data360":
        return REQUIRED_COLUMNS["data360"].issubset(data.columns)
    if REQUIRED_COLUMNS["sdmx"].issubset(data.columns):
        return True
    return False


def _is_world_bank_standard(data: pd.DataFrame) -> bool:
    return REQUIRED_COLUMNS["world_bank_standard"].issubset(data.columns)


def _observed_structure(data: pd.DataFrame) -> str:
    if "STRUCTURE_ID" in data.columns and data["STRUCTURE_ID"].notna().any():
        return str(data["STRUCTURE_ID"].dropna().iloc[0])
    if "DATABASE_ID" in data.columns and data["DATABASE_ID"].notna().any():
        return str(data["DATABASE_ID"].dropna().iloc[0])
    if "dataset_id" in data.columns and data["dataset_id"].notna().any():
        return str(data["dataset_id"].dropna().iloc[0])
    return ""


def _sha256(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_country_like_row(row: pd.Series) -> bool:
    code = str(row.get("country_code", "")).strip()
    if code:
        return len(code) == 3 and code not in AGGREGATE_AREA_CODES
    return bool(str(row.get("country_name", "")).strip())


def _complete_share(values: pd.Series) -> float:
    if len(values) == 0:
        return 0.0
    return float(values.mean())


def _coverage_year_label(row: pd.Series) -> str:
    if pd.isna(row.get("first_year")) or pd.isna(row.get("last_year")):
        return ""
    return f"{int(row['first_year'])}-{int(row['last_year'])}"


def _variable_group(variable: str) -> str:
    return VARIABLE_GROUPS.get(variable, "Other")


def _labelize(value: str) -> str:
    label = str(value).replace("_", " ")
    replacements = {
        "co2": "CO2",
        "rd": "R&D",
        "rta": "RTA",
        "rise": "RISE",
        "eps": "EPS",
        "gdp": "GDP",
        "wgi": "WGI",
        "fdi": "FDI",
        "usd": "USD",
        "ar5": "AR5",
    }
    return " ".join(replacements.get(part, part) for part in label.split())


def _configure_matplotlib() -> None:
    MPLCONFIG_DIR.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(MPLCONFIG_DIR)
    os.environ["XDG_CACHE_HOME"] = str(ROOT_DIR / ".cache")
    os.environ["MPLBACKEND"] = "Agg"
    warnings.filterwarnings("ignore", message=".*Glyph.*missing from font.*")


def _save_figure(fig, png_path: Path, pdf_path: Path) -> None:
    fig.savefig(png_path, dpi=320, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf_path, bbox_inches="tight", facecolor="white")
    import matplotlib.pyplot as plt

    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit raw downloads and build coverage diagnostics.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_PREDICTORS_V1_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    parser.add_argument("--figures-dir", type=Path, default=FIGURES_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs = run_coverage_diagnostics(args.raw_dir, args.processed_dir, args.figures_dir)
    summary = outputs["coverage_summary"]
    audit = outputs["predictor_audit"]
    print(f"Combined audit CSV: {outputs['predictor_audit_path']}")
    print("Reliability status counts:")
    print(audit["reliability_status"].value_counts(dropna=False).to_string())
    print("\nCoverage summary:")
    print(summary.to_string(index=False))
    print("\nFigure paths:")
    for name, path in outputs["figure_paths"].items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
