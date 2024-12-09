from FlagEmbedding import BGEM3FlagModel
import json
import sys
from pymilvus import MilvusClient
from pymilvus.model.hybrid import BGEM3EmbeddingFunction
from pymilvus import connections
import numpy as np
import os
import utils

devFlag = os.environ.get("DEV")
if devFlag == 'True':
    devFlag = True
else:
    devFlag = False

allFewShotsFile = "all_few_shots.json"
cxDocFile = "doc.json"
vectorDbFile = "/root/.cache/canvasxpress_llm.db"
if devFlag:
    allFewShotsFile = "all_few_shots_dev.json"
    cxDocFile = "doc_dev.json"
    vectorDbFile = "/root/.cache/canvasxpress_llm_dev.db"

bge_m3_ef = BGEM3EmbeddingFunction(
                                    model_name='BAAI/bge-m3', # Specify the model name
                                    device='cpu', # Specify the device to use, e.g., 'cpu' or 'cuda:0'
                                    use_fp16=False # Specify whether to use fp16. Set to `False` if `device` is `cpu`.
                                )

def convert_boolean_dict_values(d):
    for k, v in d.items():
        if isinstance(v, dict):
            convert_boolean_dict_values(v)
        elif isinstance(v, list):
            for i in range(len(v)):
                if isinstance(v[i], dict):
                    convert_boolean_dict_values(v[i])
                elif v[i] == "true":
                    v[i] = True
                elif v[i] == "false":
                    v[i] = False
        else:
            if v == "true":
                d[k] = True
            elif v == "false":
                d[k] = False
    return d

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

def generateSchemaRecs(cxConfigInfo):

    schemaRecs = []
    for curField in cxConfigInfo:
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

def gen_vectordb(train_docs, vectorDbFile):
    """
    Generate a vector database from the training documents.

    Args:
    - train_docs (dict): The training documents.
    - vectorDbFile (str): The path to the vector database file.

    Returns:
    - None
    """

    connections.disconnect("default")
    if os.path.exists(vectorDbFile):
        os.remove(vectorDbFile)

    client = MilvusClient(vectorDbFile)
    client.create_collection(
        collection_name="few_shot_examples",
        dimension=1024  # The vectors we will use have 1024 dimensions
    )

    for i in range(len(train_docs)):
        curRec = train_docs[i]
        curConfig = curRec['config']
        curHeader = curRec['header']
        curPrompt = curRec['prompt']
        few_shot_docs_to_embed = []
        alt_prompts = curRec['alt_prompts']
        all_prompts = alt_prompts + [curPrompt]
        for j in range(len(all_prompts)):
            cur_prompt = all_prompts[j]
            few_shot_docs_to_embed.append(cur_prompt)

        few_shot_docs_embeddings = bge_m3_ef.encode_documents(few_shot_docs_to_embed)

        for j in range(len(all_prompts)):
            cur_prompt = all_prompts[j]
            curDocsBatch = [ {"id": i * 4 + j, "vector": few_shot_docs_embeddings["dense"][j], "configEnglish": cur_prompt, "headers": json.dumps(curHeader), "config": json.dumps(curConfig) } ]
            few_shot_res = client.insert(
                collection_name="few_shot_examples",
                data=curDocsBatch
            )

    return(client)

vectordb_docs = utils.read_json_file(allFewShotsFile)
client = gen_vectordb(vectordb_docs['examples'], vectorDbFile)


client.create_collection(
    collection_name="canvasxpress_docs",
    dimension=1024  # The vectors we will use have 1024 dimensions
)

cxConfigInfo = readCanvasXpressDocs(cxDocFile)
schemaRecs = generateSchemaRecs(cxConfigInfo)
schemaRecs_embeddings = bge_m3_ef.encode_documents(schemaRecs)
for i in range(len(schemaRecs)):
    curDocsBatch = [ {"id": i, "vector": schemaRecs_embeddings["dense"][i], "docTxt": schemaRecs[i] } ]
    schemaRecs_res = client.insert(
        collection_name="canvasxpress_docs",
        data=curDocsBatch
    )

connections.disconnect("default")