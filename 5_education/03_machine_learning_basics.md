# Machine Learning Basics

This guide explains the basic machine learning ideas used in this project. It is written for collaborators who may be new to statistics, programming, or prediction models.

The project goal is to predict future country-level environment-related innovation using public country-year data. The exact target variable, predictor list, sample coverage, and final model are still open decisions.

A country-year panel is a dataset where each row is one country in one year, such as Germany in 2014 or Brazil in 2018. This structure lets the project compare countries over time while keeping the timing of predictors and target values visible.

## What Machine Learning Means Here

Machine learning means using data to learn a rule for making predictions.

In this project, the rule will use earlier country conditions to predict a later innovation outcome. For example, the model may use a country's earlier GDP per capita, R&D expenditure, renewable energy share, CO2 emissions, or environmental policy index to predict a future OECD environment-related patent measure.

This is not magic and it is not automatic truth. A model finds patterns in the data it is given. The project still needs human judgment to decide which variables make theoretical sense, whether the timing is defensible, and how the results should be interpreted.

## Supervised Learning

This project uses supervised learning.

Supervised learning means the model learns from examples where both the inputs and the answer are known.

For this project, one example could be:

- Inputs: Germany's country conditions in 2014.
- Known answer: Germany's environment-related innovation measure in 2015.

After seeing many examples like this, the model learns a prediction rule. The project can then ask the model to predict future innovation for country-years that were not used to train it.

## Features And Target

A feature is an input used by the model. A feature is also called a predictor.

In this project, possible features include:

- GDP per capita.
- R&D expenditure as a share of GDP.
- Researchers per million people.
- Renewable energy share.
- Fossil fuel energy share.
- CO2 emissions per capita.
- Environmental policy stringency.

The target is the value the model tries to predict.

In this project, the target will be a country-year measure of environment-related innovation. Candidate targets include OECD patent-based indicators such as environment-related patent shares or environment-related inventions per million people. The final target has not been selected yet.

## Training Data

Training data are the examples the model uses to learn.

For this project, training data may contain many country-year rows. Each row would usually describe one country in one year, with predictor values from an earlier year and a target innovation value from a later year.

For example:

- Predictors from 2014: R&D expenditure, GDP per capita, renewable energy share, and policy stringency.
- Target from 2015: environment-related innovation.

The model compares the predictors with the known target values and learns a rule that tries to make useful predictions.

## Validation And Test Data

Validation data are data used while developing the model. They help compare choices such as which predictors to include, which model family to use, or how much model tuning is needed. Tuning means choosing model settings, such as how flexible a model should be.

Test data are held back for final evaluation. The test data should be used as little as possible during model development, because repeatedly checking the test set can make the final result look better than it really is.

For this project, validation and test data should respect the time-oriented nature of the task. If the goal is to predict future innovation, evaluation should imitate that future-facing situation.

## Prediction

A prediction is the model's guess for the target value.

For example, the model might predict that a country will have an environment-related patent share of 8 percent in a future year. The observed value might later turn out to be 6 percent.

The difference between the observed value and the predicted value is the prediction error:

`error = observed value - predicted value`

If the observed value is 6 and the predicted value is 8, the error is -2. That means the model predicted too high by 2 units.

## Why Error Matters

Error tells us how far the model's predictions are from the observed values.

Small errors mean the predictions are close to the observed data. Large errors mean the model missed the target by more. A model can be wrong because it is too simple, because the data are noisy, because important predictors are missing, or because the relationship changes over time.

In this project, error should be interpreted in the unit of the chosen target. An error for a patent share is different from an error for patents per million people.

## Underfitting

Underfitting happens when a model is too simple to capture useful patterns.

Imagine a model that predicts almost the same environment-related innovation value for every country, regardless of R&D capacity, energy structure, or policy conditions. That model may be easy to explain, but it may miss important differences between countries.

Signs of underfitting can include:

- Poor predictions on training data.
- Poor predictions on validation or test data.
- Predictions that barely change when important country conditions change.

Underfitting is a problem because the model may not learn enough from the data to answer the research question.

## Overfitting

Overfitting happens when a model learns accidental patterns in the training data instead of patterns that generalize to new data.

For example, a very flexible model might learn details that are specific to a few countries or years in the training sample. It may look strong on the data it already saw, but perform poorly when predicting later years or different country-years.

Signs of overfitting can include:

- Very good predictions on training data.
- Much worse predictions on validation or test data.
- Results that depend heavily on small data changes.

Overfitting is risky in this project because the panel may have limited coverage for some variables, such as R&D indicators or environmental policy stringency. A complex model can find patterns that look impressive but are not stable.

## Why Random Row Splits Are Risky

A random row split means randomly putting some rows into training data and other rows into validation or test data.

This can be risky for time-oriented panel forecasting. The reason is timing.

If the project randomly splits country-year rows, the training data might include future years while the test data include earlier years. For example, the model might learn from Germany in 2020 and then be evaluated on Germany in 2015. That does not match the real prediction question, because 2020 information would not have been available in 2015.

Random row splits can also place nearly identical neighboring years for the same country in both training and test data. This can make performance look better than it would be when predicting genuinely future observations.

For this project, a time-respecting split is usually more appropriate. One possible approach is to train on earlier years and evaluate on later years. The final split strategy is still an open decision and should be recorded in the [decision log](../0_organization/decision_log.md).

## Practical Takeaway

The basic machine learning task is:

1. Build a clean country-year panel.
2. Use earlier predictor values.
3. Predict a future environment-related innovation target.
4. Compare predictions with observed values.
5. Check whether the model is useful, understandable, and free from obvious timing mistakes.

The model should not only produce a score. It should also help the project explain which country conditions are most associated with future environment-related innovation.
