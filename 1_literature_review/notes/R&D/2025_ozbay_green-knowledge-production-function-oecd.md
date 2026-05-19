# Green Innovation for a Sustainable Environment: Modeling the New Green Knowledge Production Function for OECD Countries

## Bibliographic Metadata

| Field | Value |
|---|---|
| Review ID | L014 |
| Full citation | Ozbay, F. (2025). Green innovation for a sustainable environment: Modeling the new green knowledge production function for OECD countries. Natural Resources Forum, early view. |
| Authors / organization | Fatih Ozbay (Istanbul Technical University / OECD context) |
| Year | 2025 |
| Title | Green innovation for a sustainable environment: Modeling the new green knowledge production function for OECD countries |
| Source type | Journal article |
| DOI / URL | https://doi.org/10.1111/1477-8947.12552 |
| PDF path or access note | Wiley: https://onlinelibrary.wiley.com/doi/pdf/10.1111/1477-8947.12552 |
| Note author | Jie Song |
| Last updated | 2026-05-20 |
| Review status | Candidate |

## One-Paragraph Summary

Ozbay (2025) directly models a green knowledge production function (KPF) for OECD countries, using environmental R&D expenditure as the primary input and green patent counts as the output. This is one of the most directly relevant recent papers for our project because it (a) uses the Griliches (1979) KPF framework applied specifically to green innovation, (b) operates at the country-year level, (c) uses OECD environmental R&D data (distinct from general R&D), and (d) explicitly models the R&D → green patent relationship. Key finding: environmental R&D expenditure has a strong positive effect on green patent output, with an elasticity of approximately 0.6-0.8. General R&D also matters but with a smaller elasticity (0.3-0.4). The study finds that knowledge stocks (cumulative past R&D) are more important than current R&D flows, supporting the use of lagged R&D variables.

## Why This Source Is Relevant

- **Predictor selection:** Directly justifies R&D expenditure (%GDP) as the most important predictor of green patenting
- **Lag structure:** Knowledge stocks matter more than flows → supports using multiple R&D lags
- **Data-source choice:** Confirms that OECD environmental R&D data is preferable to WDI general R&D (though WDI has broader country coverage)
- **Target-variable choice:** Validates green patents as the appropriate output measure for the KPF framework

## Data and Measurement Extraction

| Item | What the source uses / says | Relevance for our project |
|---|---|---|
| Innovation outcome | Green patent counts (PATSTAT, IPC Green Inventory) | Same as our OECD target family |
| Patent definition or technology class | IPC Green Inventory, 7 technology domains | Aligned with OECD ENV-TECH categories |
| Predictor variables | Environmental R&D expenditure, general R&D expenditure, knowledge stock (perpetual inventory), researchers | Directly supports our rd_expenditure_gdp and researchers_per_million |
| Policy variables | Not a primary focus; environmental R&D is partly policy-driven | EPS captures the policy → R&D → patent channel |
| R&D / innovation-capacity variables | Environmental R&D (core), general R&D, knowledge stock, researchers | Central to our model |
| Energy or emissions variables | Not included | We add these separately |
| Macro controls | GDP per capita, trade openness | Standard |
| Unit of analysis | Country-year (OECD countries, 2000-2020) | Same as our design |
| Years | 2000-2020 | Overlaps our panel |
| Lag structure | Knowledge stock (t-1 to t-5); current R&D (t-1) | Supports lagging R&D variables |
| Transformations | Log-log KPF; knowledge stock as perpetual inventory (delta=0.15) | Log R&D and patent variables |

## Key Findings for Predictor Selection

1. Environmental R&D elasticity for green patents: 0.6-0.8. Strong, consistent, and directly relevant.
2. General R&D also positive but smaller (0.3-0.4). Our WDI R&D is general R&D — expect smaller but still significant effect.
3. Knowledge stocks (cumulative past R&D) dominate current R&D flows. This means lagged R&D variables are more predictive than contemporaneous R&D.
4. Researchers per capita has an independent positive effect beyond R&D expenditure. Supports including both.

## Predictor Implications for Our Model

| Candidate predictor concept | Supported? | Expected sign | Evidence from source | Caveat |
|---|---|---|---|---|
| GDP per capita / income level | Yes | Positive | Control variable; positive in all specs | May absorb R&D effect if collinear |
| R&D expenditure | Strongly | Positive | Core finding; elasticity 0.3-0.4 for general R&D | Our WDI R&D is general R&D — lower elasticity expected |
| Researchers / human capital | Yes | Positive | Independent effect beyond R&D spending | Coverage in WDI is thinner (145 countries) |
| Renewable energy share | Not discussed | — | — | — |
| Fossil energy share | Not discussed | — | — | — |
| Energy intensity | Not discussed | — | — | — |
| CO2 emissions per capita | Not discussed | — | — | — |
| Environmental policy stringency | Indirectly | Positive | Environmental R&D is partly policy-driven | EPS captures the policy channel |
| Environmental R&D (new) | Strongly | Positive | Elasticity 0.6-0.8 | Not in WDI; OECD-only data |

## Strengths

1. Extremely recent (2025) and directly models the exact relationship we study (R&D → green patents).
2. Uses the well-established knowledge production function framework (Griliches 1979).
3. Distinguishes environmental R&D from general R&D — useful for interpreting our WDI general R&D variable.
4. Explicitly models knowledge stocks vs. flows — provides theoretical basis for our lag structure.

## Limitations

1. OECD countries only — findings may not generalize to developing countries in our broader panel.
2. Environmental R&D data is not available in WDI — we must use general R&D as a proxy.
3. Relatively new paper (2025) with limited citation track record.
4. Does not include energy or policy variables, so cannot assess their relative importance vs. R&D.

## How We Should Use This Source

`Core` — This is one of the most directly relevant papers for justifying R&D as our primary predictor. The green knowledge production function framework provides the theoretical backbone for our model. We should cite this to justify: (a) why R&D expenditure is the #1 predictor, (b) why we lag R&D variables, and (c) why general R&D (WDI proxy) is a valid but conservative measure of innovation capacity.

## Extractable Text for Report

1. "Environmental R&D expenditure has a strong positive effect on green patent output, with an elasticity of approximately 0.6-0.8."
2. "Knowledge stocks, representing cumulative past R&D investment, are more important determinants of green innovation than current R&D flows alone."
3. "The knowledge production function framework (Griliches 1979) provides a robust theoretical foundation for modeling the R&D-to-green-patent relationship."

## Open Questions After Reading

1. Can we approximate the knowledge stock with a moving average of past R&D (e.g., 3-year or 5-year rolling mean)?
2. Should we test an R&D × GDP interaction, as the KPF framework suggests absorptive capacity matters?
3. How much predictive power do we lose by using general R&D instead of environmental R&D?

---

## Chinese Translation

# 绿色创新促进可持续环境：为 OECD 国家建模新型绿色知识生产函数

## 文献元数据

| 字段 | 值 |
|---|---|
| 审查编号 | L014 |
| 完整引用 | Ozbay, F. (2025). Green innovation for a sustainable environment: Modeling the new green knowledge production function for OECD countries. Natural Resources Forum. |
| 作者/机构 | Fatih Ozbay（伊斯坦布尔技术大学）|
| 年份 | 2025 |
| 标题 | 绿色创新促进可持续环境：为 OECD 国家建模新型绿色知识生产函数 |
| 来源类型 | 期刊论文 |
| DOI | https://doi.org/10.1111/1477-8947.12552 |
| 笔记作者 | Jie Song |
| 审查状态 | 候选 |

## 一段话总结

Ozbay（2025）直接为 OECD 国家建模了绿色知识生产函数（KPF），使用环境 R&D 支出作为主要输入，绿色专利计数作为输出。这是与我们的项目最直接相关的近期论文之一，因为它 (a) 将 Griliches（1979）的 KPF 框架专门应用于绿色创新，(b) 在国家-年份层面操作，(c) 使用 OECD 环境 R&D 数据（区别于通用 R&D），(d) 明确建模了 R&D→绿色专利的关系。核心发现：环境 R&D 支出对绿色专利产出有强正效应，弹性约为 0.6-0.8。通用 R&D 也重要但弹性较小（0.3-0.4）。研究发现知识存量（累积的过往 R&D）比当期 R&D 流量更重要，支持使用滞后 R&D 变量。

## 预测因子选择的关键发现

1. 环境 R&D 对绿色专利的弹性：0.6-0.8。强劲、一致且直接相关。
2. 通用 R&D 也为正但较小（0.3-0.4）。我们的 WDI R&D 是通用 R&D——预期效应较小但仍显著。
3. 知识存量（累积过往 R&D）比当期 R&D 流量更能解释创新产出。
4. 研究人员人均数量在 R&D 支出之外有独立的正面效应。

## 我们应该如何使用此来源

`核心` — 这是证明 R&D 作为我们首要预测因子的最直接相关论文之一。绿色知识生产函数框架为我们的模型提供了理论支柱。我们应引用此文来证明：(a) 为什么 R&D 支出是 #1 预测因子，(b) 为什么我们对 R&D 变量进行滞后处理，(c) 为什么通用 R&D（WDI 代理）是创新能力的有效但保守的测量。
