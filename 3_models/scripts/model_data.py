from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# The two main predictors GDP and scientific output are collinear (Spearman
# r=0.97, VIF~14) and jointly proxy national economic scale and research
# capacity. They are merged into a single interpretable component so the other
# predictors' coefficients stay stable and separately readable. See the
# 2026-07-03 decision-log entry.
SIZE_FACTOR_SOURCES = ("gdp_constant_2015_usd", "scientific_journal_articles")
SIZE_FACTOR_NAME = "size_factor"
_LAG_SUFFIXES = ("lag1", "lag1_3_mean")


@dataclass(frozen=True)
class ChronologicalSplit:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame
    train_years: list[int]
    validation_years: list[int]
    test_years: list[int]


def load_model_panel(panel_path: str | Path, target_column: str) -> pd.DataFrame:
    """Load a model panel and enforce the supervised-learning target contract."""
    panel = pd.read_csv(panel_path)
    if target_column not in panel.columns:
        raise ValueError(f"Missing target column: {target_column}")
    if panel[target_column].isna().any():
        missing_count = int(panel[target_column].isna().sum())
        raise ValueError(f"Panel contains {missing_count} rows with missing target values")
    required_columns = {"country_code", "country_name", "year"}
    missing_columns = sorted(required_columns.difference(panel.columns))
    if missing_columns:
        raise ValueError(f"Panel is missing required columns: {missing_columns}")
    duplicate_keys = panel.duplicated(["country_code", "year"], keep=False)
    if duplicate_keys.any():
        duplicate_count = int(duplicate_keys.sum())
        raise ValueError(f"Duplicate country-year keys found: {duplicate_count} rows")
    panel = add_size_factor_columns(panel)
    return panel.sort_values(["year", "country_code"]).reset_index(drop=True)


def add_size_factor_columns(panel: pd.DataFrame) -> pd.DataFrame:
    """Replace the collinear GDP and scientific-output predictors with one PCA
    economic-scale/research-capacity component, per lag scheme.

    The first principal component is fit on standardized complete-case rows of the
    two source columns; rows missing either source keep ``NaN`` so the modeling
    pipeline's per-fold median imputer handles them exactly as before. The sign is
    oriented so the component increases with economic size (GDP). Fitting the PCA on
    the full panel is leakage-negligible here: at r=0.97 the loading is effectively
    fixed, and a train-only fit yields an identical column (corr 0.99999, test-MAE
    delta 2e-4). Panels without both source columns (submodels) are returned
    unchanged.
    """
    panel = panel.copy()
    for suffix in _LAG_SUFFIXES:
        source_columns = [f"{name}_{suffix}" for name in SIZE_FACTOR_SOURCES]
        if not all(column in panel.columns for column in source_columns):
            continue
        complete = panel[source_columns].notna().all(axis=1)
        component = np.full(len(panel), np.nan)
        if complete.any():
            fitted = Pipeline(
                steps=[("scaler", StandardScaler()), ("pca", PCA(n_components=1))]
            ).fit(panel.loc[complete, source_columns])
            scores = fitted.transform(panel.loc[complete, source_columns])[:, 0]
            gdp = panel.loc[complete, source_columns[0]]
            if np.corrcoef(scores, gdp)[0, 1] < 0:
                scores = -scores
            component[complete.to_numpy()] = scores
        panel[f"{SIZE_FACTOR_NAME}_{suffix}"] = component
        panel = panel.drop(columns=source_columns)
    return panel


def select_lag_features(panel: pd.DataFrame, lag_suffix: str) -> list[str]:
    """Return feature columns for one lag scheme without mixing paired lag designs."""
    if lag_suffix not in {"lag1", "lag1_3_mean"}:
        raise ValueError("lag_suffix must be 'lag1' or 'lag1_3_mean'")
    suffix = f"_{lag_suffix}"
    features = [
        column
        for column in panel.columns
        if column.endswith(suffix) and pd.api.types.is_numeric_dtype(panel[column])
    ]
    if not features:
        raise ValueError(f"No numeric features found for lag suffix: {lag_suffix}")
    return features


def chronological_train_validation_test_split(
    panel: pd.DataFrame,
    year_column: str = "year",
    train_share: float = 0.80,
    validation_share: float = 0.10,
) -> ChronologicalSplit:
    """Split by sorted distinct years: earliest train, middle validation, latest test."""
    years = sorted(int(year) for year in panel[year_column].dropna().unique())
    if len(years) < 3:
        raise ValueError("At least three distinct years are required for train/validation/test")
    train_count = int(len(years) * train_share)
    validation_count = int(len(years) * validation_share)
    train_count = max(1, train_count)
    validation_count = max(1, validation_count)
    if train_count + validation_count >= len(years):
        train_count = len(years) - 2
        validation_count = 1

    train_years = years[:train_count]
    validation_years = years[train_count : train_count + validation_count]
    test_years = years[train_count + validation_count :]
    if not test_years:
        raise ValueError("Chronological split produced an empty test period")

    return ChronologicalSplit(
        train=panel[panel[year_column].isin(train_years)].copy(),
        validation=panel[panel[year_column].isin(validation_years)].copy(),
        test=panel[panel[year_column].isin(test_years)].copy(),
        train_years=train_years,
        validation_years=validation_years,
        test_years=test_years,
    )


def chronological_split_for_years(
    panel: pd.DataFrame,
    *,
    train_years: list[int],
    validation_years: list[int],
    test_years: list[int],
    year_column: str = "year",
) -> ChronologicalSplit:
    """Split a panel using an already chosen chronological year assignment."""
    train_years = _normalize_years(train_years)
    validation_years = _normalize_years(validation_years)
    test_years = _normalize_years(test_years)
    if not train_years or not validation_years or not test_years:
        raise ValueError("train_years, validation_years, and test_years must be non-empty")

    overlaps = (
        set(train_years).intersection(validation_years)
        | set(train_years).intersection(test_years)
        | set(validation_years).intersection(test_years)
    )
    if overlaps:
        raise ValueError(f"Split years must be disjoint; overlapping years: {sorted(overlaps)}")

    split = ChronologicalSplit(
        train=panel[panel[year_column].isin(train_years)].copy(),
        validation=panel[panel[year_column].isin(validation_years)].copy(),
        test=panel[panel[year_column].isin(test_years)].copy(),
        train_years=train_years,
        validation_years=validation_years,
        test_years=test_years,
    )
    empty_splits = [
        split_name
        for split_name, split_panel in [
            ("train", split.train),
            ("validation", split.validation),
            ("test", split.test),
        ]
        if split_panel.empty
    ]
    if empty_splits:
        raise ValueError(f"Fixed chronological split produced empty split(s): {empty_splits}")
    return split


def _normalize_years(years: list[int]) -> list[int]:
    return sorted({int(year) for year in years})


def matrix_from_panel(panel: pd.DataFrame, feature_columns: list[str], target_column: str):
    """Build X/y matrices while preserving predictor missingness for pipeline imputation."""
    return panel.loc[:, feature_columns].copy(), panel.loc[:, target_column].astype(float).copy()
