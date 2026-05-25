import datetime as dt
import os
from pathlib import Path

import pandas as pd
from prefect import flow, get_run_logger, task

from recipes import audible_clean_steps
from src.extract import extract_audible_csv
from src.load import upload_to_snowflake_stage
from src.main import scrape_site
from src.notification import email_notify, is_workday
from src.transform import transform_data


@task
def scrape(category_name: str, output_path: str) -> None:
    """Scrape Audible and save to dynamic file path."""
    scrape_site(category_name=category_name, output_path=output_path)


@task(retries=5, retry_delay_seconds=5)
def file_exists(file_path: str) -> bool:
    print(f"Checking if {file_path} exists...")
    if os.path.exists(file_path):
        return True

    raise FileNotFoundError(f"{file_path} not found.")


@task
def read_recently_export_csv(dirty_file_path: str) -> pd.DataFrame:
    return extract_audible_csv(dirty_file_path)


@task
def clean_audible_df(df: pd.DataFrame) -> pd.DataFrame:
    return transform_data(df, audible_clean_steps)


@task
def export_audible_df(df: pd.DataFrame, clean_file_path: str) -> str:
    df.to_csv(clean_file_path, index=False)
    print(f"Clean CSV exported to {clean_file_path}")
    return clean_file_path


@task
def send_to_snowflake(clean_file_path: str) -> None:
    upload_to_snowflake_stage(clean_file_path)


@task
def email_the_boss(clean_file_path: str) -> None:
    today = dt.date.today()
    if not is_workday(today):
        print("Today is not a workday, skipping email.")
        return

    email_notify(clean_file_path)
    print(f"Email sent to boss with {clean_file_path}")


@flow
def audible_etl(category_name: str) -> None:
    """ETL flow with fully dynamic filenames."""
    logger = get_run_logger()
    today_str = "20260324"
    dirty_file_path = str(
        Path(f"flatfiles/dirty/export_audible_dirty_{today_str}.csv").resolve()
    )
    clean_file_path = str(
        Path(f"flatfiles/clean/export_audible_clean_{today_str}.csv").resolve()
    )

    logger.info(
        f"/~/ Scraping from Audible --> {category_name}, saving to\n{dirty_file_path} ..."
    )
    scrape(category_name=category_name, output_path=dirty_file_path)

    if not file_exists(dirty_file_path):
        logger.error(
            "/!/ Scraped CSV file was not found in time ... Shutting down ETL flow."
        )
        raise TimeoutError

    logger.info(f"/~/ Beginning data cleaning, saving to\n{clean_file_path} ...")
    raw_df = read_recently_export_csv(dirty_file_path)
    clean_df = clean_audible_df(raw_df)
    export_audible_df(clean_df, clean_file_path)

    if not file_exists(clean_file_path):
        logger.error(
            "/!/ Clean CSV file was not found in time ... Shutting down ETL flow."
        )
        raise TimeoutError

    send_to_snowflake(clean_file_path)
    logger.info(f"Sent {clean_file_path} to Snowflake stage")

    email_the_boss(clean_file_path)
