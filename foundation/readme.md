Goal: Retrace steps as outlined by Will to reproduce results (and understand data provenance).

Key differences:
1. Slightly different input list (b/c of file availability)
2. Used Propublica's Nonprofit explorer API to find foundations (not FDO manual interface)
3. Didn't employ NCAIS codes to keep (or chuck) foundations (instead used web descriptions of foundaitons, companies)
4. Didn't lump institutions

Overview of steps taken:
1. Manually assembled list of organizations following description provided by Will
    * Top 50 GOGEL (to 50 each Midstream LNG, Midstream Pipeline, Upstream, O&G Power Expansion)
        * n.b.: Used data from the column 'Company' (*not* 'Parent Company') to inform the Propublica search string
        * n.b.: Used 2024 version of the GOGEL file (b/c couldn't find earlier version online)
    * Top 50 GCEL
        * n.b.: Used data from the column 'Company' (*not* 'Parent Company') to inform the Propublica search string
         * n.b.: Used 2024 version of the GOGEL file (b/c couldn't find earlier version online)
    * Brulle (CSV provided by will plus a few from Geoffrey's List of Entities identified as Bruelle)
    * Carbon Underground 200 (obtained from Geoffrey's List of Entities)
    * Farrell 2015
    * Climate Action 100 (scraped with script get_ca100.py from [Climate Action 100+ website](https://www.climateaction100.org/whos-involved/companies/) on 7/13/2025)
    * Carbon Majors companies (downloaded from [CarbonMajors platform](https://carbonmajors.org/EN/index.html): assumed this is the update of Heede et al.'s 2014 method)
    Resulting file is a bit of a data dump: `all_names_for_ein_search.csv`
2. For each organization, shortened name for better search results (E.g., used 'Valero' to search for 'Valero Energy Corp.') (ad hoc step: see `search_string` column of `all_names_for_ein_search.csv`)
3. Used the search terms from (2) as input to Propublica's Nonprofit Explorer API for 501c3 and 501c6 organizations. API query returned foudnation names and EINs.
    * *Tools:* propublica_ein.py (command-line script); propublica_all_names.yml (configuration file)
    To use at the command line:
    ```
    > python3 [path/to/propublica_ein.py] --config [path/to/propublica_all_names.yml]
    ```
4. Matched the identified foundations from the returned list to organizations on the list in (1) above. Removed irrelevant foundations from list.  From the remaining foundations, semi-manually reviewed foundations, identified parent organizations & locations as well as subsidiary organizations & locations. Used util code to specify lat/lon locations. Classified foundations as being corporate, 501c6, fossil-fuel tied, family foundations, etc. Resulting file: `propublica_ein_result_data_with_loc.csv`
    Additional tool used: `process_propublica_results.py`, a command-line script (hacky!) to process propublica Nonprofit explorer api search results (removing duplicates, appending leading 0 to EINs that have only 8 characters, and prints to the screen a temporary yaml-formatted list of eins for use in the configuration file for command-line script fd_scrape.py (see next step) )
5. Used a web-scraper to identify (and save as CSV files) all grants for each of the eins identified for both 'higher ed' and 'graduate and professional school' within Foundation Directory's FDO dashboard. Note: this requires a FDO professional subscription & associated login credentials.
    *Tools:* `fd_scrape.py` (command-line script), `fd_scrape_utils.py` (utility functions), `fd_config_higher_graduate_ed.yml` (config file)
    Grant data were saved as individual CSVs in the same format as the files in will's metadata_csv folder with the addition of an EIN column.
    To use at the command line:
    ```
    > python3 [path/to/fd_scrape.py] --config [path/to/fd_config_higher_graduate_ed.yml]
    ```
6. Semi-manually matched all grant-recipient organizations headquartered in the US and receiving more than a total of $1000 to Carnegie Schools naming (with UnitID) (used text matching to make a first pass, then manually reviewed the results...probably a bit sloppily on the small-dollar end of things.)
    * n.b.: This is analogous to `recipient_keys_cleaned.csv`
    * Resulting file: organization_names.csv
7. Compiled all organization-level grant data from the FDO searches into a single grants flat file, removing grant instances in which the given EIN was the recipient rather than the grantmaker (the queries to FDO didn't separate out these two)
    * *Tools:* compile_grants.py, compile.yml (config file)
    * File locations and other configuration settings are specified in `compile.yml`
    To use at the command line:
    ```
    > python3 [path/to/compile_grants.py] --config [path/to/compile.yml]
    ```
8. Merged Grantmaker characteristics (from propublica_ein_result_data.csv) with specific grant data from the FDO (compiled_grant_data.csv), with Carnegie Naming Keys/org information (organization_names.csv), recipient location information, and institution data from Carnegie Data (2025). Computed distances between grantmakers and grant recipients for individual grants
    * *Tools:* merge_data.py (command-line script), merge_data.yml (configuration file)
    * File locations and other configuration settings are specified in `merge_data.yml`
    To use at the command line:
    ```
    > python3 [path/to/merge_data.py] --config [path/to/merge_data.yml]
    ```
