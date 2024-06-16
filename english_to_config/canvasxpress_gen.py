import sqlite3
import json
import os
import sys
import requests
import re
import csv
import time
from FlagEmbedding import BGEM3FlagModel
from pymilvus import MilvusClient
from pymilvus.model.hybrid import BGEM3EmbeddingFunction
import numpy as np
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

def generate_prompt(canvasxpress_config_english, headers_column_names, schema_info_file="schema_info.txt", schema_info_string=None,
                    prompt_file="prompt.md", few_shot_examples_file="few_shot_examples_all.txt", few_shot_examples_string=None):
    with open(prompt_file, "r") as f:
        prompt = f.read()

    if few_shot_examples_string is None:
        with open(few_shot_examples_file, "r") as f:
            few_shot_examples_string = f.read()

    if schema_info_string is None:
        with open(schema_info_file, "r") as f:
            schema_info_string = f.read()

    prompt = prompt.format(
        canvasxpress_config_english=canvasxpress_config_english, headers_column_names=headers_column_names, schema_info=schema_info_string,few_shot_examples=few_shot_examples_string
    )

    return prompt


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

def read_tsv_file(file_path):
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file, delimiter='\t')
        data = [row for row in reader]
    return data

def getCxFieldsToUse():
    fieldsArrDict = read_tsv_file("field_counts_use.txt")

    fieldsUseSet = set()
    for curRec in fieldsArrDict:
        if "Use?" in curRec and curRec["Use?"].lower() == "y":
            fieldsUseSet.add(curRec["FieldName"])

    return(fieldsUseSet)

def generateSchema(cxConfigInfo,fieldsUseSet=None):

    schemaTxt = "Here is detailed information about the CanvasXpress JSON configuration fields:\n"
    for curField in cxConfigInfo:
        if fieldsUseSet is None or curField not in fieldsUseSet:
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
            schemaTxt = schemaTxt + curFieldConfigTxt + "\n"

    return(schemaTxt)
            
def genEnglishTextFromCanvasXpressConfig(configJsonTxt,cxConfigInfo):
    configObj = json.loads(configJsonTxt)
    schemaTxt = generateSchemaForExample(configObj,cxConfigInfo)
    prompt = generate_prompt(configJsonTxt, schemaTxt, prompt_file="prompt.md", few_shot_examples_file="few_shot_examples.txt")
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
        resultTxt = genEnglishTextFromCanvasXpressConfig(configTxt,cxConfigInfo)
        curRec['configEnglish'] = resultTxt
        updatedInfo.append(curRec)
        time.sleep(5)

    # Close the connection
    conn.close()

    print(json.dumps(updatedInfo))

def genFewShotExamples():

    fewShotTxt = ''

    cxDatasets = None
    with open("datasets.json", "r") as f:
        cxDatasetsJsonTxt = f.read()
        cxDatasets = json.loads(cxDatasetsJsonTxt)

    for curRec in cxDatasets:
        curConfig = curRec['config'].replace("\n"," ")
        curEnglishConfig = curRec['configEnglish'].replace("\n", " ")
        fewShotTxt = fewShotTxt + f"English Text: {curEnglishConfig}, Answer: {curConfig}" + "\n"

    return(fewShotTxt)


numFewShots = 25
bge_m3_ef = BGEM3EmbeddingFunction(
    model_name='BAAI/bge-m3', # Specify the model name
    device='cpu', # Specify the device to use, e.g., 'cpu' or 'cuda:0'
    use_fp16=False # Specify whether to use fp16. Set to `False` if `device` is `cpu`.
)

dbLoc = "/root/.cache/canvasxpress_llm.db"
userQuestion = "Generate a box plot with legend at the top"
headers_column_names = str(['col1','col2','col3'])
client = MilvusClient(dbLoc)
queries = [userQuestion]

query_embeddings = bge_m3_ef.encode_queries(queries)
#collection_name="few_shot_examples",
#collection_name="canvasxpress_docs",


res = client.search(
    collection_name="few_shot_examples",
    data=[query_embeddings["dense"][0]],
    limit=numFewShots,
    output_fields=["config", "configEnglish", "headers", "id"],
)
#English Text: ..., Answer: ...
#See here for where got below to get the hits: https://github.com/milvus-io/pymilvus/blob/master/examples/milvus_client/simple.py#L68
fewShotTxt = ""
for hits in res:
    for hit in hits:
        curConfig = hit['entity']['config'].replace("\n"," ")
        curEnglishConfig = hit['entity']['configEnglish'].replace("\n", " ")
        curHeadersColumnNames = hit['entity']['headers'].replace("\n", " ")
        fewShotTxt = fewShotTxt + f"English Text: {curEnglishConfig}; Headers/Column Names: {curHeadersColumnNames}, Answer: {curConfig}" + "\n"

fieldsUseSet = getCxFieldsToUse()
cxConfigInfo = readCanvasXpressDocs()
schemaTxt = generateSchema(cxConfigInfo,fieldsUseSet=fieldsUseSet)
generatedPrompt = generate_prompt(userQuestion,headers_column_names, schema_info_string=schemaTxt,few_shot_examples_string=fewShotTxt)
encoding_tokens = openai_enc.encode(generatedPrompt)
print(generatedPrompt)
print("num tokens: " + str(len(encoding_tokens)))

