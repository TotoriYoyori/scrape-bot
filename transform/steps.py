import regex
import pandas as pd
import numpy as np

from typing import Dict, Iterable, Callable


# ----- Orchestrator Framework
def transform_data(df: pd.DataFrame, steps: list[Callable]) -> pd.DataFrame:
    for func in steps:
        df = func(df)

    return df


# ----- Step Factories
class StepsFactory:
    @staticmethod
    def trim_prefix(prefix_map: Dict[str, str]) -> Callable[[pd.DataFrame], pd.DataFrame]:
        """
        Remove 'Specified' from the author column and 'Narratedby:' from the narrator column
        """
        def step(df: pd.DataFrame) -> pd.DataFrame:
            res = df.copy()
            for col, prefix in prefix_map.items():
                res[col] = res[col].str.strip(prefix)

            return res

        return step

    @staticmethod
    def replace_null(na_values: Iterable[str]) -> Callable[[pd.DataFrame], pd.DataFrame]:
        """
        Replace 'Not rated yet' with NaN
        """
        def step(df: pd.DataFrame) -> pd.DataFrame:
            return df.replace(na_values, np.nan)

        return step

    @staticmethod
    def extract_stars_ratings() -> Callable[[pd.DataFrame], pd.DataFrame]:
        """
        Extract number of stars into rating_stars and turn into float.
        Replace the comma, extract number of ratings into n_ratings and turn into float
        """
        def step(df: pd.DataFrame) -> pd.DataFrame:
            return (
                df.assign(
                    rating_stars=df["stars"]
                    # .str.extract(r"^(\d+\.?\d*) out of 5 stars\d[\d,]* ratings?$", expand=False)
                    .str.extract(r"^\"?(\d+\.?\d*)", expand=False)
                    .astype("Float64")
                )
                .assign(
                    n_ratings=df["stars"]
                    # .str.extract(r"^\d+\.?\d* out of 5 stars(\d[\d,]*) ratings?$", expand=False)
                    .str.extract(r"(\d[\d,]*)\s+ratings?", expand=False)
                    .str.replace(",", "")
                    .astype("Float64")
                )
                .drop(columns=["stars"])
            )

        return step

    @staticmethod
    def price_string_to_float(
        currency_sep: str = ",", zero_val: str = "Free"
    ) -> Callable[[pd.DataFrame], pd.DataFrame]:
        """
        Explore the price column
        """
        def step(df: pd.DataFrame) -> pd.DataFrame:
            return df.assign(
                price=df["price"]
                .str.replace(currency_sep, "")
                .str.replace(zero_val, "0")
                .astype("Float64")
            )

        return step

    @staticmethod
    def simple_currency_converter() -> Callable[[pd.DataFrame], pd.DataFrame]:
        def step(df: pd.DataFrame) -> pd.DataFrame:
            return df.assign(
                price=df["price"]
                .astype("Float64")
            )

        return step

    @staticmethod
    def cast_string_category(
        category_count_threshold: int
    ) -> Callable[[pd.DataFrame], pd.DataFrame]:
        """
        Automatically cast columns to string/category type according to threshold of unique item count.
        """
        def step(df: pd.DataFrame) -> pd.DataFrame:
            return df.astype(
                {col: "string" for col in df.columns if df[col].dtype == "object"}
            ).astype(
                {
                    col: "category"
                    for col in df.columns
                    if df[col].nunique() <= category_count_threshold
                }
            )

        return step

    @staticmethod
    def convert_datetime(
        datetime_maps: Dict[str, str]
    ) -> Callable[[pd.DataFrame], pd.DataFrame]:
        def step(df: pd.DataFrame) -> pd.DataFrame:
            for dtcol, dtformat in datetime_maps.items():
                df[dtcol] = pd.to_datetime(df[dtcol], format=dtformat)

            return df

        return step

    @staticmethod
    def extract_time() -> Callable[[pd.DataFrame], pd.DataFrame]:
        def step(df: pd.DataFrame) -> pd.DataFrame:
            time_arr = np.array(
                df["runtime"]
                .str.extract(
                    "^(?:Less than 1 minute|(\d+) hrs?(?: and (\d+) mins?)?|(\d+) mins?)$"
                )
                .fillna(0)
                .astype("int64")
            )
            time_arr[:, 0] = time_arr[:, 0] * 60

            return (
                df
                .assign(time=np.sum(time_arr, axis=1))
                .drop(columns=["runtime"])
            )

        return step

    @staticmethod
    def convert_currency() -> Callable[[pd.DataFrame], pd.DataFrame]:
        """
        Transform prices to USD (multiply times 0.012)
        """
        def step(df: pd.DataFrame) -> pd.DataFrame:
            return df.assign(price=lambda x: round(x["price"] * 0.012 + 1e-9, 2))

        return step

    @staticmethod
    def capitalize() -> Callable[[pd.DataFrame], pd.DataFrame]:
        def step(df: pd.DataFrame) -> pd.DataFrame:
            return df.assign(
                author=lambda x: x["author"].str.title(),
                narrator=lambda x: x["narrator"].str.title(),
                language=lambda x: x["language"].str.title()
            )

        return step

    @staticmethod
    def keep_latest_release_date() -> Callable[[pd.DataFrame], pd.DataFrame]:
        def step(df: pd.DataFrame) -> pd.DataFrame:
            return df.drop_duplicates(
                subset=["name", "author", "narrator", "price"], keep="last"
            )

        return step

    @staticmethod
    def advance_regex() -> Callable[[pd.DataFrame], pd.DataFrame]:
        def clean_authors(text):
            if pd.isna(text):
                return []

            # Insert space between lowercase-to-uppercase boundaries.
            text = regex.sub(r"(?<=\p{Ll})(?=\p{Lu})", " ", text)

            # Add space after periods followed by uppercase characters.
            text = regex.sub(r"\.(?=\p{Lu})", ". ", text)

            authors = regex.split(r"\s*,\s*", text)

            return ", ".join([a.strip() for a in authors if a.strip()])

        def step(df: pd.DataFrame) -> pd.DataFrame:
            return (
                df.assign(author=df["author"].apply(clean_authors))
                .assign(narrator=df["narrator"].apply(clean_authors))
                .assign(name=df["name"].str.title())
            )

        return step
