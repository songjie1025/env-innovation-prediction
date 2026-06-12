# Decision Log

This file records important project decisions so that the research direction stays traceable.

Decision entries should be short. Each entry should explain what was decided, why it was decided, and which alternatives were considered.

## Format

```text
### YYYY-MM-DD: Short decision title
Decision:
Reason:
Alternatives considered:
Status:
```

Status options:

1. `Active`: currently guiding the project.
2. `Revised`: replaced by a later decision.
3. `Deferred`: discussed but not decided yet.

## Decisions

### 2026-06-12: Store model-panel outputs in a dedicated subfolder and add readiness figures

Decision:
Write generated model-panel CSVs and panel metadata to `2_data/processed/model_panels/`, not directly to `2_data/processed/`. Add data-cleaning-stage readiness figures under `4_analysis/figures/model_panels/`: sample construction, prediction-safe versus retrospective sensitivity coverage, main-panel missingness, corrected RTA distribution, and interpolation audit.

Reason:
The processed root already contains raw audits and candidate-discovery artifacts. A dedicated model-panel subfolder keeps deliverables scannable and makes it clear which files are generated panel inputs. The figures are diagnostic rather than model-result visuals; they help defend sample construction, missingness, RTA measurement, and the decision not to use full-series interpolation as the primary prediction input.

Alternatives considered:
Keeping panel CSVs in the processed root was rejected because it mixes final panel candidates with upstream audit artifacts. Model-performance plots were rejected for this notebook stage because the modeling pipeline and validation design are not yet built.

Status:
Active

### 2026-06-12: Correct RTA source and mark no-imputation panels as primary

Decision:
Use OECD `IX.DEV.ENV_PAT._Z` as the main model's environmental-technology RTA predictor, with the project variable name `env_technology_rta`. Treat no-imputation panels as the primary prediction-safe analysis-base panels. Keep full-series linear-interpolated panels only as retrospective sensitivity outputs, not as the main forecasting or pseudo-out-of-sample modeling input.

Reason:
The previously downloaded `PT_TECH.DEV.ENV_PAT._Z` series is the percentage of technologies, not the RTA-style specialization index expected from the literature variable. The OECD `IX.DEV.ENV_PAT._Z` series is an index: local validation shows that `PT_TECH / IX` is constant within each year, implying that `IX` scales a country's environmental-technology share by the corresponding annual benchmark. Values above 1 therefore indicate relative environmental-technology specialization. This matches the intended path-dependence predictor better than the raw PT_TECH percentage, which can exceed 100 and had already been rejected as a main target because of interpretation risk.

Full-series linear interpolation is not prediction-safe because an internal gap before target year `t` can be filled using observations from year `t` or later before lag construction. It remains useful for a retrospective coverage sensitivity check, but the main analysis should report no-imputation samples or use imputation inside the later modeling pipeline after train/test splits are defined.

Alternatives considered:
Keeping `PT_TECH.DEV.ENV_PAT._Z` under the old `env_technology_share_for_rta` name was rejected because it would invite a reviewer to challenge the variable as not actually being RTA. Dropping the RTA predictor was rejected because the literature list explicitly motivates lagged environmental-technology specialization as a path-dependence predictor. Using the full-series linear-interpolated panels as the primary sample was rejected because it can introduce look-ahead leakage.

Status:
Active

### 2026-06-12: Build lagged main and submodel predictor panels

Decision:
Split the 20 selected predictors into one main model group and three submodel groups, and build lagged analysis-base country-year panels for each group. The main model uses 11 predictors: `gdp_constant_2015_usd`, `renewable_energy_share`, `wgi_regulatory_quality`, `co2_per_capita_ar5`, `fdi_net_inflows`, `tertiary_enrollment`, `env_technology_rta`, `scientific_journal_articles`, `trade_openness`, `inflation`, and `fossil_energy_share`. Submodel A uses `rise_energy_efficiency`, `rise_renewable_energy`, and `high_tech_exports`. Submodel B uses `rd_expenditure_gdp`, `env_co_invention_share`, `energy_imports_net`, `researchers_per_million`, and `environmental_tax_revenue`. Submodel C uses `eps_index`.

For every predictor `x`, create `x_lag1` and `x_lag1_3_mean`. Produce a no-imputation primary version and a linear-interpolated retrospective sensitivity version of each panel. The no-imputation version keeps source missing values unchanged and requires all three lag years to compute `x_lag1_3_mean`. The linear-interpolated version fills only internal gaps within the same country-predictor series before lag construction; it does not extrapolate at country-series starts or ends, and it does not impute the target, but it is not prediction-safe because it can use future endpoints. The main model uses the raw predictor window 1996-2022 and `fossil_energy_share` as the anchor variable. Submodels automatically select the predictor with the fewest covered World Bank/OECD-style 3-letter-code countries in the common raw predictor window as the anchor.

Reason:
The project is now moving from broad candidate screening to reproducible data cleaning. Separate main and submodel panels preserve the agreed predictor grouping while avoiding premature complete-case dropping across all 20 predictors. Reporting both no-imputation and retrospective linear-interpolated panels makes the sample-size tradeoff visible without making interpolation the primary prediction design. Lagged features preserve temporal ordering, and anchoring each panel on its most restrictive predictor documents the effective country and year coverage. The current `predictorsv1` files and aggregate-entity filter produce 178 main-model anchor countries for 1996-2022.

Alternatives considered:
Using only a no-imputation panel for all reporting was considered but would hide the coverage sensitivity created by internal gaps. Using linear interpolation as the main dataset was rejected because it adds assumptions and can introduce look-ahead leakage in a prediction design. Building one combined 20-predictor table was rejected because the narrow policy and R&D variables would make the main sample unnecessarily small. Manually setting submodel anchors was rejected in favor of a reproducible coverage-based rule. Extrapolating missing values at the beginning or end of a country series was rejected because it would add stronger assumptions and potential timing risk.

Status:
Active

### 2026-06-12: Compare lag-1 and three-year lagged mean ML specifications

Decision:
Pre-specify and compare two machine-learning timing specifications rather than treating one as the only main design. For each selected predictor `x`, construct a one-year lag specification, `x_lag1 = x_{t-1}`, and a three-year lagged moving-average specification, `x_lag1_3_mean = mean(x_{t-1}, x_{t-2}, x_{t-3})`, to predict the target in year `t`. Both supervised-learning tables should use pre-outcome predictor information only and should be evaluated under the same time-aware validation or pseudo-out-of-sample split. If the three-year lagged mean is used and the predictor window begins in 1996, the corresponding target years should begin in 1999 so that all three lag years are observed before the outcome.

Reason:
The project is closer to a Kaggle-style prediction task than to a single-coefficient causal panel regression. In economic machine-learning forecasting, lagged values and rolling or moving-average transformations are standard feature-engineering choices, while model choice and feature usefulness should be evaluated out of sample. The one-year lag is transparent and aligns with common panel practice. The three-year lagged mean captures more persistent pre-outcome conditions and smooths one-year measurement noise. Running both specifications lets the project compare short-run and medium-run predictive signals while preserving temporal ordering and avoiding contemporaneous or future information.

Alternatives considered:
Using only contemporaneous predictors was rejected because it risks simultaneity and look-ahead leakage. Using only `x_lag1` was considered more standard and interpretable but may miss slower R&D, energy-system, or policy effects. Using only `x_lag1_3_mean` was considered defensible but adds a stronger feature-engineering assumption and is less directly comparable to standard lagged-panel studies. Including both `x_lag1` and `x_lag1_3_mean` in the same primary model can be explored later, but it is not the pre-specified primary comparison because the two features are mechanically related. Selecting an optimized lag separately for every predictor was rejected for the main protocol because it would increase researcher degrees of freedom. Random row-level splits were rejected because they can leak future panel information across train and test rows.

Status:
Active

### 2026-06-12: Clarify lag-window rationale and robustness checks

Decision:
Keep `x_lag1_3_mean` as the pre-specified main predictor timing specification. Treat the three-year lagged mean as a pragmatic simplification of delayed innovation-response logic, not as a claim that the literature uses one universal three-year average. When the predictor window begins in 1996, the main target years should begin in 1999 so that the `t-1`, `t-2`, and `t-3` predictors are all pre-outcome information. Include robustness checks with a single `t-1` lag and, where coverage allows, a longer lag window such as `t-1` to `t-5`, especially for R&D and policy submodels.

Reason:
The reviewed literature uses heterogeneous timing strategies rather than one standard lag rule: single-year lags, distributed-lag or dynamic-response models, knowledge-stock or cumulative past-input measures, and sometimes lagged patent stock controls. Policy and energy-price studies suggest that patent responses unfold over several years, while R&D and knowledge-production-function studies emphasize accumulated knowledge stocks rather than contemporaneous flows. A three-year pre-outcome average preserves temporal ordering, avoids time leakage, reduces noise from any single lag year, and keeps the main interpretable ML specification simple and reproducible.

Alternatives considered:
Using contemporaneous predictors was rejected because it risks simultaneity and future-information leakage. Using only `t-1` was considered too short for R&D, energy-system, and environmental-policy mechanisms, but remains useful as a robustness check. Selecting a different optimized lag for each predictor was rejected for the main model because it would increase researcher degrees of freedom and make the specification harder to defend. Full distributed-lag or formal knowledge-stock models are theoretically richer, but are better reserved for robustness checks or submodels given the project's sample size, coverage constraints, and interpretability goals.

Status:
Revised by the 2026-06-12 lag-feature protocol decision.

### 2026-06-08: Use lagged moving averages for predictors

Decision:
Use three-year lagged moving averages as the main predictor timing specification. For each selected predictor `x`, construct `x_lag1_3_mean` as the mean of years `t-1`, `t-2`, and `t-3` to predict the target in year `t`.

Reason:
Environment-related innovation is unlikely to respond immediately to economic, R&D, energy-system, or policy conditions. A three-year lagged moving average captures persistent pre-outcome conditions, reduces reliance on a single arbitrary lag year, and preserves temporal ordering so that future information does not enter the prediction. This specification is especially defensible for R&D capacity and environmental policy, where the literature suggests delayed innovation responses.

Alternatives considered:
Using only `t-1` lags was considered too short for innovation responses, although it remains useful as a robustness check. Selecting different single-year lags separately for each predictor was rejected for the main model because it would increase researcher degrees of freedom and make the specification harder to defend. Single-year `t-1`, `t-2`, and `t-3` lags may still be used in robustness checks.

Status:
Revised by the 2026-06-12 lag-feature protocol decision.

### 2026-05-29: Initial screening of predictors

Decision:
Establish 27 candidate predictors across four domains.

Reason:
A broad initial screening based on supporting literature, known database filters, and joint discussions yielded 28 candidate predictors across R&D (6), energy (7), environmental policy (6), and macroeconomic (9) domains. Out of these, 27 have usable data (energy prices were excluded due to a lack of reliable data).
Predictor-Sheet: https://docs.google.com/spreadsheets/d/1SlEGhS8oKusUw6yMD-uIx9nkF4bgEVjYap7jfiHd6Q8/edit?gid=0#gid=0 

Alternatives considered:
A preliminary review indicates high correlation among many of the predictors. We estimate that the final modeling set will likely be narrowed down to 6-8 predictors representing the various domains.

Status:
Deferred

### 2026-05-20: Set the target variable

Decision:
Use PT_INV.DEV.ENV_PAT._Z (Percentage of inventions) as the main target variable.

Reason:
Based on the screening in `GitHub/2_data/notebook/candidate_discovery.ipynb`, combined with offline reviews and discussions, "Percentage of inventions" was selected over "Inventions per person". This choice was made because the "Percentage of inventions" measure offers better country coverage, higher data quality, and is logically more compelling.

Alternatives considered:
Inventions per person as other possible target variable candidate

Status:
Active

### 2026-05-20: Treat RISE as an alternative policy predictor

Decision:
RISE will be kept as an alternative or robustness policy predictor rather than replacing OECD EPS as the main policy candidate at this stage.

Reason:
OECD EPS has stronger direct support in the environmental-policy and green-patent literature, but its country coverage is narrow. RISE has broader country coverage and annual pillar data from 2010-2023, but it measures sustainable-energy regulatory readiness rather than general environmental policy stringency. If used, the project should prefer lagged RISE Renewable Energy or Energy Efficiency pillar scores over the overall RISE score.

Alternatives considered:
Replacing EPS with RISE was rejected for now because RISE is conceptually broader and has weaker direct patent-innovation evidence. Dropping RISE was also rejected because its broader country coverage may be valuable for an alternative policy specification.

Status:
Active

### 2026-05-19: Add candidate discovery before model building

Decision:
Before building the modeling panel, the project will use a dedicated candidate discovery step that catalogs OECD patent target combinations and literature/database-driven predictor candidates.

Reason:
The first-pass data exploration checked feasibility for a small initial set, but it did not by itself show that the relevant target and predictor candidate space had been systematically screened. A candidate discovery catalog makes the screening logic, coverage status, inclusion decisions, and dropped alternatives auditable before final variable selection.

Alternatives considered:
Moving directly to model construction was rejected because it would make variable selection look ad hoc. Downloading every possible indicator time series was also rejected because it would add complexity without improving the interpretability of the final project.

Status:
Active

### 2026-05-19: Keep predictor selection provisional

Decision:
The predictor candidate catalog is a provisional discovery artifact, not the final predictor list for modeling.

Reason:
The literature review is still in progress. The current catalog organizes plausible predictors, coverage status, measurement caveats, and inclusion labels so the project can avoid ad hoc variable choice, but the final predictor set should only be selected after the remaining literature notes and coverage checks are reviewed together.

Alternatives considered:
Treating the current predictor catalog as the final model specification was rejected because it would overstate the completeness of the literature review.

Status:
Active

### 2026-05-18: Treat `env_patent_share_inventions` as the leading target candidate

Decision:
The first literature-review pass treats `env_patent_share_inventions` as the leading main target candidate, with `env_patents_per_million` kept as a robustness or alternative intensity target.

Reason:
OECD target metadata and patent-measurement sources support a normalized patent-share measure tied to domestic inventions. This choice is easier to defend than `env_patent_share_tech`, which was already excluded as a main target because values above 100 create interpretation risk. A per-million indicator remains useful because it preserves patent intensity, but it may be more sensitive to general innovation-system scale.

Alternatives considered:
Using `env_patents_per_million` as the main target was considered but deferred because the project should first check skewness and size effects. Returning to `env_patent_share_tech` as the main target was rejected under the active 2026-05-16 decision.

Status:
Deferred

### 2026-05-16: Do not use `env_patent_share_tech` as the main target

Decision:
`env_patent_share_tech` (`PT_TECH.DEV.ENV_PAT._Z`) will not be used as the main target variable.

Reason:
The OECD API and the locally downloaded raw data both report Eritrea in 2016 with `PT_TECH = 350` and status `Normal value`. This is not a download or parsing error. However, values above 100 make the variable difficult to interpret as a simple country-level share of green innovation. The most plausible explanation is that the "percentage of technologies" measure can be inflated in very small patent systems when inventions are assigned to multiple technology categories. This creates a high interpretation risk for the main analysis.

Alternatives considered:
Using `env_patent_share_tech` as the main target was rejected. It may still be considered as a robustness or sensitivity variable if the sample is filtered and the interpretation is stated carefully. `env_patents_per_million` and `env_patent_share_inventions` remain candidate target variables.

Status:
Active

### 2026-05-15: Use lightweight project governance

Decision:
The project will use lightweight governance rules stored in `0_organization/project_rules.md`.

Reason:
The project needs enough structure to prevent scope drift and documentation disorder, but it should remain practical for a course project.

Alternatives considered:
A more formal project-management structure with detailed issue tracking and approval gates was considered unnecessary at this stage.

Status:
Active

### 2026-05-15: Treat the organization file as the source of truth

Decision:
The main requirement file, `0_organization/predicting_environment-related_innovation.txt`, is the highest-priority source for project scope.

Reason:
Some repository content was generated as an initial skeleton. The project should follow the seminar requirement first and use generated content only as a starting point.

Alternatives considered:
Using the generated README as the fixed project plan was rejected because it contains specific modeling and analysis choices that are not required by the organization file.

Status:
Active

### 2026-05-15: Use controlled first-pass data exploration

Decision:
The first data step is a controlled feasibility exploration of OECD patent indicators, World Bank candidate predictors, and OECD EPS, rather than a full modeling dataset build.

Reason:
The target variable, final predictor list, country coverage, and year coverage must be checked before committing to a modeling pipeline.

Alternatives considered:
Building the full data pipeline immediately was rejected because it could lock in weak variables or mismatched coverage too early.

Status:
Active

### 2026-05-15: Keep target-variable choice deferred after first data exploration

Decision:
The OECD `Patents - indicators` dataset provides strong target candidates, but the final target variable is not selected yet.

Reason:
The first-pass exploration found three viable candidates: `env_patent_share_tech`, `env_patent_share_inventions`, and `env_patents_per_million`. The final choice should depend on literature fit and modeling interpretation, not coverage alone.

Alternatives considered:
Immediately selecting `env_patent_share_tech` was considered but deferred because the difference between "percentage of technologies" and "percentage of inventions" should be understood from OECD metadata and the literature first.

Status:
Deferred

## Deferred Decisions

The following decisions should be made after literature review and initial data inspection:

1. Final predictor list.
2. Country and year coverage.
3. Main evaluation metric.
4. Final model family or model comparison strategy.
5. Final report structure.
