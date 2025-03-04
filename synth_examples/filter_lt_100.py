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

def remove_section(text, section_name):
    """
    Remove the section that begins with the specified section name from the input text.

    Args:
    - text (str): The input text containing various sections.
    - section_name (str): The name of the section to remove.

    Returns:
    - str: The text with the specified section removed.
    """
    pattern = rf'{re.escape(section_name)}:.*?(?=\n[A-Z ]+?:|$)'
    cleaned_text = re.sub(pattern, '', text, flags=re.DOTALL)
    # Remove any trailing newline characters
    cleaned_text = re.sub(r'\n+', '\n', cleaned_text).strip()
    return cleaned_text

def extract_section_value_from_string(input_string, section_name):
    """
    Extract the value of a specified section from the input string.

    Args:
    - input_string (str): The input string containing the section.
    - section_name (str): The name of the section to extract the value for.

    Returns:
    - str: The extracted value if the pattern matches, otherwise None.
    """
    # Define a regular expression pattern to match the section and its value
    pattern = re.compile(rf'{re.escape(section_name)}:\s*(.*?)(?=\n\S|$)', re.DOTALL)
    
    match = pattern.search(input_string)
    if match:
        return match.group(1).strip()
    return None

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
    similarity_score = extract_section_value_from_string(cur_rec_txt, "SIMILARITY SCORE")
    if similarity_score is None:
        print("BAD BAD BAD:")
        print(cur_rec_txt)
        sys.exit()
    similarity_score = float(similarity_score)
    error_decoding_json = extract_section_value_from_string(cur_rec_txt, "ERROR DECODING RESPONSE AS JSON")
    if similarity_score is not None and similarity_score < 100.0:
        cleaned_text = cur_rec_txt
        if error_decoding_json == "False":
            cleaned_text = remove_section(cleaned_text, "LLM GENERATED RESPONSE") #Just have the pretty version of the section
        cleaned_text = remove_section(cleaned_text, "FEW SHOT ANSWER") #Just have the pretty version of the section
        print(cleaned_text)

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

orig_file = "all_results.txt"
filter_records_lt_100(orig_file)

