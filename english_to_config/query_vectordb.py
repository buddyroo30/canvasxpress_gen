from FlagEmbedding import BGEM3FlagModel
import json
import sys
from pymilvus import MilvusClient
from pymilvus.model.hybrid import BGEM3EmbeddingFunction
import numpy as np

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

bge_m3_ef = BGEM3EmbeddingFunction(
    model_name='BAAI/bge-m3', # Specify the model name
    device='cpu', # Specify the device to use, e.g., 'cpu' or 'cuda:0'
    use_fp16=False # Specify whether to use fp16. Set to `False` if `device` is `cpu`.
)

dbLoc = "/root/.cache/canvasxpress_llm.db"
client = MilvusClient(dbLoc)

with open("datasets.json", "r") as f:
    cxDatasetsJsonTxt = f.read()
    cxDatasets = json.loads(cxDatasetsJsonTxt)

cxConfigInfo = readCanvasXpressDocs()

queries = ["The graph type is bar."]

query_embeddings = bge_m3_ef.encode_queries(queries)
#collection_name="few_shot_examples",
#collection_name="canvasxpress_docs",


res = client.search(
    collection_name="few_shot_examples",
    data=[query_embeddings["dense"][0]],
    limit=10,
    output_fields=["configEnglish", "headers", "config", "id"]
)
print(res)

sys.exit()
