# app/api/v1/ml/dataset.py

import pandas as pd
import requests


DATASET_URL = "http://127.0.0.1:8000/api/v1/dataset"


def load_dataset(limit: int = 10_000) -> pd.DataFrame:
    response = requests.get(DATASET_URL, params={"limit": limit})
    response.raise_for_status()

    data = response.json()["items"]
    df = pd.DataFrame(data)

    return df
