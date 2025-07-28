"""This hacky command-line script sorts through post-processed pro-publica nonprofit explorer API search
results (executed by propublica_ein.py), removes duplicates, appends a leading 0 to EINs that have only
8 characters, and prints to the screen a temporary yaml-formatted list of eins for use in the fdo
querying process (fd_scrape.py)
To use:
> python3 [path/to/this/file] --input [path/to/ein/file] --output_dir [path/to/dir/for/csv/output]
"""

# pylint: disable = broad-exception-caught, bare-except
import logging
from pathlib import Path

import click
import pandas as pd
from utils.io import dict_to_yaml

logging.basicConfig(level=logging.INFO)


# Function below is what is executed at the command line
@click.command()
@click.option(
    "--input",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    required=True,
)
@click.option(
    "--output_dir",
    type=click.Path(file_okay=False, dir_okay=True),
    required=False,
    default=".",
)
def process_ein(input: str, output_dir: str):
    """For a set of EINs, scrapes grant results from foundation
    Args:
        input: Path to csv ein results (hand-reviewed) (column with eins must be called 'ein')
        output_dir: path to the directory where write the subsetted file
    Returns:
        None
    """
    # read configuration details from configuration yaml specified at command line
    ein_df = pd.read_csv(input, dtype={"ein": str})
    if "notes" in ein_df.columns:
        ein_df["notes"] = ein_df["notes"].fillna("")

    # append a leading 0
    ein_df["ein"] = ["0" + ein if len(ein) == 8 else ein for ein in ein_df.ein]
    ein_df = ein_df.drop_duplicates(subset=["ein"])

    # write out for copying and pasting into yaml file for fdo query (fd_scrape.py)
    ein_df.sort_values(by="search_term", ascending=True, inplace=True)
    for i, row in ein_df.iterrows():
        print(f" - {row['search_term'].lower().replace(' ','_')} : '{row['ein']}'")

    ein_df.to_csv(
        Path(output_dir) / Path("eins_for_fdo_query.csv"), index=False
    )  # save


if __name__ == "__main__":
    process_ein()
