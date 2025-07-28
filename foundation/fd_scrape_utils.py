"""Bespoke utility funcitons for the fd_scrape.py command-line web scraper for Foundation Directory"""

# pylint: disable = broad-exception-caught, bare-except, raise-missing-from
import logging
import math
import os
import re
import time
from typing import List

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from utils.io import dict_to_yaml, yaml_to_dict

logging.basicConfig(level=logging.INFO)


def play_ding():
    """Plays a ding on a Mac -- used to alert the user to handle a Cloudfare 'human test'"""
    # TODO Works only on Mac: make this operating system independent
    # To make this work, your sound effects have to be played through a working speaker
    # Check system audio settings
    os.system("afplay /System/Library/Sounds/Ping.aiff")


def wait_for_human_verification(driver, timeout=120):
    """Detects and waits for a Cloudflare human verification challenge to be completed.
    Args:
        driver: webdriver instance
        timeout: number of seconds to wait for the human to do something.
    Returns:
        None
    """

    # play_ding()
    logging.info("⚠️ Cloudflare verification detected! Please complete the checkbox.")

    # Wait for the challenge to be removed (checkbox disappears)
    try:
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.CLASS_NAME, "cb-c"))
        )

    except TimeoutException:
        logging.info(" ! Waited for human verification, but ran out of patience.")
    # input("🔓 Press Enter when the verification has passed and page is fully loaded..."


def get_web_driver() -> webdriver:
    """Configure a Chrome web driver for navigating FD dashboard
    Args:
        None
    Returns:
        driver: chrome web driver configured for FD querying purpose
    """
    # Add a download directory for chrome if it doesn't exist
    download_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_dir, exist_ok=True)

    # --- Configure Chrome to auto-download CSV ---
    options = Options()
    options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        },
    )
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    return driver


def scrape_table_pages(
    driver: webdriver, config_info: dict, ein: int, max_page: int
) -> pd.DataFrame:
    """Compile all table-page results into a single dataframe
    Args:
        driver: webdriver with open, logged in browsing session on FD website
        config_info: dictionary with configuration settings read in from fd_config.yml
        ein: EIN of the foundation that is currently being interrogated
        max_page: total number of pages into which results table is split
    Returns:
        pandas dataframe containing compiled grant results
    """
    df_list = []

    for p in range(1, max_page + 1):
        driver.get(config_info["page_url"] + f"&ein={ein}&page={p}")  # + f"{p}")

        # Wait for  content to confirm the page loaded
        while True:
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "search-results-container"))
                )

                break
            except TimeoutException:
                play_ding()
                wait_for_human_verification(driver)
                time.sleep(5)

        logging.info(
            "✅ Navigated to target search URL for page %s of %s!",
            str(p),
            str(max_page),
        )

        # get html for this page
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # find the results table and get the results row
        results_table = soup.find("tbody", id="search-results-grants")
        rows = results_table.find_all("tr")

        visible_data = []

        # assemble the data from each row of the reusults table into a dataframe
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 9:
                continue  # skip malformed rows

            visible_data.append(
                {
                    "Grantmaker": cols[1].get_text(strip=True),
                    "Recipient": cols[2].get_text(strip=True),
                    "Recipient City": cols[3].get_text(strip=True),
                    "Recipient State": cols[4].get_text(strip=True),
                    "Recipient Country": cols[5].get_text(strip=True),
                    "Primary Subject": cols[6].get_text(strip=True),
                    "Year": cols[7].get_text(strip=True),
                    "Grant Amount": cols[8].get_text(strip=True),
                    "ein": ein,
                    "search_result_page": p,
                }
            )

        visible_df = pd.DataFrame(visible_data)

        # append this table's dataframe into a list of all dfs for the foundation
        df_list.append(visible_df)

    df = pd.concat(df_list)
    return df


def login_to_foundation_directory(driver: webdriver, config_info: dict) -> webdriver:
    """Use FD login and password information to log into an FD browswer session

    Args:
        driver: Chrome browser configured for this purpose
        config_info: dictionary read in from configuration yaml with login/pw info
    Returns:
        driver: browser session that's logged in with FD credentials
    """
    # Go to login page
    driver.get(config_info["login_url"])

    # Wait for username input to appear
    username_input = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                "form.form-horizontal.gray-box.login-form input[name='username']",
            )
        )
    )
    password_input = driver.find_element(
        By.CSS_SELECTOR,
        "form.form-horizontal.gray-box.login-form input[name='password']",
    )
    submit_button = driver.find_element(
        By.CSS_SELECTOR,
        "form.form-horizontal.gray-box.login-form input[type='submit']",
    )

    # use config information to fill in and submit login form for FD dashboard
    username_input.send_keys(config_info["username"])
    password_input.send_keys(config_info["password"])
    submit_button.click()

    # wait for login to complete
    try:
        WebDriverWait(driver, 15).until(EC.url_changes(config_info["login_url"]))
        logging.info(" ✅ Login successful!")
    except TimeoutException:
        logging.info(" Timed out while trying to log in")
        # TODO handle this better

    return driver


def perform_initial_search(driver: webdriver, config_info: dict, ein: int) -> webdriver:
    """Search for any grant results for this EIN
    Args:
        driver: webdriver with a logged-in session on the FD dashboard
        config_info: configuration settings read in from fd_config.yml
        ein: EIN for the foundation currently being interrogated
    Returns:
        webdriver with the results of the initial search
    """
    # Navigate to the target URL using the same session
    driver.get(config_info["target_url"] + f"&ein={ein}")

    # Wait for some content to confirm the page loaded
    WebDriverWait(driver, config_info["wait_seconds"]).until(
        EC.presence_of_element_located((By.ID, "search-results-container"))
    )

    logging.info(" ✅ Navigated to target search URL!")

    return driver


def count_table_pages(driver: webdriver) -> int:
    """
    Get the total number of pages based on the number of results and results per page.

    Args:
        driver: webdriver instance
    Returns:
        total_number_of_pages: number pages into which the table is parsed
    """

    soup = BeautifulSoup(driver.page_source, "html.parser")

    try:
        showing_span = soup.select_one("span.showing-number")
    except:
        raise ValueError("Could not find html for grant numbers.")

    # If span.showing-number was not in the html, then there aren't any grants for this EIN
    if showing_span is None:
        return 0

    # find the three numbers in the showing span text.
    # Should be of the form Showing [FIRST MATCH]-[SECOND MATCH] of [THIRD MATCH] Results
    match = re.search(r"Showing\s+(\d+)[–-](\d+)\s+of\s+([\d,]+)", showing_span.text)
    if not match:
        raise ValueError(
            """
            Structure of text shown on table doesn't match expected structure:\n
            'Showing [FIRST MATCH]-[SECOND MATCH] of [THIRD MATCH] Results'
            """
        )
    # Convert match results to integers, removing any thousands-separator commas
    start = int(match.group(1).replace(",", ""))
    end = int(match.group(2).replace(",", ""))
    total_results = int(match.group(3).replace(",", ""))

    results_per_page = end - start + 1
    total_number_of_pages = math.ceil(total_results / results_per_page)
    logging.debug(
        " Found %s pages of the results table for this ein.", str(total_number_of_pages)
    )

    return total_number_of_pages


def write_ein_list(ein_list: List[int], ein_filepath: str):
    """appends new list of eins to yaml file containing list
    Args:
        ein_list: list of ein numbers to be written to a simple yaml
        ein_filepath: filepath where eins will be written (or already exist)
    Returns:
        None
    """
    if ein_filepath.exists():
        more_than_100_dict = yaml_to_dict(ein_filepath)
        ein_list_from_file = more_than_100_dict["eins"]
        ein_list.extend(ein_list_from_file)

    dict_to_yaml({"eins": ein_list}, ein_filepath)
