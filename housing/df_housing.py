import pandas as pd


def load():
    filename = "housing/zillow_housing_2020.csv"
    df = pd.read_csv(filename)
    df.loc[:, "fips"] = df.fips.astype(str).str.zfill(2)
    data = {
        "df": df,
        "keys": ["state", "fips"],
    }
    data["types"] = {
        col: float for col in data["df"].columns if col not in ("state", "fips")
    }
    return data
