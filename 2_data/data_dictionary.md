# Data Dictionary

This file documents every dataset and variable used in the project.

The data dictionary should be updated whenever a dataset is added, cleaned, renamed, merged, or removed.

## Dataset Inventory

| Dataset ID | Source | Purpose | File location | Download date | Coverage | Status |
|---|---|---|---|---|---|---|
| `oecd_patents_environment` | OECD patents on environment technologies | Candidate target variable | `2_data/raw/` | Not downloaded yet | To verify after download | Planned |
| `world_bank_wdi` | World Bank World Development Indicators | Candidate macroeconomic, R&D, energy, and emissions predictors | `2_data/raw/` | Not downloaded yet | To verify after download | Planned |
| `oecd_eps` | OECD Environmental Policy Stringency index | Candidate environmental policy predictor | `2_data/raw/` | Not downloaded yet | To verify after download | Planned |
| `rise` | Regulatory Indicators for Sustainable Energy | Candidate sustainable energy policy predictor | `2_data/raw/` | Not downloaded yet | To verify after download | Optional |

Status options:

1. `Planned`: identified as a possible source but not downloaded.
2. `Raw`: downloaded but not cleaned.
3. `Processed`: cleaned and ready for modeling or analysis.
4. `Dropped`: considered but not used.

## Core Panel Structure

The main modeling dataset should use one row per country-year.

Required identifiers:

| Variable name | Description | Type | Required | Notes |
|---|---|---|---|---|
| `country_code` | ISO 3-letter country code | String | Yes | Preferred country identifier for merging datasets. |
| `country_name` | Country name | String | Yes | Use a consistent naming convention after merging. |
| `year` | Calendar year | Integer | Yes | Used for panel structure and lag creation. |

## Target Variable

The exact target variable must be confirmed after inspecting the OECD data.

| Final variable name | Source variable name | Dataset ID | Description | Unit | Transformation | Status | Notes |
|---|---|---|---|---|---|---|---|
| `env_patent_share` | To verify | `oecd_patents_environment` | Share of patents related to environment technologies | Percent or share, to verify | May be used directly or lag-aligned as outcome year `t` | Candidate | Preferred if available because it reduces country-size effects. |
| `env_patent_count` | To verify | `oecd_patents_environment` | Number of patents related to environment technologies | Count | May require log transform or size controls | Optional | Use only if a count-based target is more defensible after data inspection. |

## Candidate Predictor Variables

The final predictor list should be selected through the literature review and data coverage checks.

### Macroeconomic Development

| Final variable name | Source variable name | Dataset ID | Description | Unit | Expected transform | Status | Notes |
|---|---|---|---|---|---|---|---|
| `gdp_per_capita` | To verify | `world_bank_wdi` | GDP per capita | Constant USD or current USD, to verify | Log transform likely | Candidate | Measures development level. |
| `gdp` | To verify | `world_bank_wdi` | Gross domestic product | USD, to verify | Log transform likely | Candidate | Measures market size; may be unnecessary if target is already normalized. |
| `population` | To verify | `world_bank_wdi` | Total population | Persons | Log transform likely | Candidate | Useful for scale controls if count target is used. |
| `manufacturing_share` | To verify | `world_bank_wdi` | Manufacturing value added share | Percent of GDP | None or standardized | Candidate | Captures industrial structure. |

### Research and Development Capacity

| Final variable name | Source variable name | Dataset ID | Description | Unit | Expected transform | Status | Notes |
|---|---|---|---|---|---|---|---|
| `rd_expenditure_gdp` | To verify | `world_bank_wdi` | R&D expenditure | Percent of GDP | None or standardized | Candidate | Core innovation-capacity predictor. |
| `researchers_per_million` | To verify | `world_bank_wdi` | Researchers in R&D | Per million people | Log transform or standardization possible | Candidate | Coverage may be limited. |
| `tertiary_enrollment` | To verify | `world_bank_wdi` | Tertiary school enrollment | Percent | None or standardized | Optional | Human-capital proxy if coverage is acceptable. |

### Energy System

| Final variable name | Source variable name | Dataset ID | Description | Unit | Expected transform | Status | Notes |
|---|---|---|---|---|---|---|---|
| `renewable_energy_share` | To verify | `world_bank_wdi` | Renewable energy consumption share | Percent of final energy consumption | None or standardized | Candidate | Captures clean-energy adoption. |
| `fossil_energy_share` | To verify | `world_bank_wdi` | Fossil fuel energy consumption share | Percent of total energy use | None or standardized | Candidate | May indicate fossil lock-in. |
| `energy_intensity` | To verify | `world_bank_wdi` | Energy use per unit of output | To verify | Log transform possible | Candidate | Efficiency or energy-dependence proxy. |
| `co2_per_capita` | To verify | `world_bank_wdi` | CO2 emissions per capita | Metric tons per capita | Log transform possible | Candidate | Environmental pressure proxy. |

### Environmental Policy

| Final variable name | Source variable name | Dataset ID | Description | Unit | Expected transform | Status | Notes |
|---|---|---|---|---|---|---|---|
| `eps_index` | To verify | `oecd_eps` | Environmental Policy Stringency index | Index value | None or standardized | Candidate | Coverage may be OECD-heavy. |
| `rise_score` | To verify | `rise` | Sustainable energy regulation score | Index value | None or standardized | Optional | Use if coverage aligns with the main panel. |

## Processed Modeling Dataset

Planned processed file:

| File | Description | Status |
|---|---|---|
| `2_data/processed/model_panel.csv` | Final country-year panel used for modeling | Not created yet |

Expected columns:

1. `country_code`
2. `country_name`
3. `year`
4. Target variable for year `t`
5. Lagged predictors, usually from year `t-1`
6. Optional metadata columns for sample filters or source coverage

## Transformation Rules

1. Preserve raw downloaded files unchanged in `2_data/raw/`.
2. Cleaned variables should use lowercase `snake_case` names.
3. Use ISO 3-letter country codes for merges.
4. Record all unit changes and transformations in this file.
5. Create lagged predictors explicitly, for example `rd_expenditure_gdp_lag1`.
6. Do not overwrite raw values when creating transformed variables.

## Missing Data Rules

1. Record missingness before modeling.
2. Avoid silently dropping countries or years.
3. If imputation is used, document the method and affected variables.
4. Prefer transparent handling over complex imputation unless missingness threatens the core analysis.

## Data Quality Checks

Run and document these checks after creating the processed panel:

1. Unique key check: one row per `country_code` and `year`.
2. Coverage check: number of countries and years by variable.
3. Missingness check: missing values by variable and year.
4. Range check: impossible values, negative shares, or values above expected limits.
5. Lag check: predictors from future years must not enter the model.
6. Merge check: country codes and names should remain consistent across sources.

## Change Log

| Date | Change | Reason |
|---|---|---|
| 2026-05-15 | Created initial data dictionary structure | Establish documentation rules before data collection. |
