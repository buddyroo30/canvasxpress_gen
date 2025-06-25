import json
import os
import sys
import requests
import re
import time
from dotenv import load_dotenv

load_dotenv()

from openai import AzureOpenAI

def generate_results_openai(prompt, model='gpt-4o-global', max_new_tokens=512, topp=1.0, temperature=0.0, presence_penalty=0.0, frequency_penalty=0.0):

    client = AzureOpenAI()

    completion = client.chat.completions.create(
        model=model,
        max_tokens=max_new_tokens,
        temperature=temperature,
        top_p=topp,
        messages=[
         {
            "role": "user",
            "content": prompt,
            },
        ],
    )
    generated_text = completion.choices[0].message.content

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

def generate_prompt(canvasxpress_config, schema_info, prompt_file="prompt.md", few_shot_examples_file="few_shot_examples.txt"):
    with open(prompt_file, "r") as f:
        prompt = f.read()

    prompt_orig = prompt

    with open(few_shot_examples_file, "r") as f:
        few_shot_examples_string = f.read()

    prompt = prompt_orig.format(
        canvasxpress_config=canvasxpress_config, schema_info=schema_info,few_shot_examples=few_shot_examples_string
    )

    return(prompt)

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
            
def genEnglishTextFromCanvasXpressConfig(configObj,headerRow,cxConfigInfo):
    questionObj = { "headers": headerRow, "configuration": configObj}
    questionJsonTxt = json.dumps(questionObj)
    schemaTxt = generateSchemaForExample(configObj,cxConfigInfo)
    prompt = generate_prompt(questionJsonTxt, schemaTxt, prompt_file="prompt.md", few_shot_examples_file="few_shot_examples.txt")
    if prompt is None:
        return(None)
    resultTxt = generate_results_openai(prompt)

    return(resultTxt)
    
def genEnglishTextsFromAllCanvasXpressConfigs(examplesJsonFile,cxConfigInfo):

    with open(examplesJsonFile, "r") as f:
        cxExamplesJsonTxt = f.read()
        cxExamples = json.loads(cxExamplesJsonTxt)

    # Iterate through the records and print them
    for row in cxExamples['examples']:
        configObj = row["config"]
        headerRow = row["header"]
        resultTxt = genEnglishTextFromCanvasXpressConfig(configObj,headerRow,cxConfigInfo)
        if resultTxt is not None:
            row['alt_prompts'] = [resultTxt]

    print(json.dumps(cxExamples))

cxConfigInfo = readCanvasXpressDocs("doc.json")
genEnglishTextsFromAllCanvasXpressConfigs("synth_examples.json",cxConfigInfo)