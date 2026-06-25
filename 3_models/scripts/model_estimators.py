from __future__ import annotations

from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_linear_model_candidates(random_state: int = 42) -> dict[str, Pipeline]:
    """Create interpretable linear candidates with preprocessing inside each pipeline."""
    candidates: dict[str, Pipeline] = {
        "linear_regression": _linear_pipeline(LinearRegression()),
    }
    for alpha in [0.1, 1.0, 10.0]:
        candidates[f"ridge_alpha_{_format_number(alpha)}"] = _linear_pipeline(Ridge(alpha=alpha))
    for alpha in [0.001, 0.01, 0.1, 1.0]:
        candidates[f"lasso_alpha_{_format_number(alpha)}"] = _linear_pipeline(
            Lasso(
                alpha=alpha,
                max_iter=20000,
                random_state=random_state,
            )
        )
    for alpha in [0.001, 0.01, 0.1, 1.0]:
        for l1_ratio in [0.2, 0.5, 0.8]:
            candidates[
                f"elastic_net_alpha_{_format_number(alpha)}_l1_{_format_number(l1_ratio)}"
            ] = _linear_pipeline(
                ElasticNet(
                    alpha=alpha,
                    l1_ratio=l1_ratio,
                    max_iter=20000,
                    random_state=random_state,
                )
            )
    return candidates


def _linear_pipeline(model) -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("scaler", StandardScaler()),
            ("model", model),
        ]
    )


def _format_number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)
