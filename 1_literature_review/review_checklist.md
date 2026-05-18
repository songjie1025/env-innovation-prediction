# Literature Review Checklist

This file is the central index for the project literature review. It tracks which sources have been found, whether their PDFs or access notes are stored, whether project-focused notes exist, and whether the source informs target-variable or predictor selection.

Use this file together with `1_literature_review/paper_note_guide.md`.

## Review Purpose

The literature review should support three project decisions:

1. Which OECD patent indicator is the most defensible target variable.
2. Which small set of country-year predictors should enter the main model.
3. How to interpret predictor signs, lags, sample limits, and robustness checks.

The review is not a general survey of green innovation. It should focus on sources that help explain, predict, or measure environment-related patenting at the country level.

## Current Status

| Item | Count |
|---|---:|
| Sources screened | 0 |
| PDFs or access notes stored | 0 |
| Paper notes drafted | 0 |
| Paper notes reviewed | 0 |
| Sources used for predictor selection | 0 |

Update these counts whenever a source is added or reviewed.

## Folder Convention

| Folder | Purpose | Rule |
|---|---|---|
| `1_literature_review/pdfs/` | PDF files or access-note files | Store a PDF only when permitted. Otherwise add a short `.md` access note with DOI, URL, and access status. |
| `1_literature_review/notes/` | Project-focused paper notes | Every reviewed source should have one Markdown note following `paper_note_guide.md`. |

Recommended file naming:

```text
1_literature_review/pdfs/YYYY_author_short-title.pdf
1_literature_review/notes/YYYY_author_short-title.md
```

Examples:

```text
1_literature_review/pdfs/2015_oecd_measuring-environmental-innovation.pdf
1_literature_review/notes/2015_oecd_measuring-environmental-innovation.md
```

## Review Status Definitions

| Status | Meaning |
|---|---|
| `Candidate` | Found and potentially relevant, but not screened yet. |
| `Screened` | Abstract, metadata, and likely relevance checked. |
| `PDF/access stored` | PDF is stored or an access note is recorded. |
| `Notes drafted` | A paper note exists but has not been reviewed. |
| `Notes reviewed` | Note quality is checked and ready for project use. |
| `Included` | Source informs target choice, predictor selection, interpretation, or report writing. |
| `Dropped` | Source was screened and rejected with a short reason. |

## Literature Index

| ID | Citation / source | Type | Status | PDF or access note | Paper note | Main relevance | Decision use | Owner | Last updated |
|---|---|---|---|---|---|---|---|---|---|
| L001 | OECD, `Patents on environment technologies` | OECD data source | Candidate | To add | To add | Target-variable metadata | Target choice | Unassigned | 2026-05-18 |
| L002 | OECD, `Measuring environmental innovation using patent data` | OECD methodological source | Candidate | To add | To add | Patent measurement and technology taxonomy | Target choice | Unassigned | 2026-05-18 |
| L003 | OECD, `Environmental Policy Stringency` | OECD data source | Candidate | To add | To add | Environmental policy predictor | Predictor selection | Unassigned | 2026-05-18 |
| L004 | World Bank Data / WDI documentation | Data source | Candidate | To add | To add | Candidate macro, R&D, energy, and emissions predictors | Predictor selection | Unassigned | 2026-05-18 |
| L005 | RISE, Regulatory Indicators for Sustainable Energy | Data source | Candidate | To add | To add | Optional energy-policy predictor | Predictor selection | Unassigned | 2026-05-18 |

Add empirical papers below this block as they are found.

## Search Queue

Use these searches first. Record useful hits in the Literature Index before reading deeply.

| Search theme | Search query | Priority | Notes |
|---|---|---|---|
| General determinants | `determinants of environmental innovation patents country panel` | High | Look for country-year or OECD panel studies. |
| Green patents and predictors | `green innovation patents determinants OECD countries` | High | Extract predictor groups and target definitions. |
| Environmental policy | `environmental policy stringency green patents OECD` | High | Especially useful for EPS justification. |
| Porter hypothesis | `Porter hypothesis environmental regulation green patents` | Medium | Useful for policy mechanism and expected sign. |
| R&D capacity | `R&D expenditure environmental innovation patents` | High | Extract R&D measures, lags, and sample limits. |
| Energy system | `renewable energy energy intensity environmental patents` | Medium | Useful for energy predictor mechanisms. |
| Patent measurement | `OECD environmental innovation patent data measurement` | High | Useful for target-variable choice and limitations. |

## Source Screening Checklist

Before adding a source as `Included`, check:

1. Does it use or discuss environmental, green, clean-energy, climate, or environment-related patents?
2. Does it provide predictor variables, mechanisms, or target-variable measurement guidance?
3. Does it use country-level, regional, sectoral, or firm-level data? Record the level clearly.
4. Does it help our country-year panel project, even if the original paper uses a different method?
5. Does it add new information beyond sources already reviewed?
6. Are there data limitations, sample restrictions, or measurement caveats relevant to our design?

## Handoff Instructions for AI Assistants

Before continuing the literature review, read:

1. `0_organization/predicting_environment-related_innovation.txt`
2. `0_organization/project_rules.md`
3. `1_literature_review/variable_framework.md`
4. `1_literature_review/review_checklist.md`
5. `1_literature_review/paper_note_guide.md`
6. `2_data/data_dictionary.md`

When adding a source:

1. Check the Literature Index for duplicates.
2. Save the PDF or create an access note in `1_literature_review/pdfs/`.
3. Create a paper note in `1_literature_review/notes/` using the required template.
4. Update the Literature Index row with links, status, relevance, owner, and date.
5. If the source changes a project decision, update `0_organization/decision_log.md`.
6. Do not invent bibliographic details. If metadata are incomplete, mark them explicitly.
