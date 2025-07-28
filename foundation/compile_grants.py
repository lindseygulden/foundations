"""This  command-line reads in all FDO outputs into a single dataframe and does light processing
> python3 [path/to/this/file] --config [path/to/compile.yml]
"""

import logging
from pathlib import Path

import click
import pandas as pd

from utils.io import yaml_to_dict
from utils.strings import similar_strings, similarity_score

logging.basicConfig(level=logging.INFO)


def replace_terms(s, term_dict):
    """replaces a list of terms in string s according to term dictionary"""
    for t, rt in term_dict.items():
        s = s.replace(t, rt)

    return s


# Function below is what is executed at the command line
@click.command()
@click.option(
    "--config",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    required=True,
)
def compile(config: str):
    # Read in carnegie data; transform to dict with states as keys and university list as values

    config_info = yaml_to_dict(config)

    csv_paths = [str(file) for file in Path(config_info["data_dir"]).glob("*.csv")]

    # get ein list and associated names to separate out grants where organization is recipient
    ein_df = pd.read_csv(config_info["ein_data_file"], dtype={"ein": str})

    df_list = []

    for csv in csv_paths:
        logging.info(f" --- reading file {csv}")
        df = pd.read_csv(csv, dtype={"ein": str})
        df.columns = [x.lower().replace(" ", "_") for x in df.columns.values]

        # the FDO search hack (in fd_search.py) doesn't separate out whether an EIN is
        # the grantmaker or the grant recipient. So we have to go through and adjust
        # the raw grant search data to only select records in which the EIN is the
        # grantmaker.
        this_ein = list(df.ein.unique())[0]
        try:
            grantmaker_search_term = list(
                ein_df.loc[ein_df["ein"] == this_ein].search_term.unique()
            )[0]
            alternative_name = list(
                ein_df.loc[ein_df["ein"] == this_ein].alternative_name.unique()
            )[0]
        except:
            logging.info(f"could not earh term find data for {this_ein}")
        print(grantmaker_search_term)
        print(alternative_name)
        df = df.loc[
            [
                (grantmaker_search_term.lower() in g.lower())
                | (alternative_name.lower() in g.lower())
                for g in df.grantmaker
            ]
        ]

        # save original value
        df["recipient_original"] = df["recipient"].copy()

        df.recipient = [
            replace_terms(s, config_info["replacements"]).strip() for s in df.recipient
        ]

        df["recipient_state"] = df["recipient_state"].fillna(
            config_info["missing_state_string"]
        )

        # df["carnegie"] = [
        #    similar_strings(recipient, state_college_dict[state], 1)[0]
        #    for recipient, state in zip(df.recipient, df.recipient_state)
        # ]
        # df["similarity"] = [
        #    similarity_score(r.lower(), c.lower())
        #    for r, c in zip(df.recipient, df.carnegie)
        # ]
        df = df[
            [
                "grantmaker",
                "recipient_original",
                "recipient",
                # "carnegie",
                # "similarity",
                "recipient_city",
                "recipient_state",
                "recipient_country",
                "primary_subject",
                "year",
                "grant_amount",
                "ein",
                "search_result_page",
            ]
        ]
        df_list.append(df.copy())

    all_df = pd.concat(df_list)

    output_file = config_info["output_file"]
    all_df.to_csv(output_file, index=False)
    logging.info(f" >>> WROTE DATA TO {output_file}")


if __name__ == "__main__":
    compile()
