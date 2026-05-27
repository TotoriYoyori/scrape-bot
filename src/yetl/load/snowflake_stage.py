import snowflake.connector
from yetl.load.settings import snowflake_settings


def upload_to_snowflake_stage(file_path: str) -> None:
    credentials = _fetch_login_credentials()
    with snowflake.connector.connect(**credentials) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f'PUT file:///{file_path} @SCRAPE_CSV AUTO_COMPRESS=TRUE'
            )


def _fetch_login_credentials() -> dict[str, str]:
    return {
        'user': snowflake_settings.SNOWFLAKE_USERNAME,
        'password': snowflake_settings.SNOWFLAKE_PASSWORD,
        'account': snowflake_settings.SNOWFLAKE_ACCOUNT,
        'warehouse': 'COMPUTE_WH',
        'database': 'AUDIBLE_CATALOG',
        'schema': 'L00_STG'
    }
