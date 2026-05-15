# Project Computing Context

This guide explains why the project uses code, public datasets, scripts, notebooks, and documentation. It is written for collaborators who may not have the same computing background.

## Why Use Code Instead Of Manual Spreadsheet Work?

This project works with public country-year data from sources such as OECD patent indicators, World Bank indicators, and OECD policy data. These datasets cover many countries, many years, and many candidate variables.

Manual spreadsheet work can be useful for a quick look, but it becomes risky when the same cleaning step must be repeated many times. A copied formula, hidden filter, or manually changed cell can be hard to trace later.

Code helps because it makes the workflow repeatable:

- The same download or cleaning step can be run again.
- Other collaborators can inspect exactly how a variable was created.
- Mistakes are easier to find because the steps are written down.
- Results can be updated when a source file changes.

Using code does not mean every decision is automatic. Research choices, such as the final target variable, predictor list, country-year coverage, and model strategy, still need human judgment and documentation.

## The Country-Year Panel Idea

The main dataset should be a country-year panel. This means each row represents one country in one calendar year, such as Germany in 2010 or Brazil in 2015.

An outcome is the value a later analysis or model tries to explain or predict. In this project, a candidate outcome could be an OECD environment-related patent measure.

A predictor is an input variable that may help explain or predict the outcome. Candidate predictors usually come from earlier years, such as GDP per capita, R&D expenditure, renewable energy share, CO2 emissions per capita, or an environmental policy index. Same-year predictors should be used only if they are clearly justified and documented.

This structure lets the project compare countries over time while keeping the timing of predictors and outcomes clear.

## What Each Project Area Does

The repository separates different kinds of work so collaborators can find the right file and understand where changes belong.

### Raw Data

Raw data are downloaded source files stored in `2_data/raw/`.

Raw files should stay unchanged. They are the record of what came from the public source. If a value looks odd, we should clean it in a processed file or script, not quietly edit the raw file by hand.

### Processed Data

Processed data live in `2_data/processed/`.

These files are cleaned outputs created from raw data. For example, a future `model_panel.csv` would be the cleaned country-year panel used for modeling. Processed files should have consistent country codes, year formats, variable names, units, and documented transformations.

### Scripts

Scripts are reusable code files, usually stored in folders such as `2_data/scripts/` or `3_models/scripts/`.

A script is best for work that should be run the same way again, such as downloading data, checking coverage, cleaning variables, creating lags, or training a model.

### Notebooks

Notebooks are narrative exploration files, usually stored in folders such as `2_data/notebooks/`.

A notebook is useful when collaborators want to see code, tables, charts, and explanation together. In this project, notebooks should use reusable scripts where possible instead of copying large blocks of logic.

### Documentation

Documentation explains decisions, definitions, and workflow rules.

Good documentation prevents confusion about what a variable means, where a file came from, or why a modeling choice was made. It should not pretend that open decisions are already settled.

## How Existing Files Fit Together

These files are the main starting points for the current workflow:

- [README.md](../README.md) gives the project goal, research direction, repository structure, setup steps, and collaboration rules.
- [2_data/data_dictionary.md](../2_data/data_dictionary.md) records datasets, candidate variables, units, coverage notes, transformation rules, missing-data rules, and data-quality checks.
- [2_data/scripts/data_exploration.py](../2_data/scripts/data_exploration.py) downloads or inspects current candidate data sources and writes coverage summaries and OECD patent metadata outputs.
- [2_data/notebooks/data_exploration.ipynb](../2_data/notebooks/data_exploration.ipynb) provides a narrative way to inspect the exploration results, display tables, and connect the script output to research questions.
- [3_models/model_plan.md](../3_models/model_plan.md) describes the intended modeling workflow, candidate model families, evaluation ideas, and open modeling decisions.

Together, these files form a chain:

1. The [README.md](../README.md) explains the project direction.
2. The data dictionary defines candidate datasets and variables.
3. The exploration script checks what data are actually available.
4. The exploration notebook helps collaborators inspect and discuss those results.
5. The model plan explains how a cleaned panel may later be used for interpretable prediction.

The chain is still provisional. The final target, final predictors, final coverage, and final model are not fixed yet.

## What Collaborators Should Know

- Use English for project files saved in the repository, code comments, figure titles, table titles, and commit messages.
- Treat raw data as source material; do not manually overwrite raw downloaded values.
- Expect the main modeling dataset to use one row per `country_code` and `year`.
- Remember that candidate variables are not automatically final variables.
- Keep predictor timing clear so future information does not enter past predictions.
- Put repeated logic in scripts and use notebooks for explanation, inspection, and discussion.
- Record important choices in the [decision log](../0_organization/decision_log.md), the short record of important project decisions and reasons, when the project selects a target, predictors, coverage, model family, or evaluation metric.
- Keep additions focused on predicting and interpreting country-level environment-related innovation.
