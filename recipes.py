from transform import StepsFactory


audible_clean_steps = [
    StepsFactory.replace_null(["Not rated yet", "nonymous", "Not Yet Known"]),
    StepsFactory.extract_stars_ratings(),
    StepsFactory.price_string_to_float(),
    StepsFactory.simple_currency_converter(),
    StepsFactory.cast_string_category(50),
    StepsFactory.convert_datetime({"release_date": "%m-%d-%y"}),
    StepsFactory.extract_time(),
    StepsFactory.capitalize(),
    StepsFactory.keep_latest_release_date(),
]
