# Data Dictionary

This file documents every dataset and variable used in the project.

The data dictionary should be updated whenever a dataset is added, cleaned, renamed, merged, or removed.

## Dataset Inventory

| Dataset ID | Source | Purpose | File location | Download date | Coverage | Status |
|---|---|---|---|---|---|---|
| `oecd_patents_environment` | OECD Patents - indicators | Candidate target variables | `2_data/raw/` | 2026-05-15 | 1990-2023, 196-202 countries depending on candidate target | Raw |
| `world_bank_wdi` | World Bank World Development Indicators and ESG source for CO2 | Candidate macroeconomic, R&D, energy, and emissions predictors | `2_data/raw/` | 2026-05-15 | 1990-2024 requested; coverage varies by indicator | Raw |
| `oecd_eps` | OECD Environmental Policy Stringency index | Candidate environmental policy predictor | `2_data/raw/` | 2026-05-15 | 1990-2020, 40 countries | Raw |
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

The exact target variable must still be selected. The first exploration identified three strong OECD target candidates from `OECD.ENV.EPI:DSD_PAT_IND@DF_PAT_IND`.

| Final variable name | Source variable name | Dataset ID | Description | Unit | Transformation | Status | Notes |
|---|---|---|---|---|---|---|---|
| `env_patent_share_tech` | `PT_TECH.DEV.ENV_PAT._Z` | `oecd_patents_environment` | Environment-related technologies as a percentage of all technologies | Percent | May be used directly as outcome year `t` | Candidate | Strong first-pass target candidate; 3,538 observations, 202 countries, 1990-2023. |
| `env_patent_share_inventions` | `PT_INV.DEV.ENV_PAT._Z` | `oecd_patents_environment` | Environment-related technologies as a percentage of inventions | Percent | May be used directly as outcome year `t` | Candidate | Strong first-pass target candidate; 3,538 observations, 202 countries, 1990-2023. |
| `env_patents_per_million` | `INV_PS.DEV.ENV_PAT._Z` | `oecd_patents_environment` | Environment-related inventions per million people | Per million people | May require transformation if heavily skewed | Candidate | Useful size-normalized alternative; 3,528 observations, 196 countries, 1990-2023. |
| `env_patent_count` | To verify | OECD patents raw-count dataset | Number of patents related to environment technologies | Count | May require log transform or size controls | Optional | Not part of the first-pass indicator exploration. |

## Candidate Predictor Variables

The final predictor list should be selected through the literature review and data coverage checks.

### Macroeconomic Development

| Final variable name | Source variable name | Dataset ID | Description | Unit | Expected transform | Status | Notes |
|---|---|---|---|---|---|---|---|
| `gdp_per_capita` | `NY.GDP.PCAP.KD` | `world_bank_wdi` | GDP per capita | Constant 2015 US dollars | Log transform likely | Candidate | 7,096 observations, 213 countries, 1990-2024. |
| `gdp` | `NY.GDP.MKTP.KD` | `world_bank_wdi` | Gross domestic product | Constant 2015 US dollars | Log transform likely | Candidate | 7,096 observations, 213 countries, 1990-2024; may be unnecessary if target is normalized. |
| `population` | `SP.POP.TOTL` | `world_bank_wdi` | Total population | Persons | Log transform likely | Candidate | 7,595 observations, 217 countries, 1990-2024. |
| `manufacturing_share` | `NV.IND.MANF.ZS` | `world_bank_wdi` | Manufacturing value added share | Percent of GDP | None or standardized | Candidate | 6,000 observations, 203 countries, 1990-2024. |

### Research and Development Capacity

| Final variable name | Source variable name | Dataset ID | Description | Unit | Expected transform | Status | Notes |
|---|---|---|---|---|---|---|---|
| `rd_expenditure_gdp` | `GB.XPD.RSDV.GD.ZS` | `world_bank_wdi` | R&D expenditure | Percent of GDP | None or standardized | Candidate | 2,467 observations, 156 countries, 1996-2024; coverage is much thinner than macro variables. |
| `researchers_per_million` | `SP.POP.SCIE.RD.P6` | `world_bank_wdi` | Researchers in R&D | Per million people | Log transform or standardization possible | Candidate | 1,973 observations, 145 countries, 1996-2024; coverage may constrain the sample. |
| `tertiary_enrollment` | To verify | `world_bank_wdi` | Tertiary school enrollment | Percent | None or standardized | Optional | Human-capital proxy if coverage is acceptable. |

### Energy System

| Final variable name | Source variable name | Dataset ID | Description | Unit | Expected transform | Status | Notes |
|---|---|---|---|---|---|---|---|
| `renewable_energy_share` | `EG.FEC.RNEW.ZS` | `world_bank_wdi` | Renewable energy consumption share | Percent of final energy consumption | None or standardized | Candidate | 6,746 observations, 212 countries, 1990-2022. |
| `fossil_energy_share` | `EG.USE.COMM.FO.ZS` | `world_bank_wdi` | Fossil fuel energy consumption share | Percent of total energy use | None or standardized | Candidate | 4,978 observations, 179 countries, 1990-2024. |
| `energy_intensity` | `EG.EGY.PRIM.PP.KD` | `world_bank_wdi` | Energy intensity level of primary energy | To verify from World Bank metadata | Log transform possible | Candidate | 4,486 observations, 201 countries, 2000-2022. |
| `co2_per_capita` | `EN.ATM.CO2E.PC` | `world_bank_wdi` source 75 | CO2 emissions per capita | Metric tons per capita | Log transform possible | Candidate | 5,920 observations, 191 countries, 1990-2020; default WDI API source archived this indicator, so the script uses World Bank source 75. |

### Environmental Policy

| Final variable name | Source variable name | Dataset ID | Description | Unit | Expected transform | Status | Notes |
|---|---|---|---|---|---|---|---|
| `eps_index` | `POL_STRINGENCY.EPS` | `oecd_eps` | Environmental Policy Stringency index | 0-6 scale | None or standardized | Candidate | 1,240 observations, 40 countries, 1990-2020; useful but likely restricts sample coverage. |
| `rise_score` | To verify | `rise` | Sustainable energy regulation score | Index value | None or standardized | Optional | Use if coverage aligns with the main panel. |

## First-Pass Availability Outputs

| File | Description | Status |
|---|---|---|
| `2_data/processed/data_availability.csv` | Coverage summary for first-pass target and predictor candidates | Created 2026-05-15 |
| `2_data/processed/data_exploration_summary.md` | Human-readable summary generated from the exploration script | Created 2026-05-15 |

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
| 2026-05-15 | Added first-pass data-source coverage results | Document controlled exploration of OECD patent indicators, OECD EPS, and World Bank predictors. |
