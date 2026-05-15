# Variable Framework

This document connects the research question, the literature review, and the candidate variables for the empirical analysis.

The final predictor list should be small, interpretable, and justified by theory or prior empirical work. Candidate variables listed here are not automatically included in the final model.

## Research Question

How can country-level economic, technological, energy-related, and policy conditions help predict future environment-related innovation?

## Target Concept

Environment-related innovation is measured through patent-based indicators from the OECD.

Candidate target:

| Concept | Candidate source | Candidate measure | Status | Notes |
|---|---|---|---|---|
| Environment-related innovation | OECD `Patents - indicators` | `env_patent_share_tech`: environment-related technologies as percentage of all technologies | Candidate | Strong coverage in first-pass exploration: 1990-2023, 202 countries. |
| Environment-related innovation | OECD `Patents - indicators` | `env_patent_share_inventions`: environment-related technologies as percentage of inventions | Candidate | Strong coverage in first-pass exploration: 1990-2023, 202 countries. |
| Environment-related innovation | OECD `Patents - indicators` | `env_patents_per_million`: environment-related inventions per million people | Candidate | Useful normalized alternative: 1990-2023, 196 countries. |

Target-variable decision rule:

1. Prefer a country-year measure that is comparable across countries and time.
2. Prefer a normalized measure, such as a patent share, if country size would otherwise dominate the outcome.
3. Use patent counts only if the model explicitly controls for country size or innovation system scale.
4. Confirm the OECD metadata distinction between "percentage of technologies" and "percentage of inventions" before choosing the final target.
5. Record the final target choice in `0_organization/decision_log.md`.

## Predictor Groups

The organization file suggests a small set of covariates from macroeconomic development, research and development, energy, and environmental policy. The framework below follows those areas.

### 1. Macroeconomic Development

Expected mechanism:
Countries with higher income, stronger industrial capacity, and larger markets may have more resources and demand for green innovation.

Candidate variables:

| Variable concept | Possible measure | Possible source | Expected relationship | Status |
|---|---|---|---|---|
| Economic development | GDP per capita | World Bank WDI | Positive | Candidate |
| Market size | GDP or population | World Bank WDI | Positive, but may require normalization | Candidate |
| Industrial structure | Manufacturing value added share | World Bank WDI | Ambiguous | Candidate |

Research notes to collect:

1. Does the literature model green patenting as a function of income level or market size?
2. Should GDP per capita be log-transformed?
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

Research notes to collect:

1. Is OECD EPS coverage broad enough for the intended panel?
2. Does RISE cover the same countries and years as the patent target?
3. Should policy variables be lagged to reflect delayed innovation response?

## Lag Structure

The project predicts future innovation, so predictors should usually be lagged.

Default plan:

1. Use predictor values from year `t-1` to predict environment-related innovation in year `t`.
2. Test `t-2` lags if the literature suggests slower innovation response or if `t-1` is too short.
3. Avoid using same-year predictors unless clearly justified and documented.

## Selection Principles

The final model should use a small predictor set. Prefer variables that satisfy most of the following:

1. Clear theoretical mechanism.
2. Reliable public source.
3. Good country-year coverage.
4. Comparable units across countries.
5. Low risk of measuring the same concept twice.
6. Interpretability for the final report.

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

## Open Research Decisions

Record final answers in `0_organization/decision_log.md`.

1. Should the target be a patent share, a patent count, or both?
2. Which countries and years have enough data for a balanced or usable unbalanced panel?
3. Which predictors survive the literature and coverage checks?
4. Which lag structure is most defensible?
