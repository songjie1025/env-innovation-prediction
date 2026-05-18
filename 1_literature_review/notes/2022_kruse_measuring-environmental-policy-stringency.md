# Measuring Environmental Policy Stringency in OECD Countries

## Bibliographic Metadata

| Field | Value |
|---|---|
| Review ID | L003 |
| Full citation | Kruse, T., A. Dechezlepretre, R. Saffar and L. Robert (2022), `Measuring environmental policy stringency in OECD countries: An update of the OECD composite EPS indicator`, OECD Economics Department Working Papers, No. 1703. |
| Authors / organization | Tobias Kruse, Antoine Dechezlepretre, Romain Saffar and Lucie Robert / OECD |
| Year | 2022 |
| Title | Measuring environmental policy stringency in OECD countries: An update of the OECD composite EPS indicator |
| Source type | Working paper / data documentation |
| DOI / URL | https://doi.org/10.1787/90ab82e8-en |
| PDF path or access note | `1_literature_review/pdfs/2022_kruse_measuring-environmental-policy-stringency_access.md` |
| Note author | Codex |
| Last updated | 2026-05-18 |
| Review status | Notes drafted |

## One-Paragraph Summary

This OECD working paper documents the updated Environmental Policy Stringency (EPS) indicator for 1990-2020. The EPS is a composite policy measure designed to capture the stringency of selected market-based, non-market-based, and technology-support environmental policy instruments, mainly around climate-change mitigation and air pollution. For this project, the source is important because `eps_index` is the strongest policy predictor candidate in the local data dictionary, but it also has a major coverage tradeoff: local exploration found only 40 countries and years 1990-2020. The source does not prove that EPS predicts patents by itself, but it provides the policy variable's construction logic and comparability rationale. Empirical patent-policy studies are needed to justify the expected positive relationship.

## Why This Source Is Relevant

- Predictor selection.
- Data-source choice.
- Lag structure.
- Interpretation of model results.
- Limitation or caution.

## Data and Measurement Extraction

| Item | What the source uses / says | Relevance for our project |
|---|---|---|
| Innovation outcome | Not an innovation outcome source. | Pair with patent studies when using EPS to predict environment-related patents. |
| Patent definition or technology class | Not applicable. | No target-variable guidance. |
| Predictor variables | Composite environmental policy stringency. | Directly supports `eps_index` as a candidate predictor. |
| Policy variables | Composite EPS and subindices for market-based, non-market-based, and technology-support policies; raw instruments are scored on a 0-6 scale. | Main policy predictor candidate. |
| R&D / innovation-capacity variables | Not central. | No R&D predictor evidence. |
| Energy or emissions variables | Policy instruments may relate to energy and emissions. | Do not replace energy-system variables. |
| Macro controls | Not central. | No direct GDP guidance. |
| Unit of analysis | Country-year policy index. | Matches project panel structure. |
| Countries / regions | 40 countries in the updated EPS source according to subagent screening. | Local data show a narrower sample than OECD patent target coverage. |
| Years | Local exploration found 1990-2020 for downloaded EPS data. | Shortens usable panel if used in the main model. |
| Lag structure | Policy effects on innovation are unlikely to be instantaneous. | Use at least `t-1`; consider longer lags as robustness if coverage allows. |
| Data sources | OECD EPS data and methodology, drawing on public, country-specific, and ministry data collection. | Official source for `eps_index`. |
| Transformations | Raw policy measures converted to 0-6 scores, then weighted into subindices and composite EPS; missing observations are partly imputed in the source construction. | Keep original scale documented and note imputation limits. |

## Key Findings for Predictor Selection

1. EPS is a defensible policy predictor because it is a structured cross-country policy index rather than an ad hoc regulation proxy.
2. EPS should be treated as sample-restricting: it may improve theory and interpretability while reducing country coverage.
3. EPS does not cover all environmental domains; it focuses mainly on climate-change and air-pollution policy instruments.
4. The source supports using lagged policy variables, but it does not by itself establish the patent response window.

## Predictor Implications for Our Model

| Candidate predictor concept | Supported? | Expected sign | Evidence from source | Caveat |
|---|---|---|---|---|
| GDP per capita / income level | Not discussed | Ambiguous | No macro predictor evidence. | EPS levels may correlate with income, so multicollinearity should be checked. |
| R&D expenditure | Not discussed | Ambiguous | No R&D predictor evidence. | Pair with innovation-capacity variables separately. |
| Researchers / human capital | Not discussed | Ambiguous | No direct evidence. | No guidance. |
| Renewable energy share | Mixed | Positive | EPS includes policy pressure that can affect energy-related innovation. | EPS is not the same as renewable adoption. |
| Fossil energy share | Not discussed | Ambiguous | No direct evidence. | Use energy-system data separately. |
| Energy intensity | Not discussed | Ambiguous | No direct evidence. | No guidance. |
| CO2 emissions per capita | Not discussed | Ambiguous | No direct evidence. | No guidance. |
| Environmental policy stringency | Yes | Positive | The source defines and updates the EPS indicator for cross-country policy stringency. | This is measurement support, not causal evidence. |
| Other useful predictor | Yes | Positive | Individual policy subcomponents may be useful if available. | A small course model should probably start with the aggregate EPS. |

## Strengths

1. Official OECD documentation for the exact policy index used in the project data.
2. Country-year format fits the planned modeling panel.
3. Transparent subindex structure helps separate market, non-market, and technology-support policies.

## Limitations

1. Data coverage limitations: EPS coverage is much narrower than the OECD patent target and WDI macro variables.
2. Measurement limitations: A composite index may hide differences between tax, market, standard, and technology-specific policies; it also excludes several environmental domains.
3. Identification or interpretation limitations: EPS construction does not identify causal effects on patents.
4. Transferability limitations: Use outside OECD-style countries may be limited by coverage and policy comparability.

## How We Should Use This Source

`Core`: Use this as the data-source justification for `eps_index`. The model should either include EPS in a narrower policy sample or compare a broad model without EPS against a policy-sample model with EPS. The report should clearly say that EPS is a policy-stringency measure, not proof that policy caused the modeled patent outcomes.

## Extractable Text for Report

1. The EPS index provides a structured, cross-country measure of environmental policy stringency and is therefore a defensible policy predictor.
2. Including EPS improves theoretical alignment but may reduce the modeling sample because its coverage is much narrower than the patent target coverage.

## Open Questions After Reading

1. Should the main model prioritize broad country coverage or include EPS as a core predictor in a smaller OECD-style sample?
2. Should the project use total EPS, or exclude technology-support components if general R&D expenditure is also included?

## Chinese Translation

### 书目信息

| 字段 | 值 |
|---|---|
| 审阅 ID | L003 |
| 完整引用 | Kruse, T., A. Dechezlepretre, R. Saffar and L. Robert (2022), `Measuring environmental policy stringency in OECD countries: An update of the OECD composite EPS indicator`, OECD Economics Department Working Papers, No. 1703. |
| 作者 / 机构 | Tobias Kruse, Antoine Dechezlepretre, Romain Saffar and Lucie Robert / OECD |
| 年份 | 2022 |
| 标题 | Measuring environmental policy stringency in OECD countries: An update of the OECD composite EPS indicator |
| 来源类型 | Working paper / data documentation |
| DOI / URL | https://doi.org/10.1787/90ab82e8-en |
| PDF 路径或访问说明 | `1_literature_review/pdfs/2022_kruse_measuring-environmental-policy-stringency_access.md` |
| 笔记作者 | Codex |
| 最后更新 | 2026-05-18 |
| 审阅状态 | Notes drafted |

### 一段式摘要

这篇 OECD working paper 记录了 1990-2020 年更新后的 Environmental Policy Stringency (EPS) indicator。EPS 是一种综合政策度量，旨在捕捉选定的 market-based、non-market-based 和 technology-support environmental policy instruments 的严格程度，主要围绕 climate-change mitigation 和 air pollution。对本项目而言，该来源很重要，因为 `eps_index` 是本地 data dictionary 中最强的政策预测变量候选，但它也存在重大的覆盖范围取舍：本地探索只发现 40 个国家和 1990-2020 年。该来源本身并不证明 EPS 能预测专利，但它提供了政策变量的构造逻辑和可比性理由。仍需要 empirical patent-policy studies 来证明预期的正向关系。

### 为什么这个来源相关

- 预测变量选择。
- 数据源选择。
- 滞后结构。
- 模型结果解释。
- 限制或谨慎说明。

### 数据与测量提取

| 项目 | 来源使用 / 说明的内容 | 对本项目的相关性 |
|---|---|---|
| 创新结果 | 不是创新结果来源。 | 使用 EPS 预测 environment-related patents 时，应与专利研究搭配。 |
| 专利定义或技术类别 | 不适用。 | 不提供目标变量指导。 |
| 预测变量 | Composite environmental policy stringency。 | 直接支持 `eps_index` 作为候选预测变量。 |
| 政策变量 | Composite EPS，以及 market-based、non-market-based 和 technology-support policies 的 subindices；原始工具按 0-6 scale 评分。 | 主要政策预测变量候选。 |
| R&D / 创新能力变量 | 不是核心内容。 | 不提供 R&D 预测变量证据。 |
| 能源或排放变量 | 政策工具可能与能源和排放相关。 | 不能替代 energy-system variables。 |
| 宏观控制变量 | 不是核心内容。 | 不提供直接的 GDP 指导。 |
| 分析单位 | Country-year policy index。 | 匹配项目的 panel structure。 |
| 国家 / 地区 | 根据 subagent screening，更新后的 EPS 来源覆盖 40 个国家。 | 本地数据样本比 OECD patent target coverage 更窄。 |
| 年份 | 本地探索发现下载的 EPS 数据覆盖 1990-2020 年。 | 如果在主模型中使用，会缩短可用 panel。 |
| 滞后结构 | 政策对创新的影响不太可能是即时的。 | 至少使用 `t-1`；如果覆盖范围允许，可考虑更长滞后作为稳健性检验。 |
| 数据来源 | OECD EPS data and methodology，基于 public、country-specific 和 ministry data collection。 | `eps_index` 的官方来源。 |
| 转换 | 原始政策度量被转换为 0-6 scores，然后加权形成 subindices 和 composite EPS；来源构造中对部分缺失观测进行了 imputation。 | 记录原始尺度，并注明 imputation 限制。 |

### 预测变量选择的关键发现

1. EPS 是一个有依据的政策预测变量，因为它是结构化的跨国政策指数，而不是临时的 regulation proxy。
2. EPS 应被视为会限制样本：它可能提升理论和可解释性，同时减少国家覆盖。
3. EPS 并不覆盖所有环境领域；它主要聚焦 climate-change 和 air-pollution policy instruments。
4. 该来源支持使用滞后政策变量，但本身并不确定专利响应窗口。

### 对我们模型的预测变量含义

| 候选预测变量概念 | 是否支持？ | 预期符号 | 来源证据 | 注意事项 |
|---|---|---|---|---|
| GDP per capita / income level | 未讨论 | 不明确 | 没有宏观预测变量证据。 | EPS 水平可能与 income 相关，因此应检查 multicollinearity。 |
| R&D expenditure | 未讨论 | 不明确 | 没有 R&D 预测变量证据。 | 应与 innovation-capacity variables 分开搭配。 |
| Researchers / human capital | 未讨论 | 不明确 | 没有直接证据。 | 无指导。 |
| Renewable energy share | 混合 | 正向 | EPS 包含可影响 energy-related innovation 的政策压力。 | EPS 不等同于 renewable adoption。 |
| Fossil energy share | 未讨论 | 不明确 | 没有直接证据。 | 单独使用 energy-system data。 |
| Energy intensity | 未讨论 | 不明确 | 没有直接证据。 | 无指导。 |
| CO2 emissions per capita | 未讨论 | 不明确 | 没有直接证据。 | 无指导。 |
| Environmental policy stringency | 是 | 正向 | 该来源定义并更新了用于跨国 policy stringency 的 EPS indicator。 | 这是测量支持，不是 causal evidence。 |
| Other useful predictor | 是 | 正向 | 如果可获得，单个 policy subcomponents 可能有用。 | 小型课程模型可能应从 aggregate EPS 开始。 |

### 优势

1. 官方 OECD 文档，说明项目数据中使用的确切政策指数。
2. Country-year 格式适合计划中的 modeling panel。
3. 透明的 subindex structure 有助于区分 market、non-market 和 technology-support policies。

### 局限

1. 数据覆盖限制：EPS 覆盖范围远窄于 OECD patent target 和 WDI macro variables。
2. 测量限制：综合指数可能掩盖 tax、market、standard 和 technology-specific policies 之间的差异；它还排除了若干环境领域。
3. 识别或解释限制：EPS 构造并不识别对专利的因果效应。
4. 可迁移性限制：在 OECD-style countries 之外使用可能受到覆盖范围和政策可比性的限制。

### 本项目应如何使用这个来源

`Core`：将其作为 `eps_index` 的数据源依据。模型应要么在较窄的政策样本中纳入 EPS，要么比较不含 EPS 的广泛模型与含 EPS 的政策样本模型。报告应清楚说明 EPS 是 policy-stringency measure，而不是政策导致所建模专利结果的证据。

### 可提取到报告中的文本

1. EPS index 提供了一个结构化的跨国 environmental policy stringency 度量，因此是有依据的政策预测变量。
2. 纳入 EPS 可以提高理论一致性，但可能减少建模样本，因为其覆盖范围远窄于专利目标覆盖。

### 阅读后的开放问题

1. 主模型应优先考虑广泛国家覆盖，还是将 EPS 作为较小 OECD-style 样本中的核心预测变量？
2. 项目应使用 total EPS，还是在同时纳入 general R&D expenditure 时排除 technology-support components？
