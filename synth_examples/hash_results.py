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

def extract_section_value_from_string(input_string, section_name):
    """
    Extract the value of a specified section from the input string.
    
    :param input_string: The input string containing multiple sections.
    :param section_name: The name of the section to extract.
    :return: The extracted value of the section as a string, or None if the section is not found.
    """
    pattern = re.compile(rf'{section_name}:(.*?)(?=\n[A-Z ]+:|$)', re.DOTALL)
    match = pattern.search(input_string)
    if match:
        return match.group(1).strip()
    return None

def hash_rec(cur_rec_txt, curNumFewShots, hashed_results):
    few_shot_question = extract_section_value_from_string(cur_rec_txt, "FEW SHOT QUESTION")
    llm_generated_response = extract_section_value_from_string(cur_rec_txt, "LLM GENERATED RESPONSE")
    if empty(few_shot_question) or empty(llm_generated_response):
        print("Error: Few shot question or LLM generated response is empty")
        sys.exit()
    subhash = hashed_results.setdefault(few_shot_question, {})
    subhash[curNumFewShots] = llm_generated_response

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

def hash_results(file_path):
    cur_rec_txt = ""
    curNumFewShots = 100
    hashed_results = {}
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('--- TESTING NUM_FEW_SHOTS'):
                match = re.search(r'--- TESTING NUM_FEW_SHOTS (\d+) ---', line)
                if match:
                    curNumFewShots = int(match.group(1))
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
                    hash_rec(cur_rec_txt, curNumFewShots, hashed_results)
                    cur_rec_txt = ""
            cur_rec_txt += line
    if not empty(cur_rec_txt):
        hash_rec(cur_rec_txt, curNumFewShots, hashed_results)

    return(hashed_results)

#orig_file = "all_results.txt"
#hashed_results = hash_results(orig_file)
#print(json.dumps(hashed_results, indent=2))

