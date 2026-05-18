# Environmental Policy Stringency and Technological Innovation

## Bibliographic Metadata

| Field | Value |
|---|---|
| Review ID | L012 |
| Full citation | Johnstone, N., I. Hascic, J. Poirier, M. Hemar and C. Michel (2012), `Environmental Policy Stringency and Technological Innovation: Evidence from Survey Data and Patent Counts`, Applied Economics, 44(17), 2157-2170. |
| Authors / organization | Nick Johnstone, Ivan Hascic, Julien Poirier, Myriam Hemar and Camille Michel |
| Year | 2012 |
| Title | Environmental Policy Stringency and Technological Innovation: Evidence from Survey Data and Patent Counts |
| Source type | Journal article |
| DOI / URL | https://doi.org/10.1080/00036846.2011.560110 |
| PDF path or access note | `1_literature_review/pdfs/2012_johnstone_environmental-policy-stringency_access.md` |
| Note author | Codex |
| Last updated | 2026-05-18 |
| Review status | Notes drafted |

## One-Paragraph Summary

This paper is one of the closest empirical matches to the project because it links country-level environmental policy stringency to environment-related patenting. Subagent screening reports that the study uses an unbalanced panel of 77 countries from 2001-2007, combining PATSTAT environmental patents with a World Economic Forum survey measure of environmental regulation stringency. The accessible summaries indicate that both general innovative capacity and policy stringency are positively associated with environment-related patent counts. For our model, this supports a positive expected sign for lagged policy stringency and a separate R&D or innovation-capacity predictor. It should still be interpreted cautiously because the policy variable is perception-based and the time window is short.

## Why This Source Is Relevant

- Predictor selection.
- Lag structure.
- Interpretation of model results.
- Limitation or caution.

## Data and Measurement Extraction

| Item | What the source uses / says | Relevance for our project |
|---|---|---|
| Innovation outcome | Environment-related patent counts. | Strong empirical match to the project outcome concept. |
| Patent definition or technology class | PATSTAT, IPC-based environmental technology classes, inventor country, priority year, and high-value patent treatment according to subagent screening. | Supports OECD-style environmental patent target and measurement caveats. |
| Predictor variables | Policy stringency, general innovative capacity, and economic controls. | Directly informs predictor set. |
| Policy variables | World Economic Forum perceived environmental regulation stringency, reported as a 1-7 scale in subagent screening. | Conceptually close to EPS, though not the same measure. |
| R&D / innovation-capacity variables | Total high-value patents in other fields; two-stage setup reportedly includes R&D expenditure as percent of GDP. | Supports R&D/innovation capacity controls. |
| Energy or emissions variables | Not central in the note pass. | No direct support for WDI energy proxies. |
| Macro controls | Reported controls include OECD dummy, year effects, trade openness, IPR strength, and lagged real GDP in some specifications. | Supports GDP/development controls but may be too broad for the course model. |
| Unit of analysis | Country-year. | Strong alignment with project design. |
| Countries / regions | 77 countries according to subagent screening. | Broader than many OECD-only studies. |
| Years | 2001-2007 according to subagent screening. | Shorter than the project panel. |
| Lag structure | Uses temporal ordering and possibly lagged macro variables; exact specification should be verified. | Supports lagging predictors. |
| Data sources | PATSTAT and WEF Executive Opinion Survey, with additional economic controls. | Different policy source than OECD EPS. |
| Transformations | Count-data and two-stage specifications in accessible summaries. | Our normalized target changes coefficient interpretation. |

## Key Findings for Predictor Selection

1. Environmental policy stringency is positively associated with environmental patenting in a country-level panel.
2. General innovative capacity is important, supporting R&D intensity or patent-capacity controls.
3. Because the policy measure is perception-based and the period is short, this is strong support for predictor inclusion but not causal proof.

## Predictor Implications for Our Model

| Candidate predictor concept | Supported? | Expected sign | Evidence from source | Caveat |
|---|---|---|---|---|
| GDP per capita / income level | Yes | Positive | Lagged real GDP appears in reported specifications. | GDP may capture several mechanisms at once. |
| R&D expenditure | Yes | Positive | R&D expenditure as percent of GDP appears in two-stage evidence per subagent screening. | Coverage in WDI is thin. |
| Researchers / human capital | Mixed | Positive | General innovation capacity matters. | Researchers not directly identified in the note pass. |
| Renewable energy share | Not discussed | Ambiguous | No direct evidence. | No support. |
| Fossil energy share | Not discussed | Ambiguous | No direct evidence. | No support. |
| Energy intensity | Not discussed | Ambiguous | No direct evidence. | No support. |
| CO2 emissions per capita | Not discussed | Ambiguous | No direct evidence. | No support. |
| Environmental policy stringency | Yes | Positive | Perceived stringency is positively associated with environmental patent counts. | WEF perception index differs from OECD EPS. |
| Other useful predictor | Yes | Positive | Total patents in other fields proxy general innovative capacity. | If using a patent-share target, total patents may be mechanically related. |

## Strengths

1. Very close to the project's country-year environmental-patent design.
2. Directly supports policy stringency and innovation capacity as predictors.
3. Uses environmental patent counts rather than total patenting.

## Limitations

1. Data coverage limitations: Short 2001-2007 window in subagent screening.
2. Measurement limitations: Policy stringency is perception-based and not identical to EPS.
3. Identification or interpretation limitations: Limited time variation and observational design constrain causal interpretation.
4. Transferability limitations: Count outcome differs from the project's likely normalized share target.

## How We Should Use This Source

`Core`: Use this as a core empirical source for including lagged policy stringency and innovation capacity. It is one of the best bridges between the literature and the project's country-year patent prediction design, but the report should still use associative language.

## Extractable Text for Report

1. Country-level evidence links stricter environmental policy with more environment-related patenting, while also showing that general innovative capacity matters.
2. This supports a compact model with lagged policy stringency, R&D capacity, and a small set of macro or market controls.

## Open Questions After Reading

1. Does the final Applied Economics version differ from the accessible manuscript or summary records?
2. Should the project include a general patent-capacity control, or does `env_patent_share_inventions` already normalize enough?

## Chinese Translation

### 书目信息

| 字段 | 值 |
|---|---|
| 审阅 ID | L012 |
| 完整引用 | Johnstone, N., I. Hascic, J. Poirier, M. Hemar and C. Michel (2012), `Environmental Policy Stringency and Technological Innovation: Evidence from Survey Data and Patent Counts`, Applied Economics, 44(17), 2157-2170. |
| 作者 / 机构 | Nick Johnstone, Ivan Hascic, Julien Poirier, Myriam Hemar and Camille Michel |
| 年份 | 2012 |
| 标题 | Environmental Policy Stringency and Technological Innovation: Evidence from Survey Data and Patent Counts |
| 来源类型 | Journal article |
| DOI / URL | https://doi.org/10.1080/00036846.2011.560110 |
| PDF 路径或访问说明 | `1_literature_review/pdfs/2012_johnstone_environmental-policy-stringency_access.md` |
| 笔记作者 | Codex |
| 最后更新 | 2026-05-18 |
| 审阅状态 | Notes drafted |

### 一段式摘要

本文是与本项目最接近的实证匹配之一，因为它将 country-level environmental policy stringency 与 environment-related patenting 联系起来。Subagent screening 报告称，该研究使用 2001-2007 年 77 个国家的不平衡 panel，将 PATSTAT environmental patents 与 World Economic Forum survey measure of environmental regulation stringency 结合起来。可访问摘要表明，general innovative capacity 和 policy stringency 都与 environment-related patent counts 正相关。对我们的模型而言，这支持 lagged policy stringency 的正向预期符号，也支持单独的 R&D 或 innovation-capacity predictor。由于政策变量基于 perception 且时间窗口较短，仍应谨慎解释。

### 为什么这个来源相关

- 预测变量选择。
- 滞后结构。
- 模型结果解释。
- 限制或谨慎说明。

### 数据与测量提取

| 项目 | 来源使用 / 说明的内容 | 对本项目的相关性 |
|---|---|---|
| 创新结果 | Environment-related patent counts。 | 与项目结果概念高度匹配。 |
| 专利定义或技术类别 | 根据 subagent screening，使用 PATSTAT、IPC-based environmental technology classes、inventor country、priority year 和 high-value patent treatment。 | 支持 OECD-style environmental patent target 和测量注意事项。 |
| 预测变量 | Policy stringency、general innovative capacity 和 economic controls。 | 直接影响预测变量集合。 |
| 政策变量 | World Economic Forum perceived environmental regulation stringency，subagent screening 报告为 1-7 scale。 | 概念上接近 EPS，但不是同一个度量。 |
| R&D / 创新能力变量 | Total high-value patents in other fields；据报告，两阶段设置包含 R&D expenditure as percent of GDP。 | 支持 R&D / innovation capacity controls。 |
| 能源或排放变量 | 在本轮 note pass 中不是核心内容。 | 不直接支持 WDI energy proxies。 |
| 宏观控制变量 | 报告的控制变量包括 OECD dummy、year effects、trade openness、IPR strength，以及某些 specification 中的 lagged real GDP。 | 支持 GDP / development controls，但对课程模型可能过宽。 |
| 分析单位 | Country-year。 | 与项目设计高度一致。 |
| 国家 / 地区 | 根据 subagent screening，77 个国家。 | 比许多 OECD-only studies 更广。 |
| 年份 | 根据 subagent screening，2001-2007 年。 | 比项目 panel 更短。 |
| 滞后结构 | 使用 temporal ordering，并可能使用 lagged macro variables；确切 specification 应核实。 | 支持滞后预测变量。 |
| 数据来源 | PATSTAT 和 WEF Executive Opinion Survey，并包含额外 economic controls。 | 与 OECD EPS 的政策来源不同。 |
| 转换 | 可访问摘要中的 count-data 和 two-stage specifications。 | 我们的 normalized target 改变了系数解释。 |

### 预测变量选择的关键发现

1. Environmental policy stringency 在 country-level panel 中与 environmental patenting 正相关。
2. General innovative capacity 很重要，支持 R&D intensity 或 patent-capacity controls。
3. 因为政策度量基于 perception 且时期较短，这强力支持纳入预测变量，但不是 causal proof。

### 对我们模型的预测变量含义

| 候选预测变量概念 | 是否支持？ | 预期符号 | 来源证据 | 注意事项 |
|---|---|---|---|---|
| GDP per capita / income level | 是 | 正向 | Lagged real GDP 出现在已报告的 specifications 中。 | GDP 可能同时捕捉多个机制。 |
| R&D expenditure | 是 | 正向 | 根据 subagent screening，R&D expenditure as percent of GDP 出现在 two-stage evidence 中。 | WDI 中的覆盖较薄。 |
| Researchers / human capital | 混合 | 正向 | General innovation capacity 很重要。 | 本轮 note pass 未直接识别 researchers。 |
| Renewable energy share | 未讨论 | 不明确 | 没有直接证据。 | 不支持。 |
| Fossil energy share | 未讨论 | 不明确 | 没有直接证据。 | 不支持。 |
| Energy intensity | 未讨论 | 不明确 | 没有直接证据。 | 不支持。 |
| CO2 emissions per capita | 未讨论 | 不明确 | 没有直接证据。 | 不支持。 |
| Environmental policy stringency | 是 | 正向 | Perceived stringency 与 environmental patent counts 正相关。 | WEF perception index 不同于 OECD EPS。 |
| Other useful predictor | 是 | 正向 | Other fields 中的 total patents 代理 general innovative capacity。 | 如果使用 patent-share target，total patents 可能存在机械相关性。 |

### 优势

1. 非常接近本项目的 country-year environmental-patent design。
2. 直接支持 policy stringency 和 innovation capacity 作为预测变量。
3. 使用 environmental patent counts，而不是 total patenting。

### 局限

1. 数据覆盖限制：subagent screening 中为较短的 2001-2007 年窗口。
2. 测量限制：Policy stringency 基于 perception，且不等同于 EPS。
3. 识别或解释限制：有限的时间变化和 observational design 限制因果解释。
4. 可迁移性限制：Count outcome 不同于项目可能使用的 normalized share target。

### 本项目应如何使用这个来源

`Core`：将其作为纳入 lagged policy stringency 和 innovation capacity 的核心实证来源。它是连接文献与本项目 country-year patent prediction design 的最佳桥梁之一，但报告仍应使用关联性语言。

### 可提取到报告中的文本

1. Country-level evidence 将更严格的 environmental policy 与更多 environment-related patenting 联系起来，同时也显示 general innovative capacity 很重要。
2. 这支持一个包含 lagged policy stringency、R&D capacity 以及少量 macro 或 market controls 的紧凑模型。

### 阅读后的开放问题

1. 最终 Applied Economics 版本是否不同于可访问的 manuscript 或 summary records？
2. 项目是否应纳入 general patent-capacity control，还是 `env_patent_share_inventions` 已经进行了足够归一化？
