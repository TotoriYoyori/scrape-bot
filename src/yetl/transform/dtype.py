from typing import Callable

import pandas as pd

from yetl.transform.base import TransformStepCollection

# =============== DECLARATIVE WRAPPER AROUND DATA TYPING OPERATIONS ===============
class DTypeTransform(TransformStepCollection):

    @staticmethod
    def upgrade_dtype() -> Callable:
        """Callable factory. Upgrades pandas DataFrame column dtypes to pd-native, nullable versions.

        The transformation currently performs the following upgrades:
            - ``int64`` -> ``Int64``
            - ``float64`` -> ``Float64``
            - ``object`` / ``str`` -> ``string``

        Returns:
            A callable that accepts and returns a DataFrame with upgraded column dtypes.

        Example:
            >>> this_step = upgrade_dtype()
            >>> df = pd.DataFrame({
            ...     "id": [1, 2, None],
            ...     "name": ["Alice", "Bob", None]
            ... })
            >>>
            >>> upgraded = this_step(df)
            >>> upgraded.dtypes
            id               Int64
            name    string[python]
            dtype: object
        """

        def step(df: pd.DataFrame) -> pd.DataFrame:
            numeric_upgrade = {
                col: str(df[col].dtype).capitalize()
                for col in df.columns
                if str(df[col].dtype) in {"int64", "float64"}
            }
            string_upgrade = {
                col: "string"
                for col in df.columns
                if str(df[col].dtype) in {"object", "str"}
            }

            return (df
                .astype(numeric_upgrade)
                .astype(string_upgrade)
            )

        return step

    @staticmethod
    def cast_categorical(
        ignore_columns: list[str] = None,
        pct_threshold: float = 0.05,
    ) -> Callable:
        """Callable factory. Converts low-cardinality string columns to categorical.

        Automatically detects string-like columns with relatively few unique
        values and converts them to pandas ``category`` dtype.

        Args:
            ignore_columns: Optional list of column names to skip.
            pct_threshold: Maximum unique-value ratio allowed for conversion.
                The ratio is calculated as: ``unique_values / non_null_values``

                Columns at or below this threshold will be converted to
                ``category``.

        Returns:
            A callable that accepts and returns a DataFrame with selected
            columns converted to ``category`` dtype.

        Example:
            >>> this_step = cast_categorical(
            ...     ignore_columns=["description"],
            ...     pct_threshold=0.10,
            ... )
            >>> cleaned_df = this_step(df)
        """
        def step(df: pd.DataFrame) -> pd.DataFrame:
            non_null_counts = df.notna().sum()
            unique_counts = df.nunique()

            upgrade_conditions = [
                lambda series: series.name not in (ignore_columns or []),
                lambda series: series.dtype in ["str", "string", "object"],
                lambda series: non_null_counts[series.name] > 0,
                lambda series: unique_counts[series.name] / non_null_counts[series.name] <= pct_threshold,
            ]
            categorical_mapping = {
                col: "category"
                for col in df.columns
                if all(cond(df[col]) for cond in upgrade_conditions)
            }

            return df.astype(categorical_mapping)

        return step
