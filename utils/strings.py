"""string maniuplation functions"""

import difflib
from typing import List


def similar_strings(s: str, string_list: List[str], n_strings: int) -> List[str]:
    """
    Finds a specified number of strings from a list most similar to input string s.

    Args:
        s: string to compare to the list
        string_list: list of strings that will be compared to string s
        n_strings: number of similar strings to return
    Returns:
        n_strings-long list of the strings from string_list that are most simliar to s
    """
    # compute similarity
    similarities = [
        (candidate, difflib.SequenceMatcher(None, s, candidate).ratio())
        for candidate in string_list
    ]

    # sort by similarity score in descending order
    similarities.sort(key=lambda x: x[1], reverse=True)

    # Return the n_strings most matching strings
    return [match[0] for match in similarities[:n_strings]]


def similarity_score(s1: str, s2: str) -> float:
    """
    Returns a similarity score between two strings using difflib.SequenceMatcher.

    Args:
        s1: First string to compare
        s2: Second string to compare

    Returns:
        float between 0.0 and 1.0 (0 is most dissimilar; 1 is most similar)
    """
    return difflib.SequenceMatcher(None, s1, s2).ratio()
