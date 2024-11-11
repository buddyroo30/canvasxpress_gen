import json
import sys
import re

def empty(str):
    """
    Return True if the str is None or composed of only whitespace, False otherwise
    """

    if str is None:
        return True
    if str.strip() == "":
        return True
    return False

def extract_similarity_score_from_string(input_string):
    """
    Extract the float value of SIMILARITY SCORE from the input string.

    Args:
    - input_string (str): The input string containing the value.

    Returns:
    - float: The extracted float value if the pattern matches, otherwise None.
    """
    match = re.search(r'SIMILARITY SCORE: (\d+(\.\d+)?)', input_string)
    if match:
        return float(match.group(1))
    return None

def print_rec(cur_rec_txt):
    similarity_score = extract_similarity_score_from_string(cur_rec_txt)
    if similarity_score is not None and similarity_score < 100.0:
        print(cur_rec_txt, end='')

skip_lines = [
"***SUMMARY***",
"NUMBER OF FEW SHOTS TESTED SUCCESSFULLY",
"NUMBER OF EXACT MATCHES",
"PERCENT EXACT MATCHES",
"NUMBER OF SUBSET MATCHES",
"PERCENT SUBSET MATCHES",
"AVERAGE SIMILARITY SCORE",
"MEDIAN SIMILARITY SCORE",
"MAXIMUM SIMILARITY SCORE",
"MINIMUM SIMILARITY SCORE"
]

def filter_records_lt_100(file_path):
    cur_rec_txt = ""
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('--- TESTING NUM_FEW_SHOTS'):
                print(line, end='')
                continue
            skipLineFlag = False
            for cur_skip_line in skip_lines:
                if line.startswith(cur_skip_line):
                    skipLineFlag = True
                    break
            if skipLineFlag:
                continue
            if line.startswith('FEW SHOT QUESTION:'):
                if not empty(cur_rec_txt):
                    print_rec(cur_rec_txt)
                    cur_rec_txt = ""
            cur_rec_txt += line
    if not empty(cur_rec_txt):
        print_rec(cur_rec_txt)

orig_file = "length_10_prompts/all_results.txt"
filter_records_lt_100(orig_file)

