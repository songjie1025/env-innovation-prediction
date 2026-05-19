# The Impact of Energy Prices on Green Innovation

## Bibliographic Metadata

| Field | Value |
|---|---|
| Review ID | L012 |
| Full citation | Ley, M., Stucki, T., & Woerter, M. (2016). The impact of energy prices on green innovation. The Energy Journal, 37(1), 41-75. |
| Authors / organization | Marius Ley, Tobias Stucki, Martin Woerter (ETH Zurich / KOF) |
| Year | 2016 |
| Title | The impact of energy prices on green innovation |
| Source type | Journal article |
| DOI / URL | https://doi.org/10.5547/01956574.37.1.mley |
| PDF path or access note | PDF available via EconStor: https://www.econstor.eu/bitstream/10419/80816/1/756537436.pdf |
| Note author | Jie Song |
| Last updated | 2026-05-20 |
| Review status | Candidate |

## One-Paragraph Summary

Ley et al. (2016) investigate whether energy prices drive green innovation using industry-level panel data for 18 OECD countries over 1990-2010. They construct industry-specific energy price indices and match them with green patent counts from PATSTAT. The key finding is that higher energy prices significantly increase green patenting, with an elasticity of approximately 0.3-0.5 — a 10% increase in energy prices leads to a 3-5% increase in green patents. The effect is stronger in energy-intensive industries and for technologies closer to market maturity. This provides direct empirical support for the induced innovation hypothesis (Hicks 1932) applied to environmental technologies, and is one of the few studies using panel data with industry-level energy price variation rather than aggregate country-level proxies.

## Why This Source Is Relevant

- **Predictor selection:** Strongly supports using energy-price or energy-cost variables as predictors of green patenting
- **Lag structure:** Finds innovation response within 2-4 years of price changes
- **Interpretation of model results:** Provides a theoretical mechanism (induced innovation) for why energy variables predict green patenting
- **Limitation or caution:** Industry-level energy prices are not available in WDI; country-level proxies (energy intensity, fossil share) are weaker substitutes

## Data and Measurement Extraction

| Item | What the source uses / says | Relevance for our project |
|---|---|---|
| Innovation outcome | Green patent counts from PATSTAT, IPC-based classification | Same data source family as our OECD target |
| Patent definition or technology class | IPC Green Inventory + EPO Y02 classification | Aligned with OECD ENV-TECH |
| Predictor variables | Industry-specific energy prices, knowledge stock (patent citations), R&D expenditure | Energy prices not in WDI; need country-level proxy |
| Policy variables | Not directly used; price effects interpreted as market-driven innovation incentive | Complements our EPS/RISE policy variables |
| R&D / innovation-capacity variables | Knowledge stock (cumulative patent citations) as technology-push factor | Supports including lagged patent stock or R&D stock |
| Energy or emissions variables | Industry energy price index (core variable) | WDI renewable share and energy intensity are imperfect proxies |
| Macro controls | GDP, industry fixed effects, time trends | Standard controls |
| Unit of analysis | Industry-country-year (18 OECD countries, 1990-2010) | We use country-year |
| Years | 1990-2010 | Overlaps with our 1990-2023 panel |
| Lag structure | 2-4 year lags for price → patent response | Supports t-2 or t-3 lag for energy variables |
| Transformations | Log-log specification; knowledge stock as perpetual inventory of past patents | Log transform energy variables |

## Key Findings for Predictor Selection

1. Energy prices have a statistically significant positive effect on green patenting (elasticity 0.3-0.5). Supports including energy-cost or energy-transition variables.
2. The effect is stronger in energy-intensive industries — suggests interaction between industrial structure and energy predictors.
3. Both demand-pull (energy prices) and technology-push (knowledge stocks) matter independently. Supports including both R&D and energy variables, not just one.
4. The innovation response takes 2-4 years. Supports using lagged energy predictors (t-2 or t-3).

## Predictor Implications for Our Model

| Candidate predictor concept | Supported? | Expected sign | Evidence from source | Caveat |
|---|---|---|---|---|
| GDP per capita / income level | Mixed | Positive | Used as control; not a primary finding | Standard development control |
| R&D expenditure | Yes | Positive | Knowledge stock (cumulative patents) as technology-push factor | We have general R&D, not green R&D |
| Researchers / human capital | Not discussed | — | — | — |
| Renewable energy share | Indirectly | Positive | Renewable energy reduces fossil dependence → lower energy prices → less pressure? | Direction is complex; renewable share may proxy both transition and reduced pressure |
| Fossil energy share | Yes | Positive | Higher fossil dependence → higher energy cost exposure → more green innovation | But fossil share can also indicate lock-in |
| Energy intensity | Yes | Positive | More energy-intensive → more price exposure → more innovation incentive | WDI energy intensity is not equivalent to industry energy prices |
| CO2 emissions per capita | Not discussed | — | — | — |
| Environmental policy stringency | Not directly | Positive | Market prices and policy both matter; prices are the demand-pull channel | Our EPS variable captures the policy channel |
| Energy prices (new concept) | Strongly | Positive | Core finding: elasticity 0.3-0.5 | No WDI energy price variable at country level |

## Strengths

1. Uses industry-level energy price variation rather than aggregate country proxies — stronger identification than most cross-country studies.
2. Covers 18 OECD countries and 20 years — reasonable panel for generalization.
3. Clearly distinguishes demand-pull (energy prices) from technology-push (knowledge stocks) mechanisms.
4. Provides elasticity estimates useful for interpreting our model coefficients.

## Limitations

1. Industry-level energy prices are not available in WDI. We cannot replicate the exact variable.
2. Findings are for OECD countries only; generalizability to developing countries is uncertain.
3. Green patent classification uses IPC Green Inventory, which may differ slightly from OECD ENV-TECH.
4. No explicit policy variables; cannot compare price effects to regulatory effects within the same model.

## How We Should Use This Source

`Supporting` — Provides strong theoretical and empirical backing for including energy-related predictors (especially energy prices or intensity) in our model. The induced innovation mechanism helps interpret why energy variables matter. However, we cannot directly replicate the energy price variable, so we must use WDI proxies (energy intensity, renewable share, fossil share) with appropriate caveats.

## Extractable Text for Report

1. "Higher energy prices significantly increase green patenting, with an elasticity of approximately 0.3-0.5."
2. "Both demand-pull (energy prices) and technology-push (knowledge stocks) matter independently for green innovation."
3. "The induced innovation hypothesis (Hicks 1932) receives strong empirical support when energy prices are measured at the industry level."

## Open Questions After Reading

1. Can we construct a country-level energy price proxy from WDI variables (e.g., energy intensity × fossil share)?
2. Should we test an interaction between industrial structure (manufacturing share) and energy variables, as the industry-level results suggest?
3. Is the 2-4 year lag robust when using country-level rather than industry-level data?

---

## Chinese Translation

# 能源价格对绿色创新的影响

## 文献元数据

| 字段 | 值 |
|---|---|
| 审查编号 | L012 |
| 完整引用 | Ley, M., Stucki, T., & Woerter, M. (2016). The impact of energy prices on green innovation. The Energy Journal, 37(1), 41-75. |
| 作者/机构 | Marius Ley, Tobias Stucki, Martin Woerter (ETH Zurich / KOF) |
| 年份 | 2016 |
| 标题 | 能源价格对绿色创新的影响 |
| 来源类型 | 期刊论文 |
| DOI / URL | https://doi.org/10.5547/01956574.37.1.mley |
| PDF 路径或访问说明 | EconStor 可获取：https://www.econstor.eu/bitstream/10419/80816/1/756537436.pdf |
| 笔记作者 | Jie Song |
| 最后更新 | 2026-05-20 |
| 审查状态 | 候选 |

## 一段话总结

Ley 等人（2016）使用 18 个 OECD 国家 1990-2010 年的行业层面面板数据，研究了能源价格是否驱动绿色创新。他们构建了行业特定的能源价格指数，并将其与 PATSTAT 的绿色专利计数进行匹配。核心发现：更高的能源价格显著增加绿色专利产出，弹性约为 0.3-0.5——能源价格上涨 10% 导致绿色专利增加 3-5%。这一效应在能源密集型行业更强，且对接近市场成熟度的技术更为显著。这为应用于环境技术的引致创新假说（Hicks 1932）提供了直接的实证支持。

## 为什么此来源对本项目重要

- **预测因子选择：** 强烈支持使用能源价格或能源成本变量作为绿色专利的预测因子
- **滞后期结构：** 发现创新响应在价格变化后 2-4 年内出现
- **模型结果解读：** 为能源变量为何预测绿色专利提供了理论机制（引致创新）
- **局限性或注意事项：** 行业能源价格在 WDI 中不可用；国家级代理变量（能源强度、化石占比）是较弱的替代

## 数据和测量提取

| 项目 | 来源使用/说明的内容 | 对本项目的相关性 |
|---|---|---|
| 创新结果 | PATSTAT 绿色专利计数，基于 IPC 分类 | 与我们的 OECD 目标同一数据源家族 |
| 专利定义或技术类别 | IPC 绿色清单 + EPO Y02 分类 | 与 OECD ENV-TECH 一致 |
| 预测变量 | 行业特定能源价格、知识存量（专利引用）、R&D 支出 | WDI 中无能源价格变量；需国家级代理 |
| 政策变量 | 未直接使用；价格效应被解读为市场驱动的创新激励 | 补充我们的 EPS/RISE 政策变量 |
| 能源变量 | 行业能源价格指数（核心变量） | WDI 可再生能源占比和能源强度是不完美代理 |
| 分析单位 | 行业-国家-年份（18 个 OECD 国家，1990-2010） | 我们使用国家-年份 |
| 滞后期结构 | 价格→专利响应滞后 2-4 年 | 支持能源变量使用 t-2 或 t-3 滞后 |
| 变换方式 | 双对数设定；知识存量按永续盘存法计算 | 对能源变量取对数 |

## 预测因子选择的关键发现

1. 能源价格对绿色专利有统计显著的正效应（弹性 0.3-0.5）。支持纳入能源成本或能源转型变量。
2. 效应在能源密集型行业更强——表明产业结构和能源预测因子之间可能存在交互效应。
3. 需求拉动（能源价格）和技术推动（知识存量）均独立起作用。支持同时纳入 R&D 和能源变量。
4. 创新响应需要 2-4 年。支持使用滞后能源预测因子（t-2 或 t-3）。

## 对我们模型的预测因子启示

| 候选预测因子概念 | 是否支持？ | 预期方向 | 来源证据 | 注意事项 |
|---|---|---|---|---|
| GDP 人均/收入水平 | 混合 | 正向 | 作为控制变量使用；非主要发现 | 标准发展水平控制 |
| R&D 支出 | 是 | 正向 | 知识存量（累积专利）作为技术推动因子 | 我们的是通用 R&D，非绿色 R&D |
| 可再生能源占比 | 间接 | 正向 | 可再生能源降低化石依赖→更低能源价格→更少压力？ | 方向复杂；可再生占比可能同时代表转型和减压 |
| 化石能源占比 | 是 | 正向 | 更高化石依赖→更高能源成本暴露→更多绿色创新 | 但化石占比也可能表示锁定效应 |
| 能源强度 | 是 | 正向 | 更高能源密集度→更多价格暴露→更多创新激励 | WDI 能源强度不等同于行业能源价格 |
| 环境政策严格度 | 不直接 | 正向 | 市场价格和政策都重要；价格是需求拉动渠道 | 我们的 EPS 变量捕捉政策渠道 |
| 能源价格（新概念） | 强 | 正向 | 核心发现：弹性 0.3-0.5 | WDI 无国家级能源价格变量 |

## 优势

1. 使用行业层面而非国家级能源价格变异——比大多数跨国研究的识别更强。
2. 覆盖 18 个 OECD 国家和 20 年——合理的推广面板。
3. 清晰区分需求拉动（能源价格）和技术推动（知识存量）机制。
4. 提供了可用于解释我们模型系数的弹性估计。

## 局限性

1. 行业能源价格在 WDI 中不可得。我们无法精确复制此变量。
2. 发现仅适用于 OECD 国家；对发展中国家的推广性不确定。
3. 绿色专利分类基于 IPC 绿色清单，可能与 OECD ENV-TECH 略有差异。
4. 未包含明确政策变量；无法在同一模型内比较价格效应与监管效应。

## 我们应该如何使用此来源

`支持性` — 为在我们的模型中纳入能源相关预测因子（尤其是能源价格或能源强度）提供了强有力的理论和实证支持。引致创新机制有助于解释能源变量为何重要。但我们无法直接复制能源价格变量，必须使用 WDI 代理变量（能源强度、可再生能源占比、化石占比）并附上适当的局限性说明。

## 报告中可提取的文本

1. "更高的能源价格显著增加绿色专利产出，弹性约为 0.3-0.5。"
2. "需求拉动（能源价格）和技术推动（知识存量）均独立地对绿色创新起作用。"
3. "当能源价格在行业层面测量时，引致创新假说（Hicks 1932）获得了强有力的实证支持。"

## 阅读后的开放问题

1. 我们能否从 WDI 变量构建国家级能源价格代理（例如能源强度 × 化石占比）？
2. 是否应该检验产业结构（制造业占比）与能源变量之间的交互效应？
3. 当使用国家级而非行业级数据时，2-4 年滞后期是否仍然稳健？
