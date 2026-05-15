# Predicting Environment-Related Innovation

> Managerial AI Course Project — LMU Munich, SS 2026  
> Prof. Stefan Feuerriegel | Institute of AI in Management

## Project Goal

This project predicts country-level environment-related innovation using publicly available panel data.

The core task is to:

1. Identify a suitable target variable from OECD patent data.
2. Select a small, literature-based set of predictors.
3. Build an interpretable machine learning model.
4. Assess which predictors are most strongly associated with future environment-related innovation.

The exact target variable, predictor list, country-year coverage, and final model strategy will be confirmed after literature review and data inspection.

## Source of Truth

The main project requirement is:

- `0_organization/predicting_environment-related_innovation.txt`

Project governance and research decisions are documented in:

- `0_organization/project_rules.md`
- `0_organization/decision_log.md`
- `1_literature_review/variable_framework.md`
- `2_data/data_dictionary.md`

Generated or preliminary content should be treated as a starting point, not as a fixed plan.

## Current Research Direction

The project will use a country-year panel structure.

Candidate data sources include:

| Source | Intended role |
|---|---|
| OECD patents on environment technologies | Candidate target variable |
| World Bank World Development Indicators | Candidate macroeconomic, R&D, energy, and emissions predictors |
| OECD Environmental Policy Stringency index | Candidate environmental policy predictor |
| RISE | Optional sustainable energy policy predictor |

Candidate predictor groups:

1. Macroeconomic development.
2. Research and development capacity.
3. Energy system characteristics.
4. Environmental policy.

Predictors should normally be lagged so that earlier country conditions are used to predict future innovation.

## Modeling Principle

The modeling strategy should stay interpretable and proportional to the research question.

Planned approach:

1. Start with a simple interpretable baseline.
2. Add more complex models only if they improve the research question, not just the score.
3. Use clear interpretation methods such as coefficients, permutation importance, SHAP, or partial dependence.
4. Report both predictive performance and substantive interpretation.

The final model family and evaluation metrics are deferred decisions and should be recorded in `0_organization/decision_log.md`.

## Repository Structure

```text
├── 0_organization/          Project requirements, rules, and decisions
├── 1_literature_review/     Literature notes and variable framework
├── 2_data/                  Data collection, raw data placeholders, processed data, and data dictionaries
│   ├── raw/                 Raw datasets, usually not committed
│   └── processed/           Cleaned panel data
├── 3_models/                Model plans, scripts, experiments, and outputs
│   ├── scripts/             Modeling scripts and experiment code
│   └── outputs/             Model metrics, summaries, and importance tables
├── 4_analysis/              Figures, tables, interpretation, and case-study material
│   ├── figures/
│   └── tables/
└── report/                  Final report or Overleaf-synced files
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Collaboration Rules

Use English for committed project documents, code comments, figure titles, table titles, and commit messages.

Use small, focused commits with the format:

```text
<type>: <short imperative summary>
```

Examples:

```text
docs: add project rules
data: add OECD patent download script
model: add elastic net baseline
analysis: add SHAP summary plot
fix: correct target variable lag
```

See `0_organization/project_rules.md` for the full project rules.
