"""Bespoke script for getting the climate action 100 companies off their pretty-but-hard-to-access website"""

"""
To use, at command line, type:
python3 [path/to/get_ca100.py] --output [path/to/output/csv]
"""
from urllib.parse import urljoin

import click
import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.climateaction100.org/whos-involved/companies/"

SECTORS = [
    "oil-and-gas",
    "oil-and-gas-distribution",
    "airlines",
    "automobiles",
    "cement",
    "chemicals",
    "coal-mining",
    "consumer-goods-services",
    "diversified-mining",
    "electric-utilities",
    "other-industrials",
    "paper",
    "shipping",
    "steel",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ClimateAction100 scraper/1.0)"}


@click.command()
@click.option(
    "--output",
    type=click.Path(file_okay=False, dir_okay=True),
    required=False,
    default=".",
)
def scrape_ca100_companies(output: str) -> pd.DataFrame:
    session = requests.Session()
    session.headers.update(HEADERS)

    rows: list[tuple[str, str]] = []

    for sector in SECTORS:
        # first page for this sector
        next_url: str | None = f"{BASE_URL}?search_companies&company_sector={sector}"

        while next_url:
            resp = session.get(next_url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # company names live in <h3> tags inside the cards
            for h3 in soup.select("h3"):
                name = h3.get_text(strip=True)
                if name and name.upper() != "COMPANIES":  # skip page heading
                    rows.append((name, sector))

            # follow the pagination “Next” link, if any
            nxt = soup.find("a", string=lambda s: s and s.strip().lower() == "next")
            next_url = urljoin(next_url, nxt["href"]) if nxt else None

    # build a tidy DataFrame
    df = (
        pd.DataFrame(rows, columns=["company", "ca100_sector"])
        .drop_duplicates()
        .sort_values(["ca100_sector", "company"], ignore_index=True)
    )
    df.to_csv(output, index=False)
    return df


if __name__ == "__main__":
    df = scrape_ca100_companies()
    df.to_csv("ca100_companies.csv")
