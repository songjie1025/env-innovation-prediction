# World Bank Data Requests With Code Notes

This guide explains the World Bank data request code used by this project. It is meant for collaborators who want to learn how the code works, not only what the workflow does.

The real implementation lives in `2_data/scripts/data_exploration.py`. The examples below are shortened from that script.

## The Goal

The project needs World Bank indicators as candidate predictors in a country-year panel. Each downloaded file should become a table with the same basic columns:

- `dataset_id`
- `variable`
- `source_variable`
- `country_code`
- `country_name`
- `year`
- `value`

That shared shape makes World Bank data easier to merge later with OECD patent and policy data.

## Why Use The API

The API makes the download reproducible. Instead of manually clicking around the World Bank website, the script records the exact indicator code, year range, response format, and optional source ID. That means another collaborator can rerun the same request later and check whether the source changed.

The API also returns metadata together with the data. The script saves useful fields such as `lastupdated` and `total`, which helps document when the World Bank source was last updated and how many records were returned.

## What The World Bank Data Looks Like

The World Bank JSON response is usually a list with two parts:

```python
payload[0]  # metadata about the request
payload[1]  # list of country-year records
```

A simplified record looks like this:

```python
{
    "countryiso3code": "DEU",
    "country": {"value": "Germany"},
    "date": "2020",
    "value": 42310.2,
}
```

The script turns these source fields into the project format: `countryiso3code` becomes `country_code`, `country.value` becomes `country_name`, `date` becomes `year`, and `value` stays as the numeric indicator value.

## 1. Store Indicator Choices In One Place

Source location: `2_data/scripts/data_exploration.py`, lines 86-128.

```python
WORLD_BANK_INDICATORS = {
    "gdp_per_capita": {
        "indicator": "NY.GDP.PCAP.KD",
        "description": "GDP per capita, constant 2015 US dollars.",
    },
    "rd_expenditure_gdp": {
        "indicator": "GB.XPD.RSDV.GD.ZS",
        "description": "Research and development expenditure as percent of GDP.",
    },
    "co2_per_capita": {
        "indicator": "EN.ATM.CO2E.PC",
        "description": "CO2 emissions per capita.",
        "source_id": 75,
    },
}
```

How to read this:

- `gdp_per_capita` is the project variable name. This is the name we want in our cleaned project tables.
- `NY.GDP.PCAP.KD` is the official World Bank indicator code.
- `description` is saved into metadata so a future reader knows what was requested.
- `source_id` is optional. Most variables do not need it, but CO2 uses source `75` in the current project.

Why this pattern is useful: new World Bank variables can be added by adding one small dictionary entry instead of changing the download logic.

## 2. Build The API URL

Source location: `2_data/scripts/data_exploration.py`, lines 38 and 432-441.

```python
WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2/country/all/indicator"


def world_bank_indicator_url(
    source_variable: str,
    start_year: int,
    end_year: int,
    source_id: int | None = None,
) -> str:
    url = (
        f"{WORLD_BANK_BASE_URL}/{source_variable}"
        f"?format=json&per_page=20000&date={start_year}:{end_year}"
    )
    if source_id is not None:
        url += f"&source={source_id}"
    return url
```

Key ideas:

- The base URL says: request data for all countries and one indicator.
- `source_variable` is the World Bank indicator code, such as `NY.GDP.PCAP.KD`.
- `format=json` asks for data in JSON format.
- `per_page=20000` asks for enough rows to fit the country-year result in one response.
- `date=1990:2024` controls the requested year range.
- `source_id` is optional. The `if` statement adds it only when needed.

Example result:

`https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.KD?format=json&per_page=20000&date=1990:2024`

## 3. Send The Request And Check It

Source location: `2_data/scripts/data_exploration.py`, lines 418-429.

```python
def fetch_world_bank_indicator(
    variable: str,
    source_variable: str,
    start_year: int,
    end_year: int,
    source_id: int | None = None,
) -> tuple[pd.DataFrame, dict]:
    url = world_bank_indicator_url(source_variable, start_year, end_year, source_id)
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError(f"Unexpected World Bank response for {source_variable}")
    metadata = payload[0]
    records = payload[1]
    return world_bank_records_to_frame(records, variable, source_variable), metadata
```

What each part does:

- `requests.get(...)` sends the API request.
- `timeout=90` prevents the script from waiting forever.
- `raise_for_status()` stops the script if the server returns an HTTP error.
- `response.json()` converts the JSON response into Python objects.
- World Bank responses usually contain two parts: metadata first, records second.
- The function returns two things: a cleaned DataFrame and a metadata dictionary.

The response check is important. If the API changes shape or returns an error message, the project should fail clearly instead of saving a broken file.

## 4. Turn World Bank Records Into Project Rows

Source location: `2_data/scripts/data_exploration.py`, lines 159-177.

```python
def world_bank_records_to_frame(
    records: Iterable[dict],
    variable: str,
    source_variable: str,
) -> pd.DataFrame:
    rows = []
    for record in records:
        rows.append(
            {
                "dataset_id": "world_bank_wdi",
                "variable": variable,
                "source_variable": source_variable,
                "country_code": record.get("countryiso3code"),
                "country_name": (record.get("country") or {}).get("value"),
                "year": int(record["date"]),
                "value": record.get("value"),
            }
        )
    frame = pd.DataFrame(rows)
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame
```

What this teaches:

- `rows = []` starts an empty list where each future table row will be stored.
- `for record in records:` loops through the API records one by one.
- `record.get(...)` safely reads a field from the World Bank record.
- `(record.get("country") or {}).get("value")` avoids crashing if the nested country field is missing.
- `int(record["date"])` turns the year into a number.
- `pd.DataFrame(rows)` turns the list of dictionaries into a table.
- `pd.to_numeric(..., errors="coerce")` converts values to numbers and turns invalid values into missing values.

That last line matters: missing data should stay missing. It should not become zero.

## 5. Loop Over All Indicators

Source location: `2_data/scripts/data_exploration.py`, lines 507-524.

```python
wb_metadata = {}
for variable, config in WORLD_BANK_INDICATORS.items():
    frame, metadata = fetch_world_bank_indicator(
        variable,
        config["indicator"],
        start_year,
        end_year,
        config.get("source_id"),
    )
    wb_metadata[variable] = {
        "indicator": config["indicator"],
        "description": config["description"],
        "source_id": config.get("source_id", 2),
        "lastupdated": metadata.get("lastupdated"),
        "total": metadata.get("total"),
    }
    raw_path = RAW_DIR / f"world_bank_{variable}_{config['indicator']}_{start_year}_{end_year}.csv"
    frame.to_csv(raw_path, index=False)
```

How to read the loop:

- `.items()` gives both the project variable name and its settings.
- `config["indicator"]` is required. If it is missing, the script should fail.
- `config.get("source_id")` is optional. If no source ID exists, Python returns `None`.
- `wb_metadata[variable] = ...` saves request metadata under the project variable name.
- `raw_path` builds a clear filename that records the variable, indicator code, and year range.
- `index=False` prevents pandas from writing an extra row-number column to the CSV.

This is the part students should recognize as automation: the same request-and-save logic runs once for every indicator in the dictionary.

## Indicators Currently Requested

| Project variable | World Bank indicator | Meaning |
|---|---|---|
| `gdp_per_capita` | `NY.GDP.PCAP.KD` | GDP per capita, constant 2015 US dollars |
| `gdp` | `NY.GDP.MKTP.KD` | GDP, constant 2015 US dollars |
| `population` | `SP.POP.TOTL` | Total population |
| `manufacturing_share` | `NV.IND.MANF.ZS` | Manufacturing value added as percent of GDP |
| `rd_expenditure_gdp` | `GB.XPD.RSDV.GD.ZS` | R&D expenditure as percent of GDP |
| `researchers_per_million` | `SP.POP.SCIE.RD.P6` | Researchers in R&D per million people |
| `renewable_energy_share` | `EG.FEC.RNEW.ZS` | Renewable energy share |
| `fossil_energy_share` | `EG.USE.COMM.FO.ZS` | Fossil fuel energy consumption share |
| `energy_intensity` | `EG.EGY.PRIM.PP.KD` | Energy intensity |
| `co2_per_capita` | `EN.ATM.CO2E.PC` | CO2 emissions per capita, using source `75` |

These are candidate predictors. They are downloaded for exploration, but they are not automatically final model variables.

## What Students Should Notice

- The indicator dictionary controls what gets downloaded.
- The URL function controls how the API request is written.
- The fetch function handles the network request and basic error checks.
- The records-to-frame function standardizes messy API records into project columns.
- The loop makes the workflow reusable across many indicators.
- Raw files are saved before deeper cleaning, so the source download remains traceable.

## Quick Checks After Running

After the script runs, check:

- Raw World Bank CSV files exist in `2_data/raw/`.
- `world_bank_metadata.json` records indicator codes, source IDs, update dates, and row totals.
- `year` is numeric.
- `value` is numeric or missing.
- Missing values were not converted to zero.
- Coverage summaries in `2_data/processed/` exclude aggregate areas when counting country-level coverage.
- New indicators are documented in `2_data/data_dictionary.md`.

---

# World Bank 数据请求代码说明（中文版）

这份说明解释本项目如何用代码请求 World Bank 数据。它不是只讲流程，而是帮助同学读懂代码：每段代码在做什么，为什么要这样写。

真实代码在 `2_data/scripts/data_exploration.py`。下面的例子是从真实脚本里简化出来的。

## 目标

项目需要把 World Bank 指标作为国家-年份面板数据里的候选预测变量。每个下载下来的指标，最后都要整理成同样的基本列：

- `dataset_id`
- `variable`
- `source_variable`
- `country_code`
- `country_name`
- `year`
- `value`

这样做的好处是：World Bank 数据之后可以更容易和 OECD patent 数据、policy 数据合并。

## 为什么用 API

API 的好处是可复现。脚本会清楚记录请求了哪个指标代码、哪个年份范围、什么返回格式，以及是否使用了特殊 source ID。以后其他人可以重新运行同一个请求，检查 World Bank 的数据有没有更新。

API 还会把 metadata 和数据一起返回。脚本会保存 `lastupdated` 和 `total` 这类字段，用来记录 World Bank 数据源最近更新时间，以及本次请求返回了多少条记录。

这比手动从网页下载更稳：手动下载容易忘记筛选条件，也不容易知道后来文件是怎么来的。

## World Bank 返回的数据格式长什么样

World Bank 的 JSON 响应通常是一个包含两部分的 list：

```python
payload[0]  # 本次请求的 metadata
payload[1]  # country-year 数据 records
```

一个简化后的 record 大概长这样：

```python
{
    "countryiso3code": "DEU",
    "country": {"value": "Germany"},
    "date": "2020",
    "value": 42310.2,
}
```

脚本会把这些原始字段转成项目统一格式：`countryiso3code` 变成 `country_code`，`country.value` 变成 `country_name`，`date` 变成 `year`，`value` 保留为该指标的数值。

## 1. 把指标选择集中放在一个地方

源码位置：`2_data/scripts/data_exploration.py` 第 86-128 行。

```python
WORLD_BANK_INDICATORS = {
    "gdp_per_capita": {
        "indicator": "NY.GDP.PCAP.KD",
        "description": "GDP per capita, constant 2015 US dollars.",
    },
    "rd_expenditure_gdp": {
        "indicator": "GB.XPD.RSDV.GD.ZS",
        "description": "Research and development expenditure as percent of GDP.",
    },
    "co2_per_capita": {
        "indicator": "EN.ATM.CO2E.PC",
        "description": "CO2 emissions per capita.",
        "source_id": 75,
    },
}
```

怎么读这段：

- `gdp_per_capita` 是项目内部使用的变量名，也就是我们希望以后表格里出现的名字。
- `NY.GDP.PCAP.KD` 是 World Bank 官方指标代码。
- `description` 会被保存进 metadata，方便以后知道当时请求的是什么变量。
- `source_id` 是可选项。大多数变量不需要写，但当前项目里的 CO2 指标使用 source `75`。

这种写法的好处是：以后要新增 World Bank 变量，只需要加一个小字典，不需要改下载函数。

## 2. 构造 API URL

源码位置：`2_data/scripts/data_exploration.py` 第 38 行和第 432-441 行。

```python
WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2/country/all/indicator"


def world_bank_indicator_url(
    source_variable: str,
    start_year: int,
    end_year: int,
    source_id: int | None = None,
) -> str:
    url = (
        f"{WORLD_BANK_BASE_URL}/{source_variable}"
        f"?format=json&per_page=20000&date={start_year}:{end_year}"
    )
    if source_id is not None:
        url += f"&source={source_id}"
    return url
```

关键点：

- base URL 表示：请求所有国家的某一个指标。
- `source_variable` 是 World Bank 指标代码，比如 `NY.GDP.PCAP.KD`。
- `format=json` 表示希望返回 JSON 格式。
- `per_page=20000` 表示一次请求尽量拿到足够多的行，避免分页问题。
- `date=1990:2024` 控制请求年份范围。
- `source_id` 是可选的；只有需要特殊 source 的指标才会加到 URL 后面。

例子：

`https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.KD?format=json&per_page=20000&date=1990:2024`

## 3. 发送请求并检查结果

源码位置：`2_data/scripts/data_exploration.py` 第 418-429 行。

```python
def fetch_world_bank_indicator(
    variable: str,
    source_variable: str,
    start_year: int,
    end_year: int,
    source_id: int | None = None,
) -> tuple[pd.DataFrame, dict]:
    url = world_bank_indicator_url(source_variable, start_year, end_year, source_id)
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or len(payload) < 2:
        raise ValueError(f"Unexpected World Bank response for {source_variable}")
    metadata = payload[0]
    records = payload[1]
    return world_bank_records_to_frame(records, variable, source_variable), metadata
```

每一行在做什么：

- `requests.get(...)` 发送 API 请求。
- `timeout=90` 防止程序一直卡住。
- `raise_for_status()` 如果服务器返回错误，就立刻停止程序。
- `response.json()` 把 JSON 响应转换成 Python 可以处理的对象。
- World Bank 的响应通常有两部分：第一部分是 metadata，第二部分是真正的数据 records。
- 这个函数返回两个东西：整理好的 DataFrame，以及 metadata 字典。

为什么要检查 response shape：如果 API 返回格式变了，或者返回的是错误信息，项目应该明确失败，而不是默默保存一个坏文件。

## 4. 把 World Bank records 转成项目表格

源码位置：`2_data/scripts/data_exploration.py` 第 159-177 行。

```python
def world_bank_records_to_frame(
    records: Iterable[dict],
    variable: str,
    source_variable: str,
) -> pd.DataFrame:
    rows = []
    for record in records:
        rows.append(
            {
                "dataset_id": "world_bank_wdi",
                "variable": variable,
                "source_variable": source_variable,
                "country_code": record.get("countryiso3code"),
                "country_name": (record.get("country") or {}).get("value"),
                "year": int(record["date"]),
                "value": record.get("value"),
            }
        )
    frame = pd.DataFrame(rows)
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame
```

这段代码教什么：

- `rows = []` 先创建一个空列表，用来存放整理后的每一行。
- `for record in records:` 一个一个读取 API 返回的数据记录。
- `record.get(...)` 是比较安全的取值方式；如果字段不存在，不会直接崩。
- `(record.get("country") or {}).get("value")` 用来读取嵌套的国家名称，同时避免 `country` 缺失时报错。
- `int(record["date"])` 把年份从文本转成数字。
- `pd.DataFrame(rows)` 把字典列表变成 pandas 表格。
- `pd.to_numeric(..., errors="coerce")` 把 `value` 转成数字；无法转换的值会变成 missing value。

最后一行很重要：缺失值应该保持缺失，而不是被改成 0。

## 5. 循环下载所有指标

源码位置：`2_data/scripts/data_exploration.py` 第 507-524 行。

```python
wb_metadata = {}
for variable, config in WORLD_BANK_INDICATORS.items():
    frame, metadata = fetch_world_bank_indicator(
        variable,
        config["indicator"],
        start_year,
        end_year,
        config.get("source_id"),
    )
    wb_metadata[variable] = {
        "indicator": config["indicator"],
        "description": config["description"],
        "source_id": config.get("source_id", 2),
        "lastupdated": metadata.get("lastupdated"),
        "total": metadata.get("total"),
    }
    raw_path = RAW_DIR / f"world_bank_{variable}_{config['indicator']}_{start_year}_{end_year}.csv"
    frame.to_csv(raw_path, index=False)
```

怎么读这个循环：

- `.items()` 同时拿到项目变量名和这个变量对应的设置。
- `config["indicator"]` 是必填项；如果没有，程序应该报错。
- `config.get("source_id")` 是可选项；如果没有 source ID，就返回 `None`。
- `wb_metadata[variable] = ...` 把每个变量的请求信息保存下来。
- `raw_path` 生成清楚的文件名，里面包含变量名、指标代码和年份范围。
- `index=False` 防止 pandas 把额外的行号写进 CSV。

这就是自动化的核心：同一套请求、整理、保存逻辑，会对字典里的每个指标运行一遍。

## 当前请求的指标

| 项目变量名 | World Bank 指标代码 | 含义 |
|---|---|---|
| `gdp_per_capita` | `NY.GDP.PCAP.KD` | 人均 GDP，constant 2015 US dollars |
| `gdp` | `NY.GDP.MKTP.KD` | GDP，constant 2015 US dollars |
| `population` | `SP.POP.TOTL` | 总人口 |
| `manufacturing_share` | `NV.IND.MANF.ZS` | 制造业增加值占 GDP 比例 |
| `rd_expenditure_gdp` | `GB.XPD.RSDV.GD.ZS` | R&D 支出占 GDP 比例 |
| `researchers_per_million` | `SP.POP.SCIE.RD.P6` | 每百万人 R&D 研究人员数 |
| `renewable_energy_share` | `EG.FEC.RNEW.ZS` | 可再生能源占最终能源消费比例 |
| `fossil_energy_share` | `EG.USE.COMM.FO.ZS` | 化石燃料能源消费比例 |
| `energy_intensity` | `EG.EGY.PRIM.PP.KD` | 能源强度 |
| `co2_per_capita` | `EN.ATM.CO2E.PC` | 人均 CO2 排放，使用 source `75` |

这些都是候选预测变量。下载它们是为了探索和检查覆盖率，不代表它们一定会进入最终模型。

## 学代码时应该注意什么

- 指标字典控制下载哪些变量。
- URL 函数控制 API 请求怎么写。
- fetch 函数负责发送网络请求和做基础错误检查。
- records-to-frame 函数把 API 返回的数据整理成项目统一列。
- 循环让同一套逻辑可以复用到很多指标。
- raw 文件先保存，之后再做更深入的清洗，这样数据来源可以追溯。

## 运行后快速检查

脚本运行后，检查：

- `2_data/raw/` 里是否出现 World Bank CSV 文件。
- `world_bank_metadata.json` 是否记录了指标代码、source ID、更新时间和总行数。
- `year` 是否是数字。
- `value` 是否是数字或缺失值。
- 缺失值有没有被错误改成 0。
- `2_data/processed/` 里的 coverage summary 在统计国家覆盖率时是否排除了 aggregate areas。
- 新增指标是否记录在 `2_data/data_dictionary.md`。
