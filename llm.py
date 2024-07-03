import os
from FlagEmbedding import BGEM3FlagModel
from pymilvus import MilvusClient
from pymilvus.model.hybrid import BGEM3EmbeddingFunction
import boto3
import openai
import json
from dotenv import load_dotenv

load_dotenv()

# OpenAI Azure Config
openai.api_type = os.environ.get('OPENAI_API_TYPE')
openai.api_key = os.environ.get('OPENAI_API_KEY')
openai.api_base = os.environ.get('OPENAI_API_BASE')
openai.api_version = os.environ.get('OPENAI_API_VERSION')

bge_m3_ef = BGEM3EmbeddingFunction(
    model_name='BAAI/bge-m3', # Specify the model name
    device='cpu', # Specify the device to use, e.g., 'cpu' or 'cuda:0'
    use_fp16=False # Specify whether to use fp16. Set to `False` if `device` is `cpu`.
)

def getMilvusClient(app):
    if 'MILVUS_CLIENT' not in app.config:
        fewShotDbLoc = "/root/.cache/canvasxpress_llm.db"
        app.config['MILVUS_CLIENT'] = MilvusClient(fewShotDbLoc)
    return(app.config['MILVUS_CLIENT'])

def getAllFewShots(milvusClient, format='text'):

    allRes = milvusClient.query("few_shot_examples", filter = "id >= 0", output_fields=["config", "configEnglish", "headers", "id"])
    fewShotTxt = ""
    fewShotObj = []
    #See here: https://github.com/milvus-io/pymilvus/blob/master/examples/milvus_client/simple.py#L52
    for hit in allRes:
        curConfig = hit['config'].replace("\n"," ")
        curEnglishConfig = hit['configEnglish'].replace("\n", " ")
        curHeadersColumnNames = hit['headers'].replace("\n", " ")
        if format == 'text':
            fewShotTxt = fewShotTxt + f"English Text: {curEnglishConfig}; Headers/Column Names: {curHeadersColumnNames}, Answer: {curConfig}" + "\n"
        elif format == 'json':
            curRec = { 'English Text': curEnglishConfig, 'Headers/Column Names': curHeadersColumnNames, 'Answer': curConfig }
            fewShotObj.append(curRec)

    if format == 'json':
        fewShotTxt = json.dumps(fewShotObj)

    return(fewShotTxt)

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

def generate_prompt(canvasxpress_config_english, headers_column_names, schema_info_file="schema_info.txt", schema_info_string=None,
                    prompt_file="prompt.md", few_shot_examples_file="few_shot_examples.txt", few_shot_examples_string=None):
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

def generate_results_titan(prompt, model='amazon.titan-tg1-large', max_token_count=2048, topp=1, temperature=0):

    bedrockRuntime = boto3.client('bedrock-runtime')

    body = json.dumps({
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": max_token_count,
            "stopSequences": [],
            "temperature":temperature,
            "topP":topp
        }
    })

    response = bedrockRuntime.invoke_model(body=body, modelId=model, accept='application/json', contentType='application/json')
    response_body = json.loads(response.get('body').read())
    generated_text = response_body['results'][0]['outputText']

    return(generated_text)

def generate_results_openai(prompt, model='gpt-4-0314', max_new_tokens=500, topp=1.0, temperature=1.0, presence_penalty=0.0, frequency_penalty=0.0):

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


