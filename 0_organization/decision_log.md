# Decision Log

This file records important project decisions so that the research direction stays traceable.

Decision entries should be short. Each entry should explain what was decided, why it was decided, and which alternatives were considered.

## Format

```text
Date: YYYY-MM-DD
Decision:
Reason:
Alternatives considered:
Status:
```

Status options:

1. `Active`: currently guiding the project.
2. `Revised`: replaced by a later decision.
3. `Deferred`: discussed but not decided yet.

## Decisions

### 2026-05-15: Use lightweight project governance

Date: 2026-05-15

Decision:
The project will use lightweight governance rules stored in `0_organization/project_rules.md`.

Reason:
The project needs enough structure to prevent scope drift and documentation disorder, but it should remain practical for a course project.

Alternatives considered:
A more formal project-management structure with detailed issue tracking and approval gates was considered unnecessary at this stage.

Status:
Active

### 2026-05-15: Treat the organization file as the source of truth

Date: 2026-05-15

Decision:
The main requirement file, `0_organization/predicting_environment-related_innovation.txt`, is the highest-priority source for project scope.

Reason:
Some repository content was generated as an initial skeleton. The project should follow the seminar requirement first and use generated content only as a starting point.

Alternatives considered:
Using the generated README as the fixed project plan was rejected because it contains specific modeling and analysis choices that are not required by the organization file.

Status:
Active

### 2026-05-15: Use controlled first-pass data exploration

Date: 2026-05-15

Decision:
The first data step is a controlled feasibility exploration of OECD patent indicators, World Bank candidate predictors, and OECD EPS, rather than a full modeling dataset build.

Reason:
The target variable, final predictor list, country coverage, and year coverage must be checked before committing to a modeling pipeline.

Alternatives considered:
Building the full data pipeline immediately was rejected because it could lock in weak variables or mismatched coverage too early.

Status:
Active

### 2026-05-15: Keep target-variable choice deferred after first data exploration

Date: 2026-05-15

Decision:
The OECD `Patents - indicators` dataset provides strong target candidates, but the final target variable is not selected yet.

Reason:
The first-pass exploration found three viable candidates: `env_patent_share_tech`, `env_patent_share_inventions`, and `env_patents_per_million`. The final choice should depend on literature fit and modeling interpretation, not coverage alone.

Alternatives considered:
Immediately selecting `env_patent_share_tech` was considered but deferred because the difference between "percentage of technologies" and "percentage of inventions" should be understood from OECD metadata and the literature first.

Status:
Deferred

### 2026-05-16: Do not use `env_patent_share_tech` as the main target

Date: 2026-05-16

Decision:
`env_patent_share_tech` (`PT_TECH.DEV.ENV_PAT._Z`) will not be used as the main target variable.

Reason:
The OECD API and the locally downloaded raw data both report Eritrea in 2016 with `PT_TECH = 350` and status `Normal value`. This is not a download or parsing error. However, values above 100 make the variable difficult to interpret as a simple country-level share of green innovation. The most plausible explanation is that the "percentage of technologies" measure can be inflated in very small patent systems when inventions are assigned to multiple technology categories. This creates a high interpretation risk for the main analysis.

Alternatives considered:
Using `env_patent_share_tech` as the main target was rejected. It may still be considered as a robustness or sensitivity variable if the sample is filtered and the interpretation is stated carefully. `env_patents_per_million` and `env_patent_share_inventions` remain candidate target variables.

Status:
Active

### 2026-05-18: Treat `env_patent_share_inventions` as the leading target candidate

Date: 2026-05-18

Decision:
The first literature-review pass treats `env_patent_share_inventions` as the leading main target candidate, with `env_patents_per_million` kept as a robustness or alternative intensity target.

Reason:
OECD target metadata and patent-measurement sources support a normalized patent-share measure tied to domestic inventions. This choice is easier to defend than `env_patent_share_tech`, which was already excluded as a main target because values above 100 create interpretation risk. A per-million indicator remains useful because it preserves patent intensity, but it may be more sensitive to general innovation-system scale.

Alternatives considered:
Using `env_patents_per_million` as the main target was considered but deferred because the project should first check skewness and size effects. Returning to `env_patent_share_tech` as the main target was rejected under the active 2026-05-16 decision.

Status:
Deferred

### 2026-05-19: Add candidate discovery before model building

Date: 2026-05-19

Decision:
Before building the modeling panel, the project will use a dedicated candidate discovery step that catalogs OECD patent target combinations and literature/database-driven predictor candidates.

Reason:
The first-pass data exploration checked feasibility for a small initial set, but it did not by itself show that the relevant target and predictor candidate space had been systematically screened. A candidate discovery catalog makes the screening logic, coverage status, inclusion decisions, and dropped alternatives auditable before final variable selection.

Alternatives considered:
Moving directly to model construction was rejected because it would make variable selection look ad hoc. Downloading every possible indicator time series was also rejected because it would add complexity without improving the interpretability of the final project.

Status:
Active

### 2026-05-19: Keep predictor selection provisional

Date: 2026-05-19

Decision:
The predictor candidate catalog is a provisional discovery artifact, not the final predictor list for modeling.

Reason:
The literature review is still in progress. The current catalog organizes plausible predictors, coverage status, measurement caveats, and inclusion labels so the project can avoid ad hoc variable choice, but the final predictor set should only be selected after the remaining literature notes and coverage checks are reviewed together.

Alternatives considered:
Treating the current predictor catalog as the final model specification was rejected because it would overstate the completeness of the literature review.

Status:
Active

### 2026-05-20: Treat RISE as an alternative policy predictor

Date: 2026-05-20

Decision:
RISE will be kept as an alternative or robustness policy predictor rather than replacing OECD EPS as the main policy candidate at this stage.

Reason:
OECD EPS has stronger direct support in the environmental-policy and green-patent literature, but its country coverage is narrow. RISE has broader country coverage and annual pillar data from 2010-2023, but it measures sustainable-energy regulatory readiness rather than general environmental policy stringency. If used, the project should prefer lagged RISE Renewable Energy or Energy Efficiency pillar scores over the overall RISE score.

Alternatives considered:
Replacing EPS with RISE was rejected for now because RISE is conceptually broader and has weaker direct patent-innovation evidence. Dropping RISE was also rejected because its broader country coverage may be valuable for an alternative policy specification.

Status:
Active

## Deferred Decisions

The following decisions should be made after literature review and initial data inspection:

1. Exact OECD target variable and variable code.
2. Final predictor list.
3. Country and year coverage.
4. Main evaluation metric.
5. Final model family or model comparison strategy.
6. Final report structure.
