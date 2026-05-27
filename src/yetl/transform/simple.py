from typing import Callable

import pandas as pd

from yetl.transform.base import TransformStepCollection

# =============== SIMPLE DECLARATIVE WRAPPER AROUND PANDAS OPERATION ===============
class SimpleTransform(TransformStepCollection):
    @staticmethod
    def drop_columns(column_names: list[str]) -> Callable:
        """Wrapper around pd.DataFrame.drop(columns=[column_names]).

        Silently ignores requested columns that are not present in the DataFrame.
        """

        def step(df: pd.DataFrame) -> pd.DataFrame:
            return df.drop(columns=[col for col in column_names if col in df.columns])

        return step

    @staticmethod
    def reset_index(drop: bool = True) -> Callable:
        """Wrapper around pd.DataFrame.reset_index()"""

        def step(df: pd.DataFrame) -> pd.DataFrame:
            return df.reset_index(drop=drop)

        return step

    @staticmethod
    def rename_columns(rename_map: dict[str, str]) -> Callable:
        """Wrapper around pd.DataFrame.rename_columns(columns={old: new})"""

        def step(df: pd.DataFrame) -> pd.DataFrame:
            return df.rename(columns=rename_map)

        return step

    @staticmethod
    def cast_columns(type_mapping: dict[str, str]) -> Callable:
        """Wrapper around pd.DataFrame.astype(dict[col_name, type])"""

        def step(df: pd.DataFrame) -> pd.DataFrame:
            return df.astype(type_mapping)

        return step

    @staticmethod
    def null_fill(fill_map: dict[str, str]) -> Callable:
        """Wrapper around pd.DataFrame.fillna(dict[col_name, value])"""
        def step(df: pd.DataFrame) -> pd.DataFrame:
            return df.fillna(fill_map)

        return step

    @staticmethod
    def rename_columns_by_replace(pattern_map: dict[str, str]) -> Callable:
        """Callable factory. Renames DataFrame columns using string replacement.

        Intended for simple use only where column names is known.

        Args:
            pattern_map: A dictionary mapping substrings to their replacement values.

        Returns:
            A callable that will return a new DataFrame with renamed columns.

        Example:
            >>> this_step = rename_columns_by_replace({" ": "_", "-": "_"})
            >>> df = pd.DataFrame(columns=["first name", "user-id"])
            >>> this_step(df).columns
            Index(['first_name', 'user_id'], dtype='object')
        """

        def step(df: pd.DataFrame) -> pd.DataFrame:
            for pattern_to_replace, target in pattern_map.items():
                df = df.rename(columns={
                    col: str(col).replace(pattern_to_replace, target)
                    for col in df.columns
                    if pattern_to_replace in str(col)
                })

            return df

        return step
