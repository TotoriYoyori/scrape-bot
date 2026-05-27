from typing import Callable

import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import numpy as np

from src.etl.services.utils import TransformStepCollection

# ================ ORCHESTRATOR TRANSFORM STEP ===============
def transform_data(
    steps: list[Callable],
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Use to process a series of Callable with its arguments on the DF, and return the final result.

    Args:
        steps: a list of Callables that accepts the dataframe as arguments. The steps' order matter.
        df: A dataframe to be cleaned.

    Returns:
        The final cleaned dataframe.
    """
    for step in steps:
        df = step(df)

    return df

# =============== CLEANING FUNCTIONS ===============

    # ========== CASTING AND TYPING ==========
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
                .astype(**numeric_upgrade)
                .astype(**string_upgrade)
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

    # ========== DATE PARSINGS ==========
class DateTransform(TransformStepCollection):

    @staticmethod
    def parse_date_columns(
        format_mapping: dict[str, str],
        slice_length: int | None = 10,
    ) -> Callable:
        """Callable factory. Parses date-like DataFrame columns into datetimes.

        Supports per-column datetime formats with optional string slicing.

        Args:
            format_mapping:
                Mapping of DataFrame column names to their corresponding
                datetime format strings passed into ``pd.to_datetime``.
            slice_length:
                Optional number of characters to slice from the beginning
                of each string value before parsing.

        Returns:
            A callable that accepts and returns a DataFrame with parsed datetime columns.

        Example:
            >>> this_step = parse_date_columns({
            ...     "created_date": "%Y-%m-%d",
            ...     "updated_at": "%Y-%m-%d %H:%M:%S",
            ... })
            >>> cleaned_df = this_step(df)
        """

        def step(df: pd.DataFrame) -> pd.DataFrame:
            assign_mapping = {
                col: pd.to_datetime(
                    (
                        df[col].str.slice(0, slice_length)
                        if slice_length is not None
                        else df[col]
                    ),
                    format=date_format,
                    errors="coerce",
                )
                for col, date_format in format_mapping.items()
            }

            return df.assign(**assign_mapping)

        return step

    @staticmethod
    def parse_military_time_column(
        column: str,
        output_column: str | None = None,
    ) -> Callable:
        """Callable factory. Parses HHMM military time values.

        Converts integer-like HHMM military time values into pandas timedelta
        objects using hour and minute arithmetic.

        Example conversions:
            - ``845`` -> ``08:45``
            - ``1330`` -> ``13:30``
            - ``1`` -> ``00:01``

        Args:
            column: The DataFrame column containing HHMM-style military time values.
            output_column:
                Optional output column name for the parsed timedelta values,
                if omitted, the source column is overwritten.

        Returns:
            A callable that accepts and returns a DataFrame with parsed timedelta values.

        Example:
            >>> this_step = parse_military_time_column(
            ...     column="time_occ",
            ...     output_column="time_occ_delta",
            ... )
            >>>
            >>> cleaned_df = this_step(df)
        """

        def step(df: pd.DataFrame) -> pd.DataFrame:
            time_value = (
                pd.to_numeric(df[column], errors="coerce")
                .fillna(0)
                .astype("int16")
            )

            hours = time_value // 100
            minutes = time_value % 100

            return df.assign(**{
                output_column or column: (
                    pd.to_timedelta(hours, unit="h")
                    + pd.to_timedelta(minutes, unit="m")
                )
            })

        return step

    @staticmethod
    def combine_date_and_time(
        date_column: str,
        time_column: str,
        output_column: str,
        columns_to_drop: list[str] | None = None,
    ) -> Callable:
        """Callable factory. Combines date and time columns.

        Args:
            date_column: The column containing date or datetime values.
            time_column: The column containing timedelta-compatible time offsets.
            output_column: The name of the output column containing the combined datetime.
            columns_to_drop: Optional list of columns to drop after the combination step.

        Returns:
            A callable transformation function that accepts and returns a
            pandas DataFrame with the combined datetime column.

        Example:
            >>> this_step = combine_date_and_time(
            ...     date_column="date_occ",
            ...     time_column="time_occ_delta",
            ...     output_column="occurred_at",
            ...     columns_to_drop=["time_occ", "time_occ_delta"],
            ... )
            >>>
            >>> cleaned_df = this_step(df)
        """

        def step(df: pd.DataFrame) -> pd.DataFrame:
            date_col = df[date_column]
            time_col = df[time_column]

            is_datetime = date_col.dtype.kind == "M" or isinstance(date_col.dtype, pd.DatetimeTZDtype)
            is_timedelta = time_col.dtype.kind == "m"

            if not is_datetime:
                raise TypeError(f"Column '{date_column}' must be datetime dtype, got '{date_col.dtype}'.")
            if not is_timedelta:
                raise TypeError(f"Column '{time_column}' must be timedelta dtype, got '{time_col.dtype}'.")

            result = df.assign(**{output_column: date_col + time_col})
            if columns_to_drop:
                result = result.drop(columns=columns_to_drop)

            return result

        return step

    # ========== STRING OPS ==========
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


    # ========== NULL OPS ==========
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
