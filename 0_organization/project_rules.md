# Project Rules

These rules keep the project focused, traceable, and easy to maintain.

## 1. Source of Truth

1. The main project requirement is `0_organization/predicting_environment-related_innovation.txt`.
2. If another file conflicts with the organization file, the organization file wins.
3. Hermes-generated content, including the current README structure, is treated as a starting point, not as a fixed plan.
4. New tasks must support the core goal: predicting country-level environment-related innovation with public panel data and interpretable machine learning.

## 2. Project Scope

Before adding a new dataset, model, analysis, or section, check:

1. Does it help predict or explain environment-related innovation?
2. Is it supported by the project requirement, the literature, or the available data?
3. Does it add more value than complexity?

If the answer to any question is unclear, discuss it before adding the item.

## 3. Language

1. Use English for committed project documents, code comments, variable descriptions, figure titles, table titles, and commit messages.
2. Internal chat and quick planning can be in Chinese when helpful.
3. Final report materials should be written in academic English unless the course explicitly requires otherwise.

## 4. Documentation Rules

Keep documentation small and specific:

1. `0_organization/` stores project rules, requirements, and decision records.
2. `1_literature_review/` stores literature notes and the variable framework.
3. `2_data/` stores data scripts, raw data placeholders, processed data, and data dictionaries.
4. `3_models/` stores model code, model plans, and model outputs.
5. `4_analysis/` stores figures, tables, interpretation, and case-study material.
6. `report/` stores the final report or files synced from Overleaf.

Do not duplicate the same explanation across many files. Link to the source file instead.

## 5. Decision Logging

Important choices should be recorded briefly in `0_organization/decision_log.md`.

Log a decision when we choose or change:

1. The target variable.
2. Predictor groups or specific predictors.
3. Data sources and year or country coverage.
4. Model families.
5. Evaluation metrics.
6. Report structure.

Each entry should include the date, the decision, the reason, and any rejected alternative.

## 6. Data Rules

1. Raw data belongs in `2_data/raw/` and should not be committed unless it is tiny and explicitly useful.
2. Processed data belongs in `2_data/processed/`.
3. Every dataset used in the project needs a source URL, download date, variable names, units, and coverage notes.
4. Use country-year panel structure unless there is a clear reason not to.
5. Avoid time leakage: predictors should come from earlier years when predicting future innovation.

## 7. Modeling Rules

1. Start with a simple, interpretable baseline before adding complex models.
2. Add a more complex model only if it improves the research question, not just the score.
3. Keep model outputs reproducible with fixed random seeds where applicable.
4. Interpretability is required. Use coefficients, permutation importance, SHAP, partial dependence, or another clearly explained method.
5. Report both predictive performance and substantive interpretation.

## 8. Commit Rules

Use small, focused commits. One commit should represent one logical change.

Commit message format:

```text
<type>: <short imperative summary>
```

Allowed types:

1. `docs`: documentation-only changes.
2. `data`: data collection, cleaning, or metadata changes.
3. `model`: modeling code or experiment changes.
4. `analysis`: figures, tables, interpretation, or case studies.
5. `report`: final report writing or formatting.
6. `fix`: bug fixes or corrections.
7. `chore`: maintenance, setup, dependency, or repository housekeeping.

Examples:

```text
docs: add project rules
data: add OECD patent download script
model: add elastic net baseline
analysis: add SHAP summary plot
fix: correct target variable lag
```

Commit message rules:

1. Use English.
2. Use the imperative mood, for example "add", "fix", "update", "remove".
3. Keep the first line under 72 characters when possible.
4. Do not mix unrelated changes in one commit.
5. Mention the affected area in the summary when helpful.

## 9. Branch Rules

1. `main` should stay stable and reviewed.
2. Use feature branches for work in progress.
3. Branch names should follow `<owner>/<short-task>`, for example `jies/data-oecd-patents`, `teammate/literature-review`, or `codex/project-rules`.
4. Keep branch names lowercase and use hyphens instead of spaces.

## 10. Anti-Drift Rule

If the project starts expanding beyond the organization file, pause and ask:

1. What requirement does this serve?
2. Which file should record this decision?
3. What simpler version would still satisfy the project?

The default choice is the smaller, clearer version.
