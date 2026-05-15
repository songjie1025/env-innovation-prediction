# Education Guides Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a beginner-friendly `5_education/` folder that explains the computing, data processing, and interpretable machine learning background needed for this course project.

**Architecture:** The folder will contain short Markdown guides, each with one clear topic and links back to the project source-of-truth documents. The guides should explain concepts in plain English, use project-specific examples, and include only light mathematical notation where it improves understanding.

**Tech Stack:** Markdown documentation in the existing repository; no runtime dependencies.

---

### Task 1: Data And Panel-Data Education Guides

**Files:**
- Create: `5_education/01_project_computing_context.md`
- Create: `5_education/02_data_cleaning_and_panel_data.md`

- [x] **Step 1: Draft `01_project_computing_context.md`**

Create a beginner-friendly guide that explains:
- Why this project uses code and public datasets instead of manual spreadsheet work.
- The country-year panel idea in one paragraph.
- The role of raw data, processed data, scripts, notebooks, and documentation.
- How existing files fit together: `README.md`, `2_data/data_dictionary.md`, `2_data/scripts/data_exploration.py`, `2_data/notebooks/data_exploration.ipynb`, and `3_models/model_plan.md`.
- A short "What collaborators should know" checklist.

Acceptance criteria:
- Plain English, suitable for collaborators with uneven computing backgrounds.
- No long formulas.
- No claims that final target, predictors, or models are already fixed.
- Keep the guide focused on this project, not generic programming advice.

- [x] **Step 2: Draft `02_data_cleaning_and_panel_data.md`**

Create a beginner-friendly guide that explains:
- The purpose of data cleaning.
- Raw versus processed data.
- Typical cleaning steps for this project: consistent country codes, year format, units, missing values, duplicates, range checks, merging, transformations, and lagged predictors.
- Why panel data needs one row per country-year.
- Why lagging predictors reduces time leakage.
- Missing data options: transparent dropping, simple imputation, and why complex imputation should be documented.
- Light formulas for a one-year lag and a log transform:
  - `x_lag1(country, year) = x(country, year - 1)`
  - `log_gdp_per_capita = log(gdp_per_capita)`

Acceptance criteria:
- Use examples from candidate variables in `2_data/data_dictionary.md`.
- Explain technical terms when first introduced.
- Keep formulas sparse and explained in words.

### Task 2: Machine Learning And Model Choice Education Guides

**Files:**
- Create: `5_education/03_machine_learning_basics.md`
- Create: `5_education/04_model_choices_for_this_project.md`
- Create: `5_education/05_evaluation_and_interpretability.md`

- [x] **Step 1: Draft `03_machine_learning_basics.md`**

Create a beginner-friendly guide that explains:
- Supervised learning in this project: predictors from earlier years, target innovation in a future year.
- Features, target, training data, validation/test data, prediction, and error.
- Underfitting and overfitting.
- Why random row splits are risky for time-oriented panel forecasting.
- Light formula for prediction error:
  - `error = observed value - predicted value`

Acceptance criteria:
- Avoid assuming readers know statistics or programming.
- Keep the explanation connected to country-level environment-related innovation.

- [x] **Step 2: Draft `04_model_choices_for_this_project.md`**

Create a guide that explains likely model families:
- Naive mean or country-group baseline.
- Linear regression.
- Elastic Net.
- Random Forest.
- Gradient boosting.
- Why interpretability matters for this course project.
- Why more complex models are optional and need justification.

Acceptance criteria:
- Explain each model by intuition, when it helps, when it can mislead, and how to interpret it.
- Include only light formulas for linear regression and regularization:
  - `prediction = beta0 + beta1*x1 + beta2*x2 + ...`
  - `loss = prediction error + penalty for large coefficients`
- Align with `3_models/model_plan.md`.

- [x] **Step 3: Draft `05_evaluation_and_interpretability.md`**

Create a guide that explains:
- Why model evaluation is more than reporting one score.
- RMSE, MAE, R-squared, and rank-based evaluation in plain English.
- Why evaluation should avoid time leakage.
- Coefficients, permutation importance, SHAP, and partial dependence.
- How interpretation should connect back to literature and mechanisms.

Acceptance criteria:
- Keep formulas limited to RMSE and MAE if used:
  - `MAE = average(|error|)`
  - `RMSE = sqrt(average(error^2))`
- Explain that final metrics and interpretation methods are open decisions until the model is built.

### Task 3: Integration, Index, And Glossary

**Files:**
- Create: `5_education/README.md`
- Create: `5_education/glossary.md`
- Modify: `README.md`

- [x] **Step 1: Create `5_education/README.md`**

Create an index that:
- Introduces the folder as beginner-friendly background material.
- Lists each guide with a one-sentence purpose.
- Suggests a reading order for collaborators.
- Links back to relevant existing project documents.

- [x] **Step 2: Create `5_education/glossary.md`**

Create a concise glossary for terms used across the project:
- Country-year panel
- Target variable
- Predictor / feature
- Lag
- Time leakage
- Missing value
- Imputation
- Transformation
- Baseline model
- Overfitting
- Validation set
- Test set
- RMSE
- MAE
- R-squared
- Interpretability
- Coefficient
- Permutation importance
- SHAP
- Partial dependence

Acceptance criteria:
- One short paragraph or bullet per term.
- Use project-specific examples where helpful.

- [x] **Step 3: Update root `README.md`**

Add `5_education/` to the repository structure and source-of-truth section as supporting background material.

Acceptance criteria:
- Do not make `5_education/` a source of research decisions.
- Keep the README wording concise.

### Verification

- [x] Run `find 5_education docs/superpowers/plans -type f | sort`.
- [x] Search for unresolved placeholders with `rg -n "TBD|TODO|FIXME|placeholder|lorem" 5_education docs/superpowers/plans README.md`.
- [x] Check internal Markdown links by listing links and confirming linked files exist.
- [x] Review the final diff with `git diff --stat` and `git diff -- README.md 5_education docs/superpowers/plans/2026-05-16-education-guides.md`.
