import json
import sys
import os

def read_json_file(file_path):
    """
    Read a file containing JSON text and evaluate the contents to a Python dictionary.

    Args:
    - file_path (str): The path to the JSON file.

    Returns:
    - dict: The contents of the file as a Python dictionary.
    """
    try:
        with open(file_path, 'r') as file:
            # Read the file contents
            file_contents = file.read()
            # Parse the JSON text to a Python dictionary
            data = json.loads(file_contents)
            return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {file_path}")
        return None

#C == Comment
#D == Default value
#M == category
#O == Options (only values from this list can be used)
#T == Type
def readCanvasXpressDocs (docsFile):
    cxConfigInfo = None
    with open(docsFile) as f_in:
        cxConfigInfo = json.load(f_in)
    cxConfigInfo = cxConfigInfo['P']
    for curField in cxConfigInfo:
        curFieldInfo = cxConfigInfo[curField]
        if "C" in curFieldInfo:
            commentTxt = curFieldInfo["C"]
            commentTxt = commentTxt.rstrip('<br>')
            curFieldInfo["C"] = commentTxt
    return(cxConfigInfo)

def generateSchemaRecs(cxConfigInfo, useSet):

    schemaRecs = []
    for curField in cxConfigInfo:
        if curField not in useSet:
            continue
        curFieldInfo = cxConfigInfo[curField]
        curFieldInfoList = []
        if "C" in curFieldInfo:
            curFieldInfoList.append("Description: '" + curFieldInfo["C"] + "'")
        if "T" in curFieldInfo:
            curFieldType = curFieldInfo["T"]
            curFieldInfoList.append(f"Type: '{curFieldType}'")
        if "M" in curFieldInfo:
            curFieldCategory = curFieldInfo["M"]
            curFieldInfoList.append(f"Category: '{curFieldCategory}'")
        if "O" in curFieldInfo:
            curFieldOptions = [str(curV) for curV in curFieldInfo["O"]]
            curFieldOptionsTxt = "[" + ",".join(curFieldOptions) + "]"
            curFieldInfoList.append(f"Options for Field Value: {curFieldOptionsTxt}")
        if "D" in curFieldInfo:
            curFieldDefaultVal = curFieldInfo["D"]
            curFieldInfoList.append(f"Default Value: '{curFieldDefaultVal}'")
        if len(curFieldInfoList) > 0:
            curFieldConfigTxt = curField + ": " + ", ".join(curFieldInfoList)
            schemaRecs.append(curFieldConfigTxt)

    return(schemaRecs)

def recurse_and_collect_keys(input_dict, keys_set):
    """
    Recursively traverse a dictionary and collect all the keys into a set.

    Args:
    - input_dict (dict): The dictionary to traverse.
    - keys_set (set): The set to collect the keys into.

    Returns:
    - None: The keys are added to the provided set.
    """
    for key, value in input_dict.items():
        keys_set.add(key)
        if isinstance(value, dict):
            recurse_and_collect_keys(value, keys_set)

train_file = "train_set.json"
test_file = "test_set.json"
cxDocFile = "doc.json"

params_set = set()
train_set = read_json_file(train_file)
for curRec in train_set:
    recurse_and_collect_keys(curRec['config'], params_set)
test_set = read_json_file(test_file)
for curRec in test_set:
    recurse_and_collect_keys(curRec['config'], params_set)

cxConfigInfo = readCanvasXpressDocs(cxDocFile)
schemaRecs = generateSchemaRecs(cxConfigInfo, params_set)
print("\n".join(schemaRecs))
