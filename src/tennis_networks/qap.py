"""Permutation tests for network data (course slide L04).

* `qap_correlation`: Quadratic Assignment Procedure for dyadic hypotheses. Rows and columns of one
  matrix are permuted together, which keeps its structure (degrees, reciprocity, cliques) but breaks
  its alignment with the other matrix.
* `permutation_regression`: monadic hypotheses. The dependent vector is permuted and the regression
  refitted; each coefficient is compared with its permutation distribution.
"""

import numpy as np


def _offdiag(m):
    m = np.asarray(m, dtype=float)
    return m[~np.eye(m.shape[0], dtype=bool)]


def qap_correlation(x, y, n_perm=999, seed=0):
    """Pearson correlation between two n x n matrices (diagonal excluded) and its QAP p-value.

    Returns the observed correlation, the mean of the permuted correlations and the two-sided p-value
    with the +1 correction.
    """
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if x.shape != y.shape or x.shape[0] != x.shape[1]:
        raise ValueError("QAP needs two square matrices of the same size")
    xv = _offdiag(x)
    observed = float(np.corrcoef(xv, _offdiag(y))[0, 1])
    rng = np.random.default_rng(seed)
    n = y.shape[0]
    perm = np.empty(n_perm)
    for k in range(n_perm):
        p = rng.permutation(n)
        perm[k] = np.corrcoef(xv, _offdiag(y[np.ix_(p, p)]))[0, 1]
    extreme = np.sum(np.abs(perm) >= abs(observed) - 1e-12)
    return {"r": observed, "perm_mean": float(perm.mean()), "p_value": (extreme + 1) / (n_perm + 1)}


def _ols(y, design):
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    fitted = design @ coef
    ss_res = float(((y - fitted) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return coef, 1 - ss_res / ss_tot


def collinearity_diagnostics(x, names=None):
    """Return pairwise predictor correlations and the condition number of standardized X."""
    x = np.asarray(x, dtype=float).reshape(len(x), -1)
    if x.shape[1] == 0:
        return {"max_abs_correlation": float("nan"), "condition_number": float("nan"), "correlations": {}}
    labels = list(names or [f"x{j}" for j in range(x.shape[1])])
    corr = np.corrcoef(x, rowvar=False) if x.shape[1] > 1 else np.array([[1.0]])
    correlations = {
        f"{labels[i]}~{labels[j]}": float(corr[i, j]) for i in range(x.shape[1]) for j in range(i + 1, x.shape[1])
    }
    z = (x - x.mean(axis=0)) / x.std(axis=0)
    return {
        "max_abs_correlation": max((abs(v) for v in correlations.values()), default=0.0),
        "condition_number": float(np.linalg.cond(z)) if x.shape[1] > 1 else 1.0,
        "correlations": correlations,
    }


def permutation_regression(y, x, names, n_perm=999, seed=0):
    """OLS of y on the columns of x (standardised, with intercept) and permutation p-values.

    Variables are standardised so that coefficients are comparable (standardised betas).
    Returns one row per predictor: beta, two-sided p-value, and the model R squared.
    """
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float).reshape(len(y), -1)
    z = (x - x.mean(axis=0)) / x.std(axis=0)
    yz = (y - y.mean()) / y.std()
    design = np.column_stack([np.ones(len(yz)), z])
    coef, r2 = _ols(yz, design)
    diagnostics = collinearity_diagnostics(x, names)
    rng = np.random.default_rng(seed)
    perm = np.array([_ols(rng.permutation(yz), design)[0] for _ in range(n_perm)])
    rows = []
    for j, name in enumerate(names, start=1):
        extreme = np.sum(np.abs(perm[:, j]) >= abs(coef[j]) - 1e-12)
        rows.append(
            {
                "predictor": name,
                "beta": float(coef[j]),
                "p_value": (extreme + 1) / (n_perm + 1),
                "r2": r2,
                **diagnostics,
            }
        )
    return rows
