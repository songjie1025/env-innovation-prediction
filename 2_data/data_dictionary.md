# Data Dictionary

This file documents every dataset and variable used in the project.

The data dictionary should be updated whenever a dataset is added, cleaned, renamed, merged, or removed.

## Dataset Inventory

| Dataset ID | Source | Purpose | File location | Download date | Coverage | Status |
|---|---|---|---|---|---|---|
| `oecd_patents_environment` | OECD Patents - indicators | Main target and robustness target variables | `2_data/raw/predictorsv1/` | 2026-05-15 | 1990-2023, 196-202 countries depending on indicator | Raw |
| `world_bank_wdi` | World Bank World Development Indicators and ESG source for CO2 | Candidate macroeconomic, R&D, energy, and emissions predictors | `2_data/raw/predictorsv1/` | 2026-05-15 | 1990-2024 requested; coverage varies by indicator | Raw |
| `world_bank_wgi` | World Bank Worldwide Governance Indicators | Explicit WGI Regulatory Quality predictor | `2_data/raw/predictorsv1/` | 2026-06-11 | 1990-2024 requested; coverage varies by country and year | Raw |
| `oecd_eps` | OECD Environmental Policy Stringency index | Candidate environmental policy predictor | `2_data/raw/predictorsv1/` | 2026-05-15 | 1990-2020, 40 countries | Raw |
| `world_bank_data360` | World Bank Data360 Regulatory Indicators for Sustainable Energy | Selected RISE Renewable Energy and Energy Efficiency sub-indicator groups | `2_data/raw/predictorsv1/` | 2026-06-11 | 2010-2023 long-form RISE table filtered by selected indicator prefixes | Raw |
| `oecd_carbon_pricing` | OECD Net Effective Carbon Rates | Carbon-tax policy predictor from the literature CSV | `2_data/raw/predictorsv1/` | 2026-06-11 | 1990-2024 requested; OECD coverage varies by country and year | Raw |
| `oecd_environment_tax` | OECD Environmentally Related Tax Revenue | Environmental tax revenue predictor from the literature CSV | `2_data/raw/predictorsv1/` | 2026-06-11 | 1990-2024 requested; OECD coverage varies by country and year | Raw |
| `policy_uncertainty` | Economic Policy Uncertainty Index | Economic policy uncertainty predictor from the literature CSV | `2_data/raw/predictorsv1/` | 2026-06-11 | All-country workbook; coverage varies by country | Raw |

Status options:

1. `Planned`: identified as a possible source but not downloaded.
2. `Raw`: downloaded but not cleaned.
3. `Processed`: cleaned and ready for modeling or analysis.
4. `Not selected`: considered but not used in the current modeling artifact.

## Core Panel Structure

The main modeling dataset should use one row per country-year.

Required identifiers:

| Variable name | Description | Type | Required | Notes |
|---|---|---|---|---|
| `country_code` | ISO 3-letter country code | String | Yes | Preferred country identifier for merging datasets. |
| `country_name` | Country name | String | Yes | Use a consistent naming convention after merging. |
| `year` | Calendar year | Integer | Yes | Used for panel structure and lag creation. |

## Target Variable

The main target variable has been selected in `0_organization/decision_log.md`: `PT_INV.DEV.ENV_PAT._Z`, stored as `env_patent_share_inventions`. The first exploration also identified robustness and diagnostic alternatives from `OECD.ENV.EPI:DSD_PAT_IND@DF_PAT_IND`.

| Final variable name | Source variable name | Dataset ID | Description | Unit | Transformation | Status | Notes |
|---|---|---|---|---|---|---|---|
| `env_patent_share_inventions` | `PT_INV.DEV.ENV_PAT._Z` | `oecd_patents_environment` | Environment-related technologies as a percentage of inventions | Percent | Use directly as outcome year `t` unless diagnostics show a need for transformation | Main target | Active decision; 3,538 observations, 202 countries, 1990-2023. |
| `env_patents_per_million` | `INV_PS.DEV.ENV_PAT._Z` | `oecd_patents_environment` | Environment-related inventions per million people | Per million people | May require transformation if heavily skewed | Robustness target | Useful size-normalized alternative; 3,528 observations, 196 countries, 1990-2023. |
| `env_patent_share_tech` | `PT_TECH.DEV.ENV_PAT._Z` | `oecd_patents_environment` | Environment-related technologies as a percentage of all technologies | Percent | Diagnostic or sensitivity use only | Diagnostic target | Not used as the main target because values above 100 create interpretation risk. |
| `env_patent_count` | To verify | OECD patents raw-count dataset | Number of patents related to environment technologies | Count | May require log transform or size controls | Exploratory target | Not part of the first-pass indicator exploration. |

## Candidate Predictor Variables

The final predictor list should be selected through literature review, data coverage checks, collinearity checks, and model diagnostics. The variables below, `2_data/processed/predictor_candidate_catalog.csv`, and `1_literature_review/Managerial AI- literature review - List 1.csv` together form the current predictor consideration pool. Predictors should be classified into main-model, robustness, exploratory, or data-limited roles rather than directly removed from consideration.

### Macroeconomic Development

| Final variable name | Source variable name | Dataset ID | Description | Unit | Expected transform | Status | Notes |
|---|---|---|---|---|---|---|---|
| `gdp_per_capita` | `NY.GDP.PCAP.KD` | `world_bank_wdi` | GDP per capita | Constant 2015 US dollars | Log transform likely | Candidate | 7,096 observations, 213 countries, 1990-2024. |
| `gdp` | `NY.GDP.MKTP.KD` | `world_bank_wdi` | Gross domestic product | Constant 2015 US dollars | Log transform likely | Candidate | 7,096 observations, 213 countries, 1990-2024; may be unnecessary if target is normalized. |
| `manufacturing_share` | `NV.IND.MANF.ZS` | `world_bank_wdi` | Manufacturing value added share | Percent of GDP | None or standardized | Candidate | 6,000 observations, 203 countries, 1990-2024. |
| `trade_openness` | `NE.TRD.GNFS.ZS` | `world_bank_wdi` | Trade as percent of GDP | Percent of GDP | None or standardized | Consideration | From literature CSV; download and coverage check needed. |
| `inflation` | `FP.CPI.TOTL.ZG` | `world_bank_wdi` | Inflation, consumer prices | Annual percent | Winsorization or standardization may be needed | Consideration | From literature CSV; download and coverage check needed. |
| `fdi` | `BX.KLT.DINV.CD.WD` | `world_bank_wdi` | Foreign direct investment, net inflows | Current US dollars | Log or percent-of-GDP alternative likely preferable | Consideration | From literature CSV; source-variable choice should be checked before use. |
| `wgi_regulatory_quality` | `GOV_WGI_RQ.EST` | `world_bank_wgi` | Regulatory Quality estimate from Worldwide Governance Indicators | Index | None or standardized | Consideration | Explicitly retained WGI predictor; generic institutional-quality rows are not downloaded automatically. |

### Research and Development Capacity

| Final variable name | Source variable name | Dataset ID | Description | Unit | Expected transform | Status | Notes |
|---|---|---|---|---|---|---|---|
| `rd_expenditure_gdp` | `GB.XPD.RSDV.GD.ZS` | `world_bank_wdi` | R&D expenditure | Percent of GDP | None or standardized | Candidate | 2,467 observations, 156 countries, 1996-2024; coverage is much thinner than macro variables. |
| `researchers_per_million` | `SP.POP.SCIE.RD.P6` | `world_bank_wdi` | Researchers in R&D | Per million people | Log transform or standardization possible | Candidate | 1,973 observations, 145 countries, 1996-2024; coverage may constrain the sample. |
| `tertiary_enrollment` | To verify | `world_bank_wdi` | Tertiary school enrollment | Percent | None or standardized | Optional | Human-capital proxy if coverage is acceptable. |
| `scientific_journal_articles` | `IP.JRN.ARTC.SC` | `world_bank_wdi` | Scientific and technical journal articles | Count | Log transform likely | Consideration | From literature CSV; may proxy scientific output but overlaps with innovation capacity. |
| `high_tech_exports` | `TX.VAL.TECH.MF.ZS` | `world_bank_wdi` | High-technology exports | Percent of manufactured exports | None or standardized | Consideration | From literature CSV; may proxy technological structure. |
| `env_tech_rta_lagged` | To calculate | OECD patent data | Lagged revealed technological advantage in environmental technologies | Index | Lagged moving average or prior-year value | Consideration | From literature CSV; useful for path-dependence checks. |
| `co_invention_rate` | To calculate | OECD patent data | International co-invention rate | Share or percent | None or standardized | Consideration | From literature CSV; useful for knowledge diffusion mechanisms. |

### Energy System

| Final variable name | Source variable name | Dataset ID | Description | Unit | Expected transform | Status | Notes |
|---|---|---|---|---|---|---|---|
| `renewable_energy_share` | `EG.FEC.RNEW.ZS` | `world_bank_wdi` | Renewable energy consumption share | Percent of final energy consumption | None or standardized | Candidate | 6,746 observations, 212 countries, 1990-2022. |
| `fossil_energy_share` | `EG.USE.COMM.FO.ZS` | `world_bank_wdi` | Fossil fuel energy consumption share | Percent of total energy use | None or standardized | Candidate | 4,978 observations, 179 countries, 1990-2024. |
| `co2_per_capita_ar5` | `EN.GHG.CO2.PC.CE.AR5` | `world_bank_wdi` | CO2 emissions per capita, AR5 climate source | Tonnes CO2 equivalent per capita | Log transform possible | Candidate | Literature CSV source used by the raw downloader. |
| `energy_imports_net` | `EG.IMP.CONS.ZS` | `world_bank_wdi` | Net energy imports | Percent of energy use | None or standardized | Consideration | From literature CSV; download and coverage check needed. |

### Environmental Policy

| Final variable name | Source variable name | Dataset ID | Description | Unit | Expected transform | Status | Notes |
|---|---|---|---|---|---|---|---|
| `eps_index` | `POL_STRINGENCY.EPS` | `oecd_eps` | Environmental Policy Stringency index | 0-6 scale | None or standardized | Candidate | 1,240 observations, 40 countries, 1990-2020; useful but likely restricts sample coverage. |
| `rise_renewable_energy` | `WB_RISE_RE_*` | `world_bank_data360` | RISE Renewable Energy broad-category score and sub-indicators | Index value | None or standardized | Consideration | Downloaded as a separate raw file by filtering World Bank Data360 RISE indicators with the `WB_RISE_RE_` prefix. |
| `rise_energy_efficiency` | `WB_RISE_EE_*` | `world_bank_data360` | RISE Energy Efficiency broad-category score and sub-indicators | Index value | None or standardized | Consideration | Downloaded as a separate raw file by filtering World Bank Data360 RISE indicators with the `WB_RISE_EE_` prefix. |
| `carbon_tax` | `OECD.CTP.TPS,DSD_NECR@DF_NECRS,1.1/.ENE.FFUEL.CARBTAX._Z.EUR_TCO2.MEANW.V.A` | `oecd_carbon_pricing` | Carbon tax rate for energy-use sectors and fossil fuels | EUR per tonne of CO2 | None or standardized | Consideration | From literature CSV; raw OECD SDMX table downloaded by `2_data/scripts/raw_data_download.py`. |
| `environmental_tax_revenue` | `OECD.ENV.EPI,DSD_ERTR@DF_ERTR,1.0/A..TAXREV._T._T.PT_B1GQ._Z` | `oecd_environment_tax` | Total environmentally related tax revenue | Percent of GDP | None or standardized | Consideration | From literature CSV; raw OECD SDMX table downloaded by `2_data/scripts/raw_data_download.py`. |
| `fossil_fuel_subsidies` | To verify | OECD, IEA, IMF, or other public source | Fossil fuel support or subsidy measure | Currency, percent of GDP, or index | Depends on source | Consideration | From literature CSV; do not substitute fossil consumption share without relabeling the concept. |
| `economic_policy_uncertainty` | `All_Country_Data` | `policy_uncertainty` | Policy uncertainty | Index | None or standardized | Consideration | From literature CSV; all-country workbook downloaded by `2_data/scripts/raw_data_download.py`; country-year extraction is a cleaning step. |
| `policy_stability` | To calculate | OECD EPS | Stability of environmental policy stringency | Inverse rolling standard deviation | Rolling calculation | Consideration | From literature CSV; possible robustness variable distinct from EPS level. |

## First-Pass Availability Outputs

| File | Description | Status |
|---|---|---|
| `2_data/processed/data_availability.csv` | Coverage summary for first-pass target and predictor candidates | Created 2026-05-15 |
| `2_data/processed/data_exploration_summary.md` | Human-readable summary generated from the exploration script | Created 2026-05-15 |
| `2_data/processed/oecd_patent_dimension_values.csv` | OECD patent indicator dimension values for unit measures, counting types, technology domains, and patent-office breakdowns | Created 2026-05-15 |
| `2_data/processed/oecd_patent_target_candidates.csv` | Structured explanation of the three broad OECD target candidates and their source-variable construction | Created 2026-05-15 |
| `2_data/processed/oecd_patent_technology_domains.csv` | OECD technology-domain metadata, including broad available domains and detailed taxonomy codes | Created 2026-05-15 |
| `2_data/processed/oecd_patent_technology_category_summary.csv` | Summary of broad environment-related patent domains and example detailed subdomains | Created 2026-05-15 |

## Candidate Discovery Outputs

These files document the systematic candidate screen before final variable selection.

| File | Description | Status |
|---|---|---|
| `2_data/processed/target_candidate_catalog.csv` | OECD patent target search-space catalog built from available `UNIT_MEASURE`, `TYPE`, `TECH`, and `PAT` metadata combinations, with reviewer-facing role, recommended use, inclusion status, and coverage where checked | Created 2026-05-19 |
| `2_data/processed/predictor_candidate_catalog.csv` | Provisional literature- and metadata-driven predictor candidate catalog with source codes, rationale, coverage status, lag recommendation, measurement caveats, and inclusion decision; final predictors remain deferred until the literature review is complete | Created 2026-05-19 |
| `2_data/processed/candidate_discovery_summary.md` | Human-readable summary generated from `2_data/scripts/candidate_discovery.py` | Created 2026-05-19 |
| `1_literature_review/Managerial AI- literature review - List 1.csv` | Manual literature-review predictor screening sheet; all listed predictor concepts remain in consideration for main, robustness, exploratory, or data-limited roles | Added 2026-06-10 |

## Raw Reliability and Coverage Outputs

These files are generated by `2_data/scripts/raw_coverage_diagnostics.py` and executed from `2_data/notebooks/data_cleaning.ipynb`. Detailed panel and by-year coverage tables are computed in memory for visualization, but are not written as intermediate CSV files.

| File | Description | Status |
|---|---|---|
| `2_data/processed/raw_predictor_audit.csv` | Consolidated source reliability and variable-level country/entity-year coverage audit with source URL domain, actual shape, checksum, reliability status, and coverage statistics | Created 2026-06-11 |
| `4_analysis/figures/predictorsv1/raw_coverage_heatmap.png` | High-resolution coverage heatmap generated by the notebook/script for predictor v1 diagnostics | Created 2026-06-11 |
| `4_analysis/figures/predictorsv1/raw_coverage_heatmap.pdf` | Vector coverage heatmap generated by the notebook/script for publication-quality export | Created 2026-06-11 |
| `4_analysis/figures/predictorsv1/raw_coverage_summary.png` | High-resolution side-by-side cross-sectional and temporal coverage summary generated by the notebook/script | Created 2026-06-11 |
| `4_analysis/figures/predictorsv1/raw_coverage_summary.pdf` | Vector coverage summary figure generated by the notebook/script for publication-quality export | Created 2026-06-11 |

## Processed Modeling Dataset

Planned processed file:

| File | Description | Status |
|---|---|---|
| `2_data/processed/model_panel.csv` | Final country-year panel used for modeling | Not created yet |

Expected columns:

1. `country_code`
2. `country_name`
3. `year`
4. `env_patent_share_inventions` target variable for year `t`
5. Main predictor variables as three-year lagged moving averages, named like `rd_expenditure_gdp_lag1_3_mean`
6. Optional metadata columns for sample filters or source coverage

## Transformation Rules

1. Preserve raw downloaded files unchanged in their versioned subfolder under `2_data/raw/`, for example `2_data/raw/predictorsv1/`.
2. Cleaned variables should use lowercase `snake_case` names.
3. Use ISO 3-letter country codes for merges.
4. Record all unit changes and transformations in this file.
5. Create lagged predictors explicitly. The main specification should use names like `rd_expenditure_gdp_lag1_3_mean` for the mean of `t-1`, `t-2`, and `t-3`.
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
| 2026-05-15 | Added OECD patent metadata catalog outputs | Make target-variable and technology-domain options visible before choosing the final target. |
| 2026-05-19 | Added candidate discovery catalogs | Document systematic target and predictor candidate screening before model construction. |
| 2026-06-10 | Synchronized target, lag, and predictor consideration pool with decision log and manual CSV screening | Reflect selected main target, three-year lagged moving-average timing, and the instruction not to directly exclude CSV predictors. |
| 2026-06-11 | Synchronized raw source inventory with the reproducible literature-based downloader | Document code-generated RISE, OECD carbon-pricing, OECD environmental-tax, WGI, and EPU raw sources. |
| 2026-06-11 | Added raw reliability and coverage diagnostics | Document reproducible source audit, country-year availability checks, and coverage figures generated from the raw download manifest. |
| 2026-06-11 | Refined predictor v1 selection | Remove population, resident patent applications, energy intensity, carbon/energy prices, and generic WGI institutional-quality rows; split RISE into Renewable Energy and Energy Efficiency groups; explicitly retain WGI Regulatory Quality. |
| 2026-06-11 | Consolidated raw diagnostics CSV outputs | Replace separate reliability, summary, by-year, and panel CSV outputs with one reproducible `raw_predictor_audit.csv`; keep detailed panel and by-year coverage in memory for figures. |
| 2026-06-11 | Versioned predictor diagnostics figures | Write notebook-generated coverage figures under `4_analysis/figures/predictorsv1/` to match the predictor v1 raw-data folder. |
