import pandas as pd
import pycountry

# Path to the Kaggle CSV (place under data/)
CSV_PATH = "data/companies-2023-q4-sm.csv"
USE_ROWS = 500_000  # Adjust for performance vs. coverage

_cached_df = None

def get_country_name(code):
    """
    Convert a 2-letter country_code (e.g. 'US', 'GB', 'FR') into the full country name.
    Returns empty string on missing/invalid code.
    """
    if not code or not isinstance(code, str):
        return ""
    try:
        return pycountry.countries.get(alpha_2=code.upper()).name
    except:
        return ""

def load_company_data():
    """
    Load (and cache) a subset of the Kaggle company dataset.
    Adds a 'country_name' column for user-friendly filtering.
    Columns: name, industry, size, founded, city, state, country_code, country_name.
    """
    global _cached_df
    if _cached_df is None:
        cols = ["name", "industry", "size", "founded", "city", "state", "country_code"]
        _cached_df = pd.read_csv(
            CSV_PATH,
            usecols=cols,
            nrows=USE_ROWS,
            dtype={
                "name": "string",
                "industry": "string",
                "size": "string",
                "founded": "Int64",
                "city": "string",
                "state": "string",
                "country_code": "string"
            },
            low_memory=True
        )
        # Ensure no NaN in text fields
        for c in ["name", "industry", "city", "state", "country_code", "size"]:
            _cached_df[c] = _cached_df[c].fillna("")

        # Add 'country_name' by mapping country_code → full name
        _cached_df["country_name"] = _cached_df["country_code"].apply(get_country_name)
    return _cached_df
