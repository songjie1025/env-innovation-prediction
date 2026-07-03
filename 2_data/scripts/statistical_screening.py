"""Phase-3 statistical screening (data-side feature diagnostics).

Location rationale: statistical screening is a *filter*-type feature diagnostic
that sits between data cleaning (P1/P2) and modeling (P4). It does not change the
data and does not train a model, so it lives on the data side (2_data/scripts).

ALL logic lives in this script. The companion notebook
`2_data/notebooks/statistical_screening.ipynb` only *calls* these functions and
*displays* their results (no computation logic in the notebook).

What this module owns (the "missing" screening metrics):
  - compute_near_zero_variance()  : is any predictor almost constant?
  - compute_vif()                 : multicollinearity (variance inflation factor)

What it REUSES (does not recompute; leakage-safe train+validation versions are
already produced by 3_models/scripts/run_modeling.py):
  - predictor-predictor correlation matrix, top correlated pairs, and
    predictor-target correlations -> load_existing_correlation_outputs()

Figure functions return a matplotlib Figure (no disk I/O) so both the notebook
(inline display) and main() (save to disk) can reuse them.

Run as a script to (re)generate the screening CSVs + paper figures:
    python 2_data/scripts/statistical_screening.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Reuse the shared project config + panel IO utilities (model layer depends on the
# data layer conceptually; here we add its path so a data-side script can reuse the
# canonical panel definitions instead of duplicating them).
_MODEL_SCRIPTS = ROOT / "3_models" / "scripts"
if str(_MODEL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_MODEL_SCRIPTS))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.impute import SimpleImputer  # noqa: E402
from sklearn.linear_model import LinearRegression  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from model_config import OUTPUT_DIR, PANEL_CONFIGS, PRIMARY_LAG_SUFFIX  # noqa: E402
from model_data import load_model_panel, select_lag_features  # noqa: E402

FIG_DIR = ROOT / "4_analysis" / "figures" / "paper"

# thresholds (standard rules of thumb)
NZV_CV_THRESHOLD = 0.01     # coefficient of variation below this -> near constant
NZV_DOMINANT_SHARE = 0.95   # one value covers >95% of rows -> near constant
VIF_MODERATE = 5.0
VIF_SEVERE = 10.0

_DISPLAY_NAMES = {
    "size_factor": "Economic scale / research capacity",
    "gdp_constant_2015_usd": "GDP (constant USD)", "co2_per_capita_ar5": "CO2 per capita",
    "wgi_regulatory_quality": "Regulatory quality", "env_technology_rta": "Env. tech RTA",
    "scientific_journal_articles": "Scientific articles", "fdi_net_inflows": "FDI net inflows",
    "renewable_energy_share": "Renewable share", "trade_openness": "Trade openness",
    "inflation": "Inflation", "rise_energy_efficiency": "RISE energy efficiency",
    "rise_renewable_energy": "RISE renewable", "high_tech_exports": "High-tech exports",
    "rd_expenditure_gdp": "R&D expenditure", "env_co_invention_share": "Co-invention share",
    "energy_imports_net": "Net energy imports", "researchers_per_million": "Researchers/million",
    "environmental_tax_revenue": "Env. tax revenue", "eps_index": "EPS index",
}


def _clean(feature: str) -> str:
    stem = str(feature).replace("_" + PRIMARY_LAG_SUFFIX, "")
    return _DISPLAY_NAMES.get(stem, stem.replace("_", " "))


# ---------------------------------------------------------------------------
# (1) computation — the missing screening metrics
# ---------------------------------------------------------------------------
def compute_near_zero_variance(panel: pd.DataFrame, feats: list[str], panel_id: str) -> pd.DataFrame:
    """Flag (almost) constant predictors."""
    rows = []
    for f in feats:
        obs = panel[f].astype(float).dropna()
        mean = float(obs.mean())
        std = float(obs.std(ddof=1)) if len(obs) > 1 else 0.0
        cv = float(abs(std / mean)) if mean != 0 else np.inf
        n_unique = int(obs.nunique())
        dominant = float(obs.value_counts(normalize=True).iloc[0]) if len(obs) else 1.0
        rows.append({
            "panel_id": panel_id, "feature": f.replace("_" + PRIMARY_LAG_SUFFIX, ""),
            "n_obs": int(len(obs)), "n_unique": n_unique, "std": std,
            "coef_of_variation": cv, "dominant_value_share": round(dominant, 4),
            "near_zero_variance": bool(n_unique <= 2 or cv < NZV_CV_THRESHOLD or dominant > NZV_DOMINANT_SHARE),
        })
    return pd.DataFrame(rows)


def compute_vif(panel: pd.DataFrame, feats: list[str], panel_id: str) -> pd.DataFrame:
    """VIF on median-imputed, standardized features (no target used -> no leakage)."""
    x = panel.loc[:, feats].astype(float)
    x_imp = SimpleImputer(strategy="median", keep_empty_features=True).fit_transform(x)
    x_std = StandardScaler().fit_transform(x_imp)
    rows = []
    for i, f in enumerate(feats):
        others = [j for j in range(len(feats)) if j != i]
        if not others:  # single-predictor panel (SubC): VIF undefined -> 1.0
            vif = 1.0
        else:
            r2 = LinearRegression().fit(x_std[:, others], x_std[:, i]).score(x_std[:, others], x_std[:, i])
            vif = float(1.0 / (1.0 - r2)) if r2 < 1 else np.inf
        flag = "severe" if vif >= VIF_SEVERE else ("moderate" if vif >= VIF_MODERATE else "ok")
        rows.append({"panel_id": panel_id, "feature": f.replace("_" + PRIMARY_LAG_SUFFIX, ""),
                     "vif": round(vif, 3), "flag": flag})
    return pd.DataFrame(rows).sort_values("vif", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# reuse already-computed (leakage-safe) correlation diagnostics
# ---------------------------------------------------------------------------
def load_existing_correlation_outputs() -> dict:
    """Read correlation diagnostics produced by run_modeling.py (not recomputed)."""
    sp = OUTPUT_DIR / "linear_model_main_feature_spearman_correlations.csv"
    tp = OUTPUT_DIR / "linear_model_target_correlations.csv"
    pp = OUTPUT_DIR / "linear_model_top_correlated_pairs.csv"
    return {
        "spearman_matrix": pd.read_csv(sp, index_col=0) if sp.exists() else None,
        "target_correlations": pd.read_csv(tp) if tp.exists() else None,
        "top_pairs": pd.read_csv(pp) if pp.exists() else None,
    }


def run_screening() -> dict:
    """Compute NZV + VIF for every panel and load the existing correlation outputs."""
    panels, nzv_all, vif_all = {}, [], []
    for cfg in PANEL_CONFIGS:
        p = load_model_panel(cfg["panel_path"], cfg["target_column"])
        feats = select_lag_features(p, PRIMARY_LAG_SUFFIX)
        panels[cfg["panel_id"]] = (p, feats, cfg["target_column"])
        nzv_all.append(compute_near_zero_variance(p, feats, cfg["panel_id"]))
        vif_all.append(compute_vif(p, feats, cfg["panel_id"]))
    return {
        "panels": panels,
        "near_zero_variance": pd.concat(nzv_all, ignore_index=True),
        "vif": pd.concat(vif_all, ignore_index=True),
        "correlations": load_existing_correlation_outputs(),
    }


# ---------------------------------------------------------------------------
# figure functions — return a self-contained Figure (Agg canvas so it renders
# via IPython display but is NOT registered in pyplot, avoiding double display).
# No disk I/O; the caller displays (notebook) or saves (main).
# ---------------------------------------------------------------------------
def _new_figure(**kwargs):
    import matplotlib.pyplot as plt

    return plt.figure(**kwargs)


def figure_vif(vif_all: pd.DataFrame, panel_id: str = "main"):
    mv = vif_all[vif_all["panel_id"].eq(panel_id)].sort_values("vif")
    colors = ["#B5482F" if v >= VIF_SEVERE else "#D9822B" if v >= VIF_MODERATE else "#2F6DB5"
              for v in mv["vif"]]
    fig = _new_figure(figsize=(8.4, 5.0), constrained_layout=True)
    ax = fig.subplots()
    ax.barh([_clean(f) for f in mv["feature"]], mv["vif"], color=colors, edgecolor="white")
    for y, v in enumerate(mv["vif"]):
        ax.text(v + 0.1, y, f"{v:.1f}", va="center", fontsize=9)
    ax.axvline(VIF_MODERATE, color="#888", ls="--", lw=1)
    ax.axvline(VIF_SEVERE, color="#B5482F", ls="--", lw=1)
    ax.set_xlabel("Variance Inflation Factor")
    ax.set_title(f"Multicollinearity (VIF) — {panel_id} model")
    ax.set_xlim(0, max(VIF_SEVERE * 1.1, float(mv["vif"].max()) * 1.15))
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    return fig


def figure_correlation_heatmap(spearman_matrix: pd.DataFrame):
    import seaborn as sns

    m = spearman_matrix.copy()
    m.index = [_clean(x) for x in m.index]
    m.columns = [_clean(x) for x in m.columns]
    fig = _new_figure(figsize=(8.5, 7), constrained_layout=True)
    ax = fig.subplots()
    sns.heatmap(m, vmin=-1, vmax=1, cmap="vlag", square=True, annot=True, fmt=".2f",
                annot_kws={"size": 7}, cbar_kws={"label": "Spearman r"}, ax=ax)
    ax.set_title("Predictor–predictor Spearman correlation (main model)")
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", rotation=0)
    return fig


def figure_target_correlations(target_correlations: pd.DataFrame):
    t = target_correlations.sort_values("correlation").copy()
    fig = _new_figure(figsize=(8, 5), constrained_layout=True)
    ax = fig.subplots()
    ax.barh([_clean(f) for f in t["feature"]], t["correlation"], color="#5F8B95", edgecolor="white")
    ax.axvline(0, color="#333", lw=1)
    ax.set_xlabel("Spearman correlation with target (train+validation, leakage-safe)")
    ax.set_title("Predictor–target association (descriptive)")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    return fig


# ---------------------------------------------------------------------------
# CLI: compute, save CSVs + paper figures, print summary
# ---------------------------------------------------------------------------
def main() -> None:
    import os
    import tempfile

    os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "env_innovation_matplotlib"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
    plt.rcParams.update({"savefig.dpi": 300, "axes.titleweight": "bold",
                         "font.family": "DejaVu Sans"})
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    res = run_screening()
    res["near_zero_variance"].to_csv(OUTPUT_DIR / "statistical_screening_near_zero_variance.csv", index=False)
    res["vif"].to_csv(OUTPUT_DIR / "statistical_screening_vif.csv", index=False)

    print("=== (1) Near-zero variance ===")
    flagged = list(res["near_zero_variance"].query("near_zero_variance")["feature"])
    print("near-zero-variance predictors:", flagged if flagged else "NONE")
    print("\n=== (2) VIF ===")
    print(res["vif"].to_string(index=False))

    def _save(fig, name):
        fig.savefig(FIG_DIR / f"{name}.png", bbox_inches="tight")
        fig.savefig(FIG_DIR / f"{name}.pdf", bbox_inches="tight")
        plt.close(fig)
        print(f"  wrote {name}.png / .pdf")

    _save(figure_vif(res["vif"], "main"), "fig8_vif_main")
    corr = res["correlations"]
    if corr["spearman_matrix"] is not None:
        _save(figure_correlation_heatmap(corr["spearman_matrix"]), "fig9_correlation_heatmap")
    if corr["target_correlations"] is not None:
        _save(figure_target_correlations(corr["target_correlations"]), "fig10_target_correlations")
    print("\nDone.")


if __name__ == "__main__":
    main()
