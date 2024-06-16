import sqlite3
import json
import os
import sys
import requests
import re
import time
import tiktoken
from dotenv import load_dotenv

load_dotenv()

import openai
# OpenAI Azure Config
openai.api_type = os.environ.get('OPENAI_API_TYPE')
openai.api_key = os.environ.get('OPENAI_API_KEY')
openai.api_base = os.environ.get('OPENAI_API_BASE')
openai.api_version = os.environ.get('OPENAI_API_VERSION')

openai_enc = tiktoken.encoding_for_model('gpt-4-32k')

def generate_results_openai(prompt, model='gpt-4-32k', max_new_tokens=1200, topp=1.0, temperature=0.0, presence_penalty=0.0, frequency_penalty=0.0):

    response = openai.ChatCompletion.create(
        engine=model, # replace this value with the deployment name you chose when you deployed the associated model.
        messages = [{"role":"user","content":prompt}],
        temperature=temperature,
        max_tokens=max_new_tokens,
        top_p=topp,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        stop=None)

    generated_text = response['choices'][0]['message']['content']

    return(generated_text)

def determineValueType(val):

    if isinstance(val,dict):
        return('dict')
    if isinstance(val,list):
        return('list')
    try:
        int(val)
        return('int')
    except ValueError:
        pass
    try:
        float(val)
        return('float')
    except ValueError:
        pass

    if val == 'true' or val == 'false':
        return('boolean')
    return('str')

def determineOverallType(valsList):

    allTypes = set()
    listTypes = set()

    for curVal in valsList:
        curValType = determineValueType(curVal)
        allTypes.add(curValType)
        if curValType == 'list':
            curListTypes = set()
            for curListVal in curVal:
                curListValType = determineValueType(curListVal)
                curListTypes.add(curListValType)
            listTypes.update(curListTypes)

    allTypesList = list(allTypes)
    listTypesList = list(listTypes)
    if len(allTypesList) == 1 and allTypesList[0] == "list":
        listTypesStr = "list[" + ",".join(listTypesList) + "]"
        return(listTypesStr)
    elif 'list' in allTypesList:
        listTypesStr = "list[" + ",".join(listTypesList) + "]"
        allTypesList.remove('list')
        allTypesList.append(listTypesStr)
        allTypesTxt = ",".join(allTypesList)
        return(allTypesTxt)
    else:
        allTypesTxt = ",".join(allTypesList)
        return(allTypesTxt)

def generate_prompt(canvasxpress_config, schema_info, prompt_file="prompt.md", few_shot_examples_file="few_shot_examples.txt", max_num_tokens=32768):
    with open(prompt_file, "r") as f:
        prompt = f.read()

    prompt_orig = prompt

    with open(few_shot_examples_file, "r") as f:
        few_shot_examples_string = f.read()

    prompt = prompt_orig.format(
        canvasxpress_config=canvasxpress_config, schema_info=schema_info,few_shot_examples=few_shot_examples_string
    )

    encoding_tokens = openai_enc.encode(prompt)
    if len(encoding_tokens) > max_num_tokens:
        return(None)
    else:
        return(prompt)

def iterate_records(database_path):

    configInfo = {}
    # Connect to the SQLite database
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Execute a SELECT query to fetch all records from the table
    cursor.execute(f"SELECT name, type, config, array2d FROM datasets")

    # Iterate through the records and print them
    for row in cursor.fetchall():
        name = row[0]
        type = row[1]
        config = row[2]
        configObj = json.loads(config)
        for curField in configObj:
            curFieldVal = configObj[curField]
            curFieldValType = determineValueType(curFieldVal)
            if curField not in configInfo:
                configInfo[curField] = []
            if curFieldVal not in configInfo[curField]:
                configInfo[curField].append(curFieldVal)
        array2d = row[3]
        array2dObj = json.loads(array2d)
        header_row = "NONE"
        if array2dObj is not None and len(array2dObj) > 0:
            header_row = array2dObj[0]
        print(f"name: {name}\ntype: {type}\nconfig: {config}\nheader: {header_row}\n\n")

    updatedConfigInfo = {}
    for fieldName in configInfo:
        fieldValsList = configInfo[fieldName]
        typeStr = determineOverallType(fieldValsList)
        updatedConfigInfo[fieldName] = [typeStr]
        if typeStr == 'str' and not fieldName.lower().endswith("title"):
            updatedConfigInfo[fieldName].extend(fieldValsList)

    # Close the connection
    conn.close()

    return(updatedConfigInfo)

#This extracts config info from canvasxpress.min.js, but unfortunately Isaac says
#It doesn't get everything, so he just genereated a config info file doc.json for me that
#will use instead.
def canvasXpressConfigInfoFromJS ():
    r = requests.get("https://canvasxpress.org/dist/canvasXpress.min.js")
    cxTxt = r.text
    regexTxt = r'this\.\w\w\("([^"]+)"\s*,\s*"([^"]+)"(\s*,\s*\[[^\]]+\]|"[^"]+")?\s*,\s*"([^"]+)"\s*,\s*"([^"]+)",\s*k\s*\)'
    matches = re.finditer(regexTxt, cxTxt, re.MULTILINE)
    for match in matches:
        print("Full match:", match.group(0))
        print("Config Option Name:", match.group(1))
        print("default value:", match.group(2))
        optionsTxt = match.group(3)
        if optionsTxt is not None:
            optionsTxt = optionsTxt.strip()
            optionsTxt = optionsTxt.removeprefix(',')
        print("Options: ", optionsTxt)
        print("Description: ", match.group(4))
        print("Category: ", match.group(5))

#C == Comment
#D == Default value
#M == category
#O == Options (only values from this list can be used)
#T == Type
def readCanvasXpressDocs ():
    cxConfigInfo = None
    with open("doc.json") as f_in:
        cxConfigInfo = json.load(f_in)
    cxConfigInfo = cxConfigInfo['P']
    for curField in cxConfigInfo:
        curFieldInfo = cxConfigInfo[curField]
        if "C" in curFieldInfo:
            commentTxt = curFieldInfo["C"]
            commentTxt = commentTxt.rstrip('<br>')
            curFieldInfo["C"] = commentTxt
    return(cxConfigInfo)

def generateSchemaForExample(exampleConfigObj,cxConfigInfo):

    schemaTxt = "Here is detailed information about the CanvasXpress JSON configuration fields:\n"
    for curField in exampleConfigObj:
        if curField in cxConfigInfo:
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
                schemaTxt = schemaTxt + curFieldConfigTxt + "\n"

    return(schemaTxt)
            
def genEnglishTextFromCanvasXpressConfig(configJsonTxt,array2dTxt,cxConfigInfo):
    configObj = json.loads(configJsonTxt)
    array2dObj = json.loads(array2dTxt)
    headerRow = []
    if array2dObj is not None and len(array2dObj) > 0:
        headerRow = array2dObj[0]
    questionObj = { "headers": headerRow, "configuration": configObj}
    questionJsonTxt = json.dumps(questionObj)
    schemaTxt = generateSchemaForExample(configObj,cxConfigInfo)
    prompt = generate_prompt(questionJsonTxt, schemaTxt, prompt_file="prompt.md", few_shot_examples_file="few_shot_examples.txt")
    if prompt is None:
        return(None)
    resultTxt = generate_results_openai(prompt)

    return(resultTxt)

def genEnglishTextsFromAllCanvasXpressConfigs(database_path,cxConfigInfo):

    updatedInfo = []
    # Connect to the SQLite database
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Execute a SELECT query to fetch all records from the table
    cursor.execute(f"SELECT name, renderTo, type, json, array2d, data, config, events, info FROM datasets")

    # Iterate through the records and print them
    for row in cursor.fetchall():
        name = row[0]
        renderTo = row[1]
        typeTxt = row[2]
        jsonTxt = row[3]
        array2dTxt = row[4]
        dataTxt = row[5]
        configTxt = row[6]
        eventsTxt = row[7]
        infoTxt = row[8]
        curRec = { 'name': name, 'renderTo': renderTo, 'type': typeTxt, 'json': jsonTxt, 'array2d': array2dTxt, 'data': dataTxt, 'config': configTxt, 'events': eventsTxt, 'info': infoTxt }
        if curRec['config'].strip() == "" or curRec['config'].strip() == '{}':
            continue
        resultTxt = genEnglishTextFromCanvasXpressConfig(configTxt,array2dTxt,cxConfigInfo)
        if resultTxt is not None:
            curRec['configEnglish'] = resultTxt
            updatedInfo.append(curRec)
        time.sleep(1)

    # Close the connection
    conn.close()

    print(json.dumps(updatedInfo))
    
def genEnglishTextsFromAllCanvasXpressConfigs_json(datasetsJsonFile,cxConfigInfo):

    updatedInfo = []
    with open(datasetsJsonFile, "r") as f:
        cxDatasetsJsonTxt = f.read()
        cxDatasets = json.loads(cxDatasetsJsonTxt)

    # Iterate through the records and print them
    for row in cxDatasets:
        name = row['name']
        renderTo = row['renderTo']
        typeTxt = row['type']
        jsonTxt = row['json']
        array2dTxt = row['array2d']
        dataTxt = row['data']
        configTxt = row['config']
        eventsTxt = row['events']
        infoTxt = row['info']
        curRec = { 'name': name, 'renderTo': renderTo, 'type': typeTxt, 'json': jsonTxt, 'array2d': array2dTxt, 'data': dataTxt, 'config': configTxt, 'events': eventsTxt, 'info': infoTxt }
        if curRec['config'].strip() == "" or curRec['config'].strip() == '{}':
            continue
        resultTxt = genEnglishTextFromCanvasXpressConfig(configTxt,array2dTxt,cxConfigInfo)
        if resultTxt is not None:
            curRec['configEnglish'] = resultTxt
            updatedInfo.append(curRec)
        time.sleep(1)

    print(json.dumps(updatedInfo))

cxConfigInfo = readCanvasXpressDocs()
genEnglishTextsFromAllCanvasXpressConfigs("datasets.sqlite",cxConfigInfo)
#resultTxt = genEnglishTextFromCanvasXpressConfig(configJsonTxt,cxConfigInfo)
#print(resultTxt)
#print(json.dumps(cxConfigInfo))
#configInfo = iterate_records("datasets.sqlite")
#print(json.dumps(configInfo,sort_keys=True,indent=2))