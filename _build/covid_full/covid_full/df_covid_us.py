import pandas as pd

from bento.common import logger
from bento.common.structure import PathConf
from bento.common.scrub import states

logging = logger.fancy_logger(__name__)


def join_reference_data(idf, filename, on_key, filters=(), col_map=None):
    raw_df = PathConf.data.read(filename)
    if col_map:
        raw_df = raw_df[col_map.keys()].rename(columns=col_map)
    for (key, value) in filters:
        raw_df = raw_df[raw_df[key] == value].drop(key, axis=1)
    agg_df = raw_df.groupby(on_key).sum().drop("Unnamed: 0", axis=1)
    join_df = idf.join(agg_df, on=on_key)
    return join_df


def process_df(data_path):
    # Load raw data
    idf = pd.read_csv(data_path, parse_dates=["date"])

    logging.info(f"*** Loaded DF from {data_path} with {len(idf)} rows***")
    exclude = ["Guam", "Northern Mariana Islands", "Puerto Rico", "Virgin Islands"]
    idf = idf[~idf.state.isin(exclude)]
    idf["state_abbr"] = idf["state"].map(states.name_to_abbr)
    idf["county"] = idf["county"] + (", " + idf["state_abbr"]).fillna("")

    # Add population reference
    pop_file = "population/ref_county_pop"
    odf = join_reference_data(idf, pop_file, on_key=["fips"])
    odf["fips"] = odf["fips"].astype(str).str.replace("\.0", "").str.zfill(5)  # noqa
    logging.info(f"*** Loaded population data from {pop_file} ***")
    return odf


def load(repobase=PathConf.data.path):
    filename = "us-counties.csv"
    data_path = f"{repobase}/nyt-covid-states/{filename}"
    data = {
        "df": process_df(data_path),
        "keys": ["fips", "county", "state"],
        "types": {"date": "date", "cases": int, "deaths": int, "population": int,},
    }
    return data
