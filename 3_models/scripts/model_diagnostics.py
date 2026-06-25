from __future__ import annotations

import numpy as np
import pandas as pd

from model_data import ChronologicalSplit


MISSINGNESS_PATTERNS = [
    "complete",
    "late_start",
    "early_end",
    "bounded_coverage_window",
    "intermittent_gaps",
    "all_missing",
]


def build_correlation_diagnostics(
    *,
    split: ChronologicalSplit,
    feature_columns: list[str],
    target_column: str,
    coefficients: pd.DataFrame,
    panel_id: str,
    panel_label: str,
    fitted_model=None,
) -> dict[str, object]:
    """Compute train+validation correlation diagnostics without using final test labels."""
    analysis_panel = pd.concat([split.train, split.validation], ignore_index=True)
    analysis_features, correlation_design = _correlation_feature_frame(
        analysis_panel,
        feature_columns,
        fitted_model=fitted_model,
    )
    correlation_panel = pd.concat(
        [analysis_panel.loc[:, ["year", target_column]].reset_index(drop=True), analysis_features],
        axis=1,
    )
    spearman = feature_correlation_matrix(correlation_panel, feature_columns, method="spearman")
    pearson = feature_correlation_matrix(correlation_panel, feature_columns, method="pearson")
    target_correlations = predictor_target_correlations(
        correlation_panel,
        feature_columns,
        target_column,
        method="spearman",
        panel_id=panel_id,
        panel_label=panel_label,
    )
    top_pairs = top_feature_correlations(
        spearman,
        method="spearman",
        panel_id=panel_id,
        panel_label=panel_label,
    )
    alignment = coefficient_correlation_alignment(
        coefficients,
        target_correlations,
        panel_id=panel_id,
        panel_label=panel_label,
    )
    return {
        "analysis_year_start": int(analysis_panel["year"].min()),
        "analysis_year_end": int(analysis_panel["year"].max()),
        "analysis_rows": int(len(analysis_panel)),
        "correlation_design": correlation_design,
        "spearman_feature_correlations": spearman,
        "pearson_feature_correlations": pearson,
        "top_correlated_pairs": top_pairs,
        "target_correlations": target_correlations,
        "coefficient_correlation_alignment": alignment,
    }


def build_missingness_pattern_diagnostics(
    *,
    panel: pd.DataFrame,
    feature_columns: list[str],
    country_code_column: str = "country_code",
    country_name_column: str = "country_name",
    year_column: str = "year",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Classify country-feature missingness sequences across observed model rows."""
    required_columns = {country_code_column, country_name_column, year_column, *feature_columns}
    missing_columns = sorted(required_columns.difference(panel.columns))
    if missing_columns:
        raise ValueError(f"panel is missing required columns: {missing_columns}")

    detail_rows = []
    grouped = (
        panel.sort_values([country_code_column, year_column])
        .groupby(country_code_column, dropna=False, sort=False)
    )
    for feature in feature_columns:
        for country_code, country_panel in grouped:
            country_panel = country_panel.sort_values(year_column)
            country_name = _representative_country_name(country_panel, country_name_column)
            pattern_detail = _classify_missingness_pattern(country_panel, feature, year_column)
            detail_rows.append(
                {
                    "feature": feature,
                    "country_code": country_code,
                    "country_name": country_name,
                    **pattern_detail,
                }
            )

    detail_columns = [
        "feature",
        "country_code",
        "country_name",
        "year_start",
        "year_end",
        "calendar_year_span",
        "total_years",
        "observed_years",
        "missing_years",
        "missing_share",
        "first_observed_year",
        "last_observed_year",
        "leading_missing_years",
        "internal_missing_years",
        "trailing_missing_years",
        "missingness_pattern",
    ]
    detail = pd.DataFrame(detail_rows, columns=detail_columns)
    summary = _summarize_missingness_patterns(detail)
    return summary, detail


def feature_correlation_matrix(
    panel: pd.DataFrame,
    feature_columns: list[str],
    *,
    method: str,
) -> pd.DataFrame:
    """Return a feature-by-feature correlation matrix."""
    if method not in {"spearman", "pearson"}:
        raise ValueError("method must be 'spearman' or 'pearson'")
    matrix = panel.loc[:, feature_columns].corr(method=method)
    matrix.index.name = "feature"
    return matrix


def _classify_missingness_pattern(country_panel: pd.DataFrame, feature: str, year_column: str) -> dict[str, object]:
    years = country_panel[year_column].astype(int).to_numpy()
    observed = country_panel[feature].notna().to_numpy()
    total_years = int(len(observed))
    observed_years = int(observed.sum())
    missing_years = int(total_years - observed_years)

    if total_years == 0:
        return {
            "year_start": np.nan,
            "year_end": np.nan,
            "calendar_year_span": 0,
            "total_years": 0,
            "observed_years": 0,
            "missing_years": 0,
            "missing_share": np.nan,
            "first_observed_year": np.nan,
            "last_observed_year": np.nan,
            "leading_missing_years": 0,
            "internal_missing_years": 0,
            "trailing_missing_years": 0,
            "missingness_pattern": "all_missing",
        }

    if observed_years == 0:
        return {
            "year_start": int(years.min()),
            "year_end": int(years.max()),
            "calendar_year_span": int(years.max() - years.min() + 1),
            "total_years": total_years,
            "observed_years": 0,
            "missing_years": missing_years,
            "missing_share": float(missing_years / total_years),
            "first_observed_year": np.nan,
            "last_observed_year": np.nan,
            "leading_missing_years": total_years,
            "internal_missing_years": 0,
            "trailing_missing_years": 0,
            "missingness_pattern": "all_missing",
        }

    first_observed_index = int(np.flatnonzero(observed)[0])
    last_observed_index = int(np.flatnonzero(observed)[-1])
    leading_missing_years = first_observed_index
    trailing_missing_years = total_years - last_observed_index - 1
    internal_missing_years = int((~observed[first_observed_index : last_observed_index + 1]).sum())

    if missing_years == 0:
        pattern = "complete"
    elif internal_missing_years > 0:
        pattern = "intermittent_gaps"
    elif leading_missing_years > 0 and trailing_missing_years > 0:
        pattern = "bounded_coverage_window"
    elif leading_missing_years > 0:
        pattern = "late_start"
    elif trailing_missing_years > 0:
        pattern = "early_end"
    else:
        pattern = "complete"

    return {
        "year_start": int(years.min()),
        "year_end": int(years.max()),
        "calendar_year_span": int(years.max() - years.min() + 1),
        "total_years": total_years,
        "observed_years": observed_years,
        "missing_years": missing_years,
        "missing_share": float(missing_years / total_years),
        "first_observed_year": int(years[first_observed_index]),
        "last_observed_year": int(years[last_observed_index]),
        "leading_missing_years": int(leading_missing_years),
        "internal_missing_years": int(internal_missing_years),
        "trailing_missing_years": int(trailing_missing_years),
        "missingness_pattern": pattern,
    }


def _summarize_missingness_patterns(detail: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feature, feature_detail in detail.groupby("feature", sort=False):
        country_year_rows = int(feature_detail["total_years"].sum())
        missing_country_year_rows = int(feature_detail["missing_years"].sum())
        pattern_counts = feature_detail["missingness_pattern"].value_counts().to_dict()
        rows.append(
            {
                "feature": feature,
                "countries": int(feature_detail["country_code"].nunique(dropna=False)),
                "country_year_rows": country_year_rows,
                "observed_country_year_rows": int(feature_detail["observed_years"].sum()),
                "missing_country_year_rows": missing_country_year_rows,
                "missing_share": float(missing_country_year_rows / country_year_rows)
                if country_year_rows
                else np.nan,
                "first_observed_year_min": feature_detail["first_observed_year"].min(),
                "last_observed_year_max": feature_detail["last_observed_year"].max(),
                **{
                    f"{pattern}_countries": int(pattern_counts.get(pattern, 0))
                    for pattern in MISSINGNESS_PATTERNS
                },
            }
        )
    summary = pd.DataFrame(rows)
    if summary.empty:
        return pd.DataFrame(
            columns=[
                "feature",
                "countries",
                "country_year_rows",
                "observed_country_year_rows",
                "missing_country_year_rows",
                "missing_share",
                "first_observed_year_min",
                "last_observed_year_max",
                *[f"{pattern}_countries" for pattern in MISSINGNESS_PATTERNS],
            ]
        )
    return summary.sort_values(["missing_share", "feature"], ascending=[False, True]).reset_index(drop=True)


def _representative_country_name(country_panel: pd.DataFrame, country_name_column: str) -> object:
    names = country_panel[country_name_column].dropna()
    if names.empty:
        return np.nan
    return names.iloc[0]


def top_feature_correlations(
    correlation_matrix: pd.DataFrame,
    *,
    method: str,
    panel_id: str,
    panel_label: str,
    limit: int = 20,
) -> pd.DataFrame:
    """Return top absolute off-diagonal feature-correlation pairs."""
    rows = []
    columns = list(correlation_matrix.columns)
    for left_index, feature_a in enumerate(columns):
        for feature_b in columns[left_index + 1 :]:
            correlation = correlation_matrix.loc[feature_a, feature_b]
            if pd.isna(correlation):
                continue
            rows.append(
                {
                    "panel_id": panel_id,
                    "panel_label": panel_label,
                    "method": method,
                    "feature_a": feature_a,
                    "feature_b": feature_b,
                    "correlation": float(correlation),
                    "abs_correlation": float(abs(correlation)),
                }
            )
    columns_out = [
        "panel_id",
        "panel_label",
        "method",
        "feature_a",
        "feature_b",
        "correlation",
        "abs_correlation",
    ]
    if not rows:
        return pd.DataFrame(columns=columns_out)
    return (
        pd.DataFrame(rows, columns=columns_out)
        .sort_values(["abs_correlation", "feature_a", "feature_b"], ascending=[False, True, True])
        .head(limit)
        .reset_index(drop=True)
    )


def predictor_target_correlations(
    panel: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
    *,
    method: str,
    panel_id: str,
    panel_label: str,
) -> pd.DataFrame:
    """Return feature-target correlations for the supplied analysis panel."""
    rows = []
    for feature in feature_columns:
        subset = panel.loc[:, [feature, target_column]].dropna()
        correlation = subset[feature].corr(subset[target_column], method=method)
        rows.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "method": method,
                "feature": feature,
                "target": target_column,
                "non_missing_rows": int(len(subset)),
                "correlation": float(correlation) if pd.notna(correlation) else np.nan,
                "abs_correlation": float(abs(correlation)) if pd.notna(correlation) else np.nan,
            }
        )
    return pd.DataFrame(rows).sort_values("abs_correlation", ascending=False).reset_index(drop=True)


def coefficient_correlation_alignment(
    coefficients: pd.DataFrame,
    target_correlations: pd.DataFrame,
    *,
    panel_id: str,
    panel_label: str,
) -> pd.DataFrame:
    """Compare ElasticNet coefficient signs with simple feature-target correlations."""
    merge_columns = ["feature", "correlation", "abs_correlation", "non_missing_rows"]
    output = coefficients.merge(
        target_correlations.loc[:, merge_columns].rename(
            columns={
                "correlation": "target_correlation",
                "abs_correlation": "abs_target_correlation",
                "non_missing_rows": "target_correlation_rows",
            }
        ),
        on="feature",
        how="left",
    )
    output["coefficient_sign"] = np.sign(output["coefficient"]).astype(int)
    output["target_correlation_sign"] = np.sign(output["target_correlation"]).fillna(0).astype(int)
    output["coefficient_status"] = np.where(output["coefficient"].abs() <= 1e-12, "shrunk_to_zero", "nonzero")
    output["sign_aligned"] = (
        output["coefficient_status"].eq("nonzero")
        & output["target_correlation_sign"].ne(0)
        & output["coefficient_sign"].eq(output["target_correlation_sign"])
    )
    if "panel_id" not in output.columns:
        output.insert(0, "panel_id", panel_id)
    if "panel_label" not in output.columns:
        output.insert(1, "panel_label", panel_label)
    return output.sort_values("abs_coefficient", ascending=False).reset_index(drop=True)


def _correlation_feature_frame(
    analysis_panel: pd.DataFrame,
    feature_columns: list[str],
    *,
    fitted_model,
) -> tuple[pd.DataFrame, str]:
    if fitted_model is None:
        return analysis_panel.loc[:, feature_columns].copy().reset_index(drop=True), "raw_pairwise_observed"
    try:
        transformed = fitted_model[:-1].transform(analysis_panel.loc[:, feature_columns])
    except Exception:
        return analysis_panel.loc[:, feature_columns].copy().reset_index(drop=True), "raw_pairwise_observed"
    if transformed.shape[1] != len(feature_columns):
        return analysis_panel.loc[:, feature_columns].copy().reset_index(drop=True), "raw_pairwise_observed"
    return (
        pd.DataFrame(transformed, columns=feature_columns, index=analysis_panel.index).reset_index(drop=True),
        "imputed_scaled_train_validation_design",
    )
