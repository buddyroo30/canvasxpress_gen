from FlagEmbedding import BGEM3FlagModel
import json
import sys
from pymilvus import MilvusClient
from pymilvus.model.hybrid import BGEM3EmbeddingFunction
from pymilvus import connections
import numpy as np
import math
import statistics
import os
import re
from openai import AzureOpenAI
from dotenv import load_dotenv
import tiktoken
import utils

load_dotenv()

openai_enc = tiktoken.encoding_for_model('gpt-4o-global')

def extract_json_from_response(response):
    """
    Extract the legal JSON content from a response string.

    Args:
    - response (str): The input response string containing JSON content.

    Returns:
    - dict: The extracted JSON content as a dictionary if the pattern matches, otherwise None.
    """
    # Define a regular expression pattern to match JSON content
    pattern = re.compile(r'\{.*\}', re.DOTALL)
    
    match = pattern.search(response)
    if match:
        json_content = match.group(0)
        json_obj = {}
        try:
            json_obj = json.loads(json_content)
        except Exception as e:
            return False, str(e), json_content, json_obj

        return True, None, json_content, json_obj
    return False, "Did not match JSON in response", "", {}

def generate_results_openai(prompt, model='gpt-4o-global', max_new_tokens=1024, topp=1.0, temperature=0.1):

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

bge_m3_ef = BGEM3EmbeddingFunction(
    model_name='BAAI/bge-m3', # Specify the model name
    device='cpu', # Specify the device to use, e.g., 'cpu' or 'cuda:0'
    use_fp16=False # Specify whether to use fp16. Set to `False` if `device` is `cpu`.
)

def getFewShots(milvusClient, prompt,numFewShots=25,filterPrompt=False,format='text'):

    in_numFewShots = numFewShots
    if filterPrompt:
        numFewShots = numFewShots + 1

    prompt = prompt.replace("\n", " ")

    queries = [prompt]

    query_embeddings = bge_m3_ef.encode_queries(queries)
    #collection_name="few_shot_examples",
    #collection_name="canvasxpress_docs",

    res = milvusClient.search(
        collection_name="few_shot_examples",
        data=[query_embeddings["dense"][0]],
        limit=numFewShots,
        output_fields=["config", "configEnglish", "headers", "id"],
    )
    #English Text:...; Headers/Column Names: ..., Answer: ...
    #See here for where got below to get the hits: https://github.com/milvus-io/pymilvus/blob/master/examples/milvus_client/simple.py#L68
    fewShotTxt = ""
    fewShotObj = []
    fewShotsCt = 0
    for hits in res:
        for hit in hits:
            if fewShotsCt < in_numFewShots:
                curConfig = hit['entity']['config'].replace("\n"," ")
                curEnglishConfig = hit['entity']['configEnglish'].replace("\n", " ")
                if filterPrompt and prompt == curEnglishConfig:
                    continue
                curHeadersColumnNames = hit['entity']['headers'].replace("\n", " ")
                if format == 'text':
                    fewShotTxt = fewShotTxt + f"English Text: {curEnglishConfig}; Headers/Column Names: {curHeadersColumnNames}, Answer: {curConfig}" + "\n"
                elif format == 'json':
                    curRec = { 'English Text': curEnglishConfig, 'Headers/Column Names': curHeadersColumnNames, 'Answer': curConfig }
                    fewShotObj.append(curRec)
                fewShotsCt = fewShotsCt + 1

    if format == 'json':
        fewShotTxt = json.dumps(fewShotObj)

    return(fewShotTxt)

def gen_vectordb(train_docs, num_docs, vectorDbFile):
    """
    Generate a vector database from the training documents.

    Args:
    - train_docs (dict): The training documents.
    - num_docs (int): The number of documents to include in the vector database.
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

    train_docs_slice = train_docs[:num_docs]

    for i in range(len(train_docs_slice)):
        curRec = train_docs_slice[i]
        curConfig = curRec['config']
        curHeader = curRec['header']
        curPrompt = curRec['prompt']
        few_shot_docs_to_embed = []
        few_shot_docs_to_embed.append(curPrompt)
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

def exec_one_test(train_docs,num_few_shots,test_docs):
    """
    Execute a single accuracy test.

    Args:
    - train_docs (list): The training documents.
    - num_few_shots (int): The number of few-shot examples to use.
    - test_docs (list): The test documents.

    Returns:
    - None
    """

    similarityScores = []
    exactMatchCt = 0
    subsetCt = 0
    minSimilarityScore = 100.0
    maxSimilarityScore = 0.0

    all_f.write(f"--- TESTING NUM_FEW_SHOTS {num_few_shots} ---" + "\n")

    vectorDbFile = f"few_shots_{num_few_shots}.db"
    # Generate the vector database
    client = gen_vectordb(train_docs, num_few_shots, vectorDbFile)

    for i in range(len(test_docs)):
        curRec = test_docs[i]
        curConfig = curRec['config']
        curHeader = curRec['header']
        curPrompt = curRec['prompt']
        alt_prompts = curRec['alt_prompts']
        all_prompts = alt_prompts + [curPrompt]
        prompt_docs_to_embed = []
        for j in range(len(all_prompts)):
            cur_prompt = all_prompts[j]
            all_f.write("FEW SHOT QUESTION: " + cur_prompt + "\n")
            all_f.write("ORIGINAL COPILOT QUESTION:" + curPrompt + "\n")
            all_f.write("FEW SHOT HEADER: " + str(curHeader) + "\n")
            all_f.write("FEW SHOT ANSWER: " + json.dumps(curConfig) + "\n")
            all_f.write("FEW SHOT ANSWER PRETTY:" + json.dumps(curConfig,indent=2,sort_keys=True) + "\n")
            fewShotTxt = getFewShots(client, cur_prompt,numFewShots=25,filterPrompt=True,format='text')
            overall_prompt = utils.generate_prompt(cur_prompt,str(curHeader), schema_info_file="schema_info.txt",prompt_file="prompt.md",few_shot_examples_string=fewShotTxt)
            generated_text = generate_results_openai(overall_prompt)
            successFlag, decodeMsg, jsonStr, jsonObj = extract_json_from_response(generated_text)
            if not successFlag:
                all_f.write("ERROR DECODING RESPONSE AS JSON: True\n")
                all_f.write("ATTEMPTED EXTRACTION OF JSON STRING ERROR: " + decodeMsg + "\n")
                all_f.write("ATTEMPTED EXTRACTION OF JSON STRING EXTRACTED VALUE: " +  jsonStr + "\n")
                jsobObj = {}
            else:
                all_f.write("ERROR DECODING RESPONSE AS JSON: False\n")
            jsonSimilarityScore = 0.0
            answerIsSubset = "Unknown"
            jsonSimilarityScore = utils.json_similarity(curConfig,jsonObj)
            if utils.is_subset(curConfig,jsonObj):
                answerIsSubset = "True"
                subsetCt = subsetCt + 1
            else:
                answerIsSubset = "False"
            if jsonSimilarityScore < minSimilarityScore:
                minSimilarityScore = jsonSimilarityScore
            if jsonSimilarityScore > maxSimilarityScore:
                maxSimilarityScore = jsonSimilarityScore
            all_f.write("LLM GENERATED RESPONSE: " + generated_text + "\n")
            all_f.write("LLM ANSWER PRETTY:" + "\n")
            all_f.write(json.dumps(jsonObj,indent=2,sort_keys=True) + "\n")
            all_f.write("SIMILARITY SCORE: " + str(jsonSimilarityScore) + "\n")
            all_f.write("TRUE ANSWER IS SUBSET OF LLM GENERATED ANSWER: " + answerIsSubset + "\n")
            similarityScores.append(jsonSimilarityScore)
            if jsonSimilarityScore >= 100.0:
                exactMatchCt = exactMatchCt + 1

    avgSimilarityScore = statistics.mean(similarityScores)
    medSimilarityScore = statistics.median(similarityScores)
    percentExactMatch = exactMatchCt / len(similarityScores)
    percentSubsetMatch = subsetCt / len(similarityScores)

    all_f.write("***SUMMARY***" + "\n")
    all_f.write("NUMBER OF FEW SHOTS TESTED SUCCESSFULLY: " + str(len(similarityScores)) + "\n")
    all_f.write("NUMBER OF EXACT MATCHES: " + str(exactMatchCt) + "\n")
    all_f.write("PERCENT EXACT MATCHES: " + str(percentExactMatch) + "\n")
    all_f.write("NUMBER OF SUBSET MATCHES: " + str(subsetCt) + "\n")
    all_f.write("PERCENT SUBSET MATCHES: " + str(percentSubsetMatch) + "\n")
    all_f.write("AVERAGE SIMILARITY SCORE: " + str(avgSimilarityScore) + "\n")
    all_f.write("MEDIAN SIMILARITY SCORE: " + str(medSimilarityScore) + "\n")
    all_f.write("MAXIMUM SIMILARITY SCORE: " + str(maxSimilarityScore) + "\n")
    all_f.write("MINIMUM SIMILARITY SCORE: " + str(minSimilarityScore) + "\n")

    sum_result = [str(num_few_shots),str(len(similarityScores)),str(exactMatchCt),str(percentExactMatch),str(subsetCt),str(percentSubsetMatch),
                  str(avgSimilarityScore),str(medSimilarityScore),str(maxSimilarityScore),str(minSimilarityScore)]
    sum_f.write("\t".join(sum_result) + "\n")



train_file = "train_set.json"
test_file = "test_set.json"
cxDocFile = "doc.json"
test_num_few_shots = [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100,2200,2300]

all_f = open("all_results.txt", "w")
sum_f = open("summary_results.txt", "w")
sum_result_header = ["Num Few Shots", "Num Examples Tested", "Num Exact Matches", "Exact MatchPerc","Num Subset Matches",
                    "Subset Match Perc","Avg Similarity Score", "Med Similarity Score", "Max Similarity Score", "Min Similarity Score"]
sum_f.write("\t".join(sum_result_header) + "\n")

train_docs = utils.read_json_file(train_file)
test_docs = utils.read_json_file(test_file)

for num_few_shots in test_num_few_shots:
    exec_one_test(train_docs,num_few_shots,test_docs)





