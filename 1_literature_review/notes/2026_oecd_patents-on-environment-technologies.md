# OECD Patents on Environment Technologies

## Bibliographic Metadata

| Field | Value |
|---|---|
| Review ID | L001 |
| Full citation | OECD (2026), `Patents on environment technologies`, OECD Data indicator page and Patents - indicators dataset, accessed 2026-05-18. |
| Authors / organization | OECD |
| Year | 2026 |
| Title | Patents on environment technologies |
| Source type | Data documentation |
| DOI / URL | https://www.oecd.org/en/data/indicators/patents-on-environment-technologies.html |
| PDF path or access note | `1_literature_review/pdfs/2026_oecd_patents-on-environment-technologies_access.md` |
| Note author | Codex |
| Last updated | 2026-05-18 |
| Review status | Notes drafted |

## One-Paragraph Summary

This OECD data source is the closest match to the project's intended outcome because it defines environment-related innovation through patent indicators. The public indicator describes the measure as the share of environment-related inventions in all domestic inventions, covering domains such as environmental management, water-related adaptation, and climate-change mitigation, and focusing on higher-value inventions. It provides public metadata and data access for environment-related technologies, including percentage indicators and intensity indicators that can be mapped to the project's three target candidates. For this project, the most important distinction is between the OECD measure based on percentage of inventions and the measure based on percentage of technologies, because those labels affect interpretability. The source is not an empirical study of determinants, so it cannot justify predictors by itself.

## Why This Source Is Relevant

- Target-variable choice.
- Data-source choice.
- Interpretation of model results.
- Limitation or caution.

## Data and Measurement Extraction

| Item | What the source uses / says | Relevance for our project |
|---|---|---|
| Innovation outcome | Environment-related inventions as a share of all domestic inventions, plus related OECD patent indicators. | Direct source for the dependent variable; supports `env_patent_share_inventions` most directly. |
| Patent definition or technology class | Environment-related technology domains and higher-value inventions in OECD patent data. | Requires companion methodology sources for detailed taxonomy, value filters, and caveats. |
| Predictor variables | Not applicable. | Does not support predictor selection directly. |
| Policy variables | Not applicable. | Use OECD EPS and empirical policy papers for policy predictors. |
| R&D / innovation-capacity variables | Not applicable. | OECD patent data may contain patent normalization options, but it is not an R&D source for this project. |
| Energy or emissions variables | Not applicable. | Technology domains may include energy-related environmental technologies, but this is target-side classification. |
| Macro controls | Not applicable. | Use WDI or OECD macro data separately. |
| Unit of analysis | Country-year indicator values. | Matches the planned panel structure. |
| Countries / regions | OECD data include broad country coverage; local exploration found 196-202 countries depending on target candidate. | Good target coverage relative to most predictor sources. |
| Years | Local exploration found 1990-2023 coverage for the main target candidates. | Fits the project horizon, but predictors may shorten the usable panel. |
| Lag structure | Not applicable. | Target should remain at outcome year `t`; predictors should be lagged. |
| Data sources | OECD Patents - indicators / OECD Data Explorer. | Official source for raw target extraction. |
| Transformations | Percentage of inventions, percentage of technologies, and inventions per population options. | `env_patent_share_inventions` is currently the most defensible main target candidate; `env_patents_per_million` is a robustness option. |

## Key Findings for Predictor Selection

1. The source does not test predictors, so it should not be cited as evidence that R&D, policy, or energy variables predict innovation.
2. It supports using a normalized patent outcome rather than a raw patent count when cross-country comparability is central.
3. It complicates target choice because OECD percentage labels differ; the project must not treat percentage of inventions and percentage of technologies as equivalent.

## Predictor Implications for Our Model

| Candidate predictor concept | Supported? | Expected sign | Evidence from source | Caveat |
|---|---|---|---|---|
| GDP per capita / income level | Not discussed | Ambiguous | No predictor analysis. | Use empirical studies for this. |
| R&D expenditure | Not discussed | Ambiguous | No predictor analysis. | Target data only. |
| Researchers / human capital | Not discussed | Ambiguous | No predictor analysis. | Target data only. |
| Renewable energy share | Not discussed | Ambiguous | No predictor analysis. | Technology domains are not predictor variables. |
| Fossil energy share | Not discussed | Ambiguous | No predictor analysis. | No evidence. |
| Energy intensity | Not discussed | Ambiguous | No predictor analysis. | No evidence. |
| CO2 emissions per capita | Not discussed | Ambiguous | No predictor analysis. | No evidence. |
| Environmental policy stringency | Not discussed | Ambiguous | No predictor analysis. | Use EPS documentation and policy papers. |
| Other useful predictor | Not discussed | Ambiguous | No predictor analysis. | None. |

## Strengths

1. Directly matches the assigned project outcome domain.
2. Provides official, reproducible target-variable metadata and public data access.
3. Offers normalized outcome options that are more comparable across countries than raw patent counts.

## Limitations

1. Data coverage limitations: Target coverage is broad, but the final modeling panel will be constrained by predictor coverage.
2. Measurement limitations: Patent indicators capture patentable inventions, not all environmental innovation.
3. Identification or interpretation limitations: This is a data source, not causal or predictive evidence.
4. Transferability limitations: OECD metadata must be interpreted with the exact indicator code used in the local dataset.

## How We Should Use This Source

`Core`: Use this as the official target-variable source. It should be cited when defining the dependent variable and explaining why the project uses OECD environment-related patent indicators. It should not be used to justify any predictor.

## Extractable Text for Report

1. The project measures environment-related innovation with official OECD patent indicators, which makes the outcome reproducible at the country-year level.
2. Because OECD provides several normalized patent indicators, the report must define the selected target by its exact indicator code and unit.

## Open Questions After Reading

1. Does the downloaded `PT_INV.DEV.ENV_PAT._Z` series exactly match the public indicator definition on the current OECD page?
2. What OECD family-size or value threshold is used for "higher-value inventions" in the current Data Explorer release?

## Chinese Translation

### 书目信息

| 字段 | 值 |
|---|---|
| 审阅 ID | L001 |
| 完整引用 | OECD (2026), `Patents on environment technologies`, OECD Data indicator page and Patents - indicators dataset, accessed 2026-05-18. |
| 作者 / 机构 | OECD |
| 年份 | 2026 |
| 标题 | Patents on environment technologies |
| 来源类型 | 数据文档 |
| DOI / URL | https://www.oecd.org/en/data/indicators/patents-on-environment-technologies.html |
| PDF 路径或访问说明 | `1_literature_review/pdfs/2026_oecd_patents-on-environment-technologies_access.md` |
| 笔记作者 | Codex |
| 最后更新 | 2026-05-18 |
| 审阅状态 | Notes drafted |

### 一段式摘要

该 OECD 数据来源最接近本项目预期的结果变量，因为它通过专利指标定义 environment-related innovation。公共指标将该度量描述为环境相关发明在全部国内发明中的占比，覆盖 environmental management、water-related adaptation 和 climate-change mitigation 等领域，并聚焦于 higher-value inventions。它为环境相关技术提供公开元数据和数据访问，包括 percentage indicators 和 intensity indicators，可映射到本项目的三个目标候选变量。对本项目而言，最重要的区别是基于 percentage of inventions 的 OECD 度量与基于 percentage of technologies 的度量之间的区别，因为这些标签会影响可解释性。该来源不是关于决定因素的实证研究，因此不能单独为预测变量提供依据。

### 为什么这个来源相关

- 目标变量选择。
- 数据来源选择。
- 模型结果解释。
- 局限或注意事项。

### 数据与测量提取

| 项目 | 来源使用 / 说明的内容 | 对本项目的相关性 |
|---|---|---|
| 创新结果 | Environment-related inventions as a share of all domestic inventions，以及相关 OECD patent indicators。 | 因变量的直接来源；最直接支持 `env_patent_share_inventions`。 |
| 专利定义或技术类别 | OECD patent data 中的 environment-related technology domains 和 higher-value inventions。 | 需要配套方法来源来说明详细 taxonomy、value filters 和 caveats。 |
| 预测变量 | 不适用。 | 不直接支持预测变量选择。 |
| 政策变量 | 不适用。 | 政策预测变量应使用 OECD EPS 和实证政策论文。 |
| R&D / 创新能力变量 | 不适用。 | OECD patent data 可能包含专利标准化选项，但它不是本项目的 R&D 来源。 |
| 能源或排放变量 | 不适用。 | 技术领域可能包括能源相关环境技术，但这是目标侧分类。 |
| 宏观控制变量 | 不适用。 | WDI 或 OECD macro data 应单独使用。 |
| 分析单位 | Country-year indicator values。 | 与计划中的面板结构一致。 |
| 国家 / 地区 | OECD data 覆盖范围较广；本地探索显示，不同目标候选变量覆盖 196-202 个国家。 | 相对于大多数预测变量来源，目标覆盖较好。 |
| 年份 | 本地探索显示，主要目标候选变量覆盖 1990-2023。 | 符合项目时间范围，但预测变量可能缩短可用面板。 |
| 滞后结构 | 不适用。 | 目标应保持在结果年份 `t`；预测变量应进行滞后处理。 |
| 数据来源 | OECD Patents - indicators / OECD Data Explorer。 | 原始目标提取的官方来源。 |
| 变换 | Percentage of inventions、percentage of technologies 和 inventions per population 选项。 | `env_patent_share_inventions` 目前是最可辩护的主目标候选变量；`env_patents_per_million` 可作为稳健性选项。 |

### 预测变量选择的关键发现

1. 该来源不检验预测变量，因此不应被引用为 R&D、policy 或 energy variables 预测创新的证据。
2. 当跨国可比性是核心问题时，它支持使用标准化专利结果，而不是 raw patent count。
3. 它使目标选择更复杂，因为 OECD 的 percentage 标签不同；项目不能把 percentage of inventions 和 percentage of technologies 当作等价概念。

### 对我们模型的预测变量含义

| 候选预测变量概念 | 是否支持？ | 预期符号 | 来源证据 | 注意事项 |
|---|---|---|---|---|
| GDP per capita / income level | 未讨论 | 不明确 | 没有 predictor analysis。 | 应使用实证研究支持。 |
| R&D expenditure | 未讨论 | 不明确 | 没有 predictor analysis。 | 该来源只提供目标数据。 |
| Researchers / human capital | 未讨论 | 不明确 | 没有 predictor analysis。 | 该来源只提供目标数据。 |
| Renewable energy share | 未讨论 | 不明确 | 没有 predictor analysis。 | 技术领域不是预测变量。 |
| Fossil energy share | 未讨论 | 不明确 | 没有直接证据。 | 没有证据。 |
| Energy intensity | 未讨论 | 不明确 | 没有直接证据。 | 没有证据。 |
| CO2 emissions per capita | 未讨论 | 不明确 | 没有 predictor analysis。 | 没有证据。 |
| Environmental policy stringency | 未讨论 | 不明确 | 没有 predictor analysis。 | 使用 EPS documentation 和政策论文。 |
| Other useful predictor | 未讨论 | 不明确 | 没有 predictor analysis。 | 无。 |

### 优势

1. 与指定项目结果域直接匹配。
2. 提供官方、可复现的目标变量元数据和公开数据访问。
3. 提供比原始专利数更适合跨国比较的标准化结果选项。

### 局限

1. 数据覆盖局限：目标覆盖较广，但最终建模面板会受到预测变量覆盖限制。
2. 测量局限：专利指标捕捉的是可专利化发明，而不是全部环境创新。
3. 识别或解释局限：这是数据来源，不是因果或预测证据。
4. 可迁移性局限：OECD 元数据必须结合本地数据集中使用的确切 indicator code 来解释。

### 本项目应如何使用这个来源

`Core`：将其作为官方目标变量来源。定义 dependent variable 并解释项目为何使用 OECD environment-related patent indicators 时应引用该来源。不应使用它来论证任何 predictor。

### 可提取到报告中的文本

1. 本项目使用官方 OECD patent indicators 在 country-year 层面衡量 environment-related innovation，因此结果变量具有可复现性。
2. 由于 OECD 提供多个标准化专利指标，报告必须用确切的 indicator code 和 unit 定义所选目标。

### 阅读后的开放问题

1. 下载的 `PT_INV.DEV.ENV_PAT._Z` series 是否与当前 OECD 页面上的公共指标定义完全一致？
2. 当前 Data Explorer release 对 "higher-value inventions" 使用了什么 OECD family-size 或 value threshold？
