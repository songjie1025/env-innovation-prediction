# Literature Review Synthesis

This file summarizes the first reviewer-style evidence pack for the literature review. It is a working synthesis, not a substitute for the individual paper notes.

## Selection Logic

Sources are prioritized using two criteria:

1. Direct fit to this project's country-year design, OECD patent targets, WDI predictors, and OECD EPS policy data.
2. Scholarly weight, using citation counts, journal quality, and repeated use in the environmental innovation literature as supporting signals.

When these criteria conflict, direct dataset and measurement relevance wins. A lower-cited OECD methodological source can be more important for target-variable defense than a highly cited but less aligned conceptual paper.

## Current Reviewer Position

The selected main target is `env_patent_share_inventions` / `PT_INV.DEV.ENV_PAT._Z`.

Reasons:

1. It matches an OECD patent-indicator series for each country or aggregate area's contribution to worldwide environment-related inventions.
2. It has broad country-year coverage, but it should be interpreted as a global contribution share rather than a domestic portfolio share.
3. It avoids using `env_patent_share_tech` as the main target, where the domestic all-technologies share can exceed 100 in small or multi-classified patent portfolios.

`env_patents_per_million` should remain a robustness or alternative target because it captures patent intensity per population, but it may be more sensitive to country innovation-system scale and skewness. `env_patent_share_tech` should stay out of the main target role because values above 100 create interpretation risk, but it can still be used for diagnostic or sensitivity discussion if needed.

## Predictor Evidence Assessment

| Predictor concept | Current evidence strength | Reviewer interpretation |
|---|---|---|
| R&D capacity | Strong | Repeatedly supported in renewable/environmental patent studies, although project WDI R&D is general R&D rather than green R&D. |
| Environmental policy stringency | Strong | Supported by OECD EPS documentation and policy-patent studies; interpret as association/predictive signal, not causal proof. |
| GDP / market size | Moderate | Useful as an economic-scale and market-size predictor; total GDP is more aligned with the country-level innovation-share target than GDP per capita for the main raw predictor set. |
| GDP per capita / development | Moderate | Useful as a development control, but replaced by total GDP in the main raw predictor set to avoid making income level the primary macro-size proxy. |
| Manufacturing share | Moderate to weak | Industry-level evidence suggests sectoral structure matters, but country-level manufacturing share is only a rough proxy. |
| Renewable energy share | Moderate | Related evidence uses renewable capacity, demand-pull policies, or market size more often than WDI renewable final-energy share. |
| Fossil energy share | Weak to cautionary | Fossil dependence can reflect transition pressure or lock-in; sign is theoretically ambiguous. |
| Energy intensity | Weak to cautionary | Energy-price papers justify energy pressure, but WDI energy intensity is not equivalent to price incentives. |
| CO2 per capita | Weak to cautionary | Emissions pressure may motivate policy/innovation, but raw emissions are often an outcome of structure and scale. |
| Researchers per million | Moderate | Conceptually aligned with innovation capacity, but direct environmental patent studies more often use R&D spending or patent/knowledge stocks. |
| RISE score | Optional | Useful sustainable-energy policy proxy if coverage fits, but direct patent evidence is weaker than for OECD/EPS-style policy measures. |

## Design Implications

Compare one-year lagged predictors and three-year lagged moving-average predictors as pre-specified machine-learning timing specifications. For each selected predictor `x`, construct `x_lag1 = x_{t-1}` and `x_lag1_3_mean = mean(x_{t-1}, x_{t-2}, x_{t-3})` to predict the target in year `t`. Both specifications should use time-aware validation or pseudo-out-of-sample splits rather than random row-level splits.

Avoid claiming causal effects from the final machine-learning model. The literature provides mechanisms and expected signs, but this project's goal is interpretable prediction. The report should say predictors are associated with future environment-related innovation in the model, not that they cause innovation.

Keep the main model small. A reviewer will likely prefer fewer well-defended predictors in the main specification over a broad WDI variable grab. At the same time, the broader predictor pool from `Managerial AI- literature review - List 1.csv` and the candidate catalog should remain in consideration; variables should be assigned to main-model, robustness, exploratory, or data-limited roles after coverage and collinearity checks. A defensible first model would include the selected target, lagged R&D intensity, lagged total GDP, one policy variable, and one carefully interpreted energy-system variable.

## First-Pass Source Tiers

### Tier 1: Core Sources To Use In Report

1. OECD patent data documentation and the OECD patent statistics manual for target construction.
2. Hascic and Migotto (2015) for environmental patent measurement.
3. Kruse et al. (2022) and Botta and Kozluk (2014) for EPS construction and coverage.
4. Johnstone, Hascic, and Popp (2010) for renewable policy and patent count evidence.
5. Nesta, Vona, and Nicolli (2014) for policy, market structure, and renewable patent evidence.
6. Popp (2002) for induced innovation and energy-price mechanism.
7. Johnstone et al. (2012) or Martinez-Zarzoso et al. (2019) for environmental policy stringency and patent evidence.

### Tier 2: Supporting Sources

1. Jaffe and Palmer (1997) for a cautious Porter-hypothesis test.
2. Brunnermeier and Cohen (2003) for industry-level environmental patent determinants.
3. Lanzi, Hascic, and Johnstone (2012) for electricity-generation technology patents.
4. Verdolini and Galeotti (2011) for knowledge stocks and international diffusion.
5. Popp (2005) for general patent-measurement caveats.

### Tier 3: Keep For Later If Space Allows

1. EPO Y02/Y04S taxonomy paper.
2. RISE methodology documentation.
3. New OECD environmental innovation metrics papers.
4. Country- or firm-specific green innovation papers that do not map cleanly to the project panel.
