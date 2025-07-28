"""Utility functions for input/output of data"""

import logging
import os
from pathlib import PosixPath
from typing import Union

import pandas as pd
import yaml

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def yaml_to_dict(yaml_filepath: Union[str, PosixPath]) -> dict:
    """One-line function to read a yml config at a path into a dictionary
    Args:
        yaml_filepath: path to yaml file
    Returns:
        dictionary: contents of yaml file
    """

    if (str(yaml_filepath).split(".", maxsplit=1)[-1] != "yml") and (
        str(yaml_filepath).split(".", maxsplit=1)[-1] != "yaml"
    ):
        raise TypeError(
            "yaml_to_dict requires a yaml file as input (& we're assuming you named it with a .yml or .yaml extension)"
        )

    with open(yaml_filepath, "r", encoding="utf-8") as file:
        try:
            dictionary = yaml.safe_load(file)
        except yaml.YAMLError as excp:
            logging.exception(excp)

    return dictionary


def dict_to_yaml(dictionary: dict, yaml_filepath: Union[str, PosixPath]):
    """writes dictionary in yaml format to specified file location
    Args:
        dictionary: dict to be written to yaml
        yaml_filepath: location to which dictionary will be written in yaml format
    Returns:
        None
    """
    if (str(yaml_filepath).rsplit(".", maxsplit=1)[-1] != "yml") and (
        str(yaml_filepath).rsplit(".", maxsplit=1)[-1] != "yaml"
    ):
        raise ValueError(
            f"Specified filepath should end in .yml or .yaml. Current value is {yaml_filepath}"
        )
    with open(yaml_filepath, "w", encoding="utf8") as outfile:
        yaml.dump(dictionary, outfile, default_flow_style=False)


def xls_to_csvs(xls_path: str, output_dir: str = "."):
    """Reads an excel file and outputs each subsheet to its own CSV
    Args:
        xls_path: string that is file path of Excel file
        output_dir: directory where the csvs should be written
    Returns:
        None
    """
    excel_file = pd.ExcelFile(xls_path)

    os.makedirs(output_dir, exist_ok=True)

    for sheet in excel_file.sheet_names:
        # Read the sheet
        df = excel_file.parse(sheet)

        # Create safe filename by replacing spaces and making everything lowercase
        safe_name = sheet.lower().replace(" ", "_") + ".csv"
        output_path = os.path.join(output_dir, safe_name)

        # Write to CSV
        df.to_csv(output_path, index=False)
