"""Shared inference helpers for hypothesis result tables."""

import numpy as np
import pandas as pd


def add_holm_correction(frame, p_column="p_value"):
    """Add Holm step-down adjusted p-values and significance flags.

    The raw permutation or null-model p-value remains available unchanged.
    Rows with missing p-values are excluded from the correction and retain
    missing adjusted values.
    """
    result = frame.copy()
    adjusted = pd.Series(np.nan, index=result.index, dtype=float)
    valid = result[p_column].notna()
    if valid.any():
        p_values = result.loc[valid, p_column].astype(float).to_numpy()
        order = np.argsort(p_values, kind="stable")
        sorted_p = p_values[order]
        corrected = np.maximum.accumulate((len(sorted_p) - np.arange(len(sorted_p))) * sorted_p)
        corrected = np.minimum(corrected, 1.0)
        adjusted.iloc[np.flatnonzero(valid.to_numpy())[order]] = corrected
    result["p_value_holm"] = adjusted
    result["significant_holm"] = result["p_value_holm"] < 0.05
    return result
