# World Bank Open Data and WDI

## Bibliographic Metadata

| Field | Value |
|---|---|
| Review ID | L004 |
| Full citation | World Bank (2026), `World Bank Open Data` and World Development Indicators, accessed 2026-05-18. |
| Authors / organization | World Bank |
| Year | 2026 |
| Title | World Bank Open Data / World Development Indicators |
| Source type | Data documentation |
| DOI / URL | https://data.worldbank.org/ |
| PDF path or access note | `1_literature_review/pdfs/2026_world-bank-open-data_access.md` |
| Note author | Codex |
| Last updated | 2026-05-18 |
| Review status | Notes drafted |

## One-Paragraph Summary

World Bank Open Data and the World Development Indicators provide the project's broad macroeconomic, R&D, energy, and emissions predictor candidates. This source is essential for data provenance but not for theoretical justification: it tells us where variables come from and how they are measured, not whether they should predict environmental innovation. Local exploration already shows an important tradeoff. Macro and energy variables have broad coverage, while R&D expenditure and researchers per million are much thinner but theoretically stronger. This note should therefore be used as a data-source note, with predictor justification drawn from empirical literature.

## Why This Source Is Relevant

- Predictor selection.
- Data-source choice.
- Interpretation of model results.
- Limitation or caution.

## Data and Measurement Extraction

| Item | What the source uses / says | Relevance for our project |
|---|---|---|
| Innovation outcome | Not a patent outcome source. | Target remains OECD patents. |
| Patent definition or technology class | Not applicable. | No target-variable guidance. |
| Predictor variables | GDP per capita, GDP, population, manufacturing share, R&D expenditure, researchers, renewable share, fossil share, energy intensity, CO2 per capita. | Main public source for candidate non-policy predictors. |
| Policy variables | Limited for this project's current design. | EPS and RISE are separate sources. |
| R&D / innovation-capacity variables | R&D expenditure as percent of GDP and researchers per million people. | Strong candidate predictors but thinner coverage. |
| Energy or emissions variables | Renewable energy share, fossil energy share, energy intensity, CO2 per capita. | Useful energy-system proxies with mixed theoretical interpretation. |
| Macro controls | GDP per capita, GDP, population, manufacturing share. | Useful for development, size, and structure controls. |
| Unit of analysis | Country-year indicators. | Matches the project panel. |
| Countries / regions | Broad global coverage, varying by indicator. | Helps keep a broad sample if EPS or R&D constraints are not binding. |
| Years | Local exploration requested 1990-2024, with indicator-specific coverage. | Some energy and emissions variables end earlier. |
| Lag structure | Not specified by data source. | Apply project lag rules, usually `t-1`. |
| Data sources | World Bank Open Data / WDI and ESG source for some indicators. | Must record exact indicator codes in `2_data/data_dictionary.md`. |
| Transformations | Logs for size/income variables; standardization or direct shares for percentage variables. | Transformations should be documented after final variable selection. |

## Key Findings for Predictor Selection

1. WDI is a practical source for a broad country-year predictor panel.
2. Strong theoretical variables such as R&D and researchers may reduce sample size substantially.
3. Energy and emissions variables are available but need cautious interpretation because they are proxies, not direct policy or price incentives.

## Predictor Implications for Our Model

| Candidate predictor concept | Supported? | Expected sign | Evidence from source | Caveat |
|---|---|---|---|---|
| GDP per capita / income level | Yes | Positive | WDI provides comparable GDP per capita data. | Data availability is not theory; cite empirical literature for mechanism. |
| R&D expenditure | Yes | Positive | WDI provides R&D expenditure as percent of GDP. | Coverage is thinner than macro variables. |
| Researchers / human capital | Yes | Positive | WDI provides researchers per million. | Coverage is thinner and may overlap with R&D expenditure. |
| Renewable energy share | Yes | Positive | WDI provides renewable energy share. | Literature often uses renewable policy or capacity, not final-energy share. |
| Fossil energy share | Yes | Ambiguous | WDI provides fossil energy share. | Could indicate transition pressure or fossil lock-in. |
| Energy intensity | Yes | Ambiguous | WDI provides energy intensity. | Not equivalent to energy prices. |
| CO2 emissions per capita | Yes | Ambiguous | WDI/World Bank source provides CO2 per capita. | Emissions may reflect scale and structure rather than innovation incentive. |
| Environmental policy stringency | Not discussed | Positive | WDI is not the current EPS source. | Use OECD EPS. |
| Other useful predictor | Yes | Ambiguous | Manufacturing share and population are available. | Avoid redundant size controls if using normalized patent target. |

## Strengths

1. Broad, public, reproducible data source.
2. Country-year format aligns with the modeling dataset.
3. Provides many candidate predictors from one source, reducing merge complexity.

## Limitations

1. Data coverage limitations: Coverage varies sharply by indicator, especially R&D and researchers.
2. Measurement limitations: WDI proxies are general national indicators, not green-specific innovation inputs.
3. Identification or interpretation limitations: The source is data documentation, not empirical evidence.
4. Transferability limitations: Some indicators may have inconsistent reporting quality across countries and years.

## How We Should Use This Source

`Core`: Use this source for data provenance, not as literature evidence for expected signs. The report should cite empirical papers for predictor logic and cite WDI for variable definitions and data access. A reviewer will likely accept WDI as a source but will not accept it as proof that a predictor belongs in the model.

## Extractable Text for Report

1. World Bank indicators provide a reproducible source for broad country-year predictors in macroeconomic development, R&D capacity, energy structure, and emissions.
2. The final predictor list should balance theoretical strength against WDI coverage, especially for R&D-related variables.

## Open Questions After Reading

1. Which WDI variables survive both the literature screen and coverage screen?
2. Should the model use both R&D expenditure and researchers, or choose one to avoid overlapping capacity measures?

## Chinese Translation

### 书目信息

| 字段 | 值 |
|---|---|
| 审阅 ID | L004 |
| 完整引用 | World Bank (2026), `World Bank Open Data` and World Development Indicators, accessed 2026-05-18. |
| 作者 / 机构 | World Bank |
| 年份 | 2026 |
| 标题 | World Bank Open Data / World Development Indicators |
| 来源类型 | 数据文档 |
| DOI / URL | https://data.worldbank.org/ |
| PDF 路径或访问说明 | `1_literature_review/pdfs/2026_world-bank-open-data_access.md` |
| 笔记作者 | Codex |
| 最后更新 | 2026-05-18 |
| 审阅状态 | Notes drafted |

### 一段式摘要

World Bank Open Data 和 World Development Indicators 为本项目提供广泛的宏观经济、R&D、能源和排放预测变量候选项。该来源对 data provenance 很重要，但不是理论论证来源：它告诉我们变量来自哪里以及如何测量，而不是说明这些变量是否应预测 environmental innovation。本地探索已经显示出重要权衡。宏观和能源变量覆盖较广，而 R&D expenditure 和 researchers per million 覆盖更薄，但理论上更强。因此，这篇笔记应作为数据来源说明使用，预测变量依据应来自实证文献。

### 为什么这个来源相关

- 预测变量选择。
- 数据来源选择。
- 模型结果解释。
- 局限或注意事项。

### 数据与测量提取

| 项目 | 来源使用 / 说明的内容 | 对本项目的相关性 |
|---|---|---|
| 创新结果 | 不是专利结果来源。 | 目标仍然是 OECD patents。 |
| 专利定义或技术类别 | 不适用。 | 不提供目标变量指导。 |
| 预测变量 | GDP per capita、GDP、population、manufacturing share、R&D expenditure、researchers、renewable share、fossil share、energy intensity、CO2 per capita。 | 候选非政策预测变量的主要公共来源。 |
| 政策变量 | 对本项目当前设计来说有限。 | EPS 和 RISE 是单独来源。 |
| R&D / 创新能力变量 | R&D expenditure as percent of GDP 和 researchers per million people。 | 理论上强的候选预测变量，但覆盖更薄。 |
| 能源或排放变量 | Renewable energy share、fossil energy share、energy intensity、CO2 per capita。 | 有用的 energy-system proxies，但理论解释是混合的。 |
| 宏观控制变量 | GDP per capita、GDP、population、manufacturing share。 | 对 development、size 和 structure controls 有用。 |
| 分析单位 | Country-year indicators。 | 与项目面板一致。 |
| 国家 / 地区 | 覆盖全球范围较广，但因指标而异。 | 如果 EPS 或 R&D 约束不具约束性，有助于保持较大样本。 |
| 年份 | 本地探索请求了 1990-2024，覆盖范围因指标而异。 | 部分能源和排放变量较早结束。 |
| 滞后结构 | 数据来源未指定。 | 应用项目滞后规则，通常为 `t-1`。 |
| 数据来源 | World Bank Open Data / WDI，以及部分指标的 ESG source。 | 必须在 `2_data/data_dictionary.md` 中记录确切 indicator codes。 |
| 变换 | 对规模和收入变量取 logs；对百分比变量进行标准化或直接使用 shares。 | 最终变量选择后应记录变换。 |

### 预测变量选择的关键发现

1. WDI 是构建 broad country-year predictor panel 的实用来源。
2. R&D 和 researchers 等理论较强的变量可能显著减少样本量。
3. Energy 和 emissions variables 可获得，但需要谨慎解释，因为它们是 proxies，不是直接的 policy 或 price incentives。

### 对我们模型的预测变量含义

| 候选预测变量概念 | 是否支持？ | 预期符号 | 来源证据 | 注意事项 |
|---|---|---|---|---|
| GDP per capita / income level | 是 | 正向 | WDI 提供可比的 GDP per capita data。 | 数据可得性不是理论；机制应引用实证文献。 |
| R&D expenditure | 是 | 正向 | WDI 提供 R&D expenditure as percent of GDP。 | 覆盖比宏观变量更薄。 |
| Researchers / human capital | 是 | 正向 | WDI 提供 researchers per million。 | 覆盖更薄，且可能与 R&D expenditure 重叠。 |
| Renewable energy share | 是 | 正向 | WDI 提供 renewable energy share。 | 文献通常使用 renewable policy 或 capacity，而不是 final-energy share。 |
| Fossil energy share | 是 | 不明确 | WDI 提供 fossil energy share。 | 可能表示 transition pressure 或 fossil lock-in。 |
| Energy intensity | 是 | 不明确 | WDI 提供 energy intensity。 | 不等同于 energy prices。 |
| CO2 emissions per capita | 是 | 不明确 | WDI / World Bank source 提供 CO2 per capita。 | Emissions 可能反映 scale 和 structure，而不是 innovation incentive。 |
| Environmental policy stringency | 未讨论 | 正向 | WDI 不是当前 EPS 来源。 | 使用 OECD EPS。 |
| Other useful predictor | 是 | 不明确 | Manufacturing share 和 population 可获得。 | 如果使用标准化专利目标，避免冗余规模控制。 |

### 优势

1. 覆盖广、公开、可复现的数据来源。
2. Country-year 格式与建模数据集一致。
3. 从一个来源提供许多候选预测变量，降低 merge complexity。

### 局限

1. 数据覆盖局限：不同指标覆盖差异明显，尤其是 R&D 和 researchers。
2. 测量局限：WDI proxies 是一般国家指标，不是 green-specific innovation inputs。
3. 识别或解释局限：该来源是数据文档，不是经验证据。
4. 可迁移性局限：部分指标在不同国家和年份的报告质量可能不一致。

### 本项目应如何使用这个来源

`Core`：将其用于 data provenance，而不是作为 expected signs 的文献证据。报告应引用 empirical papers 说明 predictor logic，并引用 WDI 说明 variable definitions 和 data access。评审很可能接受 WDI 作为数据来源，但不会接受它作为某个预测变量应进入模型的证明。

### 可提取到报告中的文本

1. World Bank indicators 为宏观经济发展、R&D capacity、energy structure 和 emissions 的 broad country-year predictors 提供了可复现来源。
2. 最终 predictor list 应在理论强度和 WDI coverage 之间取得平衡，尤其是 R&D-related variables。

### 阅读后的开放问题

1. 哪些 WDI variables 同时通过 literature screen 和 coverage screen？
2. 模型应同时使用 R&D expenditure 和 researchers，还是选择其中一个以避免 overlapping capacity measures？
