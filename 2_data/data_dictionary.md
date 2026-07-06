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
| `country_code` | World Bank/OECD-style 3-letter country code | String | Yes | Preferred country identifier for merging datasets. Most values are ISO alpha-3; source-specific codes such as `XKX` are retained when used by the source data. |
| `country_name` | Country name | String | Yes | Use a consistent naming convention after merging. |
| `year` | Calendar year | Integer | Yes | Used for panel structure and lag creation. |

## Target Variable

The main target variable has been selected in `0_organization/decision_log.md`: `PT_INV.DEV.ENV_PAT._Z`, stored as `env_patent_share_inventions`. The first exploration also identified robustness and diagnostic alternatives from `OECD.ENV.EPI:DSD_PAT_IND@DF_PAT_IND`.

| Final variable name | Source variable name | Dataset ID | Description | Unit | Transformation | Status | Notes |
|---|---|---|---|---|---|---|---|
| `env_patent_share_inventions` | `PT_INV.DEV.ENV_PAT._Z` | `oecd_patents_environment` | Country or aggregate area's percentage contribution to worldwide environment-related inventions | Percent | Use directly as outcome year `t` unless diagnostics show a need for transformation | Main target | Active decision; 3,538 observations, 202 countries, 1990-2023. Country rows sum to about 100 by year after excluding aggregate rows such as `W`, `OECD`, `EU27_2020`, and `EA19`. |
| `env_patents_per_million` | `INV_PS.DEV.ENV_PAT._Z` | `oecd_patents_environment` | Environment-related inventions per million people | Per million people | May require transformation if heavily skewed | Robustness target | Useful size-normalized alternative; 3,528 observations, 196 countries, 1990-2023. |
| `env_patent_share_tech` | `PT_TECH.DEV.ENV_PAT._Z` | `oecd_patents_environment` | Environment-related technologies as a percentage of all domestic technologies / inventions | Percent | Diagnostic or sensitivity use only | Diagnostic target | Not used as the main target because values above 100 create interpretation risk; this is an internal country portfolio share, so country rows should not be summed. |
| `env_patent_count` | To verify | OECD patents raw-count dataset | Number of patents related to environment technologies | Count | May require log transform or size controls | Exploratory target | Not part of the first-pass indicator exploration. |

## Candidate Predictor Variables

The final predictor list should be selected through literature review, data coverage checks, collinearity checks, and model diagnostics. The variables below, `2_data/processed/predictor_candidate_catalog.csv`, and `1_literature_review/Managerial AI- literature review - List 1.csv` together form the current predictor consideration pool. Predictors should be classified into main-model, robustness, exploratory, or data-limited roles rather than directly removed from consideration.

### Macroeconomic Development

| Final variable name | Source variable name | Dataset ID | Description | Unit | Expected transform | Status | Notes |
|---|---|---|---|---|---|---|---|
| `gdp_per_capita` | `NY.GDP.PCAP.KD` | `world_bank_wdi` | GDP per capita | Constant 2015 US dollars | Log transform likely if used | Replaced | Replaced in the predictorsv1 raw download by total GDP because the selected target is a country-level innovation share and total economic scale is the intended market-size predictor. |
| `gdp_constant_2015_usd` | `NY.GDP.MKTP.KD` | `world_bank_wdi` | Gross domestic product | Constant 2015 US dollars | Log transform likely | Candidate | Raw predictorsv1 download confirmed: 7,236 non-missing observations, 217 countries, 1990-2024. |
| `manufacturing_share` | `NV.IND.MANF.ZS` | `world_bank_wdi` | Manufacturing value added share | Percent of GDP | None or standardized | Candidate | 6,000 observations, 203 countries, 1990-2024. |
| `trade_openness` | `NE.TRD.GNFS.ZS` | `world_bank_wdi` | Trade as percent of GDP | Percent of GDP | None or standardized | Candidate | Included in the main model panel from predictorsv1. |
| `inflation` | `FP.CPI.TOTL.ZG` | `world_bank_wdi` | Inflation, consumer prices | Annual percent | Winsorization or standardization may be needed | Candidate | Included in the main model panel from predictorsv1. |
| `fdi_net_inflows` | `BX.KLT.DINV.CD.WD` | `world_bank_wdi` | Foreign direct investment, net inflows | Current US dollars | Log, percent-of-GDP alternative, or robust scaling likely needed before modeling | Candidate | Included in the main model panel from predictorsv1. |
| `wgi_regulatory_quality` | `GOV_WGI_RQ.EST` | `world_bank_wgi` | Regulatory Quality estimate from Worldwide Governance Indicators | Index | None or standardized | Consideration | Explicitly retained WGI predictor; generic institutional-quality rows are not downloaded automatically. |

### Research and Development Capacity

| Final variable name | Source variable name | Dataset ID | Description | Unit | Expected transform | Status | Notes |
|---|---|---|---|---|---|---|---|
| `rd_expenditure_gdp` | `GB.XPD.RSDV.GD.ZS` | `world_bank_wdi` | R&D expenditure | Percent of GDP | None or standardized | Candidate | 2,467 observations, 156 countries, 1996-2024; coverage is much thinner than macro variables. |
| `researchers_per_million` | `SP.POP.SCIE.RD.P6` | `world_bank_wdi` | Researchers in R&D | Per million people | Log transform or standardization possible | Candidate | 1,973 observations, 145 countries, 1996-2024; coverage may constrain the sample. |
| `tertiary_enrollment` | `SE.TER.ENRR` | `world_bank_wdi` | Tertiary school enrollment, gross ratio | Percent | None or standardized | Robustness / exploratory | Included in v1, but moved out of the active v2 main specification because it is a broad human-capital proxy with weaker direct green-patent evidence than R&D, researchers, knowledge stocks, scientific output, or university-quality measures. |
| `scientific_journal_articles` | `IP.JRN.ARTC.SC` | `world_bank_wdi` | Scientific and technical journal articles | Count | Log transform likely | Consideration | From literature CSV; may proxy scientific output but overlaps with innovation capacity. |
| `high_tech_exports` | `TX.VAL.TECH.MF.ZS` | `world_bank_wdi` | High-technology exports | Percent of manufactured exports | None or standardized | Consideration | From literature CSV; may proxy technological structure. |
| `env_technology_rta` | `IX.DEV.ENV_PAT._Z` | `oecd_patents_environment` | OECD environmental-technology specialization index used as the RTA-style path-dependence predictor | Index, world benchmark = 1 | Lagged prior-year value and lagged three-year mean in model panels | Candidate | Replaces the earlier PT_TECH share support series. The OECD `IX` series equals the country's `PT_TECH` internal environmental-technology share divided by the corresponding world benchmark, so values above 1 indicate relative specialization. |
| `env_co_invention_share` | OECD patent data | `oecd_patents_co_invention` | International environmental co-invention share | Share | Lagged prior-year value and lagged three-year mean in model panels | Candidate | predictorsv1 variable name retained as the source of truth for submodel B. |

### Energy System

| Final variable name | Source variable name | Dataset ID | Description | Unit | Expected transform | Status | Notes |
|---|---|---|---|---|---|---|---|
| `renewable_energy_share` | `EG.FEC.RNEW.ZS` | `world_bank_wdi` | Renewable energy consumption share | Percent of final energy consumption | None or standardized | Candidate | 6,746 observations, 212 countries, 1990-2022. |
| `fossil_energy_share` | `EG.USE.COMM.FO.ZS` | `world_bank_wdi` | Fossil fuel energy consumption share | Percent of total energy use | None or standardized | Robustness / exploratory | 4,978 observations, 179 countries, 1990-2024 before source-quality rules. Included in v1, but moved out of the active v2 main specification because literature support is indirect and sign-ambiguous, and the current WDI source series has invalid negative and exact-zero artifacts. |
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

These files are generated by `2_data/scripts/raw_coverage_diagnostics.py` and executed from `2_data/notebooks/data_cleaning.ipynb`. Detailed panel and by-year coverage tables are computed in memory for diagnostics, but are not written as intermediate CSV files.

| File | Description | Status |
|---|---|---|
| `2_data/processed/raw_predictor_audit.csv` | Consolidated source reliability and variable-level country/entity-year coverage audit with source URL domain, actual shape, checksum, reliability status, and coverage statistics | Created 2026-06-11 |
| `4_analysis/figures/predictorsv1/raw_variable_country_rank.png` | High-resolution composite variable-level ranking by covered country/entity count and first-to-last covered year span | Created 2026-06-11 |
| `4_analysis/figures/predictorsv1/raw_variable_country_rank.pdf` | Vector composite variable-level ranking by covered country/entity count and first-to-last covered year span | Created 2026-06-11 |
| `4_analysis/figures/predictorsv1/raw_country_coverage_rank.png` | High-resolution country-level coverage ranking across 3-letter source-code raw variable-year opportunities, sorted from high to low coverage | Created 2026-06-11 |
| `4_analysis/figures/predictorsv1/raw_country_coverage_rank.pdf` | Vector country-level coverage ranking across 3-letter source-code raw variable-year opportunities, sorted from high to low coverage | Created 2026-06-11 |

## Processed Modeling Dataset

The current cleaning pipeline writes lagged analysis-base panel candidates rather than a single final `model_panel.csv`. The root `model_panels/` package preserves the original v1 panels and audit trail. The active v2 package is written to `model_panels/v2/`; its main model moves `fossil_energy_share` and `tertiary_enrollment` to robustness or exploratory status after the pre-modeling literature and coverage reassessment. The second-target robustness package is written to `model_panels/robustness/env_patents_per_million/v2/` and reuses the active v2 predictor specification with `env_patents_per_million` as the outcome. The no-imputation panels are the primary prediction-safe inputs. The linear-interpolated panels are retained only as retrospective sensitivity outputs because full-series interpolation can use future endpoints and is therefore not appropriate for the main forecasting or pseudo-out-of-sample design.

| File | Description | Status |
|---|---|---|
| `2_data/processed/model_panels/model_panel_main_no_imputation.csv` | Main 11-predictor lagged panel using source missing values only | Created 2026-06-12 |
| `2_data/processed/model_panels/model_panel_main_linear_interpolated.csv` | Main 11-predictor lagged panel after internal country-level linear interpolation of predictors | Created 2026-06-12 |
| `2_data/processed/model_panels/model_panel_suba_no_imputation.csv` | Submodel A lagged panel for RISE Energy Efficiency, RISE Renewable Energy, and high-tech exports | Created 2026-06-12 |
| `2_data/processed/model_panels/model_panel_suba_linear_interpolated.csv` | Submodel A lagged panel after internal country-level linear interpolation of predictors | Created 2026-06-12 |
| `2_data/processed/model_panels/model_panel_subb_no_imputation.csv` | Submodel B lagged panel for R&D, co-invention, energy imports, researchers, and environmental tax revenue | Created 2026-06-12 |
| `2_data/processed/model_panels/model_panel_subb_linear_interpolated.csv` | Submodel B lagged panel after internal country-level linear interpolation of predictors | Created 2026-06-12 |
| `2_data/processed/model_panels/model_panel_subc_no_imputation.csv` | Submodel C lagged panel for OECD EPS | Created 2026-06-12 |
| `2_data/processed/model_panels/model_panel_subc_linear_interpolated.csv` | Submodel C lagged panel after internal country-level linear interpolation of predictors | Created 2026-06-12 |
| `2_data/processed/model_panels/model_panel_coverage_summary.csv` | Panel-level coverage summary with anchor variable, predictor window, target years, row counts, complete-lag rows, target-plus-complete-feature rows, and imputed value counts | Created 2026-06-12 |
| `2_data/processed/model_panels/model_panel_imputation_summary.csv` | Panel-variable-level count of values filled by the retrospective linear-interpolation sensitivity treatment | Created 2026-06-12 |
| `2_data/processed/model_panels/model_panel_quality_summary.csv` | Source-data quality-control values converted to `NaN` before lag construction, including invalid fossil-energy source values | Created 2026-06-12 |
| `2_data/processed/model_panels/model_panel_variable_map.csv` | Mapping from each panel variable to raw file, source variable, source, anchor status, and RISE selection rule | Created 2026-06-12 |
| `2_data/processed/model_panels/model_panel_predictor_reassessment.csv` | Original main-predictor reassessment table with literature/coverage decision, missing rows, and leave-one-variable-out complete-case gains | Created 2026-06-13 |
| `2_data/processed/model_panels/v2/model_panel_main_no_imputation.csv` | Active v2 main 9-predictor lagged panel using source missing values only; excludes `fossil_energy_share` and `tertiary_enrollment` from the main specification | Created 2026-06-13 |
| `2_data/processed/model_panels/v2/model_panel_main_linear_interpolated.csv` | Active v2 main 9-predictor lagged panel after internal country-level linear interpolation of predictors | Created 2026-06-13 |
| `2_data/processed/model_panels/v2/model_panel_suba_no_imputation.csv` / `model_panel_suba_linear_interpolated.csv` | Active v2 copies of the submodel A lagged panels | Created 2026-06-13 |
| `2_data/processed/model_panels/v2/model_panel_subb_no_imputation.csv` / `model_panel_subb_linear_interpolated.csv` | Active v2 copies of the submodel B lagged panels | Created 2026-06-13 |
| `2_data/processed/model_panels/v2/model_panel_subc_no_imputation.csv` / `model_panel_subc_linear_interpolated.csv` | Active v2 copies of the submodel C lagged panels | Created 2026-06-13 |
| `2_data/processed/model_panels/v2/model_panel_coverage_summary.csv` | Active v2 panel-level coverage summary | Created 2026-06-13 |
| `2_data/processed/model_panels/v2/model_panel_imputation_summary.csv` | Active v2 panel-variable-level interpolation audit | Created 2026-06-13 |
| `2_data/processed/model_panels/v2/model_panel_quality_summary.csv` | Active v2 source-quality audit | Created 2026-06-13 |
| `2_data/processed/model_panels/v2/model_panel_variable_map.csv` | Active v2 panel variable map | Created 2026-06-13 |
| `2_data/processed/model_panels/v2/model_panel_predictor_reassessment.csv` | Active v2 copy of the main-predictor reassessment table documenting why `fossil_energy_share` and `tertiary_enrollment` moved out of the main specification | Created 2026-06-13 |
| `2_data/processed/model_panels/robustness/env_patents_per_million/v2/model_panel_main_no_imputation.csv` / `model_panel_main_linear_interpolated.csv` | Second-target robustness v2 main panels using `env_patents_per_million` as the outcome and the active v2 main predictor set | Created 2026-06-13 |
| `2_data/processed/model_panels/robustness/env_patents_per_million/v2/model_panel_suba_no_imputation.csv` / `model_panel_suba_linear_interpolated.csv` | Second-target robustness v2 submodel A panels | Created 2026-06-13 |
| `2_data/processed/model_panels/robustness/env_patents_per_million/v2/model_panel_subb_no_imputation.csv` / `model_panel_subb_linear_interpolated.csv` | Second-target robustness v2 submodel B panels | Created 2026-06-13 |
| `2_data/processed/model_panels/robustness/env_patents_per_million/v2/model_panel_subc_no_imputation.csv` / `model_panel_subc_linear_interpolated.csv` | Second-target robustness v2 submodel C panels | Created 2026-06-13 |
| `2_data/processed/model_panels/robustness/env_patents_per_million/v2/model_panel_coverage_summary.csv` | Second-target robustness v2 panel-level coverage summary | Created 2026-06-13 |
| `2_data/processed/model_panels/robustness/env_patents_per_million/v2/model_panel_imputation_summary.csv` | Second-target robustness v2 panel-variable-level interpolation audit | Created 2026-06-13 |
| `2_data/processed/model_panels/robustness/env_patents_per_million/v2/model_panel_quality_summary.csv` | Second-target robustness v2 source-quality audit | Created 2026-06-13 |
| `2_data/processed/model_panels/robustness/env_patents_per_million/v2/model_panel_variable_map.csv` | Second-target robustness v2 panel variable map | Created 2026-06-13 |
| `2_data/processed/model_panels/model_panel.csv` | Final single modeling panel, if later selected from one of the generated candidates | Not created yet |
| `4_analysis/figures/model_panels/model_panel_sample_funnel.png` / `.pdf` | Sample-construction funnel for no-imputation panels | Created 2026-06-12 |
| `4_analysis/figures/model_panels/model_panel_prediction_safe_comparison.png` / `.pdf` | Effective modeling-sample comparison between prediction-safe and retrospective sensitivity panels | Created 2026-06-12 |
| `4_analysis/figures/model_panels/model_panel_feature_availability_heatmap.png` / `.pdf` | All-panel feature availability heatmap by target year for no-imputation panels | Created 2026-06-13 |
| `4_analysis/figures/model_panels/model_panel_missingness_burden.png` / `.pdf` | Global missingness burden and retrospective interpolation fill-scale diagnostic by model panel | Created 2026-06-13 |
| `4_analysis/figures/model_panels/v2/model_panel_sample_funnel.png` / `.pdf` | Active v2 sample-construction funnel for no-imputation panels | Created 2026-06-13 |
| `4_analysis/figures/model_panels/v2/model_panel_prediction_safe_comparison.png` / `.pdf` | Active v2 effective modeling-sample comparison between prediction-safe and retrospective sensitivity panels | Created 2026-06-13 |
| `4_analysis/figures/model_panels/v2/model_panel_feature_availability_heatmap.png` / `.pdf` | Active v2 all-panel feature availability heatmap by target year for no-imputation panels | Created 2026-06-13 |
| `4_analysis/figures/model_panels/v2/model_panel_missingness_burden.png` / `.pdf` | Active v2 global missingness burden and retrospective interpolation fill-scale diagnostic by model panel | Created 2026-06-13 |

Expected columns:

1. `country_code`
2. `country_name`
3. `year`
4. Target variable for year `t`: `env_patent_share_inventions` in main-target panels or `env_patents_per_million` in second-target robustness panels
5. Predictor variables as one-year lags, named like `rd_expenditure_gdp_lag1`
6. Predictor variables as three-year lagged moving averages, named like `rd_expenditure_gdp_lag1_3_mean`

The v1 main panel uses raw predictor years 1996-2022 and target years 1999-2023. Its anchor variable is `fossil_energy_share`; current `predictorsv1` files produce 141 World Bank/OECD-style 3-letter-code anchor countries after excluding aggregate entities and applying fossil source-quality rules. The active v2 main panel keeps the same raw predictor years but removes `fossil_energy_share` and `tertiary_enrollment` from the main specification; its anchor is automatically selected from retained predictors and is currently `trade_openness`, with 191 anchor countries. Submodel windows and anchors are selected by `2_data/scripts/model_panel_cleaning.py` from the common raw predictor window and the least-covered predictor in each group.

Rows in the panel files are target-observed country-years: rows where the package-specific target is missing are dropped during panel generation because they cannot be used as supervised-learning labels. Predictor missing values are preserved. `model_panel_coverage_summary.csv` retains `anchor_countries`, `anchor_year_grid_rows`, and `target_missing_rows_dropped` to document the pre-filter anchor-country by target-year grid. The `countries` field reports countries remaining after target filtering. `target_lag1_complete_rows` and `target_lag1_3_mean_complete_rows` report stricter complete-feature samples for diagnostics and robustness checks, not the required main-model sample size.

Generated model-panel CSV files serialize missing values as the literal string `NaN` rather than blank cells. Pandas and common modeling libraries read this representation back as missing by default.

## Transformation Rules

1. Preserve raw downloaded files unchanged in their versioned subfolder under `2_data/raw/`, for example `2_data/raw/predictorsv1/`.
2. Cleaned variables should use lowercase `snake_case` names.
3. Use World Bank/OECD-style 3-letter country codes for merges, while documenting source-specific non-ISO codes when present.
4. Record all unit changes and transformations in this file.
5. Create lagged predictors explicitly. The main specification should use names like `rd_expenditure_gdp_lag1_3_mean` for the mean of `t-1`, `t-2`, and `t-3`.
6. Do not overwrite raw values when creating transformed variables.
7. For every selected predictor `x`, the cleaning pipeline creates both `x_lag1` and `x_lag1_3_mean`.
8. `x_lag1_3_mean` is calculated only when all three lag years are available after the chosen missing-data treatment; partial-window averages are not used.
9. RISE submodel variables use the broad `WB_RISE_RE_ALL` and `WB_RISE_EE_ALL` scores when present. If a future RISE raw file lacks an `*_ALL` score, the script falls back to a country-year mean across the selected indicator prefix and records that rule in `model_panel_variable_map.csv`.
10. `env_technology_rta` uses the OECD `IX.DEV.ENV_PAT._Z` index, not the `PT_TECH.DEV.ENV_PAT._Z` technology-share support series.
11. `fossil_energy_share` applies source-data quality control before lag construction: negative values and country-level exact zeros in World Bank WDI `EG.USE.COMM.FO.ZS` are converted to `NaN` and recorded in `model_panel_quality_summary.csv`.
12. The active v2 main model excludes `fossil_energy_share` and `tertiary_enrollment` from the main specification and records the literature/coverage rationale in `model_panel_predictor_reassessment.csv`.

## Missing Data Rules

1. Record missingness before modeling.
2. Avoid silently dropping countries or years; when rows are removed, record the rule and count.
3. If imputation is used, document the method and affected variables.
4. Prefer transparent handling over complex imputation unless missingness threatens the core analysis.
5. The no-imputation model panels keep predictor source missing values unchanged.
6. The no-imputation panels are the primary prediction-safe analysis-base panels.
7. The linear-interpolated panels impute predictor gaps only within the same country and variable series. They do not extrapolate outside each observed country-variable range, do not borrow information across countries, and do not impute the package-specific target.
8. Because the current linear-interpolation sensitivity version is applied to full country-variable series before lag construction, it can use future endpoints. It must not be used as the main predictive-modeling input.
9. Imputed predictor counts are recorded in `model_panel_coverage_summary.csv` and by panel-variable in `model_panel_imputation_summary.csv`.
10. Rows with missing package-specific targets are dropped from generated model-panel CSVs. The dropped count is recorded as `target_missing_rows_dropped` in `model_panel_coverage_summary.csv`.
11. Generated model-panel CSVs write missing values as `NaN` so missingness is explicit in the delivered files.

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
| 2026-06-12 | Revised lagged model-panel cleaning outputs | Generate main, subA, subB, and subC analysis-base panels with `lag1` and `lag1_3_mean` features; mark no-imputation panels as the primary prediction-safe inputs and linear-interpolated panels as retrospective sensitivity outputs only. |
| 2026-06-12 | Corrected environmental-technology RTA source | Replaced the PT_TECH share support series with OECD `IX.DEV.ENV_PAT._Z` for `env_technology_rta`; added target-plus-complete-feature sample counts and panel-variable imputation counts. |
| 2026-06-12 | Moved model panels into a processed subfolder and added readiness figures | Keep generated panel CSVs and panel metadata under `2_data/processed/model_panels/`; add notebook-generated global sample, feature-availability, and missingness-burden figures under `4_analysis/figures/model_panels/`. |
| 2026-06-12 | Filtered generated model panels to target-observed rows | Drop rows missing `env_patent_share_inventions` from panel CSVs while preserving predictor missing values and recording pre-filter grid counts in coverage metadata. |
| 2026-06-12 | Added fossil-energy source-quality rules and explicit `NaN` serialization | Convert invalid fossil-energy source values to missing before lag construction; write panel missing values as `NaN`; record affected values in `model_panel_quality_summary.csv`. |
| 2026-06-13 | Added active model-panel v2 after main-predictor reassessment | Move `fossil_energy_share` and `tertiary_enrollment` from the active main specification to robustness/exploratory status; write v2 outputs under `2_data/processed/model_panels/v2/` and v2 figures under `4_analysis/figures/model_panels/v2/`. |
| 2026-06-13 | Added second-target robustness panels | Generate `env_patents_per_million` v2 panels under `2_data/processed/model_panels/robustness/env_patents_per_million/v2/` using the active v2 predictor specification. |
