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
| Sources screened | 12 |
| PDFs or access notes stored | 12 |
| Paper notes drafted | 12 |
| Paper notes reviewed | 0 |
| Sources used for predictor selection | 9 |

Update these counts whenever a source is added or reviewed.

The predictor-selection count refers to sources with draft notes that currently inform candidate predictors. Final inclusion should wait until the relevant notes are checked against full text where access allows.

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
| L001 | OECD, `Patents on environment technologies` | OECD data source | Notes drafted | `1_literature_review/pdfs/2026_oecd_patents-on-environment-technologies_access.md` | `1_literature_review/notes/2026_oecd_patents-on-environment-technologies.md` | Target-variable metadata | Target choice | Codex | 2026-05-18 |
| L002 | Hascic and Migotto, `Measuring environmental innovation using patent data` | OECD methodological source | Notes drafted | `1_literature_review/pdfs/2015_hascic_measuring-environmental-innovation_access.md` | `1_literature_review/notes/2015_hascic_measuring-environmental-innovation.md` | Patent measurement and technology taxonomy | Target choice | Codex | 2026-05-18 |
| L003 | Kruse et al., `Measuring environmental policy stringency in OECD countries` | OECD data documentation / working paper | Notes drafted | `1_literature_review/pdfs/2022_kruse_measuring-environmental-policy-stringency_access.md` | `1_literature_review/notes/2022_kruse_measuring-environmental-policy-stringency.md` | Environmental policy predictor | Predictor selection | Codex | 2026-05-18 |
| L004 | World Bank Data / WDI documentation | Data source | Notes drafted | `1_literature_review/pdfs/2026_world-bank-open-data_access.md` | `1_literature_review/notes/2026_world-bank-open-data.md` | Candidate macro, R&D, energy, and emissions predictors | Predictor data source | Codex | 2026-05-18 |
| L005 | RISE, Regulatory Indicators for Sustainable Energy | Data source | Notes drafted | `1_literature_review/pdfs/2026_esmap_rise-methodology_access.md` | `1_literature_review/notes/2026_esmap_rise-methodology.md` | Optional energy-policy predictor | Predictor selection | Codex | 2026-05-18 |
| L006 | OECD, `OECD Patent Statistics Manual` | Methodological manual | Notes drafted | `1_literature_review/pdfs/2009_oecd_patent-statistics-manual_access.md` | `1_literature_review/notes/2009_oecd_patent-statistics-manual.md` | Patent counting and comparability | Target choice | Codex | 2026-05-18 |
| L007 | Johnstone, Hascic and Popp, `Renewable Energy Policies and Technological Innovation` | Journal article / working paper | Notes drafted | `1_literature_review/pdfs/2010_johnstone_renewable-energy-policies_access.md` | `1_literature_review/notes/2010_johnstone_renewable-energy-policies.md` | Policy-induced renewable patenting | Predictor selection | Codex | 2026-05-18 |
| L008 | Nesta, Vona and Nicolli, `Environmental policies, competition and innovation in renewable energy` | Journal article | Notes drafted | `1_literature_review/pdfs/2014_nesta_environmental-policies-competition_access.md` | `1_literature_review/notes/2014_nesta_environmental-policies-competition.md` | Policy, R&D, competition, renewable patenting | Predictor selection | Codex | 2026-05-18 |
| L009 | Popp, `Induced Innovation and Energy Prices` | Journal article / working paper | Notes drafted | `1_literature_review/pdfs/2002_popp_induced-innovation-energy-prices_access.md` | `1_literature_review/notes/2002_popp_induced-innovation-energy-prices.md` | Energy-price induced innovation mechanism | Predictor selection | Codex | 2026-05-18 |
| L010 | Jaffe and Palmer, `Environmental Regulation and Innovation` | Journal article / working paper | Notes drafted | `1_literature_review/pdfs/1997_jaffe_environmental-regulation-innovation_access.md` | `1_literature_review/notes/1997_jaffe_environmental-regulation-innovation.md` | Porter-hypothesis caution and R&D/patent distinction | Predictor interpretation | Codex | 2026-05-18 |
| L011 | Brunnermeier and Cohen, `Determinants of environmental innovation in US manufacturing industries` | Journal article | Notes drafted | `1_literature_review/pdfs/2003_brunnermeier_determinants-environmental-innovation_access.md` | `1_literature_review/notes/2003_brunnermeier_determinants-environmental-innovation.md` | Regulation and industrial-structure mechanisms | Predictor interpretation | Codex | 2026-05-18 |
| L012 | Johnstone et al., `Environmental Policy Stringency and Technological Innovation` | Journal article | Notes drafted | `1_literature_review/pdfs/2012_johnstone_environmental-policy-stringency_access.md` | `1_literature_review/notes/2012_johnstone_environmental-policy-stringency.md` | Country-level policy stringency and environmental patents | Predictor selection | Codex | 2026-05-18 |

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
