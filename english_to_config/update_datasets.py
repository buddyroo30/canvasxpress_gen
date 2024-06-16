import json
import sys
import csv

def read_tsv_file(file_path):
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file, delimiter='\t')
        data = [row for row in reader]
    return data

def filterToUseFields():
    fieldsArrDict = read_tsv_file("field_counts_use.txt")

    fieldsUseSet = set()
    for curRec in fieldsArrDict:
        if "Use?" in curRec and curRec["Use?"].lower() == "y":
            fieldsUseSet.add(curRec["FieldName"])

    with open("datasets.json", "r") as f:
        cxDatasetsJsonTxt = f.read()
        cxDatasets = json.loads(cxDatasetsJsonTxt)

    updatedCxDatasets = []
    for curRec in cxDatasets:
        configJson = curRec['config']
        configObj = json.loads(configJson)
        fullJson = curRec['json']
        fullObj = json.loads(fullJson)
        delFlag = False
        configObjFields = [curField for curField in configObj]
        for curField in configObjFields:
            if curField not in fieldsUseSet:
                del configObj[curField]
                del fullObj['config'][curField]
                delFlag = True
        if delFlag:
            curRec['config'] = json.dumps(configObj)
            curRec['json'] = json.dumps(fullObj)
        del curRec['configEnglish']
        updatedCxDatasets.append(curRec)

    print(json.dumps(updatedCxDatasets))

def filterRedundantRecs():

    with open("datasets.json", "r") as f:
        cxDatasetsJsonTxt = f.read()
        cxDatasets = json.loads(cxDatasetsJsonTxt)

    seenConfigObjs = []
    filteredCxDatasets = []
    for curRec in cxDatasets:
        configJson = curRec['config']
        configObj = json.loads(configJson)
        if configObj in seenConfigObjs:
            continue
        seenConfigObjs.append(configObj)
        filteredCxDatasets.append(curRec)

    print(json.dumps(filteredCxDatasets))

filterRedundantRecs()