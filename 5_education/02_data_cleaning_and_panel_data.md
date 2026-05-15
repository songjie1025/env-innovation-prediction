# Data Cleaning And Panel Data

This guide explains how raw public datasets can become a clean country-year panel for this project.

## Purpose Of Data Cleaning

Data cleaning means turning downloaded source data into a dataset that is consistent enough to analyze and model.

For this project, cleaning is not just about making a table look tidy. It helps answer practical research questions:

- Does each row refer to the right country and year?
- Are variables measured in the units we think they are?
- Are missing values visible instead of hidden?
- Are duplicate country-year rows removed or explained?
- Are predictors measured before the outcome they are supposed to predict?

Cleaning decisions can affect the final sample and results, so they should be documented in [2_data/data_dictionary.md](../2_data/data_dictionary.md) and, for major choices, in the [decision log](../0_organization/decision_log.md), which records important project decisions and reasons.

## Raw Versus Processed Data

Raw data are the downloaded source files in `2_data/raw/`. They should stay unchanged, even if they contain awkward names, missing values, or extra columns.

Processed data are cleaned outputs in `2_data/processed/`. These are the files the project can use for exploration, modeling, and reporting. A planned example is `2_data/processed/model_panel.csv`, which would contain one cleaned row per country-year.

Keeping raw and processed data separate makes the workflow easier to check. If something looks wrong in a processed file, collaborators can trace it back to the raw source and the script that created it.

## Typical Cleaning Steps For This Project

The exact cleaning steps depend on which target and predictors are selected, but the project will usually need the steps below.

### Consistent Country Codes

Country codes are short identifiers for countries. This project prefers ISO 3-letter codes in a column named `country_code`.

ISO 3-letter codes are internationally used three-letter country abbreviations. For example, Germany is `DEU`, Brazil is `BRA`, and the United States is `USA`.

Consistent codes matter because data come from different sources. OECD patent data, World Bank indicators, and the OECD Environmental Policy Stringency index must refer to the same country in the same way before they can be merged.

### Year Format

The `year` column should be a calendar year stored as an integer, such as `2010`, not a text label like `"2010 "` or a full date like `"2010-01-01"`.

A consistent year format helps create lags and check whether the panel has one row per country-year.

### Units

A unit tells us what a variable measures. Examples from the data dictionary include:

- `gdp_per_capita`: constant 2015 US dollars.
- `rd_expenditure_gdp`: percent of GDP.
- `renewable_energy_share`: percent of final energy consumption.
- `co2_per_capita`: metric tons per capita.
- `eps_index`: 0-6 policy stringency scale.
- `env_patents_per_million`: environment-related inventions per million people.

Units must be checked before variables are compared, transformed, or interpreted. A percent, a count, and an index are not interchangeable.

### Missing Values

A missing value is an empty or unavailable data point. For example, `researchers_per_million` has thinner coverage than `population`, so some countries or years may be missing.

The project should record missingness before modeling. Missing data should not silently remove important countries or years without explanation.

### Duplicates

A duplicate occurs when the same key appears more than once. In this project, the key should usually be `country_code` plus `year`.

If Germany in 2010 appears twice after a merge, the project must resolve why. The duplicate might come from different units, different patent categories, or an incorrect merge.

### Range Checks

A range check looks for values that are impossible or suspicious.

Examples:

- A percentage such as `renewable_energy_share` or `manufacturing_share` should usually not be negative.
- `rd_expenditure_gdp` should be checked because it is measured as a percent of GDP.
- `eps_index` should fit its documented 0-6 scale.
- `population` and `gdp_per_capita` should not be negative.

Range checks do not automatically prove a value is wrong, but they tell collaborators what needs inspection.

### Merging

Merging means combining datasets using shared identifiers. For this project, the usual merge keys are `country_code` and `year`.

For example, the project may merge OECD patent candidate targets with World Bank predictors such as `gdp_per_capita`, `population`, `renewable_energy_share`, and `co2_per_capita`. It may also merge policy variables such as `eps_index`, while noting that policy coverage may cover fewer countries.

After merging, the project should check that country names and codes still match and that the number of rows makes sense.

### Transformations

A transformation changes a variable's scale or form. Transformations can make variables easier to compare or model.

For example, GDP per capita is often highly unequal across countries. A log transform can make very large differences less dominant.

Log means logarithm: a mathematical rescaling that compresses large numbers more than small numbers. A standard log transform requires positive values, so zero or negative values must be checked and handled before creating a logged variable.

`log_gdp_per_capita = log(gdp_per_capita)`

In words, this creates a new variable from the logarithm of `gdp_per_capita`, after confirming that the values being logged are positive. The raw `gdp_per_capita` value should not be overwritten.

Other variables, such as `gdp`, `population`, `researchers_per_million`, `energy_intensity`, or `co2_per_capita`, may also need transformations depending on inspection and the final modeling plan.

### Lagged Predictors

A lagged predictor uses a value from an earlier year. For a one-year lag:

`x_lag1(country, year) = x(country, year - 1)`

In words, the predictor for a country in one year comes from that same country in the previous year.

For example, if the target is an environment-related patent measure in 2015, a lagged predictor might use `rd_expenditure_gdp` from 2014. The project should create lagged variables explicitly, such as `rd_expenditure_gdp_lag1` or `gdp_per_capita_lag1`.

## Why Panel Data Needs One Row Per Country-Year

The model needs a clear unit of observation. In this project, that unit is usually one country in one year.

One row per country-year helps collaborators know exactly what each prediction means. It also supports basic checks:

- Is there only one row for each `country_code` and `year`?
- Which years are available for each country?
- Which variables are missing for each country-year?
- Are predictors and outcomes aligned in time?

Without this structure, the project could accidentally mix countries, double-count years, or compare variables measured at different levels.

## Why Lagging Predictors Reduces Time Leakage

Time leakage happens when information from the future enters a prediction task.

This project wants to predict future environment-related innovation using earlier country conditions. If we use 2020 policy, income, or R&D information to predict 2019 innovation, the model has seen information that would not have been available at the time.

Lagging predictors reduces this risk. It tells the model: use earlier values, such as `gdp_per_capita_lag1`, `renewable_energy_share_lag1`, or `eps_index_lag1`, to predict a later innovation outcome.

Lagging does not solve every timing problem, but it makes the intended time order visible and easier to check.

## Missing Data Options

Missing data handling should be transparent because it can change the final sample.

### Transparent Dropping

Dropping means removing rows that have missing values in variables needed for a specific analysis.

This is simple and easy to explain, but it can shrink the sample. For example, variables such as `rd_expenditure_gdp`, `researchers_per_million`, or `eps_index` may have thinner coverage than macro variables such as `population` or `gdp_per_capita`.

If rows are dropped, the project should report which variables caused the loss and how many countries and years remain.

### Simple Imputation

Imputation means filling in missing values. A simple method might use a country average, a year average, or a nearby observed value.

Simple imputation can preserve more rows, but it adds assumptions. The project should document which variables were imputed, which rule was used, and how many values were affected.

### Complex Imputation

Complex imputation uses a more advanced method to estimate missing values.

This may be useful if missingness threatens the core analysis, but it can also make results harder to explain. If complex imputation is used, the method should be documented clearly, and the project should explain why a simpler option was not enough.

## Practical Rule For This Project

The cleaned modeling panel should make timing, units, and missingness visible. A collaborator should be able to look at a row and understand: this is one country, in one year, with a possible innovation outcome and predictors that were measured earlier or otherwise handled in a documented way.
