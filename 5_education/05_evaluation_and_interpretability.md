# Evaluation And Interpretability

This guide explains how the project can judge model performance and interpret what a model learned.

The final evaluation metrics and interpretation methods are still open decisions. They should be chosen after the target variable, predictor list, sample coverage, and model family are known.

A country-year panel is a dataset where each row represents one country in one year, such as Germany in 2014 or Brazil in 2018. In evaluation, this matters because the model should be tested in a way that respects the time order of those rows.

## Why Evaluation Is More Than One Score

A model score is useful, but it is not the whole evaluation.

For this project, evaluation should answer several questions:

- Does the model predict future environment-related innovation better than a simple baseline?
- Are errors small enough to be useful in the unit of the chosen target?
- Does the model work on later years, not only on the data used for training?
- Are mistakes concentrated in certain countries, years, or target ranges?
- Can the model be interpreted in a way that supports the research question?

A single score can hide important problems. A model may have a good average error but perform poorly for lower-income countries, countries with missing R&D data, or years with unusual patent patterns.

## Prediction Error

Prediction error is the difference between the observed target value and the predicted value. It compares what happened in the data with what the model predicted.

If the model predicts an environment-related patent share of 8 percent and the observed value is 6 percent, the error is -2 percentage points. The prediction was too high.

Different metrics summarize these errors in different ways.

## MAE

MAE means mean absolute error.

The light formula is:

`MAE = average(|error|)`

In plain English, MAE is the average size of the prediction error, ignoring whether the model predicted too high or too low.

MAE is often easy to explain. If the chosen target is a patent share measured in percentage points, MAE can be read as the average absolute percentage-point error.

MAE can be useful when the project wants an understandable measure of typical prediction error.

## RMSE

RMSE means root mean squared error.

The light formula is:

`RMSE = sqrt(average(error^2))`

In plain English, RMSE gives extra weight to large errors. A few very bad predictions can raise RMSE more than they raise MAE.

RMSE can be useful if large prediction mistakes are especially important. For example, if the model badly misses countries with very high or very low environment-related innovation, RMSE will make those mistakes more visible.

RMSE should be interpreted in the unit of the chosen target.

## R-Squared

R-squared describes how much variation in the target is captured by the model's predictions.

For this project, R-squared can help explain whether the model captures meaningful differences in environment-related innovation across country-years.

However, R-squared can mislead if it is computed only on training data. A model can fit the training data well and still predict future years poorly. For prediction, test-set or other out-of-sample performance is more important than a score from data the model already saw.

Test-set R-squared can be low or even negative. A negative value means the model predicted worse than a very simple reference prediction for that test set, such as using the test-set average. It does not mean the project failed; it means the model may not generalize well under that evaluation design.

R-squared is also not enough on its own. A model can have a lower R-squared but still be easier to interpret and more useful for the course project. R-squared is not causal explanation: it does not prove that a predictor causes environment-related innovation.

## Rank-Based Evaluation

Rank-based evaluation focuses on ordering rather than exact values.

For example, the project may care whether the model can identify countries likely to have relatively high future environment-related innovation, even if the exact predicted patent share is imperfect.

Rank-based evaluation can be useful if the research question becomes more about relative country position than exact target values.

It can mislead if the project actually needs accurate values in the original unit. A model might rank countries fairly well while still predicting values that are too high or too low.

## Avoiding Time Leakage

Evaluation should avoid time leakage.

Time leakage happens when future information enters the training or evaluation process. This can make model performance look better than it would be in a real forecasting setting.

In this project, leakage could happen if:

- Same-year or future predictors are used to predict earlier innovation.
- Random row splits let later years help predict earlier years.
- Transformations or imputations use information from the full dataset before the train-test split.
- Model tuning, meaning the process of choosing model settings, repeatedly uses the final test set.

A safer evaluation design usually trains on earlier years and evaluates on later years, or otherwise respects the time order of the country-year panel. The final split strategy is still an open decision.

## Interpreting Linear Models With Coefficients

For linear regression and Elastic Net, interpretation usually starts with coefficients.

A coefficient describes how the prediction changes when one predictor increases, holding the other included predictors constant.

For example, a positive coefficient for R&D expenditure would mean that higher R&D expenditure is associated with higher predicted future environment-related innovation, given the other predictors in the model.

Important cautions:

- A coefficient is not automatically causal evidence.
- The sign and size can change when predictors are added, removed, transformed, or lagged differently.
- Correlated predictors can make individual coefficients harder to interpret.
- Units matter. A coefficient for a percent variable is not comparable to a coefficient for a dollar variable unless variables are standardized or otherwise transformed.

## Permutation Importance

Permutation importance asks a simple question: how much worse does the model perform if one predictor is randomly shuffled?

If shuffling R&D expenditure makes predictions much worse, the model relied on that variable. If shuffling renewable energy share barely changes performance, that variable may have added little predictive information in that model and sample.

Permutation importance can be used for many model families, including tree-based models.

It can mislead when predictors are strongly correlated. If two variables carry similar information, shuffling one of them may not look very important because the model can still use the other.

## SHAP

SHAP is an interpretation method that attributes parts of a model's prediction to predictors relative to a baseline prediction.

It can be useful for complex models, especially when the project wants to explain individual predictions. For example, SHAP might help describe which predictors moved one country-year's prediction above or below the model's baseline prediction.

SHAP can also add complexity. It may produce detailed plots that look precise, but the results still depend on the data, model, predictors, and assumptions. SHAP values are model-specific attributions, not causal effects. If used, the project should explain SHAP in plain English and connect it to the research question.

## Partial Dependence

Partial dependence shows how the model's prediction changes as one predictor changes while averaging over the other predictors.

For example, a partial dependence plot for environmental policy stringency could show whether predicted innovation tends to rise as policy stringency increases.

Partial dependence is helpful for nonlinear models such as Random Forest or gradient boosting because it can reveal curved relationships.

It can mislead if the plotted predictor combinations are unrealistic. For example, the plot may average over country conditions that rarely occur together in the real data.

## Connecting Interpretation To Literature

Interpretation should not stop at a model output table or a plot.

The project should connect model findings back to the literature and the variable framework:

- If R&D capacity is important, does that match theories about innovation systems?
- If environmental policy stringency matters, is the pattern consistent with induced innovation or the Porter hypothesis?
- If energy variables have ambiguous effects, do they reflect transition pressure, fossil-fuel lock-in, or measurement limitations?
- If GDP per capita dominates, is the model mainly capturing development level rather than environmental innovation mechanisms?

The goal is to explain what the model suggests and where the evidence remains uncertain.

## Practical Takeaway

Evaluation and interpretation should work together.

The project should report:

1. Performance against a simple baseline.
2. At least one clear error metric, chosen after inspecting the target.
3. A time-respecting evaluation design.
4. Interpretation methods that match the final model family.
5. A discussion that connects the results back to theory, mechanisms, and data limitations.

The final metric choices and interpretation tools should be recorded in the [decision log](../0_organization/decision_log.md) once the model is built.
