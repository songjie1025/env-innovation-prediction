# Predicting Environment-Related Innovation

> Managerial AI Course Project — LMU Munich, SS 2026  
> Prof. Stefan Feuerriegel | Institute of AI in Management

## Project Goal

Build an interpretable machine learning model to forecast environment-related innovation at the country level using publicly available panel data.

- **Target variable:** OECD patents on environment technologies (ENV_TECH_SHARE)
- **Predictors:** Macroeconomic development, R&D, energy, and environmental policy indicators
- **Approach:** Interpretable ML with SHAP-based feature attribution

## Repository Structure

```
├── 1_literature_review/     Literature review & variable framework
├── 2_data/                  Data collection & preprocessing
│   ├── raw/                 Raw datasets (NOT committed — see .gitignore)
│   └── processed/           Cleaned panel data
├── 3_models/                Model development (v1 → v4 progression)
│   ├── v1_elasticnet/       Linear baseline (L1 + L2 regularization)
│   ├── v2_randomforest/     Tree-based model + RFE + permutation importance
│   ├── v3_xgboost/          Gradient boosting + SHAP + Optuna tuning
│   └── v4_stacking/         Ensemble + bootstrap CI + LOCO validation
├── 4_analysis/              SHAP analysis, partial dependence, case studies
│   ├── figures/
│   └── tables/
└── report/                  LaTeX final report (or Overleaf sync)
```

## Workflow

1. **Literature Review** → Identify target variable & select 10–15 predictors with causal mechanisms
2. **Data** → Collect country-year panel from OECD, World Bank, RISE; clean & engineer features
3. **Models** → Progressive 4-version architecture: ElasticNet → RandomForest → XGBoost → Stacking
4. **Analysis** → SHAP attribution, partial dependence plots, country case studies (DEU, USA, CHN, IND, BRA)
5. **Report** → LaTeX report (20,000–30,000 characters) + presentation

## Data Sources

| Source | Description | Link |
|--------|-------------|------|
| OECD PAT_IND | Patents on environment technologies (target variable) | [OECD Data](https://www.oecd.org/en/data/indicators/patents-on-environment-technologies.html) |
| World Bank WDI | Macroeconomic, R&D, energy, education indicators | [World Bank](https://data.worldbank.org/) |
| OECD EPS | Environmental Policy Stringency index | [OECD EPS](https://www.oecd.org/en/topics/sub-issues/economic-policies-to-foster-green-growth/how-stringent-are-environmental-policies.html) |
| RISE | Regulatory Indicators for Sustainable Energy | [RISE](https://rise.esmap.org/) |

## Team

- @songjie1025 (Jie Song)
- _(add teammates here)_

## Setup

```bash
# Clone the repository
git clone git@github.com:songjie1025/env-innovation-prediction.git
cd env-innovation-prediction

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Branch Naming Convention

- `main` — stable, reviewed code only
- `jies/<task>` — Jie's feature branches
- `teammate/<task>` — teammate branches

---

*Last updated: May 2026*
