import os
import pandas as pd
import logging

# ----- Logging Setups
logging.basicConfig(level=logging.INFO)


# ----- Public API
def extract_audible_csv(file_path: str) -> pd.DataFrame:
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        raise FileNotFoundError
