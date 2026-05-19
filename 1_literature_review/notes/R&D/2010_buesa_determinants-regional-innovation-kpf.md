# The Determinants of Regional Innovation in Europe: A Combined Factorial and Regression Knowledge Production Function Approach

## Bibliographic Metadata

| Field | Value |
|---|---|
| Review ID | L015 |
| Full citation | Buesa, M., Heijs, J., & Baumert, T. (2010). The determinants of regional innovation in Europe: A combined factorial and regression knowledge production function approach. Research Policy, 39(6), 722-735. |
| Authors / organization | Mikel Buesa, Joost Heijs, Thomas Baumert (Universidad Complutense de Madrid) |
| Year | 2010 |
| Title | The determinants of regional innovation in Europe: A combined factorial and regression knowledge production function approach |
| Source type | Journal article |
| DOI / URL | https://doi.org/10.1016/j.respol.2010.02.016 |
| PDF path or access note | Available via academia.edu; also in Research Policy (Elsevier) |
| Note author | Jie Song |
| Last updated | 2026-05-20 |
| Review status | Candidate |

## One-Paragraph Summary

Buesa et al. (2010) analyze the determinants of regional innovation in Europe using a knowledge production function (KPF) framework. They combine factor analysis with regression to identify which regional characteristics best predict patent output across European regions. Key finding: R&D expenditure (both public and private) is the dominant predictor of patenting, but the regional innovation environment — including the quality of universities, the presence of innovative firms, and the broader national innovation system — plays a significant independent role. The study finds that the national environment explains about 30% of regional innovation variation, while regional factors explain about 50%. This has direct implications for our country-level design: national-level R&D and institutional variables should capture a substantial portion of environmental innovation variation.

## Why This Source Is Relevant

- **Predictor selection:** Validates R&D expenditure as the primary predictor and suggests complementary variables (researchers, institutional quality)
- **Data-source choice:** Supports using multiple R&D indicators (expenditure + human capital) rather than just one
- **Interpretation of model results:** Shows that the innovation environment (beyond R&D) matters independently
- **Report background:** Provides the KPF framework as the theoretical foundation for our model

## Data and Measurement Extraction

| Item | What the source uses / says | Relevance for our project |
|---|---|---|
| Innovation outcome | Patent applications per million inhabitants (EPO) | Similar to our env_patents_per_million |
| Patent definition or technology class | All EPO patent applications (not specifically environmental) | Broader than our target; need to adapt |
| Predictor variables | R&D expenditure (public + private), researchers, university quality, innovative firm presence, national innovation environment | Directly supports rd_expenditure_gdp and researchers_per_million |
| R&D / innovation-capacity variables | Public R&D, private R&D, researchers, universities | We have R&D and researchers from WDI |
| Unit of analysis | Region-year (European NUTS regions) | We use country-year (aggregated level) |
| Lag structure | Not explicitly modeled; cross-sectional with panel elements | We need to test appropriate lags |
| Transformations | Factor analysis to reduce dimensionality; log transforms | Log R&D and patent variables |

## Key Findings for Predictor Selection

1. R&D expenditure is consistently the strongest predictor of patent output across all specifications. Validates our primary predictor choice.
2. Researchers and university quality have independent effects beyond R&D spending. Supports including researchers_per_million.
3. National-level institutional factors explain ~30% of innovation variation — our country-level design should capture these.
4. The production function approach confirms that the R&D-to-patent relationship is approximately log-linear.

## Predictor Implications for Our Model

| Candidate predictor concept | Supported? | Expected sign | Evidence from source | Caveat |
|---|---|---|---|---|
| GDP per capita / income level | Yes | Positive | National environment matters | May correlate with R&D |
| R&D expenditure | Strongly | Positive | Dominant predictor in all specifications | Our WDI R&D is general R&D |
| Researchers / human capital | Yes | Positive | Independent effect beyond R&D spending | Coverage is thinner |
| Renewable energy share | Not discussed | — | — | — |
| Environmental policy stringency | Not discussed | — | — | — |
| Institutional quality (new) | Yes | Positive | National innovation environment index | Not directly in WDI; could use WGI |

## Strengths

1. Solid methodology combining factor analysis with KPF regression.
2. Uses the well-established knowledge production function framework.
3. Distinguishes between regional and national determinants — useful for justifying country-level design.
4. Published in Research Policy — top innovation studies journal.

## Limitations

1. Focuses on European regions, not countries — may not generalize to developing countries.
2. Uses all patents, not environmental patents specifically — need to adapt.
3. Cross-sectional rather than panel design — weaker for causal claims.
4. Does not include energy or environmental policy variables.

## How We Should Use This Source

`Supporting` — Provides the methodological and theoretical foundation (KPF framework) for using R&D and researchers as predictors. Useful for justifying our variable selection in the related work and methods sections. Less directly relevant for energy or policy variables.

## Extractable Text for Report

1. "R&D expenditure is consistently the strongest predictor of patent output."
2. "The knowledge production function framework provides a robust basis for modeling the innovation process."
3. "National-level institutional factors explain approximately 30% of regional innovation variation."

---

## Chinese Translation

# 欧洲区域创新的决定因素：因子分析与回归知识生产函数的组合方法

## 文献元数据

| 字段 | 值 |
|---|---|
| 审查编号 | L015 |
| 完整引用 | Buesa, M., Heijs, J., & Baumert, T. (2010). The determinants of regional innovation in Europe. Research Policy, 39(6), 722-735. |
| 作者/机构 | Mikel Buesa, Joost Heijs, Thomas Baumert（马德里康普顿斯大学）|
| 年份 | 2010 |
| 来源类型 | 期刊论文（Research Policy）|
| 笔记作者 | Jie Song |
| 审查状态 | 候选 |

## 一段话总结

Buesa 等人（2010）使用知识生产函数框架分析欧洲区域创新的决定因素。他们结合因子分析和回归方法来识别哪些区域特征最能预测专利产出。核心发现：R&D 支出（公共和私人）是专利产出的主导预测因子，但区域创新环境——包括大学质量、创新企业的存在以及更广泛的国家创新体系——也发挥着显著的独立作用。研究发现国家环境解释了约 30% 的区域创新差异，区域因素解释了约 50%。

## 预测因子选择的关键发现

1. R&D 支出在所有设定中始终是专利产出的最强预测因子。验证了我们的首要预测因子选择。
2. 研究人员和大学质量在 R&D 支出之外具有独立效应。支持纳入 researchers_per_million。
3. 国家级制度因素解释了约 30% 的创新差异——我们的国家级设计应该能捕捉这些因素。
4. 生产函数方法确认 R&D 到专利的关系近似对数线性。

## 我们应该如何使用此来源

`支持性` — 为使用 R&D 和研究人员作为预测因子提供了方法论和理论基础（KPF 框架）。有助于在相关工作和方法章节中证明我们的变量选择。
