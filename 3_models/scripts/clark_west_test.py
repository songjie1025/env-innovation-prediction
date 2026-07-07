"""Clark-West (2007) test for the delta corrected-level forecasts.

The persistence-adjusted corrected-level model nests the history-only benchmark
(a zero predicted change reproduces the anchor, i.e. the benchmark forecast).
Clark and West (2007) give an MSPE-adjusted statistic for exactly this nested
setting, correcting for the extra estimation noise the larger model introduces.

For each panel we test H0: the covariate-based corrected-level model does not
improve on the history-only benchmark, against the one-sided alternative that it
does. A large positive statistic / small p-value means the external predictors
add statistically significant incremental predictive value beyond persistence.

Input : 3_models/outputs/persistence_adjusted_validation_selected_test_level_correction_predictions.csv
Output: 3_models/outputs/persistence_adjusted_clark_west_test.csv
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from model_config import OUTPUT_DIR

PRED_PATH = OUTPUT_DIR / "persistence_adjusted_validation_selected_test_level_correction_predictions.csv"
OUT_PATH = OUTPUT_DIR / "persistence_adjusted_clark_west_test.csv"


def clark_west(observed: np.ndarray, benchmark: np.ndarray, model: np.ndarray) -> dict[str, float]:
    """Clark-West MSPE-adjusted statistic (one-sided). Benchmark nested in model."""
    e_benchmark = observed - benchmark
    e_model = observed - model
    # f_t = benchmark squared error - (model squared error - adjustment term)
    f = e_benchmark**2 - (e_model**2 - (benchmark - model) ** 2)
    n = len(f)
    f_bar = float(np.mean(f))
    # Newey-West-free se (iid); adequate for a short one-step test block
    se = float(np.std(f, ddof=1) / np.sqrt(n))
    cw_stat = f_bar / se if se > 0 else np.nan
    p_value = float(1.0 - stats.norm.cdf(cw_stat)) if np.isfinite(cw_stat) else np.nan
    return {
        "n": n,
        "mspe_benchmark": float(np.mean(e_benchmark**2)),
        "mspe_model": float(np.mean(e_model**2)),
        "cw_mean_adjusted": f_bar,
        "cw_statistic": cw_stat,
        "cw_p_value_one_sided": p_value,
        "significant_5pct": bool(np.isfinite(cw_stat) and p_value < 0.05),
    }


def main() -> None:
    preds = pd.read_csv(PRED_PATH)
    preds = preds[preds["forecast_block"].eq("test")].copy()
    # Drop anchor-gap rows that carry no corrected-level prediction.
    preds = preds.dropna(
        subset=["observed_level", "history_only_prediction", "corrected_level_prediction"]
    )
    rows = []
    for panel_id, group in preds.groupby("panel_id"):
        stat = clark_west(
            group["observed_level"].to_numpy(dtype=float),
            group["history_only_prediction"].to_numpy(dtype=float),
            group["corrected_level_prediction"].to_numpy(dtype=float),
        )
        rows.append(
            {
                "panel_id": panel_id,
                "panel_label": group["panel_label"].iloc[0],
                "family": group["family"].iloc[0],
                "best_model": group["best_model"].iloc[0],
                **stat,
            }
        )
    result = pd.DataFrame(rows).sort_values("panel_id").reset_index(drop=True)
    result.to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH}")
    cols = ["panel_id", "family", "n", "mspe_benchmark", "mspe_model",
            "cw_statistic", "cw_p_value_one_sided", "significant_5pct"]
    print(result[cols].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
