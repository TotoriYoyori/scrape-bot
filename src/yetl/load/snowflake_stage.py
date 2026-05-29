import snowflake.connector
from src.yetl.load.settings import SnowflakeSettings

# =============== SINK WITH SNOWFLAKE STAGE ===============
def _fetch_login_credentials(settings: SnowflakeSettings) -> dict[str, str]:
    return {
        'user': settings.SNOWFLAKE_USERNAME,
        'password': settings.SNOWFLAKE_PASSWORD,
        'account': settings.SNOWFLAKE_ACCOUNT,
        'warehouse': 'COMPUTE_WH',
        'database': 'AUDIBLE_CATALOG',
        'schema': 'L00_STG'
    }

def upload_to_snowflake_stage(file_path: str) -> None:
    settings = SnowflakeSettings()  # moved here, runs only when called
    credentials = _fetch_login_credentials(settings)
    with snowflake.connector.connect(**credentials) as conn:
        with conn.cursor() as cur:
            cur.execute(f'PUT file:///{file_path} @SCRAPE_CSV AUTO_COMPRESS=TRUE')
