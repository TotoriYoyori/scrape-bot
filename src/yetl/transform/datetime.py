from typing import Callable

import pandas as pd

from yetl.transform.base import TransformStepCollection

# =============== DECLARATIVE WRAPPER AROUND DATE PARSING OPERATIONS ===============
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
