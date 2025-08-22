
# README for exploratory analysis to support Fossil Fuel Foundation Funding *(FFFF!)* research by Will Katrup and Geoffrey Supran @ U. Miami's CAL
Lindsey Gulden 08-23-25
lindsey@legupdata.com

## Goals of Exploratory Analysis 
1. Follow [written methods](https://docs.google.com/document/d/1buyLjLjZS6nLiO3q-SaqRHJx-6I5pSJta8Mqd8KzyY4/edit?usp=sharing) to roughly reproduce foundation-grant tabulation results and understand data provenance and potential limitations of methods.
2. Link resulting grant information to information about grant recipients (i.e., schools)
2. Identify methods to quantify likely strategy of fossil fuel foundations in funding academia

### Key differences between Will's method and Lindsey's method:
1. Slightly different input list (b/c of file availability)
    * e.g., used 2024 versions of GOGEL and GCEL b/c 2022 versions no longer readily available on website
2. Analysis here used Propublica's Nonprofit explorer API to find foundations; documented methods used manual querying of FDO interface
3. This analysis didn't use NCAIS codes to keep/discard foundations and instead used web descriptions of foundations, companies to confirm fossil-fuel ties.
    * All identified foundations are fairly indisputably linked to fossil fuels; NCAIS codes not employed to bypass unnecessary layer of interpretation.
4. Unlike documented approach, this method did not lump different schools from the same University system (e.g., UT Dallas, University of Texas at Austin).
    * Preserves ability to distinguish characteristics of different student bodies

### Description of steps taken:
1. Manually assembled list of organizations, adhering as much as possible to [description provided](https://docs.google.com/document/d/1buyLjLjZS6nLiO3q-SaqRHJx-6I5pSJta8Mqd8KzyY4/edit?usp=sharing)
    * Top 50 GOGEL (to 50 each Midstream LNG, Midstream Pipeline, Upstream, O&G Power Expansion)
        * n.b.: Used data from the column 'Company' (*not* 'Parent Company') to inform the Propublica search string
        * n.b.: Used [2024 version of the GOGEL file](https://docs.google.com/spreadsheets/d/19hpCQ1Dkk5-Q2Syl1UFGm4f81YG6oKU-/edit?usp=share_link&ouid=106393912456956827016&rtpof=true&sd=true) (b/c couldn't find earlier version online)
    * Top 50 GCEL
        * n.b.: Used data from the column 'Company' (*not* 'Parent Company') to inform the Propublica search string
         * n.b.: Used [2024 version of the GCEL file](https://docs.google.com/spreadsheets/d/1F9rc9O98Bz30dQ0_rjuml0M0ZVALKnoP/edit?usp=share_link&ouid=106393912456956827016&rtpof=true&sd=true) (b/c couldn't find earlier version online)
    * Brulle (CSV provided by Will plus a few additional entities from Geoffrey's List of Entities identified as Bruelle)
    * Carbon Underground 200 (obtained from Geoffrey's List of Entities, provided by Will)
    * Farrell 2015
    * Climate Action 100 (scraped with script get_ca100.py from [Climate Action 100+ website](https://www.climateaction100.org/whos-involved/companies/) on 7/13/2025)
    * Carbon Majors companies (downloaded from [CarbonMajors platform](https://carbonmajors.org/EN/index.html): assumed this is the update of Heede et al.'s 2014 method)
    **Resulting file:**  [`all_names_for_ein_search.csv`](https://drive.google.com/file/d/1mgrYb0p9zNzvPaSTGeP04KsTp-Y2VIgK/view?usp=share_link). N.B.: this file is a bit of a data dump, but it is used to cast a broad net; so its 'dumpiness' is not a crisis.
2. For each organization in `all_names_for_ein_search.csv`, I shortened the name for better search results. (E.g., used 'Valero' to search for 'Valero Energy Corp.') See `search_string` column of `all_names_for_ein_search.csv`.
3. I used the search terms from (2) as input to Propublica's Nonprofit Explorer API to find the EINs of all 501c3 and 501c6 organizations contaiing the search terms. The API query returned foundation names and EINs.
    * **Tools:** `propublica_ein.py` (command-line script); `propublica_all_names.yml` (configuration file)
    To use the `propublica_ein.py` command-line script, type the following at the command line:
    ```
    > python3 [path/to/propublica_ein.py] --config [path/to/propublica_all_names.yml]
    ```
    **Resulting file:**
4. I matched the identified foundations from the returned list to organizations on the list in (1) above and manually removed irrelevant foundations from list.  From the remaining foundations, I semi-manually reviewed foundations, identified parent organizations & locations as well as subsidiary organizations & locations. Used util code to specify lat/lon locations. Classified foundations as being corporate, 501c6, fossil-fuel tied, family foundations, etc. 
    **Resulting file:** [`propublica_ein_result_data_with_loc.csv`](https://drive.google.com/file/d/1JgmyCjlNSCmcElHDoUz_dBqRzaCHs2kv/view?usp=share_link)
    **Tools:** [`process_propublica_results.py`](https://github.com/lindseygulden/foundations/blob/main/foundation/process_propublica_results.py), a command-line script (hacky!) to process the Propublica Nonprofit eExplorer API search results. 
    * The script removes duplicates, appends a leading '0' to EINs that have only 8 characters, and prints to the screen a temporary yaml-formatted list of EINs for use in the Foundation Directory scraping step (see next)
5. Used a web-scraper to identify (and save as CSV files) all grants for each of the eins identified for both 'higher ed' and 'graduate and professional school' within Foundation Directory's [online FDO dashboard](https://fconline.foundationcenter.org/). 
__Note:__ Execution of this web scraper requires [a paid FDO professional subscription](https://shop.candid.org/Subscriptions/FDOProfessionalPlan?) & associated login credentials, which the user specifies in the configuration file.
    **Tools:** `fd_scrape.py` (command-line script), `fd_scrape_utils.py` (utility functions), `fd_config_higher_graduate_ed.yml` (config file)
    Grant data were saved as individual CSVs (see zipped directory with resulting csvs linked [here](https://drive.google.com/file/d/1BRBCKE0o7q4lbH2ryn-D_Jrh_5MLnKvt/view?usp=share_link)) in the same format as the files in Will's metadata_csv folder, with the addition of an EIN column for ease of foundation tracking and merging with other data.
    To use the `fd_scrape.py` command-line script, type the following at the command line:
    ```
    > python3 [path/to/fd_scrape.py] --config [path/to/fd_config_higher_graduate_ed.yml]
    ```
6. Semi-manually matched all grant-recipient organizations headquartered in the US and receiving more than a total of $1000 to Carnegie Schools naming (with UnitID) (used text matching to make a first pass, then manually reviewed the results...probably a bit sloppily on the small-dollar end of things.)
    * n.b.: This is analogous to `recipient_keys_cleaned.csv` of the original method.
    * **Resulting file:** [`organization_names.csv`](https://drive.google.com/file/d/1GFQe-J96B5h_BudSKGSjm3sRmOHDT1VP/view?usp=share_link)
7. Compiled all organization-level grant data from the FDO searches into a single grants flat file, removing grant instances in which the given EIN was the recipient rather than the grantmaker (the queries to FDO didn't separate out these two)
    * **Tools:** `compile_grants.py`, `compile.yml` (config file)
    * File locations and other configuration settings are specified in `compile.yml`
    To use the `compile_grants.py` command-line script, type the following at the command line:
    ```
    > python3 [path/to/compile_grants.py] --config [path/to/compile.yml]
    ```
8. Merged Grantmaker characteristics (contained in the file [`propublica_ein_result_data_with_loc.csv`](https://drive.google.com/file/d/1JgmyCjlNSCmcElHDoUz_dBqRzaCHs2kv/view?usp=share_link)) with all detailed grant data obtained from the FDO scraping ([`compiled_grant_data.csv`](https://drive.google.com/file/d/1QBc_JqFtg4DYkBC7vze0bqTfV19swVQA/view?usp=share_link)) and with Carnegie naming Keys/org information ([`organization_names.csv](https://drive.google.com/file/d/1GFQe-J96B5h_BudSKGSjm3sRmOHDT1VP/view?usp=share_link)), recipient location information, and institution data from [Carnegie Data (2025)](https://drive.google.com/file/d/1NIQk3upKbiWu9brkU5ertcGu0SopteVK/view?usp=share_link). Computed distances between grantmakers and grant recipients for individual grants
    * **Tools:** `merge_data.py` (command-line script), `merge_data.yml` (configuration file)
    * File locations and other configuration settings are specified in `merge_data.yml`
    To use `merge_data.py` at the command line:
    ```
    > python3 [path/to/merge_data.py] --config [path/to/merge_data.yml]
    ```
