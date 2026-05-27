import os
import asyncio
from functools import wraps
from httpx import AsyncClient
from typing import Callable
from io import StringIO
from itertools import batched

import asyncer
import pandas as pd

from src.extract.settings import ExtractCSVSettings


# =============== INTERNAL FUNCTIONS ===============
def _get_temporary_client(func: Callable) -> Callable:
    """Get a one-time use AsyncClient pool that will automatically open and close.

    Used as a decorator above your desired function. Best used for one-time low frequency calls.

    Args:
        func: A function to put this decorator above. Must have a use for an AsyncClient
        client as part of its dependency parameters.

    Returns:
        The function provided with an AsyncClient object.

    Example:
        >>>    @_get_temporary_client
        >>>    async def i_need_client_to_fetch_data(client, *args):
        >>>        pass
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with AsyncClient() as client:
            return await func(client, *args, **kwargs)

    return wrapper


async def _fetch_socrata_api(
    client: AsyncClient,
    data_source_url: str,
    offset: int,
    limit: int
) -> pd.DataFrame:
    """Make an API call to extract source data.

    Formula is `records[offset: offset + limit]`. Will use the configured app's settings
    by default unless overridden in the parameter.

    Args:
        client: An AsyncClient object dependency injections.
        offset: The number of records to skip, this should be provided.
        limit: The number of records to pull. Can use app's settings.

    Returns:
        A pandas DataFrame with only basic na_values catch.
    """
    params = {"$limit": limit, "$offset": offset}
    headers = {
        "Accept": "text/csv",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36",
    }
    response = await client.get(data_source_url, params=params, headers=headers)

    response.raise_for_status()

    return pd.read_csv(StringIO(response.text))


# =============== PUBLIC API FUNCTIONS ===============
def extract_csv(file_path: str) -> pd.DataFrame:
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        raise FileNotFoundError


async def extract_socrata_csv(
    *,
    data_source_url: str,
    seed_limit: int = 100_000,
    chunk_limit: int = 1_000,
    concurrent_batch_limit: int = 25,
    sleep_dur: float = 1.0,
) -> pd.DataFrame:
    """This function handles batching and compiling concurrent workflow to call the API.

    Uses async framework to speed up what would take forever.

    Args:
        data_source_url: The url to extract data from.
        seed_limit: The total number of records to pull.
        chunk_limit: The total number of records PER API call.
        concurrent_batch_limit:
            The number of API calls at a time in concurrency. The higher the value,
            the faster the function, but will be at risk of throttling or ban from the API provider.
        sleep_dur: The duration in seconds to sleep between each API call.

    Raises:
        ValidationError: If passed in values do not meet the constraint imposed by the internal pydantic contract.

    Returns:
        The final raw pandas DataFrame.
    """
    config = ExtractCSVSettings(
        data_source_url=data_source_url,
        seed_limit=seed_limit,
        chunk_limit=chunk_limit,
        concurrent_batch_limit=concurrent_batch_limit,
        sleep_dur=sleep_dur,
    )
    offset_checkpoints = range(0, config.seed_limit, config.chunk_limit)

    all_results = []
    async with AsyncClient() as client:
        for batch in batched(offset_checkpoints, config.concurrent_batch_limit):
            async with asyncer.create_task_group() as tg:
                tg_results = [
                    tg.soonify(_fetch_socrata_api)(
                        client,
                        config.data_source_url,
                        batch_offset,
                        config.chunk_limit
                    )
                    for batch_offset in batch
                ]
            all_results.extend(tg_results)

            await asyncio.sleep(config.sleep_dur)

    return pd.concat((r.value for r in all_results), ignore_index=True)


async def extract_socrata_csv_lite(*, data_source_url: str, limit: int = 1_000) -> pd.DataFrame:
    """Pull a single batch of records in one API call.

    For large paginated pulls use extract_csv_api instead.

    Args:
        data_source_url: The url to extract data from.
        limit: The number of records to pull. Max 1000.

    Returns:
        A pandas DataFrame with one page of records.
    """
    return await extract_socrata_csv(
        data_source_url=data_source_url,
        seed_limit=limit,
        chunk_limit=limit,
        concurrent_batch_limit=1,
    )
