# Education Guides

This folder explains the computing, data processing, and machine learning background behind the project in beginner-friendly language.

The guides are supporting material. They help collaborators understand the workflow, but they do not replace the project requirements, data dictionary, decision log, or model plan.

## Suggested Reading Order

1. [Project computing context](01_project_computing_context.md) explains why the project uses code, public data, scripts, notebooks, and documentation.
2. [Data cleaning and panel data](02_data_cleaning_and_panel_data.md) explains how raw country-year data becomes a usable modeling panel.
3. [Machine learning basics](03_machine_learning_basics.md) explains supervised learning, features, targets, prediction, and overfitting.
4. [Model choices for this project](04_model_choices_for_this_project.md) explains the candidate model families in the model plan.
5. [Evaluation and interpretability](05_evaluation_and_interpretability.md) explains how model performance and substantive interpretation should be assessed.
6. [Glossary](glossary.md) defines common technical terms used across the project.

## How To Use These Guides

Use these guides when a project document mentions a technical concept that is unfamiliar. For example:

- If `2_data/data_dictionary.md` mentions a lagged predictor, read the data cleaning guide.
- If `3_models/model_plan.md` mentions Elastic Net, Random Forest, or SHAP, read the model choice and interpretation guides.
- If a notebook or script feels hard to follow, start with the project computing context guide.

For research decisions, use the project source files:

- [Project rules](../0_organization/project_rules.md)
- [Decision log](../0_organization/decision_log.md)
- [Variable framework](../1_literature_review/variable_framework.md)
- [Data dictionary](../2_data/data_dictionary.md)
- [Model plan](../3_models/model_plan.md)
