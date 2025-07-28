"""This command-line script searches Foundation Directory grants for a list of foundations specified in fd_config.yml
To use:
> python3 [path/to/this/file] --config [path/to/fd_config.yml] --output_dir [path/to/dir/for/csv/outputs]
"""

# pylint: disable = broad-exception-caught, bare-except
import logging
from pathlib import Path

import click
import pandas as pd
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)

from utils.io import yaml_to_dict

logging.basicConfig(level=logging.INFO)

from projects.foundation.fd_scrape_utils import (
    count_table_pages,
    get_web_driver,
    login_to_foundation_directory,
    perform_initial_search,
    scrape_table_pages,
    write_ein_list,
)


# Function below is what is executed at the command line
@click.command()
@click.option(
    "--config",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    required=True,
)
@click.option(
    "--output_dir",
    type=click.Path(file_okay=False, dir_okay=True),
    required=False,
    default=".",
)
def fd_scrape(config: str, output_dir: str):
    """For a set of EINs, scrapes grant results from foundation
    Args:
        config: Path to configuration yml file
        output_dir: path to the directory where the foundation-grant csvs will be written
    Returns:
        None
    """
    # read configuration details from configuration yaml specified at command line
    config_info = yaml_to_dict(config)

    driver = get_web_driver()

    driver = login_to_foundation_directory(driver, config_info)

    # initialize lists for tracking empty-result EINs and EINs with more than 100 result pages
    eins_with_no_results_list = []
    eins_with_more_than_100_results = []

    # iterate through eins from configuration file
    for i, nonprofit in enumerate(config_info["eins"]):
        ein = list(nonprofit.values())[0]
        company_name = (
            list(nonprofit.keys())[0]
            .replace(" ", "_")
            .replace(".", "")
            .replace("(", "")
            .replace(")", "")
            .lower()
        )
        logging.info(
            " >>>>> Working on ein number %s (%s) for %s",
            str(i + 1),
            str(ein),
            company_name,
        )
        try:
            driver = perform_initial_search(driver, config_info, ein)

            total_number_of_pages = count_table_pages(driver)

            if total_number_of_pages > 100:
                eins_with_more_than_100_results.append(ein)
            elif total_number_of_pages > 0:
                big_df = scrape_table_pages(
                    driver, config_info, ein, total_number_of_pages
                )
                big_df.to_csv(
                    Path(output_dir)
                    / Path(f"{company_name}_{ein}{config_info['suffix']}"),
                    index=False,
                )
            else:
                eins_with_no_results_list.append(ein)

        except (TimeoutException, NoSuchElementException) as selenium_error:
            logging.warning(
                "❌ Selenium error occurred for EIN %s: %s", ein, selenium_error
            )
            input("Wait for input")
            break

        except pd.errors.EmptyDataError as pandas_error:
            logging.warning(
                "❌ Pandas data is empty: could not write data for EIN %s: %s",
                ein,
                pandas_error,
            )
            break

        except (FileNotFoundError, PermissionError) as file_error:
            logging.error(
                "❌ File-related error occurred for EIN %s: %s", ein, file_error
            )
            break

        except WebDriverException as web_driver_error:
            logging.critical(
                "❌ WebDriver encountered a fatal issue: %s", web_driver_error
            )
            break

        except Exception as e:
            logging.exception("❌ An unexpected error occurred for EIN %s: %s", ein, e)
            break

    logging.info(
        "Completed searches for all EINs listed. The EINs listed below had no grant results.",
        *eins_with_no_results_list,
    )
    logging.info(
        "Completed searches for all EINs listed. The EINs listed below had >100 table pages.",
        *eins_with_more_than_100_results,
    )
    write_ein_list(
        eins_with_more_than_100_results,
        Path(output_dir) / Path(config_info["more_than_100"]),
    )
    write_ein_list(
        eins_with_no_results_list,
        Path(output_dir) / Path(config_info["no_grants_for_ein"]),
    )

    driver.quit()


if __name__ == "__main__":
    fd_scrape()
