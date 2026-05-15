# Model Choices For This Project

This guide explains the candidate model families listed in the project [model plan](../3_models/model_plan.md). It uses plain English and project-specific examples.

The final model family has not been selected yet. The project should start simple, evaluate carefully, and only add complexity when it helps the research question.

## What A Model Does

A model is a rule for turning predictors into a target prediction.

In this project, a model may use earlier country conditions, such as R&D expenditure, GDP per capita, renewable energy share, CO2 emissions, or environmental policy stringency, to predict a later environment-related innovation measure.

The data are expected to use a country-year panel. That means each row represents one country in one year, such as Germany in 2014 or Brazil in 2018.

Different model families learn different kinds of rules. Some are simple and easy to explain. Others are more flexible but harder to interpret.

## Naive Mean Or Country-Group Baseline

### Intuition

A naive baseline is a simple reference model. It sets a low bar that more serious models should beat.

One version predicts the same average target value for every country-year. Another version may predict an average within a country group, such as an income group or region, if that grouping is defensible and available.

### When It Helps

A baseline helps answer a basic question: does the machine learning model improve on a very simple guess?

For example, if a complex model barely beats the average environment-related patent share, the complex model may not be worth using.

### When It Can Mislead

A naive baseline can hide important differences. Countries with different innovation systems, policy histories, or R&D capacity may receive the same prediction.

A country-group baseline can also mislead if the groups are too broad or if the grouping uses information that would not be available at prediction time.

### How To Interpret It

The interpretation is simple: the baseline shows what performance looks like without using detailed predictor information.

If another model cannot clearly improve on the baseline, that is a warning sign.

## Linear Regression

### Intuition

Linear regression predicts the target by adding up weighted predictor values.

The light formula is:

`prediction = beta0 + beta1*x1 + beta2*x2 + ...`

In words:

- `beta0` is the starting point.
- `x1`, `x2`, and later terms are predictors.
- `beta1`, `beta2`, and later terms are coefficients that say how strongly each predictor contributes to the prediction.

For example, a linear regression might estimate how predicted environment-related innovation changes when R&D expenditure increases, while holding other predictors in the model constant.

### When It Helps

Linear regression helps when the project needs a transparent first model. It is useful for checking whether relationships have plausible directions and sizes.

It is also easy to explain in the final report, especially if the predictor list is small and theoretically motivated.

### When It Can Mislead

Linear regression can mislead if the true relationship is not close to a straight-line pattern.

For example, R&D capacity may help innovation up to a point, but the relationship may not increase at the same rate for every country. Policy effects may also depend on country income, energy structure, or time delays.

Linear regression can also be sensitive when predictors are strongly related to each other. GDP per capita, R&D capacity, and education indicators may move together, which can make individual coefficients harder to interpret.

### How To Interpret It

The main interpretation comes from coefficients.

A positive coefficient means higher values of that predictor are associated with higher predicted innovation, holding the other included predictors constant. A negative coefficient means higher values are associated with lower predicted innovation, holding the others constant.

The interpretation should connect back to the literature. A coefficient is not automatically causal evidence.

## Elastic Net

### Intuition

Elastic Net is a regularized linear model. It keeps the basic linear regression idea but adds a penalty that discourages overly large or unstable coefficients.

The light formula is:

`loss = prediction error + penalty for large coefficients`

In words, Elastic Net tries to predict well while keeping the model controlled.

### When It Helps

Elastic Net helps when predictors are correlated or when the project has more candidate predictors than it wants in the final explanation.

For example, GDP per capita, total GDP, population, R&D expenditure, and researchers per million people may overlap in what they measure. Elastic Net can reduce unstable coefficient behavior and sometimes shrink less useful predictors toward zero.

### When It Can Mislead

Elastic Net can make a model look more objective than it is. The result still depends on the chosen target, predictors, transformations, lag structure, sample, and tuning settings. Tuning means choosing model settings, such as how strongly the model should penalize large coefficients.

It can also shrink coefficients in ways that are useful for prediction but not always straightforward for substantive interpretation. A small coefficient does not automatically mean the underlying concept is unimportant.

### How To Interpret It

Elastic Net is interpreted through its coefficients, like linear regression.

Because the model penalizes large coefficients, interpretation should focus on broad patterns:

- Which predictors remain useful after regularization?
- Are the coefficient signs plausible?
- Do the results match the literature and variable framework?

## Random Forest

### Intuition

Random Forest is a tree-based model. It builds many decision trees and combines their predictions.

A decision tree splits the data into groups. For example, it may first separate country-years by R&D intensity, then split again by GDP per capita, renewable energy share, or policy stringency.

The forest combines many such trees to make a more stable prediction.

### When It Helps

Random Forest can help when relationships are nonlinear or involve interactions.

For example, environmental policy stringency may matter more in countries with strong R&D capacity, or renewable energy share may have different meanings in high-income and lower-income countries. A Random Forest can capture patterns like that more easily than a simple linear model.

### When It Can Mislead

Random Forest can overfit if the dataset is small, noisy, or has uneven country-year coverage.

It can also make interpretation harder. The model may predict better, but it does not produce simple coefficients like linear regression. If the project cannot explain what the model learned, it may not satisfy the course project's interpretability goal.

### How To Interpret It

Common interpretation tools include permutation importance and partial dependence.

Permutation importance asks how much model performance worsens when one predictor is shuffled. Partial dependence shows how predictions change as one predictor changes, averaging over other predictors.

These tools should be used carefully and connected back to theory.

## Gradient Boosting

### Intuition

Gradient boosting is another tree-based approach. It builds many small models step by step. Each new step tries to fix errors made by earlier steps.

Gradient boosting often performs well on structured tabular data, such as country-year panels, if it is tuned carefully and evaluated honestly. Here, tuned means that the model settings are chosen carefully instead of left unchecked.

### When It Helps

Gradient boosting can help when the target has complex patterns that simpler models miss.

For example, the relationship between policy stringency and future innovation may vary across income levels, energy systems, and baseline innovation capacity. Boosting can model such patterns flexibly.

### When It Can Mislead

Gradient boosting can be easy to overuse. It has many tuning choices, meaning many model settings to choose, and can produce strong-looking scores that do not generalize if evaluation is not time-respecting.

It is also harder to explain than linear regression or Elastic Net. If the performance improvement is small, the added complexity may not be justified.

### How To Interpret It

Possible interpretation tools include permutation importance, SHAP, and partial dependence.

SHAP can attribute parts of an individual prediction to predictors relative to a baseline prediction. It does not show that a predictor caused the observed outcome. SHAP also adds another layer of method complexity, so it should be used only if the project can explain the method clearly and the final model justifies it.

## Why Interpretability Matters

The project is not only trying to forecast a number. It also asks which country-level conditions are most associated with future environment-related innovation.

Interpretability matters because the final report should explain the result in substantive terms:

- Does R&D capacity appear important?
- Does environmental policy stringency add predictive value?
- Do energy-system variables behave as expected?
- Are the findings consistent with the literature?

A model that predicts slightly better but cannot be explained may be less useful than a simpler model that gives clear, defensible insight.

## Why Complex Models Are Optional

Random Forest and gradient boosting are optional, not automatic.

They should be used only if they add value beyond the simpler baselines. A complex model needs justification from:

- Better validation or test performance.
- A time-respecting evaluation design.
- Enough data to support the added flexibility.
- Interpretation methods that can be explained clearly.
- A clear link to the research question.

The project [model plan](../3_models/model_plan.md) already follows this principle: start with interpretable baselines, then add advanced models only if they improve the research question and remain explainable.

## Practical Takeaway

A sensible model sequence for this project is:

1. Start with a naive baseline.
2. Fit a simple linear regression.
3. Try Elastic Net if correlated predictors or coefficient instability are concerns.
4. Consider Random Forest or gradient boosting only if the data and research value justify the extra complexity.
5. Record the final model choice and rejected alternatives in the [decision log](../0_organization/decision_log.md).
