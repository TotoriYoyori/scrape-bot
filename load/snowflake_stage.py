import snowflake.connector
from config import Config


def upload_to_snowflake_stage(file_path: str) -> None:
    credentials = _fetch_login_credentials()
    with snowflake.connector.connect(**credentials) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f'PUT file:///{file_path} @SCRAPE_CSV AUTO_COMPRESS=TRUE'
            )


def _fetch_login_credentials(config: Config) -> dict[str, str]:
    return {
        'user': config.SNOWFLAKE_USERNAME,
        'password': config.SNOWFLAKE_PASSWORD,
        'account': config.SNOWFLAKE_ACCOUNT,
        'warehouse': 'COMPUTE_WH',
        'database': 'AUDIBLE_CATALOG',
        'schema': 'L00_STG'
    }
