
import pandas as pd
from src.transform import StepsFactory, transform_data


audible_clean_steps = [
    StepsFactory.replace_null(["Not rated yet", "Anonymous", "Not Yet Known"]),
    StepsFactory.extract_stars_ratings(),
    StepsFactory.price_string_to_float(),
    StepsFactory.simple_currency_converter(),
    StepsFactory.cast_string_category(50),
    StepsFactory.convert_datetime({"release_date": "%d-%m-%y"}),
    StepsFactory.extract_time(),
    StepsFactory.capitalize(),
    StepsFactory.keep_latest_release_date(),
]

this_df = pd.read_csv("output/export_audible_dirty_20260526.csv")

cleaned_df = transform_data(this_df, audible_clean_steps)
cleaned_df.to_csv("cleaned_audible.csv", index=False)