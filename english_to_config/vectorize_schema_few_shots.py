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
client.create_collection(
    collection_name="few_shot_examples",
    dimension=1024  # The vectors we will use have 1024 dimensions
)
client.create_collection(
    collection_name="canvasxpress_docs",
    dimension=1024  # The vectors we will use have 1024 dimensions
)

with open("datasets.json", "r") as f:
    cxDatasetsJsonTxt = f.read()
    cxDatasets = json.loads(cxDatasetsJsonTxt)

few_shot_docs_to_embed = []
for curRec in cxDatasets:
    curConfigEnglishTxt = curRec['configEnglish']
    few_shot_docs_to_embed.append(curConfigEnglishTxt)

few_shot_docs_embeddings = bge_m3_ef.encode_documents(few_shot_docs_to_embed)
for i in range(len(few_shot_docs_to_embed)):
    array2dTxt = cxDatasets[i]["array2d"]
    array2dObj = json.loads(array2dTxt)
    headers = []
    if array2dObj is not None and len(array2dObj) > 0:
        headers = array2dObj[0]
    curDocsBatch = [ {"id": i, "vector": few_shot_docs_embeddings["dense"][i], "configEnglish": few_shot_docs_to_embed[i], "headers": json.dumps(headers), "config": cxDatasets[i]["config"] } ]
    few_shot_res = client.insert(
        collection_name="few_shot_examples",
        data=curDocsBatch
    )

cxConfigInfo = readCanvasXpressDocs()
schemaRecs = generateSchemaRecs(cxConfigInfo)
schemaRecs_embeddings = bge_m3_ef.encode_documents(schemaRecs)
for i in range(len(schemaRecs)):
    curDocsBatch = [ {"id": i, "vector": schemaRecs_embeddings["dense"][i], "docTxt": schemaRecs[i] } ]
    schemaRecs_res = client.insert(
        collection_name="canvasxpress_docs",
        data=curDocsBatch
    )

sys.exit()




docs = [
    "Artificial intelligence was founded as an academic discipline in 1956.",
    "Alan Turing was the first person to conduct substantial research in AI.",
    "Born in Maida Vale, London, Turing was raised in southern England.",
]

docs_embeddings = bge_m3_ef.encode_documents(docs)
data = [ {"id": i, "vector": docs_embeddings["dense"][i], "text": docs[i], "subject": "AlanTuring"} for i in range(len(docs)) ]
res = client.insert(
    collection_name="demo_collection",
    data=data
)

queries = ["When was artificial intelligence founded", 
           "Where was Alan Turing born?"]

query_embeddings = bge_m3_ef.encode_queries(queries)

res = client.search(
    collection_name="demo_collection",
    data=[query_embeddings["dense"][0]],
    limit=1,
    output_fields=["text", "id","subject"],
)
print(res)

sys.exit()


model = BGEM3FlagModel('BAAI/bge-m3',  
                       use_fp16=True) # Setting use_fp16 to True speeds up computation with a slight performance degradation

sent1 = "How now brown cow"
sent2 = "How now brown bovine"

embeddings_1 = model.encode(sent1)['dense_vecs']
embeddings_1_json = json.dumps(embeddings_1.tolist())
embeddings_2 = model.encode(sent2)['dense_vecs']
embeddings_2_json = json.dumps(embeddings_1.tolist())
print("\n\n\nEMBEDDINGS 1: " + str(embeddings_1_json))
print("size: " + str(embeddings_1.size))
print()
print("\n\n\nEMBEDDINGS 2: " + str(embeddings_2_json))
print("size: " + str(embeddings_2.size))
print()
sim = embeddings_1 @ embeddings_2
print("\n\n\nSIMILARITY: " + str(sim))
embeddings_1_back = np.array(json.loads(embeddings_1_json))
print("\n\nEMBDDINGS 1 BACK size: " + str(embeddings_1_back.size))
embeddings_2_back = np.array(json.loads(embeddings_2_json))
print("\n\nEMBDDINGS 2 BACK size: " + str(embeddings_2_back.size))

client.insert( collection_name="demo_collection", data = {"id": 1, "vector": embeddings_1, "text": sent1, "color": "brown"})
client.insert( collection_name="demo_collection", data = {"id": 2, "vector": embeddings_2, "text": sent2, "color": "bovine"})

res = client.search(
    collection_name="demo_collection",
    data=[embeddings_1],
    limit=2,
    output_fields=["text", "color"],
)
print(res)

sys.exit()

sentences_1 = ["What is BGE M3?", "Defination of BM25"]
sentences_2 = ["BGE M3 is an embedding model supporting dense retrieval, lexical matching and multi-vector interaction.", 
               "BM25 is a bag-of-words retrieval function that ranks a set of documents based on the query terms appearing in each document"]
sentences_3 = ["What is BGE M3?", "Defination of BM25"]

embeddings_1 = model.encode(sentences_1, 
                            batch_size=12, 
                            max_length=8192, # If you don't need such a long length, you can set a smaller value to speed up the encoding process.
                            )['dense_vecs']
embeddings_2 = model.encode(sentences_2)['dense_vecs']
embeddings_3 = model.encode(sentences_3)['dense_vecs']
similarity = embeddings_1 @ embeddings_2.T
print(similarity)
similarity = embeddings_1 @ embeddings_2.T
print(similarity)
# [[0.6265, 0.3477], [0.3499, 0.678 ]]
similarity = embeddings_1 @ embeddings_3.T
print(similarity)