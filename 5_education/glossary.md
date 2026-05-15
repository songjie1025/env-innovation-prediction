# Glossary

This glossary defines technical terms that appear in the project. The examples refer to the environment-related innovation prediction task.

## Country-Year Panel

A dataset where each row represents one country in one year. For example, Germany in 2010 and Germany in 2011 are two different rows.

## Target Variable

The outcome the model tries to predict. In this project, the target will be a country-year measure of future environment-related innovation, such as an OECD patent-based indicator.

## Predictor Or Feature

An input variable used to make a prediction. Examples include GDP per capita, R&D expenditure as a share of GDP, renewable energy share, or an environmental policy index.

## Lag

A lag uses an earlier value of a variable. If we use GDP per capita from 2010 to predict innovation in 2011, GDP per capita is lagged by one year.

## Time Leakage

Time leakage happens when information from the future accidentally enters the model. For example, using a 2015 policy value to predict 2014 innovation would make the evaluation misleading.

## Missing Value

A missing value is an empty or unavailable data point. For example, one country may have R&D expenditure data for 2010 but not for 2011.

## Imputation

Imputation means filling in missing values using a rule or model. Simple imputation might use a country average; more complex imputation should be documented carefully because it can affect results.

## Transformation

A transformation changes the scale or form of a variable. For example, taking the logarithm of GDP per capita can make very large income differences easier for a model to handle.

## Baseline Model

A simple reference model used for comparison. A model is more useful if it performs better than a naive baseline and still helps answer the research question.

## Overfitting

Overfitting happens when a model learns noise or accidental patterns in the training data instead of a relationship that generalizes to new data.

## Validation Set

A validation set is data used during model development to compare choices such as model family, predictors, or tuning settings.

## Test Set

A test set is data held back for final evaluation. It should be used as little as possible during model development.

## RMSE

Root mean squared error is an error metric that gives larger mistakes extra weight. It is useful when large prediction errors are especially undesirable.

## MAE

Mean absolute error is the average size of prediction errors, ignoring whether the prediction was too high or too low. It is often easy to explain.

## R-Squared

R-squared describes how much variation in the target is captured by the model's predictions. For prediction, out-of-sample R-squared is more useful than a score computed only on training data. It is not causal explanation, and test-set R-squared can be low or even negative.

## Interpretability

Interpretability means being able to explain what the model learned in a way that supports the research question. This project needs both prediction and substantive explanation.

## Coefficient

A coefficient is a number in a linear model that describes how the prediction changes when a predictor increases, holding other predictors constant. A coefficient is not automatically causal evidence.

## Permutation Importance

Permutation importance measures how much model performance gets worse when one predictor is randomly shuffled. If shuffling a variable hurts performance a lot, the model relied on that variable.

## SHAP

SHAP is a method for attributing parts of a model prediction to predictors relative to a baseline prediction. It can be useful for complex models, but it adds interpretation complexity and does not show causal effects.

## Partial Dependence

Partial dependence shows how the model prediction changes as one predictor changes while averaging over other predictors. It helps show nonlinear relationships in models such as trees or boosting.

## Tuning

Tuning means choosing model settings. For example, a flexible model may need settings that control how complex it is allowed to become.
