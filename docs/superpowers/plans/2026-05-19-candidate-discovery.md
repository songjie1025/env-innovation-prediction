# Candidate Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reproducible candidate-discovery step that audits OECD patent target candidates and predictor candidates before modeling.

**Architecture:** Keep reusable logic in `2_data/scripts/candidate_discovery.py`, and keep narrative inspection in `2_data/notebooks/candidate_discovery.ipynb`. The script reads existing OECD patent metadata and first-pass coverage outputs, queries lightweight World Bank metadata catalogs when requested, and writes committed processed catalogs without creating a modeling panel.

**Tech Stack:** Python, pandas, requests, unittest, Jupyter notebook JSON.

---

### Task 1: Candidate Discovery Script

**Files:**
- Create: `2_data/scripts/candidate_discovery.py`
- Read: `2_data/scripts/data_exploration.py`
- Output: `2_data/processed/target_candidate_catalog.csv`
- Output: `2_data/processed/predictor_candidate_catalog.csv`
- Output: `2_data/processed/candidate_discovery_summary.md`

- [ ] Implement OECD target combination generation from `UNIT_MEASURE`, `TYPE`, `TECH`, and `PAT` metadata.
- [ ] Classify target candidates as `main_target_candidate`, `secondary_target`, or `not_suitable` using transparent reasons.
- [ ] Attach available coverage from `data_availability.csv` for known downloaded target candidates.
- [ ] Build a literature- and database-driven predictor catalog with concepts, candidate indicators, sources, rationale, coverage status, and inclusion decisions.
- [ ] Support optional lightweight World Bank metadata scanning by keyword without downloading all time series.
- [ ] Write CSV and Markdown outputs to `2_data/processed/`.

### Task 2: Tests

**Files:**
- Create: `tests/test_candidate_discovery.py`

- [ ] Test source-variable construction and target classification.
- [ ] Test predictor catalog rows include required reviewer-facing fields.
- [ ] Test keyword filtering of World Bank metadata on representative records.
- [ ] Test output writer creates the expected CSV and Markdown files in a temporary directory.

### Task 3: Notebook

**Files:**
- Create: `2_data/notebooks/candidate_discovery.ipynb`

- [ ] Add safe optional Google Colab setup cell.
- [ ] Import `candidate_discovery.py` rather than duplicating script logic.
- [ ] Default to reading committed outputs and only refresh when `RUN_DISCOVERY = True`.
- [ ] Display target and predictor catalogs with compact reviewer-facing columns.
- [ ] Plot target candidate status counts and predictor inclusion-decision counts.

### Task 4: Verification And Commit

- [ ] Run focused unit tests for candidate discovery.
- [ ] Run the script and confirm generated outputs exist.
- [ ] Smoke-check the notebook JSON and imports.
- [ ] Commit a focused data change with an imperative English commit message.
