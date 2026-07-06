# Decision Log

This file records important project decisions so that the research direction stays traceable.

Decision entries should be short. Each entry should explain what was decided, why it was decided, and which alternatives were considered.

## Format

```text
### YYYY-MM-DD: Short decision title
Decision:
Reason:
Alternatives considered:
Status:
```

Status options:

1. `Active`: currently guiding the project.
2. `Revised`: replaced by a later decision.
3. `Deferred`: discussed but not decided yet.

## Decisions

### 2026-07-03: Merge GDP and scientific output into a single size/capacity component

Decision:
Replace the two collinear main predictors `gdp_constant_2015_usd` and `scientific_journal_articles` with a single `size_factor` predictor, defined as the first principal component of the two standardized series. Implemented in `3_models/scripts/model_data.py:add_size_factor_columns`, applied inside `load_model_panel` so every panel that carries both source columns (main and per-million) is merged consistently, while submodel panels are unchanged. The PCA is fit on standardized complete-case rows and rows missing either source keep `NaN` for the pipeline's per-fold median imputer; the sign is oriented to increase with GDP so the axis reads as "national economic scale and research capacity". `SKEW_TRANSFORM_METHODS` was updated to drop the removed columns. The full linear and tree pipelines, `statistical_screening`, and the notebooks were re-run.

Reason:
GDP and scientific output are the only severe multicollinearity in the project: pairwise Spearman r = 0.97 and VIF ≈ 14 and ≈ 13 in the main panel, while all other main predictors have VIF < 2.5 (near-zero-variance screening flags none). The selected ElasticNet (alpha=1, l1_ratio=0.2, Ridge-heavy) does not remove this; it splits the shared signal across both large coefficients (GDP 0.97, scientific output 0.82) and masks other predictors, most visibly FDI (target Spearman 0.70 but coefficient only 0.09). A single-fit coefficient cannot reveal the collinearity; only perturbation does (the l1_ratio coefficient path see-saw, a +0.83 bootstrap co-movement between the two coefficients, and coefficient jumps when other blocks are added). A merge trial run shows the intended effect: VIF collapses from ~14 to 2.60 for the merged axis, the masked coefficients revive (FDI 0.09 to 0.285, CO2 0.084 to 0.120, WGI 0.083 to 0.100), and the merged axis carries the size/capacity signal (coefficient +1.29), at a negligible predictive cost (linear test MAE 1.055 to 1.082; Random Forest test MAE 0.568 to 0.618, still far from the 0.312 persistence baseline). The merge serves the project's interpretation goal (which predictors are most associated with future innovation) by producing stable, separately readable coefficients without a target-based or post-test deletion.

Implementation results (verified re-run, 2026-07-03):
Statistical screening now shows no severe collinearity: `size_factor` VIF = 2.60 and every other main predictor VIF < 2.5 (previously GDP 14.0 and scientific output 13.4). The substantive conclusions are unchanged: no linear or tree specification beats the country-persistence baseline (0.312 test MAE). Two changes are worth recording. First, validation-MAE selection for the linear main model now picks `lasso_alpha_1`, which keeps only `size_factor` (standardized coefficient 1.82) and shrinks the other seven predictors to zero; the earlier "masked predictors revive" effect (e.g., FDI) is visible in a Ridge-heavy candidate but not in the sparse validation-selected model, so the interpretation section should read the coefficient path / correlation diagnostics rather than the selected sparse fit alone. Second, the tree multi-seed nested check flipped for Submodel B: with the merged size axis, SubB (R&D, co-invention, tax) no longer helps (0/25 seeds improve, mean delta +0.026), where the pre-merge run had reported a robust improvement. All three submodels now have positive mean nested deltas, so the merged specification yields a cleaner uniform null (no external block helps beyond the size axis) and supersedes the "SubB robustly helps trees" part of the 2026-06-29 decision. Permutation importance ranks `size_factor` first (0.88).

Alternatives considered:
Dropping GDP and keeping scientific output was considered because scientific output has the higher target correlation (0.86 vs 0.82) and the higher linear permutation importance (0.35 vs 0.28) and is more directly tied to the knowledge-production-function literature; it was not chosen as the primary option because Random Forest values GDP more (dropping GDP worsens RF test MAE to 0.657 while dropping scientific output improves it to 0.529), so a single named-variable pick is arbitrary across model families. Dropping scientific output and keeping GDP was rejected for the same asymmetry. Raising l1_ratio to force sparsity was rejected because it makes an unstable and here incorrect choice (pure Lasso keeps GDP and zeroes the stronger scientific-output predictor) and collaterally zeroes FDI/CO2/WGI before resolving the pair, with no predictive gain. Keeping both predictors unchanged was rejected because it leaves the coefficients uninterpretable for the interpretation deliverable. Keeping the merge as a named variable rather than a component was rejected because no single name captures both economic scale and research capacity.

Status:
Active

### 2026-07-01: Add Phase-3 statistical screening as a data-side diagnostic layer

Decision:
Add an explicit Phase-3 statistical screening step — near-zero variance, predictor-predictor correlation, and variance inflation factor (VIF) — as a data-side diagnostic. The new computations (VIF, near-zero variance) live in `2_data/scripts/statistical_screening.py`; the correlation matrix, top correlated pairs, and predictor-target correlations are reused from the existing leakage-safe train+validation diagnostics produced by `run_modeling.py` rather than recomputed. A visualization-only notebook `2_data/notebooks/statistical_screening.ipynb` calls the script and displays the results. The predictor set is unchanged at 18 (main 9, SubA 3, SubB 5, SubC 1). (Update: the 2026-07-03 merge of GDP and scientific output into `size_factor` reduces this to 17 model features — main 8, SubA 3, SubB 5, SubC 1 — while still spanning the same 18 underlying raw variables.)

Reason:
The pipeline previously moved from EDA (Phase 2) directly to embedded model selection (ElasticNet, Phase 4) without a documented statistical screening step. Screening is run as a diagnostic, not a hard filter: the variance and collinearity checks use no target (no leakage) and are not used to delete predictors after seeing model results. Recorded findings: no near-zero-variance predictors; only GDP (VIF 14.0) and scientific output (VIF 13.4) exceed the VIF=10 threshold and jointly proxy economic size and research capacity (Spearman r 0.88), while all other predictors are below VIF 2.5 and SubA/B/C are below 3.5. The decision is to keep all predictors and handle the GDP/scientific collinearity through the model layer (ElasticNet L2 grouping and permutation importance), so no models are re-run. Funnel effect: 35 to 22 (P1) to 18 (P2) to 18 (P3 diagnostic, no removal) to P4 embedded selection.

Alternatives considered:
Dropping one of GDP or scientific output to satisfy VIF below 10 was rejected because it discards jointly-informative signal and both represent the same substantive dimension, and permutation importance shows scientific output is the strongest predictor. Using univariate predictor-target correlation to prune predictors was rejected because weak-alone predictors can be jointly useful and target-based screening risks leakage. Moving the correlation computation out of the tested modeling pipeline into the screening module was rejected as unnecessary and high-risk; the screening module reuses those outputs instead.

Status:
Active

### 2026-06-29: Extend tree baselines to submodels and add multi-seed and permutation robustness

Decision:
Add Random Forest and XGBoost tree baselines and extend them beyond the main panel to the same-sample nested submodel comparison (SubA, SubB, SubC), the per-million robustness target, and the lag1 (t-1) timing variant, reusing the linear protocol (chronological 80/10/10 split, validation-MAE selection, prediction-safe historical baselines). Add two robustness checks in `3_models/scripts/tree_robustness_checks.py`: a fixed-RandomForest multi-seed nested check (25 seeds) that isolates the feature effect from model-selection noise, and permutation importance on the test block. Prior tree-model defects were fixed first (broken SHAP figure, mislabeled run-summary heading, `selected_linear_model` baseline label, redundant scaler in the tree pipeline).

Reason:
The linear nested comparison found no submodel improvement, but linear models cannot capture the nonlinear and interaction effects that the literature attributes to policy stringency and R&D, whereas trees can. The multi-seed check was necessary because the initial model-selected nested deltas were small and the validation window is only two years, so a lucky seed or a switched model family could manufacture a false improvement; permutation importance was necessary because impurity importance over-credits high-variance continuous predictors such as GDP. Recorded findings: on identical nested rows submodel predictors do not help the linear model (all deltas positive) but do help trees (all deltas negative); after holding the model fixed and varying the seed, only SubB (R&D, co-invention, tax) is robust (100% of seeds improve, mean delta -0.024), SubA (RISE, high-tech exports) is marginal (80% of seeds, mean -0.005) and its earlier larger improvement was inflated by model selection, and SubC (EPS) does not help. No tree specification beats the national persistence baseline, and the per-million target and t-1 timing confirm the same conclusion. Permutation importance ranks scientific output first and GDP second, reconciling the tree with the linear coefficients and correcting the impurity artifact.

Alternatives considered:
Reporting the model-selected nested deltas as the finding was rejected because they conflated feature value with model-selection noise. Dropping GDP or scientific output to reduce their correlation was rejected because both jointly proxy economic size and research capacity and permutation importance shows scientific output is the strongest predictor. Running trees only on the main panel was rejected because the nonlinear submodel check is the main scientific contribution of the tree extension. Treating the small SubA improvement as a confirmed result was rejected in favor of reporting only the seed-robust SubB finding.

Status:
Revised. The tree, multi-seed, and permutation-importance methodology introduced here remains active, but the substantive "SubB robustly helps trees" finding is superseded by the 2026-07-03 size_factor merge: after merging the collinear GDP and scientific-output predictors, the 25-seed nested check shows SubB no longer helps (0/25 seeds improve, mean delta +0.026), so all three submodels now yield a uniform null. Read the 2026-07-03 entry for the current tree-nested conclusion.

### 2026-06-25: Present the linear notebook as a first checkpoint with confirmatory diagnostics

Decision:
Keep the linear modeling notebook as a professor-style educational first checkpoint, but add script-generated confirmatory diagnostics before using it for report claims. The notebook now centers historical-baseline delta summaries, year-level and target-quantile error decomposition, missingness-indicator sensitivity, and a rolling-origin check with validation inside each pre-test window. The notebook remains a narrative runner and artifact viewer; model fitting, evaluation, and artifact verification stay in `3_models/scripts/`.

Reason:
The teacher-confirmed chronological 80/10/10 split is appropriate for the first runnable course checkpoint, but a single latest-period holdout is not enough for strong temporal-stability claims. The current feature-only linear model also does not beat the strongest prediction-safe country-history baseline, so final reporting must foreground historical inertia and avoid overclaiming external-predictor forecasting superiority. Moving artifact verification into a reusable script helper keeps the notebook educational while preserving reproducibility.

Alternatives considered:
Treating the 80/10/10 result as final forecasting evidence was rejected because it would over-read one late holdout. Replacing the notebook with a code-heavy analysis notebook was rejected because the project standard is scripts for logic and notebooks for explanation. Dropping test-set diagnostics was rejected because historical-baseline deltas, error concentration, and missingness sensitivity are necessary for reviewer-defensible interpretation.

Status:
Active

### 2026-06-25: Test skew-transformed predictors before moving to nonlinear models

Decision:
Add a skew-transformed linear robustness setting before introducing nonlinear model families. The setting keeps the same main target, same v2 no-imputation main panel, same `lag1_3_mean` timing, same chronological 80/10/10 split, and same validation-MAE selection rule. It transforms highly right-skewed positive predictors with `log1p`, signed skewed predictors with `asinh`, keeps bounded or near-symmetric predictors on their original scale, then applies the existing train-fold median imputation and StandardScaler pipeline.

Reason:
Standard scaling makes predictors comparable in units but does not remove skewness or long-tailed leverage. Testing deterministic log/asinh transformations is a defensible intermediate step: it checks whether the weak feature-only linear performance is mainly a scale-shape problem before adding nonlinear models. The check uses no target labels and does not fit transformation parameters on validation or test rows.

Alternatives considered:
Replacing the primary feature-only model with transformed predictors was rejected because the primary specification should remain pre-specified and interpretable. Jumping directly to Random Forest or boosting was deferred because the linear model should first be tested under a simple skew-reduction sensitivity. Searching many transformations per variable was rejected because it would increase researcher degrees of freedom and risk post-test tuning.

Status:
Active

### 2026-06-25: Keep target history outside the primary feature-only model

Decision:
Keep the primary linear model as a feature-only model using the pre-specified external predictors, and add past target information only as a separate persistence-augmented comparison model. The augmented comparison uses `target_history_preblock`, a block-safe target-history feature: validation rows use the latest training-period target observed for the same country, and test rows use the latest train+validation-period target observed for the same country. The feature must not use labels from inside the validation block to predict validation rows or labels from inside the test block to predict test rows.

Reason:
Country-level environmental patent shares are highly persistent. Adding past target values directly into the primary model would change the research question and could hide whether the external predictors provide useful signal on their own. A separate persistence-augmented comparison makes the historical-inertia issue explicit, keeps the feature-only baseline interpretable, and tests whether the same linear model family gains predictive accuracy after adding prediction-safe target history.

Alternatives considered:
Silently adding lagged target history to the primary model was rejected because it would blur feature-based interpretation with persistence forecasting. Ignoring target history was rejected because historical baselines already show that national inertia is the strongest benchmark. A rolling one-step target-lag design was considered but deferred because it belongs to a later backtesting stage, not the teacher-confirmed first contiguous 80/10/10 baseline.

Status:
Active

### 2026-06-22: Add predictor missingness pattern diagnostics to the model notebook

Decision:
Add formal predictor missingness pattern diagnostics to the model-stage script pipeline and educational notebook. For each active main-model predictor, classify each country-feature series among target-observed rows in the no-imputation model panel as `complete`, `late_start`, `early_end`, `bounded_coverage_window`, `intermittent_gaps`, or `all_missing`. Write both a feature-level summary and a country-feature detail table, and add a stacked country-count figure to the modeling figure index.

Reason:
Overall missing-share diagnostics are not enough for a panel time-series setting. Missing values caused by a source beginning late, a source ending early, intermittent country-year gaps, or all-missing country histories imply different interpretation risks and different future robustness options. Keeping this as a diagnostic preserves the current baseline while making train-fold median imputation easier to defend and qualify.

Alternatives considered:
Changing the primary model to full-series linear interpolation was rejected because it is not prediction-safe. Treating the diagnostic as a post-test feature-deletion rule was rejected because it would increase researcher degrees of freedom after seeing model results. Replacing the primary model with complete-case estimation was rejected because it changes sample size, country coverage, and test composition; complete-case remains a sensitivity check.

Status:
Active

### 2026-06-18: Add a limited linear robustness pack

Decision:
Extend the model-stage pipeline with a limited linear robustness pack before considering optional advanced models. The robustness pack uses the same chronological 80/10/10 split and validation-MAE selection rule as the primary model. It runs four main-panel sensitivity settings: `env_patent_share_inventions` with `lag1_3_mean`, `env_patent_share_inventions` with common-sample `lag1`, `env_patents_per_million` with `lag1_3_mean`, and `env_patents_per_million` with common-sample `lag1`. The linear candidate family now includes ordinary least squares, Ridge, Lasso, and ElasticNet. All candidate scores are reported on validation; each setting reports only the validation-selected model on the final test block and compares it with prediction-safe historical target baselines.

Reason:
The model stage is exploratory, but it should remain academically disciplined. Lag-1 timing and the alternative patent-intensity target were already planned robustness dimensions, and adding Lasso completes the standard sparse-linear model family without moving into non-linear model search. Reporting each selected linear model against its own strongest historical baseline prevents overclaiming.

Alternatives considered:
Immediately adding Random Forest or gradient boosting was rejected for this stage because the current priority is to establish whether the interpretable linear conclusions are robust. Searching many lag windows, targets, or model families was rejected because it would look like post-test model fishing. Dropping historical baselines from robustness reporting was rejected because country-level environmental patent outcomes are persistent and target-history baselines are necessary for a defensible forecasting claim.

Status:
Active

### 2026-06-18: Add reviewer-driven baselines, failure modes, and missingness sensitivity

Decision:
After cross-review of the model-stage checkpoint, add prediction-safe historical target baselines, top absolute test-error diagnostics, and a complete-case missingness sensitivity run to the linear modeling notebook and script pipeline. The historical baseline table must include the selected ElasticNet model, the global train+validation target mean, the country train+validation target mean, and the country last-pretest target value held constant across the final test block. The notebook must state that the current ElasticNet model does not beat the strongest country persistence baseline on primary test MAE, and that none of the same-sample submodel augmentations improves primary test MAE in the current run.

Reason:
The first linear model has positive out-of-sample R-squared against a global training-period mean, but this is too weak for a panel forecasting claim because country-level environmental patent shares are persistent. A rigorous notebook needs to show whether feature-based models improve beyond target-history baselines, where the model fails, and whether heavy predictor missingness affects the result. Correlation diagnostics should be interpreted on the fitted imputed/scaled design matrix when possible, and coefficients shrunk to zero should not be treated as sign-aligned.

Alternatives considered:
Keeping only the ElasticNet-versus-linear-candidate validation table was rejected because it does not answer whether the model beats national historical inertia. Reporting only aggregate test metrics was rejected because large misses for high-innovation country-years materially affect interpretation. Treating the complete-case run as a replacement main result was rejected because it changes sample size, countries, and test coverage; it is a sensitivity check. Adding rolling-origin validation and bootstrap uncertainty was deferred to the next robustness stage because the immediate notebook fix focuses on reviewer-critical diagnostics that can be generated by the current pipeline.

Status:
Active

### 2026-06-18: Add mechanism submodel comparisons and train-period correlation diagnostics

Decision:
Extend the first linear modeling checkpoint with mechanism submodel comparisons for the active v2 no-imputation Submodel A, Submodel B, and Submodel C panels. Each panel uses the same chronological 80/10/10 split rule, the same `*_lag1_3_mean` feature timing, the same linear candidate set, and validation MAE for model selection. Treat pure submodel results as own-sample diagnostics, not as a direct ranking against the main model, because the panels have different country coverage, target years, and test windows. For the comparable submodel test, run same-sample nested pairs: main predictors only on the submodel sample versus main predictors plus the submodel predictors on exactly the same country-year rows. Add main-model train+validation correlation diagnostics to explain ElasticNet coefficient interpretation under collinearity while keeping the held-out test labels unused for diagnostics.

Reason:
The course requirement asks for interpretable prediction and identification of predictors most strongly associated with future environment-related innovation. The main model remains the broad primary specification, while the submodels test narrower policy, R&D, collaboration, and sustainable-energy regulation mechanisms already built during the panel-cleaning stage. Same-sample nested pairs are needed because submodel-only panels are not comparable to the main model unless the main predictors are also present in the submodel sample. Correlation diagnostics are needed because the selected ElasticNet baseline is designed for correlated predictors, and coefficient interpretation should explicitly show where predictors overlap.

Alternatives considered:
Replacing the main model with the best-scoring pure submodel was rejected because submodel samples are not directly comparable. Reporting only pure submodel scores was rejected because it does not show whether submodel predictors add information beyond the main predictors. A single four-panel common test sample was considered but deferred because the current SubA and SubC test periods do not share a complete common final test window, and forcing a common sample would make the first modeling checkpoint less representative. Using correlations for post-test feature deletion was rejected because the diagnostics should explain the current model, not change the pre-specified v2 feature set after seeing test performance.

Status:
Active

### 2026-06-17: Use a simple chronological 80/10/10 split for the first modeling stage

Decision:
After consulting the teacher, use the simplest traditional time split for the initial modeling stage: the earliest 80% of distinct target years form the training period, the next 10% form the validation period, and the latest 10% form the held-out test period. The test set stays at the end of the timeline, and the first runnable pipeline should focus on interpretable linear models before adding more complex model families.

Reason:
The teacher confirmed that a simple train/validation/test design is sufficient and easier to explain for the course project at this stage. A contiguous chronological split preserves temporal ordering, avoids random row-level leakage, keeps the latest years as a final stress test, and gives the project a reproducible baseline that can be extended later.

Alternatives considered:
Rolling-origin outer folds were considered in the earlier modeling-stage plan, but they add complexity before the first linear baseline is running. Random row-level splits were rejected because they can leak future panel information into earlier predictions. Interleaved or shuffled validation/test blocks were rejected because the teacher advised using one simple continuous time sequence.

Status:
Active

### 2026-06-13: Generate robustness target panels for patent intensity

Decision:
Keep `env_patent_share_inventions` (`PT_INV.DEV.ENV_PAT._Z`) as the main target, and generate parallel robustness target panels for `env_patents_per_million` (`INV_PS.DEV.ENV_PAT._Z`). The robustness panels reuse the active v2 predictor specification, lag definitions, target-observed row filtering, and no-imputation versus retrospective linear-interpolation variants. Write them under `2_data/processed/model_panels/robustness/env_patents_per_million/v2/`.

Reason:
The main target measures each country or aggregate area's percentage contribution to worldwide environment-related inventions in the OECD patent-indicator series. `env_patents_per_million` is a size-normalized patent-intensity outcome, so it tests whether later model results are specific to a global-share measure or also hold for patent intensity. Keeping the robustness target in a separate package preserves the main v2 deliverable while making the modeling stage able to loop over outcomes with the same feature design.

Alternatives considered:
Replacing the main target was rejected because the active target decision still favors `PT_INV.DEV.ENV_PAT._Z`. Using `PT_TECH.DEV.ENV_PAT._Z` as the second target was rejected because the percentage-of-technologies measure has interpretation risk and values above 100. Duplicating the whole panel-cleaning script was rejected in favor of parameterizing the target variable.

Status:
Active

### 2026-06-13: Move weak main predictors to robustness and create model-panel v2

Decision:
Create an active `v2` model-panel package under `2_data/processed/model_panels/v2/`. The v2 main model removes `fossil_energy_share` and `tertiary_enrollment` from the active main predictor set and keeps them available for robustness or exploratory analysis through the original v1 package. The v2 main model keeps the 1996-2022 raw predictor window and automatically reselects the main anchor from retained predictors. Record the reassessment in `model_panel_predictor_reassessment.csv`.

Reason:
The reassessment combines literature defensibility and panel usability before modeling. The strongest energy-innovation evidence concerns energy prices, fuel prices, carbon prices, and policy incentives rather than fossil-consumption share itself; `fossil_energy_share` is a sign-ambiguous proxy for both transition pressure and lock-in, and it creates the largest complete-case loss after source-quality corrections. `tertiary_enrollment` is a broad human-capital proxy, while the more direct innovation-capacity literature emphasizes R&D expenditure, researchers, knowledge stocks, scientific output, and university quality; it also materially reduces complete-case coverage. In the current no-imputation main panel, v2 changes the anchor from `fossil_energy_share` to `trade_openness`, expands anchor countries from 141 to 191, and raises target-plus-complete-feature rows from 944 to 1,832 for `lag1` and from 670 to 1,391 for `lag1_3_mean`.

Alternatives considered:
Keeping both variables in the active main model was rejected because it would make the main specification harder to defend while substantially reducing complete-case diagnostics. Dropping the variables entirely was rejected because they remain useful for robustness, sensitivity, or exploratory comparisons. Keeping `fossil_energy_share` as the v2 anchor was rejected because a removed predictor should not define the active main country pool. Describing the change only as a missingness-driven deletion was rejected because the decision depends on both theory and data coverage.

Status:
Active

### 2026-06-12: Mark invalid fossil-energy source values as missing and serialize panel missingness as NaN

Decision:
Before lag construction, convert invalid `fossil_energy_share` source values to missing: negative values and country-level exact zeros in World Bank WDI `EG.USE.COMM.FO.ZS`. Write generated model-panel CSV missing values as the literal string `NaN` instead of blank cells. Record affected source values in `2_data/processed/model_panels/model_panel_quality_summary.csv`.

Reason:
The World Bank API and CSV download report exact zeros for country-level `EG.USE.COMM.FO.ZS`, including countries where zero fossil-fuel energy consumption is not substantively credible. The indicator is a percentage-style fossil-energy share, so negative values are also invalid. Treating these values as missing is more defensible than modeling them as observed zeros. Serializing missing values as `NaN` makes missingness visible in the delivered CSVs while preserving true missing values when read by pandas or downstream modeling code.

Alternatives considered:
Keeping the zeros as observed values was rejected because it would encode a source-data artifact as real fossil-energy structure. Dropping all rows affected by missing fossil predictors was rejected because predictor missingness should be handled later by missing-aware models or train-only imputation. Replacing missing values with numeric sentinels such as `0` or `-999` was rejected because those values could be misread as data.

Status:
Active

### 2026-06-12: Drop missing-target rows from generated model panels

Decision:
Generated model-panel CSVs keep only rows where the main target `env_patent_share_inventions` is observed. Predictor missing values remain as missing values and should be handled later by missing-aware models or train-only imputation inside the modeling pipeline. Coverage summaries keep `anchor_countries`, `anchor_year_grid_rows`, and `target_missing_rows_dropped` so the pre-filter country-year grid remains auditable.

Reason:
Rows without the target cannot train or evaluate a supervised prediction model. Dropping target-missing rows at the panel stage makes the displayed panel match the intended supervised-learning sample base while avoiding unnecessary complete-case deletion caused by missing predictors.

Alternatives considered:
Keeping target-missing rows in the panel was rejected because it made the deliverable look larger than the usable supervised-learning sample. Dropping rows with any missing predictor was rejected because it would make the sample unnecessarily small and would pre-empt later missing-data modeling choices.

Status:
Active

### 2026-06-12: Store model-panel outputs in a dedicated subfolder and add readiness figures

Decision:
Write generated model-panel CSVs and panel metadata to `2_data/processed/model_panels/`, not directly to `2_data/processed/`. Add data-cleaning-stage readiness figures under `4_analysis/figures/model_panels/`: sample construction, prediction-safe versus retrospective sensitivity coverage, all-panel feature availability, and global missingness/interpolation burden.

Reason:
The processed root already contains raw audits and candidate-discovery artifacts. A dedicated model-panel subfolder keeps deliverables scannable and makes it clear which files are generated panel inputs. The figures are diagnostic rather than model-result visuals; they help defend sample construction, panel-wide feature availability, missingness pressure, and the decision not to use full-series interpolation as the primary prediction input.

Alternatives considered:
Keeping panel CSVs in the processed root was rejected because it mixes final panel candidates with upstream audit artifacts. Model-performance plots were rejected for this notebook stage because the modeling pipeline and validation design are not yet built.

Status:
Active

### 2026-06-12: Use manufacturing value added share as the industrial-capacity predictor and mark no-imputation panels as primary

Decision:
Use World Bank WDI `NV.IND.MANF.ZS` (manufacturing value added as a percent of GDP), with the project variable name `manufacturing_share`, as the main model's industrial-capacity predictor. Treat no-imputation panels as the primary prediction-safe analysis-base panels. Keep full-series linear-interpolated panels only as retrospective sensitivity outputs, not as the main forecasting or pseudo-out-of-sample modeling input.

Reason:
The green-innovation literature argues that manufacturing capability underwrites innovation capability rather than following from it. Cohen and Zysman (1987), "Manufacturing Matters," and Pisano and Shih (2009, 2012) on the "industrial commons" show that a country's production base sustains the applied know-how, supplier networks, and process engineering that environmental technologies draw on, so present manufacturing intensity is a structural predictor of future green-patent output. `NV.IND.MANF.ZS` is well measured across 203 economies for 1990-2024, and it is close to independent of economic scale in this sample: its main-panel VIF is 1.06 (near the 1.0 floor), so it adds a distinct industrial-structure axis without reintroducing the GDP/scientific-output collinearity handled by `size_factor`.

Full-series linear interpolation is not prediction-safe because an internal gap before target year `t` can be filled using observations from year `t` or later before lag construction. It remains useful for a retrospective coverage sensitivity check, but the main analysis should report no-imputation samples or use imputation inside the later modeling pipeline after train/test splits are defined.

Alternatives considered:
Using high-technology exports (`TX.VAL.TECH.MF.ZS`) as the industrial-structure predictor was rejected because it is narrower, more volatile, and already carried in Submodel A. Dropping an industrial-structure predictor entirely was rejected because the literature explicitly motivates manufacturing capacity as a path-dependence channel for green innovation. Using the full-series linear-interpolated panels as the primary sample was rejected because it can introduce look-ahead leakage.

Status:
Active

### 2026-06-12: Build lagged main and submodel predictor panels

Decision:
Split the 20 selected predictors into one main model group and three submodel groups, and build lagged analysis-base country-year panels for each group. The main model uses 11 predictors: `gdp_constant_2015_usd`, `renewable_energy_share`, `wgi_regulatory_quality`, `co2_per_capita_ar5`, `fdi_net_inflows`, `tertiary_enrollment`, `manufacturing_share`, `scientific_journal_articles`, `trade_openness`, `inflation`, and `fossil_energy_share`. Submodel A uses `rise_energy_efficiency`, `rise_renewable_energy`, and `high_tech_exports`. Submodel B uses `rd_expenditure_gdp`, `env_co_invention_share`, `energy_imports_net`, `researchers_per_million`, and `environmental_tax_revenue`. Submodel C uses `eps_index`.

For every predictor `x`, create `x_lag1` and `x_lag1_3_mean`. Produce a no-imputation primary version and a linear-interpolated retrospective sensitivity version of each panel. The no-imputation version keeps source missing values unchanged and requires all three lag years to compute `x_lag1_3_mean`. The linear-interpolated version fills only internal gaps within the same country-predictor series before lag construction; it does not extrapolate at country-series starts or ends, and it does not impute the target, but it is not prediction-safe because it can use future endpoints. The main model uses the raw predictor window 1996-2022 and `fossil_energy_share` as the anchor variable. Submodels automatically select the predictor with the fewest covered World Bank/OECD-style 3-letter-code countries in the common raw predictor window as the anchor.

Reason:
The project is now moving from broad candidate screening to reproducible data cleaning. Separate main and submodel panels preserve the agreed predictor grouping while avoiding premature complete-case dropping across all 20 predictors. Reporting both no-imputation and retrospective linear-interpolated panels makes the sample-size tradeoff visible without making interpolation the primary prediction design. Lagged features preserve temporal ordering, and anchoring each panel on its most restrictive predictor documents the effective country and year coverage. With current `predictorsv1` files, the aggregate-entity filter, and fossil source-quality rules, v1 produces 141 main-model anchor countries for 1996-2022; active v2 re-anchors the main model after removing fossil and tertiary enrollment.

Alternatives considered:
Using only a no-imputation panel for all reporting was considered but would hide the coverage sensitivity created by internal gaps. Using linear interpolation as the main dataset was rejected because it adds assumptions and can introduce look-ahead leakage in a prediction design. Building one combined 20-predictor table was rejected because the narrow policy and R&D variables would make the main sample unnecessarily small. Manually setting submodel anchors was rejected in favor of a reproducible coverage-based rule. Extrapolating missing values at the beginning or end of a country series was rejected because it would add stronger assumptions and potential timing risk.

Status:
Active

### 2026-06-12: Compare lag-1 and three-year lagged mean ML specifications

Decision:
Pre-specify and compare two machine-learning timing specifications rather than treating one as the only main design. For each selected predictor `x`, construct a one-year lag specification, `x_lag1 = x_{t-1}`, and a three-year lagged moving-average specification, `x_lag1_3_mean = mean(x_{t-1}, x_{t-2}, x_{t-3})`, to predict the target in year `t`. Both supervised-learning tables should use pre-outcome predictor information only and should be evaluated under the same time-aware validation or pseudo-out-of-sample split. If the three-year lagged mean is used and the predictor window begins in 1996, the corresponding target years should begin in 1999 so that all three lag years are observed before the outcome.

Reason:
The project is closer to a Kaggle-style prediction task than to a single-coefficient causal panel regression. In economic machine-learning forecasting, lagged values and rolling or moving-average transformations are standard feature-engineering choices, while model choice and feature usefulness should be evaluated out of sample. The one-year lag is transparent and aligns with common panel practice. The three-year lagged mean captures more persistent pre-outcome conditions and smooths one-year measurement noise. Running both specifications lets the project compare short-run and medium-run predictive signals while preserving temporal ordering and avoiding contemporaneous or future information.

Alternatives considered:
Using only contemporaneous predictors was rejected because it risks simultaneity and look-ahead leakage. Using only `x_lag1` was considered more standard and interpretable but may miss slower R&D, energy-system, or policy effects. Using only `x_lag1_3_mean` was considered defensible but adds a stronger feature-engineering assumption and is less directly comparable to standard lagged-panel studies. Including both `x_lag1` and `x_lag1_3_mean` in the same primary model can be explored later, but it is not the pre-specified primary comparison because the two features are mechanically related. Selecting an optimized lag separately for every predictor was rejected for the main protocol because it would increase researcher degrees of freedom. Random row-level splits were rejected because they can leak future panel information across train and test rows.

Status:
Active

### 2026-06-12: Clarify lag-window rationale and robustness checks

Decision:
Keep `x_lag1_3_mean` as the pre-specified main predictor timing specification. Treat the three-year lagged mean as a pragmatic simplification of delayed innovation-response logic, not as a claim that the literature uses one universal three-year average. When the predictor window begins in 1996, the main target years should begin in 1999 so that the `t-1`, `t-2`, and `t-3` predictors are all pre-outcome information. Include robustness checks with a single `t-1` lag and, where coverage allows, a longer lag window such as `t-1` to `t-5`, especially for R&D and policy submodels.

Reason:
The reviewed literature uses heterogeneous timing strategies rather than one standard lag rule: single-year lags, distributed-lag or dynamic-response models, knowledge-stock or cumulative past-input measures, and sometimes lagged patent stock controls. Policy and energy-price studies suggest that patent responses unfold over several years, while R&D and knowledge-production-function studies emphasize accumulated knowledge stocks rather than contemporaneous flows. A three-year pre-outcome average preserves temporal ordering, avoids time leakage, reduces noise from any single lag year, and keeps the main interpretable ML specification simple and reproducible.

Alternatives considered:
Using contemporaneous predictors was rejected because it risks simultaneity and future-information leakage. Using only `t-1` was considered too short for R&D, energy-system, and environmental-policy mechanisms, but remains useful as a robustness check. Selecting a different optimized lag for each predictor was rejected for the main model because it would increase researcher degrees of freedom and make the specification harder to defend. Full distributed-lag or formal knowledge-stock models are theoretically richer, but are better reserved for robustness checks or submodels given the project's sample size, coverage constraints, and interpretability goals.

Status:
Revised by the 2026-06-12 lag-feature protocol decision.

### 2026-06-08: Use lagged moving averages for predictors

Decision:
Use three-year lagged moving averages as the main predictor timing specification. For each selected predictor `x`, construct `x_lag1_3_mean` as the mean of years `t-1`, `t-2`, and `t-3` to predict the target in year `t`.

Reason:
Environment-related innovation is unlikely to respond immediately to economic, R&D, energy-system, or policy conditions. A three-year lagged moving average captures persistent pre-outcome conditions, reduces reliance on a single arbitrary lag year, and preserves temporal ordering so that future information does not enter the prediction. This specification is especially defensible for R&D capacity and environmental policy, where the literature suggests delayed innovation responses.

Alternatives considered:
Using only `t-1` lags was considered too short for innovation responses, although it remains useful as a robustness check. Selecting different single-year lags separately for each predictor was rejected for the main model because it would increase researcher degrees of freedom and make the specification harder to defend. Single-year `t-1`, `t-2`, and `t-3` lags may still be used in robustness checks.

Status:
Revised by the 2026-06-12 lag-feature protocol decision.

### 2026-05-29: Initial screening of predictors

Decision:
Establish 27 candidate predictors across four domains.

Reason:
A broad initial screening based on supporting literature, known database filters, and joint discussions yielded 28 candidate predictors across R&D (6), energy (7), environmental policy (6), and macroeconomic (9) domains. Out of these, 27 have usable data (energy prices were excluded due to a lack of reliable data).
Predictor-Sheet: https://docs.google.com/spreadsheets/d/1SlEGhS8oKusUw6yMD-uIx9nkF4bgEVjYap7jfiHd6Q8/edit?gid=0#gid=0 

Alternatives considered:
A preliminary review indicates high correlation among many of the predictors. We estimate that the final modeling set will likely be narrowed down to 6-8 predictors representing the various domains.

Status:
Deferred

### 2026-05-20: Set the target variable

Decision:
Use PT_INV.DEV.ENV_PAT._Z (Percentage of inventions) as the main target variable.

Reason:
Based on the screening in `GitHub/2_data/notebook/candidate_discovery.ipynb`, combined with offline reviews and discussions, "Percentage of inventions" was selected over "Inventions per person". The 2026-07-06 OECD metadata correction clarifies that this selected `PT_INV` series is a global contribution share of environment-related inventions, not a domestic green-share measure. The official metadata PDF is saved at `1_literature_review/pdfs/2026_oecd_patent-indicators-metadata.pdf`.

Alternatives considered:
Inventions per person as other possible target variable candidate

Status:
Active

### 2026-05-20: Treat RISE as an alternative policy predictor

Decision:
RISE will be kept as an alternative or robustness policy predictor rather than replacing OECD EPS as the main policy candidate at this stage.

Reason:
OECD EPS has stronger direct support in the environmental-policy and green-patent literature, but its country coverage is narrow. RISE has broader country coverage and annual pillar data from 2010-2023, but it measures sustainable-energy regulatory readiness rather than general environmental policy stringency. If used, the project should prefer lagged RISE Renewable Energy or Energy Efficiency pillar scores over the overall RISE score.

Alternatives considered:
Replacing EPS with RISE was rejected for now because RISE is conceptually broader and has weaker direct patent-innovation evidence. Dropping RISE was also rejected because its broader country coverage may be valuable for an alternative policy specification.

Status:
Active

### 2026-05-19: Add candidate discovery before model building

Decision:
Before building the modeling panel, the project will use a dedicated candidate discovery step that catalogs OECD patent target combinations and literature/database-driven predictor candidates.

Reason:
The first-pass data exploration checked feasibility for a small initial set, but it did not by itself show that the relevant target and predictor candidate space had been systematically screened. A candidate discovery catalog makes the screening logic, coverage status, inclusion decisions, and dropped alternatives auditable before final variable selection.

Alternatives considered:
Moving directly to model construction was rejected because it would make variable selection look ad hoc. Downloading every possible indicator time series was also rejected because it would add complexity without improving the interpretability of the final project.

Status:
Active

### 2026-05-19: Keep predictor selection provisional

Decision:
The predictor candidate catalog is a provisional discovery artifact, not the final predictor list for modeling.

Reason:
The literature review is still in progress. The current catalog organizes plausible predictors, coverage status, measurement caveats, and inclusion labels so the project can avoid ad hoc variable choice, but the final predictor set should only be selected after the remaining literature notes and coverage checks are reviewed together.

Alternatives considered:
Treating the current predictor catalog as the final model specification was rejected because it would overstate the completeness of the literature review.

Status:
Active

### 2026-05-18: Treat `env_patent_share_inventions` as the leading target candidate

Decision:
The first literature-review pass treats `env_patent_share_inventions` as the leading main target candidate, with `env_patents_per_million` kept as a robustness or alternative intensity target.

Reason:
OECD target metadata and patent-measurement sources support a broad patent-share measure for environment-related inventions. The 2026-07-06 metadata correction clarifies that `PT_INV` is best interpreted as a global contribution share, while `env_patent_share_tech` / `PT_TECH` is the domestic all-technologies share and remains excluded as a main target because values above 100 create interpretation risk. A per-million indicator remains useful because it preserves patent intensity, but it may be more sensitive to general innovation-system scale.

Alternatives considered:
Using `env_patents_per_million` as the main target was considered but deferred because the project should first check skewness and size effects. Returning to `env_patent_share_tech` as the main target was rejected under the active 2026-05-16 decision.

Status:
Deferred

### 2026-05-16: Do not use `env_patent_share_tech` as the main target

Decision:
`env_patent_share_tech` (`PT_TECH.DEV.ENV_PAT._Z`) will not be used as the main target variable.

Reason:
The OECD API and the locally downloaded raw data both report Eritrea in 2016 with `PT_TECH = 350` and status `Normal value`. This is not a download or parsing error. The 2026-07-06 metadata correction clarifies that `PT_TECH` is the domestic all-technologies share: environment-related technologies as a percentage of all domestic technologies / inventions. However, values above 100 make the variable difficult to interpret as a simple bounded country-level share of green innovation. The most plausible explanation is that the "percentage of technologies" measure can be inflated in very small patent systems when inventions are assigned to multiple technology categories. This creates a high interpretation risk for the main analysis.

Alternatives considered:
Using `env_patent_share_tech` as the main target was rejected. It may still be considered as a robustness or sensitivity variable if the sample is filtered and the interpretation is stated carefully. `env_patents_per_million` and `env_patent_share_inventions` remain candidate target variables.

Status:
Active

### 2026-05-15: Use lightweight project governance

Decision:
The project will use lightweight governance rules stored in `0_organization/project_rules.md`.

Reason:
The project needs enough structure to prevent scope drift and documentation disorder, but it should remain practical for a course project.

Alternatives considered:
A more formal project-management structure with detailed issue tracking and approval gates was considered unnecessary at this stage.

Status:
Active

### 2026-05-15: Treat the organization file as the source of truth

Decision:
The main requirement file, `0_organization/predicting_environment-related_innovation.txt`, is the highest-priority source for project scope.

Reason:
Some repository content was generated as an initial skeleton. The project should follow the seminar requirement first and use generated content only as a starting point.

Alternatives considered:
Using the generated README as the fixed project plan was rejected because it contains specific modeling and analysis choices that are not required by the organization file.

Status:
Active

### 2026-05-15: Use controlled first-pass data exploration

Decision:
The first data step is a controlled feasibility exploration of OECD patent indicators, World Bank candidate predictors, and OECD EPS, rather than a full modeling dataset build.

Reason:
The target variable, final predictor list, country coverage, and year coverage must be checked before committing to a modeling pipeline.

Alternatives considered:
Building the full data pipeline immediately was rejected because it could lock in weak variables or mismatched coverage too early.

Status:
Active

### 2026-05-15: Keep target-variable choice deferred after first data exploration

Decision:
The OECD `Patents - indicators` dataset provides strong target candidates, but the final target variable is not selected yet.

Reason:
The first-pass exploration found three viable candidates: `env_patent_share_tech`, `env_patent_share_inventions`, and `env_patents_per_million`. The final choice should depend on literature fit and modeling interpretation, not coverage alone.

Alternatives considered:
Immediately selecting `env_patent_share_tech` was considered but deferred because the difference between "percentage of technologies" and "percentage of inventions" should be understood from OECD metadata and the literature first.

Status:
Deferred

## Deferred Decisions

The following decisions should be made after literature review and initial data inspection:

1. Final predictor list.
2. Country and year coverage.
3. Main evaluation metric.
4. Final model family or model comparison strategy.
5. Final report structure.
