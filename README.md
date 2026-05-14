# Predicting Environment-Related Innovation

> Managerial AI Course Project — LMU Munich, SS 2026  
> Prof. Stefan Feuerriegel

## Project Goal

Forecast environment-related innovation at the country level using interpretable machine learning models. Target variable: OECD patent data on environment technologies. Predictors: macroeconomic, R&D, energy, and environmental policy indicators.

## Repository Structure

```
├── 1_literature_review/     📚 Paper notes & variable framework
├── 2_data/                  📊 Data collection & preprocessing
│   ├── raw/                 ← NOT committed (in .gitignore)
│   └── processed/           ← Cleaned panel data
├── 3_models/                🤖 ML models (v1→v4 progression)
│   ├── v1_elasticnet/       Linear baseline
│   ├── v2_randomforest/     Feature selection + permutation importance
│   ├── v3_xgboost/          SHAP + hyperparameter optimization
│   └── v4_stacking/         Ensemble + uncertainty quantification
├── 4_analysis/              📈 SHAP, PDP, country case studies
└── report/                  📝 LaTeX final report
```

## Team

- @songjie1025 (jies)
- (add teammates here)

## Data Sources

- [OECD Patents on Environment Technologies](https://www.oecd.org/en/data/indicators/patents-on-environment-technologies.html)
- [World Bank World Development Indicators](https://data.worldbank.org/)
- [OECD Environmental Policy Stringency](https://www.oecd.org/en/topics/sub-issues/economic-policies-to-foster-green-growth/how-stringent-are-environmental-policies.html)
- [RISE — Regulatory Indicators for Sustainable Energy](https://rise.esmap.org/)
