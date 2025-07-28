"""Command line script to query Propublica's Nonprofit Explorer API for foundation results
Configure settings within propublica_all_names.yml

To use at command line:
> python3 [path/to/this/file] --config [path/to/propublica_all_names.yml]
"""

import requests
import pandas as pd
import logging


import click
import pandas as pd


from utils.io import yaml_to_dict

logging.basicConfig(level=logging.INFO)


def initialize_row_dict(result_id, company, fullname):
    row_dict = dict()
    row_dict["search_term"] = company
    row_dict["full_name"] = fullname
    row_dict["result_id"] = result_id
    row_dict["ein"] = ""
    row_dict["name"] = ""
    row_dict["sub_name"] = ""
    row_dict["city"] = ""
    row_dict["state"] = ""
    row_dict["501c"] = -1
    row_dict["propublica_queried"] = 0
    return row_dict


@click.command()
@click.option(
    "--config",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    required=True,
)
def propublica(config: str):
    config_info = yaml_to_dict(config)
    # read in search string file
    df = pd.read_csv(config_info["search_string_file"])

    # eliminate rows with duplicate search strings
    df = df.drop_duplicates(subset=config_info["search_string_col"])

    # ignore results with these search strings
    minus_these_terms = " -" + " -".join(config_info["ignore_results_with"])

    session = requests.Session()
    rows_list = []

    # iterate thru search strings, testing basic string + 'foundation', more general search and 501c6
    for i, row in df[
        [
            config_info["company_col"],
            config_info["search_string_col"],
            config_info["run_col"],
        ]
    ].iterrows():

        search_string = row[config_info["search_string_col"]]
        company_name = row[config_info["company_col"]]

        # search only 501(c)(3) orgs (c_code[id]==3)

        row_dict = initialize_row_dict(i, search_string, company_name)

        # if this row is marked for search, continue
        if row[config_info["run_col"]] == 1:

            # first try querying with just the basic search term and 501c3
            params = {
                "q": f'"{search_string}" {minus_these_terms}',
                "c_code[id]": str(3),
            }
            try:

                resp = session.get(config_info["api_root"], params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                row_dict = dict()
                logging.info(
                    f" >>> {data['total_results']} foundations for “{search_string}” "
                )
                for i in range(data["total_results"]):
                    row_dict = initialize_row_dict(i, search_string, company_name)
                    row_dict["ein"] = data["organizations"][i]["ein"]
                    row_dict["name"] = data["organizations"][i]["name"]
                    row_dict["sub_name"] = data["organizations"][i]["sub_name"]
                    row_dict["city"] = data["organizations"][i]["city"]
                    row_dict["state"] = data["organizations"][i]["state"]
                    row_dict["propublica_queried"] = 1
                    row_dict["501c"] = 3
                    rows_list.append(row_dict.copy())
                del data
            except:
                logging.info(
                    f"===  No foundations for basic 501c3 search “{search_string}”"
                )
                rows_list.append(row_dict.copy())
            # test search string with 'Foundation' (this specificity oddly finds more results?)
            if config_info["test_just_foundation_first"]:
                params = {
                    "q": f'"{search_string}" Foundation {minus_these_terms}',
                    "c_code[id]": str(3),
                }
                try:

                    resp = session.get(
                        config_info["api_root"], params=params, timeout=15
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    row_dict = dict()
                    logging.info(
                        f" >>> {data['total_results']} foundations for “{search_string}” "
                    )
                    for i in range(data["total_results"]):
                        row_dict = initialize_row_dict(i, search_string, company_name)
                        row_dict["ein"] = data["organizations"][i]["ein"]
                        row_dict["name"] = data["organizations"][i]["name"]
                        row_dict["sub_name"] = data["organizations"][i]["sub_name"]
                        row_dict["city"] = data["organizations"][i]["city"]
                        row_dict["state"] = data["organizations"][i]["state"]
                        row_dict["propublica_queried"] = 1
                        row_dict["501c"] = 3
                        rows_list.append(row_dict.copy())
                    del data
                except:
                    logging.info(
                        f"⚠️  No 'Foundation' foundations for “{search_string}”"
                    )
                    rows_list.append(row_dict.copy())

            # look for 501c6 nonprofits
            if config_info["501c_6"]:
                params = {
                    "q": f'"{search_string}" {minus_these_terms}',
                    "c_code[id]": str(6),
                }
                try:
                    resp = session.get(
                        config_info["api_root"], params=params, timeout=15
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    row_dict = dict()
                    logging.info(
                        f" >>> {data['total_results']} foundations for “{search_string}” "
                    )
                    for i in range(data["total_results"]):
                        row_dict = initialize_row_dict(i, search_string, company_name)
                        row_dict["ein"] = data["organizations"][i]["ein"]
                        row_dict["name"] = data["organizations"][i]["name"]
                        row_dict["sub_name"] = data["organizations"][i]["sub_name"]
                        row_dict["city"] = data["organizations"][i]["city"]
                        row_dict["state"] = data["organizations"][i]["state"]
                        row_dict["propublica_queried"] = 1
                        row_dict["501c"] = 6
                        rows_list.append(row_dict.copy())
                    del data
                except Exception as exc:
                    logging.info(f"///  No 501c6 foundations for “{search_string}”")
                    rows_list.append(row_dict.copy())

        else:
            rows_list.append(row_dict.copy())

    output_df = pd.DataFrame(rows_list)
    output_df = output_df.drop_duplicates(subset="ein")
    output_df.to_csv(config_info["output_file"], index=False)


if __name__ == "__main__":
    propublica()
