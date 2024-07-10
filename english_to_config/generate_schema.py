import sqlite3
import json
import os
import sys
import requests
import re
import csv
import time
from dotenv import load_dotenv

load_dotenv()

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

def IsaacSimpleExamplesFields(isaacSimpleExamplesFile,fieldsToUseSet):

    with open(isaacSimpleExamplesFile, "r") as f:
        cxExamplesJsonTxt = f.read()
        cxExamples = json.loads(cxExamplesJsonTxt)

    for curRec in cxExamples['Questions']:
        curConfig = curRec['Answer']
        for curConfigField in curConfig:
            fieldsToUseSet.add(curConfigField)

def read_tsv_file(file_path):
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file, delimiter='\t')
        data = [row for row in reader]
    return data

def getCxFieldsToUse(fieldsUseFile,isaacSimpleExamplesFile):
    fieldsArrDict = read_tsv_file(fieldsUseFile)

    fieldsUseSet = set()
    for curRec in fieldsArrDict:
        if "Use?" in curRec and curRec["Use?"].lower() == "y":
            fieldsUseSet.add(curRec["FieldName"])

    IsaacSimpleExamplesFields(isaacSimpleExamplesFile,fieldsUseSet)

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
            
fieldsUseSet = getCxFieldsToUse("field_counts_use.txt","canvasxpress-lmm-gpt4.json")
cxConfigInfo = readCanvasXpressDocs("doc.json")
schemaTxt = generateSchema(cxConfigInfo,fieldsUseSet=fieldsUseSet)
print(schemaTxt)

