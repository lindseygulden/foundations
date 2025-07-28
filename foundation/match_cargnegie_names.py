"""bespoke script to match carnegie names to other sources' naming convention. hard coded. kept for records"""

import pandas as pd
from utils.strings import similar_strings

# Times higher education ranking
the_df = pd.read_csv("/Volumes/T5_external/data/foundation/the_rankings.csv")
the_df.columns = [
    "name",
    "the_overall",
    "the_teaching",
    "the_research_environment",
    "the_research_quality",
    "the_industry",
    "the_international_outlook",
]
# get rid of extra text on end of names
the_df["name"] = [x.split("United States")[0] for x in the_df.name]

# read in carnegie data (for names, which is in the 'instnm' column)
carnegie_all_df = pd.read_csv(
    "/Users/lindseygulden/dev/leg-up-private/projects/foundation/data/carnegie_data_2025.csv"
)
carnegie_colleges = list(
    carnegie_all_df.loc[carnegie_all_df.research2025 > 0].instnm.unique()
)

# make a draft matching to the best carnegie college
the_df["draft_match"] = [
    similar_strings(x, carnegie_colleges, 1)[0] for x in the_df.name
]
# write to CSV for manual evaluation & correction of draft match
the_df.to_csv(
    "/Users/lindseygulden/dev/leg-up-private/projects/foundation/data/the_rankings.csv",
    index=False,
)
