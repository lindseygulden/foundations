"""This  command-line merges FDO grant data (with grantmaker eins included), Carnegie naming data, org info

To use:

> python3 [path/to/this/file] --config [path/to/merge_data.yml]

"""

import logging
from typing import Dict

import click
import cpi
import pandas as pd

from utils.io import yaml_to_dict
from utils.spatial import distance_between_points

logging.basicConfig(level=logging.INFO)


def ein_leading_zero(ein_series: pd.Series) -> pd.Series:
    """append a leading zero to 8-length eins, fill in nans with ''"""
    ein_series = ein_series.fillna("")
    ein_series = pd.Series(["0" + ein if len(ein) == 8 else ein for ein in ein_series])
    return ein_series


def get_inflation_factor(
    start_year: int, end_year: int, currency_year: int = 2024
) -> Dict[int, float]:
    """Returns inflation factor dict for each year covered (done b/c cpi is a slow library)"""
    cpi.update()  # get latest CPI data
    cpi_inflation_factor_dict = dict()
    for y in range(
        start_year, end_year + 1
    ):  # 1 added b/c range doesn't include last number in interable results
        cpi_inflation_factor_dict[y] = cpi.inflate(1, y, currency_year)
    return cpi_inflation_factor_dict


# Function below is what is executed at the command line
@click.command()
@click.option(
    "--config",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    required=True,
)
def merge_data(config: str):
    # get file location, etc.
    config_info = yaml_to_dict(config)

    # Read in grant data from compiled FDO grant information
    grant_df = pd.read_csv(
        config_info["grant_data"],
        dtype={config_info["ein_col"]: str, config_info["grant_year_col"]: int},
    )
    grant_df[config_info["ein_col"]] = grant_df[config_info["ein_col"]].fillna("")
    grant_df[config_info["ein_col"]] = [
        "0" + ein if len(ein) == 8 else ein for ein in grant_df[config_info["ein_col"]]
    ]
    # convert information contained in strings of the data in grant amount column to floats
    grant_df[config_info["grant_grant_amt_col"]] = [
        float(x.replace("$", "").replace(",", "")) if isinstance(x, str) else 0
        for x in grant_df.grant_amount
    ]

    # update grant amounts for inflation
    cpi_inflation_factor_dict = get_inflation_factor(
        start_year=int(grant_df[config_info["grant_year_col"]].min()),
        end_year=int(grant_df[config_info["grant_year_col"]].max()),
        currency_year=config_info["currency_year"],
    )
    inflated_currency_col = (
        f"{config_info['grant_grant_amt_col']}_{config_info['currency_year']}_usd"
    )
    grant_df[inflated_currency_col] = grant_df[config_info["grant_grant_amt_col"]] * [
        cpi_inflation_factor_dict[y] for y in grant_df[config_info["grant_year_col"]]
    ]
    logging.info(" Read grant data file & inflated dollar value of grants.")
    # Read in information about the orgs (universities, usually) receiving grants
    receiving_org_df = pd.read_csv(
        config_info["org_mapping_data"],
        dtype={config_info["org_uid_col"]: str},
    )

    n_multiple_orgs = receiving_org_df[
        config_info["multiple_institutions_bool_col"]
    ].sum()
    n_univ = receiving_org_df[config_info["univ_bool_col"]].sum()
    logging.info(
        """ Read info about receiving orgs: %s unique institutions of higher ed; %s unique multi-institution orgs
        """,
        str(n_univ),
        str(n_multiple_orgs),
    )
    # Read in information about the universities that get grants
    carnegie_df = pd.read_csv(
        config_info["carnegie_data"], dtype={config_info["org_uid_col"]: str}
    )
    logging.info(" Read Carnegie institution information.")

    # Read lumped naming from will's keys file
    # will_keys_df = pd.read_csv(config_info["carnegie_naming_data"])
    # will_keys_df = will_keys_df[
    #    ["CARNEGIE_NAMING", "CARNEGIE_NAMING_CLEANED"]
    # ].drop_duplicates()
    # will_keys_df.columns = ["carnegie_naming", "carnegie_lumped"]
    logging.info(" Read Carnegie name-lumping directions.")

    # Read in ein data and information about grantmaking organizations
    grantmaker_ein_df = pd.read_csv(
        config_info["grantmaker_data_file"], dtype={config_info["ein_col"]: str}
    )
    grantmaker_ein_df = grantmaker_ein_df.drop_duplicates(
        subset=[config_info["ein_col"]]
    )
    grantmaker_ein_df[config_info["ein_col"]] = ein_leading_zero(
        grantmaker_ein_df[config_info["ein_col"]]
    )

    n_grantmaker = grantmaker_ein_df[config_info["ein_col"]].nunique()
    logging.info(" Read %s grantmaker characteristics and eins.", str(n_grantmaker))

    # use ein to join information about grantmakers to grant data tabl

    grant_df = grant_df.merge(
        grantmaker_ein_df[config_info["grantmaker_df_cols"]],
        on=config_info["ein_col"],
        how="outer",
    )

    # adjust ein data in the grants dataset to append the leading 0s (get stripped in csvs)
    grant_df[config_info["ein_col"]] = ein_leading_zero(
        grant_df[config_info["ein_col"]]
    )

    # merge individual grant data with organization key matching recipient to carnegie name
    df = grant_df[
        list(
            set(
                config_info["grant_df_cols"]
                + config_info["grantmaker_df_cols"]
                + [inflated_currency_col]
            )
        )
    ].merge(receiving_org_df, on=config_info["cols_to_merge_grants_and_orgs"])

    # append lumped carnegie names to the dataframe, leaving no-matches as nan
    df = df.merge(
        carnegie_df,
        left_on=[config_info["org_uid_col"], "carnegie_matched"],
        right_on=[config_info["org_uid_col"], "instnm"],
        how="left",
    )
    # subset data according to config settings
    logging.info(" Merged data.")
    if config_info["keep_only_open_higher_ed_orgs"]:
        df = df.loc[(df[config_info["univ_bool_col"]] == 1)]
    if config_info["keep_only_definite_fossil_fuel"]:
        df = df.loc[(df.fossil_fuel_tied == 1)]
    if "min_grant_size" in config_info:
        df = df.loc[df.grant_amount >= config_info["min_grant_size"]]

    # append school locations (lat/lon) to dataframe
    school_loc_df = pd.read_csv(config_info["school_location_file"])
    df = df.merge(
        school_loc_df[["carnegie_matched", "recipient_lat", "recipient_lon"]],
        on="carnegie_matched",
        how="left",
    )

    n_grantmaker = df[config_info["ein_col"]].nunique()
    n_univ = df["carnegie_matched"].nunique() - 1
    logging.info(
        " Merged data has %s unique grantmakers and %s unique higher-ed institution recipients",
        str(n_grantmaker),
        str(n_univ),
    )

    # get neighbor-state dictionary
    neighbor_dict = yaml_to_dict(config_info["neighbor_states_info"])

    # compute boolean characteristics state adjacency between grantmaker state and recipient state
    df["neighbor_state"] = [
        1 if r in neighbor_dict[g] else 0
        for r, g in zip(df.recipient_state, df.org_state)
    ]
    df["same_state"] = [
        1 if r == g else 0 for r, g in zip(df.recipient_state, df.org_state)
    ]
    df["same_or_neighbor"] = [
        max(s, n) for s, n in zip(df.neighbor_state, df.same_state)
    ]
    df["not_same_state"] = [abs(1 - x) for x in df.same_state]

    df["not_same_or_neighbor"] = [abs(1 - x) for x in df.same_or_neighbor]

    # compute distance between all recipients and grantmakers (Great-circle distance)
    df["distance_km"] = [
        distance_between_points([r_lat, r_lon], [g_lat, g_lon])
        for r_lat, r_lon, g_lat, g_lon in zip(
            df.recipient_lat, df.recipient_lon, df.org_lat, df.org_lon
        )
    ]
    logging.info(" Distance between grantmakers and recipients computed")

    df.to_csv(config_info["output_file"], index=False)
    logging.info(f' Wrote data to {config_info["output_file"]}')


if __name__ == "__main__":
    merge_data()
