from typing import Callable

import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc

from yetl.transform.base import TransformStepCollection

# =============== DECLARATIVE WRAPPER AROUND PANDAS STRING OPS ===============
class StringTransform(TransformStepCollection):

    @staticmethod
    def trim_regex_whitespace(col_names: list[str]) -> Callable:
        """Callable factory. Normalizes repeated whitespace.

        The transformation requires importing ``pyarrow.compute.replace_substring_regex``
        And setting up pd.options to uses pyarrow type string.

        Args:
            col_names:
                A list of DataFrame column names whose string values should
                have repeated whitespace normalized.

        Returns:
            A callable that accepts and returns a pandas DataFrame
            with normalized whitespace in the specified columns.

        Example:
            >>> this_step = trim_regex_whitespace(
            ...     col_names=["address", "description"]
            ... )
            >>> cleaned_df = this_step(df)
        """
        def step(df: pd.DataFrame) -> pd.DataFrame:
            assign_mapping = {
                col: lambda x, col=col: pd.Series(
                    pc.replace_substring_regex(
                        pa.chunked_array(x[col]),
                        pattern=r"\s+",
                        replacement=" "
                    ),
                    dtype="string[pyarrow]",
                    index=x.index,
                )
                for col in col_names
            }
            return df.assign(**assign_mapping)

        return step

    @staticmethod
    def normalize_trim_case(case_map: dict[str, list]) -> Callable:
        """Callable factory. Trims and normalizes string casing.

        The transformation requires importing ``pyarrow.compute.replace_substring_regex``
        And setting up pd.options to uses pyarrow type string.

        Args:
            case_map: Map specific string case to lists of target column names.
                Supported keys: ``"title"``, ``"capitalize"``

                Example:
                    >>> {
                    ...     "title": ["street_name", "city"],
                    ...     "capitalize": ["status"]
                    ... }

        Returns:
            A callable that accepts and returns a pandas DataFrame
            with trimmed and normalized string columns.

        Example:
            >>> this_step = normalize_trim_case({
            ...     "title": ["street_name"],
            ...     "capitalize": ["status"]
            ... })
            >>>
            >>> cleaned_df = this_step(df)
        """

        def _apply(series: pd.Series, case_fn: Callable) -> pd.Series:
            arr = pa.chunked_array(series.astype("string"))
            arr = pc.utf8_trim_whitespace(arr)
            arr = case_fn(arr)

            return pd.Series(arr, dtype="string[pyarrow]", index=series.index)

        def step(df: pd.DataFrame) -> pd.DataFrame:
            to_title_mapping = {
                col: lambda x, col=col: _apply(x[col], pc.utf8_title)
                for col in case_map.get("title", [])
            }
            to_capitalize_mapping = {
                col: lambda x, col=col: _apply(x[col], pc.utf8_capitalize)
                for col in case_map.get("capitalize", [])
            }

            return (df
                .assign(**to_capitalize_mapping)
                .assign(**to_title_mapping)
            )

        return step

    @staticmethod
    def merge_string_columns(
        col_to_merge: list[str],
        new_merge_name: str,
        delimiter: str = '/'
    ) -> Callable:
        """Callable factory. Merges multiple string columns into one column.

        Combines the values of several columns into a single string column
        using the provided delimiter.

        Args:
            col_to_merge: List of column names to combine in order.
            new_merge_name: Name of the final merged output column.
            delimiter: String placed between merged values. Defaults to ``"/"``.

        Returns:
            A callable that accepts and returns a DataFrame with the merged
            column added.

        Example:
            >>> this_step = merge_string_columns(
            ...     col_to_merge=["city", "state"],
            ...     new_merge_name="location",
            ...     delimiter=", "
            ... )
            >>> cleaned_df = this_step(df)
        """
        def step(df: pd.DataFrame) -> pd.DataFrame:
            cols = df[col_to_merge].astype("str")
            merged = (cols.iloc[:, 0]
                .str.cat(
                    [cols.iloc[:, i] for i in range(1, len(cols.columns))],
                    sep=delimiter,
                    na_rep="",
                )
                .str.strip(delimiter)
            )
            return (df
                .assign(**{new_merge_name: merged})
                .drop(columns=[c for c in col_to_merge if c != new_merge_name])
            )

        return step

    @staticmethod
    def replace_values(col: str, col_mapping: dict[str, str]) -> Callable:
        """Callable factory. Replaces values in a column using a mapping.

        Updates values in a column based on the provided replacement map.

        Args:
            col: The column to update.
            col_mapping: Maps existing values to their replacement values.

        Returns:
            A callable that accepts and returns a DataFrame with updated values.

        Example:
            >>> this_step = replace_values(
            ...     col="gender",
            ...     col_mapping={"M": "Male", "F": "Female"}
            ... )
            >>> cleaned_df = this_step(df)
        """

        def step(df: pd.DataFrame) -> pd.DataFrame:
            return df.assign(**{col: lambda x: x[col].replace(col_mapping)})

        return step
