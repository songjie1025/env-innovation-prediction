# Paper Note Guide

This guide defines how to write literature notes for the project. It is designed for human collaborators and AI assistants who continue the literature search through GitHub rather than Zotero.

The note style should be project-focused and reviewer-like: concise, skeptical, and oriented toward whether the source helps our target-variable choice, predictor selection, data construction, or interpretation.

## What Matters Most

For this project, prioritize:

1. Data sources and variable definitions.
2. Innovation measure, especially patent-based environmental innovation measures.
3. Predictor variables and expected relationships.
4. Country, year, and unit-of-analysis coverage.
5. Findings that justify or challenge our candidate predictors.
6. Strengths, limitations, and transferability to our project.

Do not spend much space on econometric or machine-learning method details unless the method affects variable interpretation, lag choice, sample construction, or credibility of findings.

## Required Files for Each Reviewed Source

Each reviewed source should have:

1. A PDF file in `1_literature_review/pdfs/`, if legally and practically shareable through this repository.
2. If the PDF cannot be stored, an access note in `1_literature_review/pdfs/` with DOI, URL, access status, and reason the PDF is not stored.
3. A Markdown paper note in `1_literature_review/notes/`.
4. One row in `1_literature_review/review_checklist.md`.

Never hard-code private credentials or paywalled PDF download links in notes.

## Note File Naming

Use lowercase filenames with year, first author or organization, and a short title slug.

```text
YYYY_author_short-title.md
```

Examples:

```text
2015_oecd_measuring-environmental-innovation.md
2010_johnstone_environmental-policy-renewable-energy.md
```

## Required Paper Note Template

Copy this template into every new note.

```markdown
# Short Title

## Bibliographic Metadata

| Field | Value |
|---|---|
| Review ID | L000 |
| Full citation |  |
| Authors / organization |  |
| Year |  |
| Title |  |
| Source type | Journal article / working paper / book chapter / data documentation / policy report |
| DOI / URL |  |
| PDF path or access note |  |
| Note author |  |
| Last updated | YYYY-MM-DD |
| Review status | Candidate / Notes drafted / Notes reviewed / Included / Dropped |

## One-Paragraph Summary

Summarize the source in 4-6 sentences. Focus on what it studies, what data it uses, what it finds, and why it matters for this project.

## Why This Source Is Relevant

Explain how the source helps this project. Choose one or more:

- Target-variable choice.
- Predictor selection.
- Lag structure.
- Data-source choice.
- Interpretation of model results.
- Report background.
- Limitation or caution.

## Data and Measurement Extraction

| Item | What the source uses / says | Relevance for our project |
|---|---|---|
| Innovation outcome |  |  |
| Patent definition or technology class |  |  |
| Predictor variables |  |  |
| Policy variables |  |  |
| R&D / innovation-capacity variables |  |  |
| Energy or emissions variables |  |  |
| Macro controls |  |  |
| Unit of analysis | Country-year / region-year / firm-year / sector-year / other |
| Countries / regions |  |  |
| Years |  |  |
| Lag structure |  |  |
| Data sources |  |  |
| Transformations | Logs, shares, standardization, patent normalization, etc. |

## Key Findings for Predictor Selection

List only findings that help our model design.

1.
2.
3.

For each finding, note whether it supports, weakens, or complicates one of our candidate predictors.

## Predictor Implications for Our Model

| Candidate predictor concept | Supported? | Expected sign | Evidence from source | Caveat |
|---|---|---|---|---|
| GDP per capita / income level | Yes / No / Mixed / Not discussed | Positive / Negative / Ambiguous |  |  |
| R&D expenditure | Yes / No / Mixed / Not discussed | Positive / Negative / Ambiguous |  |  |
| Researchers / human capital | Yes / No / Mixed / Not discussed | Positive / Negative / Ambiguous |  |  |
| Renewable energy share | Yes / No / Mixed / Not discussed | Positive / Negative / Ambiguous |  |  |
| Fossil energy share | Yes / No / Mixed / Not discussed | Positive / Negative / Ambiguous |  |  |
| Energy intensity | Yes / No / Mixed / Not discussed | Positive / Negative / Ambiguous |  |  |
| CO2 emissions per capita | Yes / No / Mixed / Not discussed | Positive / Negative / Ambiguous |  |  |
| Environmental policy stringency | Yes / No / Mixed / Not discussed | Positive / Negative / Ambiguous |  |  |
| Other useful predictor | Yes / No / Mixed / Not discussed | Positive / Negative / Ambiguous |  |  |

## Strengths

Write 2-4 points. Focus on data quality, measurement clarity, conceptual relevance, or transferability to our project.

1.
2.
3.

## Limitations

Write 2-4 points. Focus on limitations that matter for our project.

1. Data coverage limitations:
2. Measurement limitations:
3. Identification or interpretation limitations:
4. Transferability limitations:

## How We Should Use This Source

Choose one:

- `Core`: central source for target or predictor selection.
- `Supporting`: useful but not central.
- `Background`: helpful for framing only.
- `Dropped`: not useful enough for this project.

Then explain the decision in 2-4 sentences.

## Extractable Text for Report

Paraphrase useful ideas. Do not copy long passages.

1.
2.

## Open Questions After Reading

1.
2.
```

## Reviewer Standards

A good note should:

1. Be understandable without opening the PDF.
2. Make clear which project decision the source informs.
3. Separate what the source finds from what we infer for our project.
4. Mark uncertainty instead of overstating evidence.
5. Record missing metadata rather than guessing.
6. Keep direct quotes short and only when necessary.

## AI Continuation Rules

When an AI assistant adds or updates notes:

1. Read the project requirement and variable framework first.
2. Search for sources using the search queue in `review_checklist.md`.
3. Prefer sources that directly discuss environmental patents, green innovation, environmental policy, R&D, energy systems, or country-level panel data.
4. Do not create notes from abstracts alone unless the note is marked `Candidate` and clearly says the full text has not been reviewed.
5. Do not claim a predictor is justified unless the note records the source evidence.
6. Update `review_checklist.md` every time a note or PDF/access note is added.
7. If a source suggests adding or dropping a predictor, record that as an open decision unless the team has already agreed.

## Quality Check Before Marking `Notes reviewed`

Before changing a note status to `Notes reviewed`, verify:

1. Bibliographic metadata are complete enough to find the source again.
2. PDF path or access note exists.
3. Data and measurement table is filled in where relevant.
4. Predictor implications table is filled in for all variables discussed by the source.
5. Strengths and limitations are specific, not generic.
6. The note explains how the source should or should not affect our project.
