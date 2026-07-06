# Variable Framework

This document connects the research question, the literature review, and the candidate variables for the empirical analysis.

The final predictor list should be small, interpretable, and justified by theory or prior empirical work. Candidate variables listed here are not automatically included in the final model.

## Research Question

How can country-level economic, technological, energy-related, and policy conditions help predict future environment-related innovation?

## Target Concept

Environment-related innovation is measured through patent-based indicators from the OECD.

Selected main target and robustness targets:

| Concept | Candidate source | Candidate measure | Status | Notes |
|---|---|---|---|---|
| Environment-related innovation | OECD `Patents - indicators` | `env_patent_share_inventions`: `PT_INV.DEV.ENV_PAT._Z`, country or aggregate area's percentage contribution to worldwide environment-related inventions | Main target | Active decision in `0_organization/decision_log.md`; strong coverage in first-pass exploration: 1990-2023, 202 countries. This is a global-share measure, not a domestic green-portfolio share. |
| Environment-related innovation | OECD `Patents - indicators` | `env_patents_per_million`: `INV_PS.DEV.ENV_PAT._Z`, environment-related inventions per million people | Robustness target | Useful normalized intensity alternative: 1990-2023, 196 countries. |
| Environment-related innovation | OECD `Patents - indicators` | `env_patent_share_tech`: `PT_TECH.DEV.ENV_PAT._Z`, environment-related technologies as percentage of all domestic technologies / inventions | Diagnostic / sensitivity only | Not used as the main target because values above 100 create interpretation risk. This is an internal country portfolio share and should not be summed across countries. |

Target-variable rule:

1. Use `env_patent_share_inventions` as the main outcome in year `t`.
2. Keep `env_patents_per_million` as the main robustness outcome.
3. Use `env_patent_share_tech` only for diagnostic or sensitivity discussion because of its interpretation risk.
4. Use raw patent counts only if the model explicitly controls for country size or innovation-system scale.

## Predictor Groups

The organization file suggests a small set of covariates from macroeconomic development, research and development, energy, and environmental policy. The framework below follows those areas.

The predictor consideration pool combines:

1. The structured catalog in `2_data/processed/predictor_candidate_catalog.csv`.
2. The manual literature screening sheet `1_literature_review/Managerial AI- literature review - List 1.csv`.
3. Paper notes in `1_literature_review/notes/`.

Predictors should remain in the consideration pool at this stage. They should be assigned to one of four roles after literature, coverage, and statistical checks: main-model candidate, robustness candidate, exploratory/descriptive variable, or data-limited variable.

### 1. Macroeconomic Development

Expected mechanism:
Countries with higher income, stronger industrial capacity, and larger markets may have more resources and demand for green innovation.

Candidate variables:

| Variable concept | Possible measure | Possible source | Expected relationship | Status |
|---|---|---|---|---|
| Market size / economic scale | GDP, constant 2015 US dollars | World Bank WDI | Positive | Candidate for raw predictorsv1 |
| Economic development | GDP per capita | World Bank WDI | Positive | Replaced by total GDP for the main raw predictor set |
| Industrial structure / capacity | Manufacturing value added share | World Bank WDI | Positive | Main predictor; industrial-commons proxy (Cohen & Zysman 1987; Pisano & Shih 2009/2012). |
| Trade exposure | Trade openness | World Bank WDI | Ambiguous / positive | Candidate from CSV; data source to verify. |
| Macroeconomic stability | Inflation | World Bank WDI | Ambiguous | Candidate from CSV; data source to verify. |
| International capital links | Foreign direct investment | World Bank WDI | Ambiguous / positive | Candidate from CSV; data source to verify. |
| Institutional quality | Regulatory quality or WGI-style institutional indicator | WGI or related source | Positive | Candidate from CSV; source and coverage to verify. |

Research notes to collect:

1. Does the literature model green patenting as a function of income level or market size?
2. Should total GDP be log-transformed?
3. Is country size already handled by the target variable?

### 2. Research and Development Capacity

Expected mechanism:
Countries with stronger R&D systems should have greater capacity to generate patentable environmental technologies.

Candidate variables:

| Variable concept | Possible measure | Possible source | Expected relationship | Status |
|---|---|---|---|---|
| R&D intensity | R&D expenditure as percent of GDP | World Bank WDI or OECD | Positive | Candidate |
| Human capital in innovation | Researchers per million people | World Bank WDI or OECD | Positive | Candidate |
| Education or skills | Tertiary enrollment or education attainment | World Bank WDI or OECD | Positive | Candidate |
| Scientific output | Scientific journal articles | World Bank WDI | Positive | Candidate from CSV; likely exploratory or capacity proxy. |
| Technology-intensive production | High-tech exports | World Bank WDI | Positive / ambiguous | Candidate from CSV; may proxy innovation system or industrial composition. |
| General patenting capacity | Total resident patent applications | World Bank WDI | Positive | Candidate from CSV; use cautiously because the target is patent-based. |
| International collaboration | Co-invention rate | OECD patent data, calculated | Positive | Candidate from CSV; useful for knowledge diffusion mechanisms. |

Research notes to collect:

1. Which R&D indicators are available for enough countries and years?
2. Does the literature distinguish general R&D from green R&D?
3. Should R&D variables be lagged more than macroeconomic variables?

### 3. Energy System

Expected mechanism:
Energy structure may shape demand for environmental technologies. Fossil-fuel dependence, energy intensity, and renewable energy adoption can create different innovation incentives.

Candidate variables:

| Variable concept | Possible measure | Possible source | Expected relationship | Status |
|---|---|---|---|---|
| Renewable energy adoption | Renewable energy share in final energy consumption | World Bank WDI | Positive | Candidate |
| Fossil-fuel dependence | Fossil fuel energy consumption share | World Bank WDI | Ambiguous | Candidate |
| Energy efficiency pressure | Energy intensity | World Bank WDI | Ambiguous | Candidate |
| Emissions pressure | CO2 emissions per capita | World Bank WDI | Ambiguous | Candidate |
| Energy security exposure | Net energy imports | World Bank WDI | Ambiguous | Candidate from CSV; source and coverage to verify. |
| Energy cost pressure | Carbon or energy prices | OECD, IEA, or other source | Positive | Candidate from CSV; data-limited and likely exploratory unless a clean panel is available. |

Research notes to collect:

1. Does higher emissions pressure lead to more green innovation or indicate lock-in?
2. Are energy variables better interpreted as innovation demand, transition pressure, or structural constraints?
3. Which indicators have stable coverage across countries and years?

### 4. Environmental Policy

Expected mechanism:
Stricter environmental regulation can increase incentives to develop cleaner technologies, consistent with induced innovation and the Porter hypothesis.

Candidate variables:

| Variable concept | Possible measure | Possible source | Expected relationship | Status |
|---|---|---|---|---|
| Environmental policy stringency | OECD Environmental Policy Stringency index | OECD | Positive | Candidate |
| Sustainable energy regulation | RISE score or sub-index | RISE | Positive | Candidate |
| Carbon pricing or climate policy | Carbon tax, emissions trading, or policy score | OECD, World Bank, or other public source | Positive | Optional |
| Environmental tax burden | Environmental tax revenue | OECD | Positive | Candidate from CSV; source and coverage to verify. |
| Fossil-fuel support | Fossil-fuel subsidies or inverse fossil-support proxy | OECD, IEA, IMF, or WDI proxy | Negative / ambiguous | Candidate from CSV; measurement must not conflate subsidies with fossil consumption share. |
| Policy uncertainty | Economic Policy Uncertainty index | PolicyUncertainty.com | Negative / ambiguous | Candidate from CSV; country-year coverage to verify. |
| Policy stability | Rolling stability measure of EPS | Calculated from OECD EPS | Positive | Candidate from CSV; possible robustness feature distinct from policy strictness. |

Research notes to collect:

1. Is OECD EPS coverage broad enough for the intended panel?
2. Does RISE cover the same countries and years as the patent target?
3. Should policy variables be lagged to reflect delayed innovation response?

## Lag Structure

The project predicts future innovation, so predictors should be measured before the target year.

Main timing specification:

1. For each selected predictor `x`, construct `x_lag1_3_mean` as the mean of years `t-1`, `t-2`, and `t-3`.
2. Use `x_lag1_3_mean` to predict `env_patent_share_inventions` in year `t`.
3. Keep single-year `t-1`, `t-2`, and `t-3` lags as possible robustness checks.
4. Avoid using same-year predictors unless clearly justified and documented.

## Selection Principles

The final main model should use a small predictor set, but the broader literature-based predictor pool remains in consideration. Prefer variables that satisfy most of the following:

1. Clear theoretical mechanism.
2. Reliable public source.
3. Good country-year coverage.
4. Comparable units across countries.
5. Low risk of measuring the same concept twice.
6. Interpretability for the final report.

Screening should classify variables rather than remove them prematurely:

1. `Main model`: strongest theory, coverage, and interpretability.
2. `Robustness`: useful alternative measures of the same mechanism.
3. `Exploratory / descriptive`: conceptually relevant but weaker, overlapping, or more difficult to operationalize.
4. `Data-limited`: relevant in the literature but not currently usable without additional data work.

## Literature Review Tasks

For each important paper or source, record:

1. Citation.
2. Main research question.
3. Innovation measure used.
4. Predictor variables used.
5. Key mechanism or hypothesis.
6. Relevance for this project.
7. Any limitation that affects our design.

## Initial Hypotheses

These hypotheses are provisional and should be updated after the literature review.

1. Higher R&D intensity is associated with stronger future environment-related innovation.
2. Stricter environmental policy is associated with stronger future environment-related innovation.
3. Higher income levels may support innovation capacity, but the relationship may weaken after controlling for R&D.
4. Energy-system variables may capture both transition pressure and structural lock-in, so their expected signs are less certain.

## Current Evidence Assessment

The first paper-note pass in `1_literature_review/review_checklist.md` supports the following reviewer-style interpretation. These are not final modeling decisions; they should be revisited after note review and coverage checks.

The predictor assessment is especially provisional. The literature review is still ongoing, so the candidate predictor catalog should be read as a structured search record rather than the final model specification.

| Project decision | Current assessment | Evidence basis | Caveat |
|---|---|---|---|
| Main target | Use `env_patent_share_inventions` / `PT_INV.DEV.ENV_PAT._Z` as the selected main target, interpreted as a global contribution share. | Active 2026-05-20 decision, corrected 2026-07-06 OECD patent-indicator metadata check, Hascic and Migotto (2015), and OECD patent-statistics guidance. | Report the exact indicator code, unit, and the fact that country rows sum to about 100 after aggregate rows are excluded. |
| Robustness target | Keep `env_patents_per_million` as a robustness or alternative intensity target. | Patent-statistics normalization logic. | May be more sensitive to general innovation-system scale and skewness. |
| Non-main target | Keep `env_patent_share_tech` out of the main model. | Corrected OECD metadata interpretation: this is the domestic all-technologies share, but observed values above 100 create interpretation risk. | Could remain a carefully caveated sensitivity variable. |
| Predictor timing | Use three-year lagged moving averages, `x_lag1_3_mean`, as the main timing specification. | Active 2026-06-08 decision and literature support for delayed innovation responses. | Single-year lags remain robustness checks. |
| Policy predictor | Treat lagged `eps_index` as the strongest policy predictor candidate. | Kruse et al. (2022), Johnstone et al. (2010), Nesta et al. (2014), and Johnstone et al. (2012). | EPS narrows the panel and should be interpreted as predictive association, not causal proof. |
| R&D capacity | Treat `rd_expenditure_gdp` as a strong candidate if coverage permits. | Patent-policy and induced-innovation literature repeatedly points to innovation capacity or knowledge stocks. | WDI R&D is general R&D, not green R&D. |
| Researchers | Keep `researchers_per_million` as a secondary capacity proxy. | Conceptually aligned with innovation capacity. | Direct environmental-patent evidence is weaker and coverage is thin. |
| Energy variables | Use at most one energy-system variable in the first small model. | Popp (2002), Johnstone et al. (2010), and Nesta et al. (2014). | WDI renewable share, fossil share, energy intensity, and CO2 are not equivalent to energy prices or policy incentives. |
| Manufacturing share | Use `manufacturing_share` as the main-model industrial-capacity predictor. | Cohen and Zysman (1987), "Manufacturing Matters," and Pisano and Shih (2009, 2012) on the "industrial commons": manufacturing capability underwrites innovation capability. | Well covered (203 countries, 1990-2024) and near-independent of economic scale (main-panel VIF 1.06). |
| RISE | Keep as an alternative or robustness policy predictor, preferably using lagged Renewable Energy or Energy Efficiency pillar scores rather than the overall score. | RISE methodology note and 2026-05-20 decision log update. | Broader coverage than EPS, but conceptually wider and with weaker direct patent evidence. |
| Manual predictor sheet | Treat all predictor concepts in `Managerial AI- literature review - List 1.csv` as part of the current consideration pool. | 2026-05-29 screening decision and team discussion. | Classify into main, robustness, exploratory, or data-limited roles after coverage and collinearity checks. |

## Open Research Decisions

Record final answers in `0_organization/decision_log.md`.

1. Which countries and years have enough data for a balanced or usable unbalanced panel?
2. Which predictors enter the compact main model, and which stay as robustness or exploratory variables?
3. Which data-limited CSV predictors can be operationalized without adding excessive complexity?
4. Which final evaluation metric and model family are most defensible?
