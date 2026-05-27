from typing import Callable

import pandas as pd
import numpy as np

from yetl.transform.base import TransformStepCollection

# =============== DECLARATIVE WRAPPER AROUND PANDAS NULL OPERATIONS ===============
class NullTransform(TransformStepCollection):

    @staticmethod
    def nullify_value(null_map: dict[str, str]) -> Callable:
        """Callable factory. Replaces null-like values with actual nulls.

        Converts placeholder values such as ``""``, ``"NULL"``, or ``"N/A"``
        into Python ``None`` values for selected columns.

        Args:
            null_map: Maps column names to the value that should be treated as null.

        Returns:
            A callable that accepts and returns a DataFrame with normalized null values.

        Example
            >>> this_step = nullify_value({
            ...     "status": "UNKNOWN",
            ...     "notes": "NULL",
            ... })
            >>> cleaned_df = this_step(df)
        """
        def step(df: pd.DataFrame) -> pd.DataFrame:
            assign_mapping = {
                col: lambda x, col=col: x[col].replace(null_like, None)
                for col, null_like in null_map.items()
            }

            return df.assign(**assign_mapping)

        return step

    @staticmethod
    def nullify_range(range_map: dict[str, tuple[int, int]]) -> Callable:
        """Callable factory. Nullifies values outside an allowed numeric range.

        Keeps values that fall within the configured range and replaces all
        other values with ``pd.NA``.

        Args:
            range_map: Maps column names to their allowed numeric range.
                Each tuple is interpreted as: ``(minimum_exclusive, maximum_inclusive)``

        Returns:
            A callable that accepts and returns a DataFrame with invalid
            values replaced by ``pd.NA``.

        Example:
            >>> this_step = nullify_range({
            ...     "age": (0, 120),
            ...     "score": (0, 100),
            ... })
            >>> cleaned_df = this_step(df)
        """

        def _nullable_dtype(series: pd.Series) -> str:
            if series.dtype.kind == "f":
                return "Float64"
            if series.dtype.kind in ("i", "u"):
                return "Int64"
            raise TypeError(f"Column '{series.name}' has non-numeric dtype '{series.dtype}'. Expected int or float.")

        def step(df: pd.DataFrame) -> pd.DataFrame:
            assign_mapping = {
                col: lambda x, col=col, notna_range=notna_range: pd.array(
                    np.where(
                        (x[col] > notna_range[0]) & (x[col] <= notna_range[1]),
                        x[col],
                        pd.NA,
                    ),
                    dtype=_nullable_dtype(x[col]),
                )
                for col, notna_range in range_map.items()
            }
            return df.assign(**assign_mapping)

        return step

    @staticmethod
    def dropna_by_threshold(
        pct_threshold: float = 0.05,
    ) -> Callable:
        """Callable factory. Drops rows with nulls in low-null columns.

        Automatically finds columns with relatively few missing values and
        drops rows where those columns contain nulls.

        Should ONLY be used in Data Science workflow to lazily trim nulls.

        Args:
            pct_threshold:
                Maximum allowed null percentage for a column to be included
                in row filtering.

        Returns:
            A callable that accepts and returns a DataFrame with rows removed
            based on null thresholds.

        Example:
            >>> this_step = dropna_by_threshold(pct_threshold=0.02)
            >>> cleaned_df = this_step(df)
        """
        def step(df: pd.DataFrame) -> pd.DataFrame:
            null_pct = df.isna().mean()
            to_drop = null_pct[null_pct <= pct_threshold].index.tolist()

            return df.dropna(subset=to_drop)

        return step
