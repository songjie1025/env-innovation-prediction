# Linear Model Run Summary

Best validation model: `elastic_net_alpha_1_l1_0.2`

## Chronological Split

- Train years: 1999-2018
- Validation years: 2019-2020
- Test years: 2021-2023

## Best Validation Metrics

| panel_id | panel_label | panel_role | comparison_group | feature_set_role | target_column | lag_suffix | model | split | train_year_start | train_year_end | validation_year_start | validation_year_end | n_train | n_validation | mae | rmse | oos_r2_vs_train_mean | spearman | comparison_scope | panel_rows | panel_countries | feature_columns | train_rows | validation_rows | train_countries | validation_countries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main | Main v2 model | main |  |  | env_patent_share_inventions | lag1_3_mean | elastic_net_alpha_1_l1_0.2 | validation | 1999 | 2018 | 2019 | 2020 | 2073 | 227 | 0.808687243765443 | 1.804720685185077 | 0.694370921341217 | 0.8580997379425421 | own_sample_not_direct_ranking | 2612 | 174 | 9 | 2073 | 227 | 171 | 130 |

## Final Test Metrics

| panel_id | panel_label | panel_role | comparison_group | feature_set_role | target_column | lag_suffix | model | split | n_train_validation | n_test | oos_r2_baseline_mean | mae | rmse | oos_r2_vs_train_mean | spearman | comparison_scope | panel_rows | panel_countries | feature_columns | train_validation_rows | test_rows | train_validation_countries | test_countries | train_year_start | train_year_end | validation_year_start | validation_year_end | test_year_start | test_year_end |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main | Main v2 model | main |  |  | env_patent_share_inventions | lag1_3_mean | elastic_net_alpha_1_l1_0.2 | test | 2300 | 312 | 0.9473702586495418 | 1.0384557278659492 | 2.416171730187962 | 0.6588600848860342 | 0.8382202193375337 | own_sample_not_direct_ranking | 2612 | 174 | 9 | 2300 | 312 | 174 | 128 | 1999 | 2018 | 2019 | 2020 | 2021 | 2023 |

The selected model is chosen by validation MAE. The final test block is the latest
contiguous period and is not used for model selection.

## Mechanism Submodel Comparison

Submodel scores are own-sample diagnostics because the model panels have different
country and year coverage. They should not be read as a direct ranking against the
main model unless a separate common country-year sample is constructed.

| panel_id | panel_label | best_model | rows | countries | test_year_start | test_year_end | test_mae | test_rmse | test_oos_r2_vs_train_mean | test_spearman | comparison_scope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main | Main v2 model | elastic_net_alpha_1_l1_0.2 | 2612 | 174 | 2021 | 2023 | 1.0384557278659492 | 2.416171730187962 | 0.6588600848860342 | 0.8382202193375337 | own_sample_not_direct_ranking |
| suba | Submodel A: RISE and high-tech exports | lasso_alpha_1 | 1031 | 128 | 2022 | 2023 | 1.7532451700734686 | 4.719537685962134 | 4.3893642070358396e-05 |  | own_sample_not_direct_ranking |
| subb | Submodel B: R&D, co-invention, and tax | lasso_alpha_1 | 2352 | 119 | 2021 | 2023 | 1.6164528055889615 | 3.9933256541709268 | 0.14719691036462446 | 0.6606854612823279 | own_sample_not_direct_ranking |
| subc | Submodel C: OECD EPS | lasso_alpha_1 | 1154 | 40 | 2018 | 2021 | 3.3949382314038994 | 5.298907662831587 | 0.005630696582187733 | 0.41838675005975734 | own_sample_not_direct_ranking |

## Same-Sample Nested Submodel Tests

Each nested comparison uses the same country-year rows for the main-controls
baseline and the main-plus-submodel augmented model. This is the preferred
incremental-value comparison for SubA, SubB, and SubC predictors.

| comparison_group | baseline_label | augmented_label | rows | countries | baseline_validation_mae | augmented_validation_mae | delta_validation_mae_augmented_minus_baseline | test_year_start | test_year_end | baseline_test_mae | augmented_test_mae | delta_test_mae_augmented_minus_baseline | improves_primary_test_mae | comparison_scope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| suba | Main controls on SUBA sample | Main controls plus SUBA predictors | 1012 | 124 | 0.9694655982121925 | 1.0004935864936766 | 0.03102798828148412 | 2022 | 2023 | 1.1741034757702178 | 1.188085626133415 | 0.013982150363197166 | False | same_sample_nested |
| subb | Main controls on SUBB sample | Main controls plus SUBB predictors | 2190 | 109 | 0.9723753166009826 | 0.9579392714270419 | -0.014436045173940704 | 2021 | 2023 | 1.1933115377528114 | 1.2499380148730832 | 0.0566264771202718 | False | same_sample_nested |
| subc | Main controls on SUBC sample | Main controls plus SUBC predictors | 918 | 40 | 1.7807289546856535 | 1.9603114366582637 | 0.17958248197261018 | 2019 | 2021 | 1.85178268213374 | 2.047999773940087 | 0.19621709180634705 | False | same_sample_nested |

In the current run, none of the submodel augmentations improves primary test MAE; positive delta values mean the augmented feature set is worse on the primary metric.

## Historical Target Baselines

These baselines use only target history available before the final test block. They
are required because country-level patent shares are persistent over time.

| model | prediction_rule | n_test | uses_test_labels | mae | rmse | oos_r2_vs_train_mean | spearman |
| --- | --- | --- | --- | --- | --- | --- | --- |
| country_last_pretest_holdconstant | country latest observed train+validation target held constant | 312 | False | 0.3118602401339744 | 1.5534402797740023 | 0.8589847558580282 | 0.9396713041005564 |
| country_train_validation_mean | country mean target through validation period, global fallback | 312 | False | 0.6794167908354009 | 3.313285418784909 | 0.3585029874515381 | 0.9410278131087497 |
| elastic_net_alpha_1_l1_0.2 | selected_linear_model | 312 | False | 1.0384557278659492 | 2.416171730187962 | 0.6588600848860342 | 0.8382202193375337 |
| global_train_validation_mean | constant mean of train+validation targets | 312 | False | 1.543124173267155 | 4.136773023191855 | -7.483574755440259e-07 |  |

## Historical Baseline Delta Summary

This table is the headline forecasting check. Positive delta MAE means the
feature-only model is worse than a prediction-safe historical target baseline.

| selected_model | baseline_model | selected_mae | baseline_mae | delta_mae_selected_minus_baseline | selected_beats_baseline | professor_interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| elastic_net_alpha_1_l1_0.2 | country_last_pretest_holdconstant | 1.0384557278659492 | 0.3118602401339744 | 0.7265954877319748 | False | The feature-only model trails this historical baseline on test MAE; do not claim that external predictors beat national historical persistence. |
| elastic_net_alpha_1_l1_0.2 | country_train_validation_mean | 1.0384557278659492 | 0.6794167908354009 | 0.35903893703054834 | False | The feature-only model trails this historical baseline on test MAE; do not claim that external predictors beat national historical persistence. |
| elastic_net_alpha_1_l1_0.2 | global_train_validation_mean | 1.0384557278659492 | 1.543124173267155 | -0.5046684454012058 | True | The feature-only model beats this historical baseline on test MAE; still interpret the result as predictive association, not causality. |

## Persistence-Augmented Model

The primary model remains feature-only so that the notebook can ask whether
economic, energy, policy, and science predictors forecast environmental
innovation beyond simple country persistence. The augmented comparison adds
`target_history_preblock`, a block-safe target-history feature: validation
years use only training-period target history, and test years use only
train+validation target history.

| model_stage | model | includes_main_predictors | includes_target_history | validation_mae | test_year_start | test_year_end | test_mae | test_rmse | test_oos_r2_vs_train_mean | test_spearman |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| history_only_baseline | country_last_pretest_holdconstant | False | True |  | 2021 | 2023 | 0.3118602401339744 | 1.5534402797740023 | 0.8589847558580282 | 0.9396713041005564 |
| persistence_augmented_linear | lasso_alpha_0.1 | True | True | 0.15205279661448934 | 2021 | 2023 | 0.3585630063734338 | 1.4422670876319315 | 0.878446260001838 | 0.9228090828332921 |
| feature_only_linear | elastic_net_alpha_1_l1_0.2 | True | False | 0.808687243765443 | 2021 | 2023 | 1.0384557278659492 | 2.416171730187962 | 0.6588600848860342 | 0.8382202193375337 |

## Missingness Pattern Diagnostics

The feature-level missingness plot and tables separate late-start coverage,
early-ending series, bounded coverage windows, intermittent gaps, and countries
with no observed value for a predictor among target-observed model rows. Internal
gaps take priority over bounded-window labels when both occur in a country-feature
sequence. This matters because train-fold median imputation is a conservative
baseline, but the interpretation differs when a source starts late versus when
isolated observations are missing inside an otherwise covered time series.

| feature | missing_share | complete_countries | late_start_countries | early_end_countries | bounded_coverage_window_countries | intermittent_gaps_countries | all_missing_countries |
| --- | --- | --- | --- | --- | --- | --- | --- |
| env_technology_rta_lag1_3_mean | 0.2572741194486983 | 47 | 27 | 1 | 17 | 15 | 67 |
| wgi_regulatory_quality_lag1_3_mean | 0.21094946401225115 | 48 | 122 | 0 | 0 | 0 | 4 |
| inflation_lag1_3_mean | 0.06623277182235834 | 148 | 11 | 3 | 2 | 0 | 10 |
| renewable_energy_share_lag1_3_mean | 0.03905053598774885 | 80 | 0 | 92 | 1 | 0 | 1 |
| fdi_net_inflows_lag1_3_mean | 0.027565084226646247 | 161 | 4 | 2 | 0 | 0 | 7 |
| scientific_journal_articles_lag1_3_mean | 0.021439509954058193 | 168 | 0 | 0 | 0 | 0 | 6 |
| trade_openness_lag1_3_mean | 0.018376722817764167 | 160 | 6 | 3 | 0 | 1 | 4 |
| co2_per_capita_ar5_lag1_3_mean | 0.01569678407350689 | 170 | 0 | 0 | 0 | 0 | 4 |
| gdp_constant_2015_usd_lag1_3_mean | 0.005742725880551302 | 170 | 2 | 1 | 0 | 0 | 1 |

## Missingness Sensitivity

The primary panel preserves missing predictors and imputes inside the sklearn
pipeline. The complete-case rerun drops rows with any missing active predictor,
and the missingness-indicator rerun keeps all rows while adding one binary
indicator per active predictor. Both reuse the primary train/validation/test
years so that the final test block remains comparable.

| analysis | best_model | rows | countries | test_rows | test_mae | test_rmse | test_oos_r2_vs_train_mean | test_spearman |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary_median_imputed_all_rows | elastic_net_alpha_1_l1_0.2 | 2612 | 174 | 312 | 1.0384557278659492 | 2.416171730187962 | 0.6588600848860342 | 0.8382202193375337 |
| complete_case_refit | elastic_net_alpha_1_l1_0.2 | 1391 | 99 | 162 | 1.2310625996058013 | 2.6806327403398478 | 0.645879722585992 | 0.809693137949459 |
| missingness_indicator_refit | elastic_net_alpha_1_l1_0.2 | 2612 | 174 | 312 | 1.0384557278659492 | 2.416171730187962 | 0.6588600848860342 | 0.8382202193375337 |

## Error Decomposition

These summaries show whether aggregate MAE hides concentrated errors in recent
years or high-target country-years.

By test year:

| year | n_test | mae | rmse | mean_error | median_absolute_error |
| --- | --- | --- | --- | --- | --- |
| 2021.0 | 108.0 | 0.9217641468706184 | 2.093689996879438 | -0.27292965754134046 | 0.4102990844053028 |
| 2022.0 | 105.0 | 1.0565416045070313 | 2.4672326189914746 | -0.31848869629455273 | 0.44022746538230034 |
| 2023.0 | 99.0 | 1.146573644029405 | 2.6758146735564177 | -0.352739900088792 | 0.49017218056058526 |

By target quantile:

| target_quantile | n_test | target_min | target_max | mae | rmse | mean_error | median_absolute_error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Q1 | 78 | 0.0004312389 | 0.002321532 | 0.30793852483495876 | 0.3456936126353483 | -0.30793852483495876 | 0.273457482137851 |
| Q2 | 78 | 0.002335878 | 0.0166027 | 0.47643439398603876 | 0.536303145185482 | -0.47643439398603876 | 0.3899732934835791 |
| Q3 | 78 | 0.01666989 | 0.132606 | 0.6772787819019798 | 0.7786483378218875 | -0.674585361254688 | 0.6321421407304709 |
| Q4 | 78 | 0.1397933 | 38.42308 | 2.69217121074082 | 4.726322560690547 | 0.20461255912461873 | 1.2540199813269597 |

## Confirmatory Rolling-Origin Check

The rolling-origin table distributes held-out blocks through time. It is stronger
confirmatory evidence than the first contiguous 80/10/10 checkpoint, while still
keeping validation inside each pre-test window.

| fold_id | train_year_start | train_year_end | validation_year_start | validation_year_end | test_year_start | test_year_end | best_model | validation_mae | test_mae | best_historical_baseline_model | best_historical_baseline_mae | delta_mae_selected_minus_best_history | beats_best_historical_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fold_1 | 1999 | 2004 | 2005 | 2006 | 2007 | 2009 | elastic_net_alpha_1_l1_0.2 | 0.8687548064028592 | 0.8684120224430975 | country_last_pretest_holdconstant | 0.1615757874998649 | 0.7068362349432326 | False |
| fold_2 | 1999 | 2007 | 2008 | 2009 | 2010 | 2012 | lasso_alpha_1 | 0.8306973036416595 | 0.8378504967903542 | country_last_pretest_holdconstant | 0.11526634161753471 | 0.7225841551728195 | False |
| fold_3 | 1999 | 2010 | 2011 | 2012 | 2013 | 2015 | lasso_alpha_0.1 | 0.8076654303999811 | 0.79705431722539 | country_last_pretest_holdconstant | 0.0977900958167991 | 0.6992642214085909 | False |
| fold_4 | 1999 | 2013 | 2014 | 2015 | 2016 | 2018 | lasso_alpha_0.1 | 0.8065415729710351 | 0.8370811229163816 | country_last_pretest_holdconstant | 0.10812322730721044 | 0.7289578956091711 | False |
| fold_5 | 1999 | 2016 | 2017 | 2018 | 2019 | 2021 | lasso_alpha_1 | 0.792678638740378 | 0.8740750922720856 | country_last_pretest_holdconstant | 0.19112934456372727 | 0.6829457477083583 | False |
| fold_6 | 1999 | 2019 | 2020 | 2021 | 2022 | 2023 | elastic_net_alpha_1_l1_0.2 | 0.8875164817584238 | 1.092190155101847 | country_last_pretest_holdconstant | 0.23600637276519607 | 0.8561837823366508 | False |

## Linear Robustness Pack

These robustness experiments are a limited, protocol-defined sensitivity package,
not a test-set model search. Each setting uses the same chronological 80/10/10
split rule and chooses among OLS, Ridge, Lasso, and ElasticNet candidates by
validation MAE before scoring the final test block. The lag1 rows are
common-sample timing sensitivities because they reuse the same generated panels
and swap only the selected lag feature columns.

The regularization grid is finite rather than exhaustive: Ridge alpha in
[0.1, 1, 10], Lasso alpha in [0.001, 0.01, 0.1, 1], and ElasticNet alpha in
[0.001, 0.01, 0.1, 1] with l1_ratio in [0.2, 0.5, 0.8]. Predictors are
standardized inside each pipeline, but the target is not standardized; therefore
regularization strength is target-scale dependent.

| robustness_id | target_column | lag_suffix | best_model | rows | countries | test_year_start | test_year_end | validation_mae | test_mae | best_historical_baseline_model | best_historical_baseline_mae | delta_test_mae_selected_minus_best_history | beats_best_historical_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| robust_main_share_lag1 | env_patent_share_inventions | lag1 | elastic_net_alpha_1_l1_0.2 | 2612 | 174 | 2021 | 2023 | 0.7952943627130686 | 1.0262450041607407 | country_last_pretest_holdconstant | 0.3118602401339744 | 0.7143847640267663 | False |
| robust_main_share_lag1_3_mean | env_patent_share_inventions | lag1_3_mean | elastic_net_alpha_1_l1_0.2 | 2612 | 174 | 2021 | 2023 | 0.808687243765443 | 1.0384557278659492 | country_last_pretest_holdconstant | 0.3118602401339744 | 0.7265954877319748 | False |
| robust_main_share_skew_transformed_lag1_3_mean | env_patent_share_inventions | lag1_3_mean | lasso_alpha_1 | 2612 | 174 | 2021 | 2023 | 1.381818539524929 | 1.5410014724338992 | country_last_pretest_holdconstant | 0.3118602401339744 | 1.229141232299925 | False |
| robust_main_per_million_lag1 | env_patents_per_million | lag1 | elastic_net_alpha_1_l1_0.8 | 2604 | 169 | 2021 | 2023 | 8.076238084600247 | 7.541364936594562 | country_train_validation_mean | 2.572789706625659 | 4.968575229968902 | False |
| robust_main_per_million_lag1_3_mean | env_patents_per_million | lag1_3_mean | elastic_net_alpha_1_l1_0.8 | 2604 | 169 | 2021 | 2023 | 8.155529632348745 | 7.70948162734486 | country_train_validation_mean | 2.572789706625659 | 5.136691920719201 | False |

The MAE scale differs across target variables, so target-robustness rows should be
read against their own historical baselines rather than as direct cross-target
rankings.

## Main-Model Correlation Diagnostics

Correlation diagnostics use train+validation rows only: 1999-2020, n=2300.
Correlation design: imputed_scaled_train_validation_design.
They are diagnostic checks for collinearity and coefficient interpretation, not a
post-test feature-selection rule.
