# Measuring Environmental Innovation Using Patent Data

## Bibliographic Metadata

| Field | Value |
|---|---|
| Review ID | L002 |
| Full citation | Hascic, I. and M. Migotto (2015), `Measuring environmental innovation using patent data`, OECD Environment Working Papers, No. 89, OECD Publishing. |
| Authors / organization | Ivan Hascic and Mauro Migotto / OECD |
| Year | 2015 |
| Title | Measuring environmental innovation using patent data |
| Source type | Working paper / methodological source |
| DOI / URL | https://doi.org/10.1787/5js009kf48xw-en |
| PDF path or access note | `1_literature_review/pdfs/2015_hascic_measuring-environmental-innovation_access.md` |
| Note author | Codex |
| Last updated | 2026-05-18 |
| Review status | Notes drafted |

## One-Paragraph Summary

This OECD working paper explains how patent data can be used to measure environmental innovation and why patent-based indicators require careful interpretation. It discusses technology development, collaboration, and diffusion indicators across environmental technology domains, with patent classification and value-filtering choices at the center of the measurement problem. It supports the use of environment-related patent indicators when the research question is about technological invention rather than adoption or emissions outcomes. It also warns that not all innovation is patented and that patent counts are affected by patenting propensity, classification choices, country size, and institutional differences. For a reviewer, this source is central because it makes the target-variable choice defensible and keeps the report from overstating what patents measure.

## Why This Source Is Relevant

- Target-variable choice.
- Data-source choice.
- Interpretation of model results.
- Limitation or caution.

## Data and Measurement Extraction

| Item | What the source uses / says | Relevance for our project |
|---|---|---|
| Innovation outcome | Patent-based environmental innovation indicators. | Directly supports using OECD environment-related patent indicators as the target. |
| Patent definition or technology class | Environmental technology classes identified through patent classification systems such as IPC/CPC search strategies. | Helps justify why the OECD target is a technology measure, not a generic patent count. |
| Predictor variables | Not the focus. | Does not justify the predictor set directly. |
| Policy variables | Discussed mainly as context for environmental innovation measurement. | Use empirical policy papers for expected signs. |
| R&D / innovation-capacity variables | Not central. | R&D is a predictor from other literature, not from this source. |
| Energy or emissions variables | Environmental technology categories can include energy and climate-related inventions. | Supports interpreting the target as broad environment-related technology, not only renewable energy. |
| Macro controls | Not central. | No direct guidance for GDP or population predictors. |
| Unit of analysis | Patent indicators can be aggregated by country, year, and technology domain; inventor country, priority date, and fractional counts are important construction choices. | Compatible with the project country-year panel and lag design. |
| Countries / regions | OECD patent indicators are designed for cross-country comparison. | Supports comparability, with caveats. |
| Years | Depends on patent data availability and indicator extraction. | Use local data dictionary for exact project coverage. |
| Lag structure | Not an empirical lag study. | Does not determine predictor lag length. |
| Data sources | OECD patent data and patent classification metadata. | Companion source for OECD Data Explorer target extraction. |
| Transformations | Patent counts, shares, technology shares, normalized indicators, and value filters such as family-size filters may be used. | Supports normalized targets but requires exact unit and filter interpretation. |

## Key Findings for Predictor Selection

1. Patent data are suitable for measuring invention output but not for measuring adoption, diffusion, or environmental performance directly.
2. Priority date and inventor-country attribution are important because they better align patent data with the timing and location of inventive activity.
3. Cross-country patent comparisons require normalization or controls because raw counts reflect country size and patenting propensity.
4. Technology classification is central; a broad environmental patent target may combine heterogeneous subdomains with different drivers.

## Predictor Implications for Our Model

| Candidate predictor concept | Supported? | Expected sign | Evidence from source | Caveat |
|---|---|---|---|---|
| GDP per capita / income level | Mixed | Positive | The measurement discussion implies country innovation capacity matters for patent output. | This is an inference, not an estimated relationship in this source. |
| R&D expenditure | Mixed | Positive | Patents are invention outputs plausibly linked to R&D capacity. | The source does not test WDI R&D as a predictor. |
| Researchers / human capital | Mixed | Positive | Innovation-capacity logic is consistent with patenting. | No direct coefficient or model evidence. |
| Renewable energy share | Not discussed | Ambiguous | Environmental technology classes may include renewable energy. | Target classification is not evidence for renewable share as predictor. |
| Fossil energy share | Not discussed | Ambiguous | No direct evidence. | Use energy-system literature. |
| Energy intensity | Not discussed | Ambiguous | No direct evidence. | Use induced-innovation or energy-price literature. |
| CO2 emissions per capita | Not discussed | Ambiguous | No direct evidence. | Emissions are not equivalent to environmental innovation demand. |
| Environmental policy stringency | Mixed | Positive | Environmental innovation is policy-relevant, but no predictor estimate is provided. | Use EPS and empirical policy papers for modeling justification. |
| Other useful predictor | Yes | Ambiguous | Overall patenting capacity or total invention output matters for normalization. | Avoid adding redundant size variables if the target is already a share. |

## Strengths

1. Directly aligned with the project's target-measurement problem.
2. Written by OECD authors close to the indicator construction and taxonomy.
3. Gives useful caveats about patent-based environmental innovation measures.

## Limitations

1. Data coverage limitations: It is methodological and does not define the exact final project panel.
2. Measurement limitations: Patent data miss non-patented innovation and adoption.
3. Identification or interpretation limitations: It does not estimate predictor effects.
4. Transferability limitations: The report must connect this source to the exact OECD indicator code used locally.

## How We Should Use This Source

`Core`: Use this as the main methodological defense for patent-based target construction. It should be cited when explaining why `env_patent_share_inventions` is preferable to raw counts and why `env_patents_per_million` is a useful robustness target. It should also be used to acknowledge patent-measurement limits.

## Extractable Text for Report

1. Patent indicators measure invention output and are appropriate for studying environment-related technological innovation, but they do not measure adoption or actual environmental performance.
2. Normalization is important because raw patent counts mix innovation intensity with country size and general patenting capacity.

## Open Questions After Reading

1. Which exact OECD environmental technology taxonomy version is used in the current Data Explorer release?
2. Do the current project target series use PF2/high-value inventions or another OECD value filter?

## Chinese Translation

### 书目信息

| 字段 | 值 |
|---|---|
| 审阅 ID | L002 |
| 完整引用 | Hascic, I. and M. Migotto (2015), `Measuring environmental innovation using patent data`, OECD Environment Working Papers, No. 89, OECD Publishing. |
| 作者 / 机构 | Ivan Hascic and Mauro Migotto / OECD |
| 年份 | 2015 |
| 标题 | Measuring environmental innovation using patent data |
| 来源类型 | 工作论文 / 方法来源 |
| DOI / URL | https://doi.org/10.1787/5js009kf48xw-en |
| PDF 路径或访问说明 | `1_literature_review/pdfs/2015_hascic_measuring-environmental-innovation_access.md` |
| 笔记作者 | Codex |
| 最后更新 | 2026-05-18 |
| 审阅状态 | Notes drafted |

### 一段式摘要

这篇 OECD 工作论文解释了如何使用 patent data 衡量 environmental innovation，以及为什么 patent-based indicators 需要谨慎解释。它讨论环境技术领域中的技术开发、合作和扩散指标，并把 patent classification 和 value-filtering choices 置于测量问题的中心。当研究问题关注 technological invention 而不是 adoption 或 emissions outcomes 时，它支持使用 environment-related patent indicators。它也提醒读者，并非所有创新都会被申请专利，patent counts 会受到 patenting propensity、classification choices、country size 和 institutional differences 的影响。对评审而言，该来源很关键，因为它使目标变量选择更可辩护，并避免报告夸大专利所能衡量的内容。

### 为什么这个来源相关

- 目标变量选择。
- 数据来源选择。
- 模型结果解释。
- 局限或注意事项。

### 数据与测量提取

| 项目 | 来源使用 / 说明的内容 | 对本项目的相关性 |
|---|---|---|
| 创新结果 | Patent-based environmental innovation indicators。 | 直接支持使用 OECD environment-related patent indicators 作为目标变量。 |
| 专利定义或技术类别 | 通过 IPC/CPC search strategies 等专利分类系统识别的 environmental technology classes。 | 有助于说明 OECD 目标是技术度量，而不是普通专利计数。 |
| 预测变量 | 不是重点。 | 不直接论证预测变量集合。 |
| 政策变量 | 主要作为 environmental innovation measurement 的背景来讨论。 | 预期符号应使用实证政策论文。 |
| R&D / 创新能力变量 | 不是中心内容。 | R&D 是来自其他文献的预测变量，不来自该来源。 |
| 能源或排放变量 | Environmental technology categories 可以包括 energy 和 climate-related inventions。 | 支持将目标解释为广义环境相关技术，而不仅是可再生能源。 |
| 宏观控制变量 | 不是中心内容。 | 不直接指导 GDP 或 population 预测变量。 |
| 分析单位 | 专利指标可按 country、year 和 technology domain 聚合；inventor country、priority date 和 fractional counts 是重要的构造选择。 | 与项目的 country-year 面板和滞后设计兼容。 |
| 国家 / 地区 | OECD patent indicators 旨在用于跨国比较。 | 在有 caveats 的前提下支持可比性。 |
| 年份 | 取决于专利数据可得性和指标提取。 | 使用本地 data dictionary 确定项目的确切覆盖范围。 |
| 滞后结构 | 不是实证滞后研究。 | 不决定预测变量的滞后长度。 |
| 数据来源 | OECD patent data 和 patent classification metadata。 | OECD Data Explorer 目标提取的配套来源。 |
| 变换 | 可以使用 patent counts、shares、technology shares、normalized indicators，以及 family-size filters 等 value filters。 | 支持标准化目标，但需要准确解释 unit 和 filter。 |

### 预测变量选择的关键发现

1. Patent data 适合衡量 invention output，但不适合直接衡量 adoption、diffusion 或 environmental performance。
2. Priority date 和 inventor-country attribution 很重要，因为它们能更好地把专利数据与发明活动的时间和地点对应起来。
3. 跨国专利比较需要标准化或控制变量，因为 raw counts 反映 country size 和 patenting propensity。
4. 技术分类是核心问题；宽泛的环境专利目标可能合并具有不同驱动因素的异质子领域。

### 对我们模型的预测变量含义

| 候选预测变量概念 | 是否支持？ | 预期符号 | 来源证据 | 注意事项 |
|---|---|---|---|---|
| GDP per capita / income level | 混合 | 正向 | 测量讨论暗示国家创新能力会影响 patent output。 | 这是推论，不是该来源估计出的关系。 |
| R&D expenditure | 混合 | 正向 | Patents 是 invention outputs，合理上与 R&D capacity 相关。 | 该来源没有检验 WDI R&D 作为预测变量。 |
| Researchers / human capital | 混合 | 正向 | 创新能力逻辑与 patenting 一致。 | 没有直接系数或模型证据。 |
| Renewable energy share | 未讨论 | 不明确 | Environmental technology classes 可能包括 renewable energy。 | 目标分类不是 renewable share 作为预测变量的证据。 |
| Fossil energy share | 未讨论 | 不明确 | 没有直接证据。 | 使用 energy-system literature。 |
| Energy intensity | 未讨论 | 不明确 | 没有直接证据。 | 使用 induced-innovation 或 energy-price literature。 |
| CO2 emissions per capita | 未讨论 | 不明确 | 没有直接证据。 | Emissions 不等同于 environmental innovation demand。 |
| Environmental policy stringency | 混合 | 正向 | Environmental innovation 与政策相关，但没有提供预测变量估计。 | 使用 EPS 和实证政策论文进行建模论证。 |
| Other useful predictor | 是 | 不明确 | Overall patenting capacity 或 total invention output 对标准化很重要。 | 如果目标已经是 share，避免加入冗余的 size variables。 |

### 优势

1. 与本项目的目标测量问题直接对齐。
2. 作者是接近指标构造和 taxonomy 的 OECD 作者。
3. 对基于专利的环境创新度量给出有用 caveats。

### 局限

1. 数据覆盖局限：该文是方法论文，不定义确切的最终项目面板。
2. 测量局限：Patent data 会遗漏 non-patented innovation 和 adoption。
3. 识别或解释局限：它不估计预测变量效应。
4. 可迁移性局限：报告必须把该来源与本地使用的确切 OECD indicator code 连接起来。

### 本项目应如何使用这个来源

`Core`：将其作为基于专利构造目标变量的主要方法依据。解释为什么 `env_patent_share_inventions` 优于 raw counts，以及为什么 `env_patents_per_million` 是有用的 robustness target 时应引用该来源。它也应被用于承认 patent-measurement limits。

### 可提取到报告中的文本

1. 专利指标衡量 invention output，适合用于研究 environment-related technological innovation，但它们不衡量 adoption 或实际 environmental performance。
2. 标准化很重要，因为 raw patent counts 会把 innovation intensity 与 country size 和 general patenting capacity 混在一起。

### 阅读后的开放问题

1. 当前 Data Explorer release 使用哪一个确切的 OECD environmental technology taxonomy version？
2. 当前项目目标 series 是否使用 PF2/high-value inventions，还是使用另一种 OECD value filter？
