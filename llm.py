import os
from FlagEmbedding import BGEM3FlagModel
from pymilvus import MilvusClient
from pymilvus.model.hybrid import BGEM3EmbeddingFunction
import boto3
from openai import AzureOpenAI
import json
from dotenv import load_dotenv
import google.generativeai as genai
import siteminder

load_dotenv()

google_api_key = os.environ.get("GOOGLE_API_KEY")

devFlag = os.environ.get("DEV")
if devFlag == 'True':
    devFlag = True
else:
    devFlag = False

vectorDbFile = "/root/.cache/canvasxpress_llm.db"
if devFlag:
    vectorDbFile = "/root/.cache/canvasxpress_llm_dev.db"

bge_m3_ef = BGEM3EmbeddingFunction(
    model_name='BAAI/bge-m3', # Specify the model name
    device='cpu', # Specify the device to use, e.g., 'cpu' or 'cuda:0'
    use_fp16=False # Specify whether to use fp16. Set to `False` if `device` is `cpu`.
)

def getMilvusClient(app):
    if 'MILVUS_CLIENT' not in app.config:
        app.config['MILVUS_CLIENT'] = MilvusClient(vectorDbFile)
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

#on CPU: "http://ip-172-25-132-16.rdcloud.bms.com:11434/api/generate"
def generate_results_ollama(prompt,model='gemma2:27b-text-q4_0',ollamaBaseUrl = "http://ip-172-25-132-16.rdcloud.bms.com:11434/api/generate"):

    postArgs = { "model": model, "prompt": prompt, "stream": False }

    resObj = siteminder.fetch(ollamaBaseUrl,postData=json.dumps(postArgs))

    resObj = json.loads(resObj['text'])
    if resObj['done']:
        return(resObj['response'])

def generate_results_llama31(prompt,model='meta.llama3-1-405b-instruct-v1:0',max_token_count=2048,topp=1.0,temperature=0.0):

    bedrockRuntime = boto3.client('bedrock-runtime',region_name="us-west-2")

    body = json.dumps({
        "prompt": prompt,
        "temperature": temperature,
        "top_p": topp,
        "max_gen_len": max_token_count
    })

    response = bedrockRuntime.invoke_model(body=body, modelId=model, accept='application/json', contentType='application/json')

    response_body = json.loads(response.get('body').read())
    generated_text = response_body['generation']

    return(generated_text)

def generate_results_mistral(prompt,model="mistral.mistral-large-2407-v1:0",max_token_count=2048,topp=1.0,temperature=0.0):

    bedrockRuntime = boto3.client('bedrock-runtime',region_name="us-west-2")

    conversation = [
        {
            "role": "user",
            "content": [{"text": prompt}],
        }
    ]
    # Send the message to the model, using a basic inference configuration.
    response = bedrockRuntime.converse(
        modelId=model,
        messages=conversation,
        inferenceConfig={"maxTokens":max_token_count,"temperature":temperature,"topP":topp},
        additionalModelRequestFields={}
    )

    # Extract and return the response text.
    generated_text = response["output"]["message"]["content"][0]["text"]
    return(generated_text)

def generate_results_titan(prompt, model='amazon.titan-tg1-large', max_token_count=2048, topp=1, temperature=0):

    bedrockRuntime = boto3.client('bedrock-runtime',region_name="us-east-1")

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

def generate_results_anthropic(prompt, model='anthropic.claude-3-5-sonnet-20240620-v1:0', max_token_count=1024, topp=1.0, temperature=0.0):

    if model == 'anthropic.claude-3-opus-20240229-v1:0':
        bedrockRuntime = boto3.client('bedrock-runtime',region_name="us-west-2")
    else:
        bedrockRuntime = boto3.client('bedrock-runtime',region_name="us-east-1")
    accept = 'application/json'
    contentType = 'application/json'

    body=json.dumps(
                    {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": max_token_count,
                        "top_p": topp,
                        "temperature": temperature,
                        "messages": [
                            {
                                "role": "user",
                                "content": [{"type": "text", "text": prompt}],
                            }
                        ],
                    }
                )
    response = bedrockRuntime.invoke_model(body=body, modelId=model, accept=accept, contentType=contentType)
    response_body = json.loads(response.get('body').read())
    output_list = response_body.get("content", [])
    generated_text = ""
    for output in output_list:
        generated_text = generated_text + output["text"]

    return(generated_text)

#Use this to access OpenAI models through Azure
def generate_results_azure_openai(prompt, model='gpt-4o-global', max_new_tokens=512, topp=1.0, temperature=0.0, presence_penalty=0.0, frequency_penalty=0.0):

    client = AzureOpenAI()

    completion = client.chat.completions.create(
        model=model,
        max_tokens=max_new_tokens,
        temperature=temperature,
        top_p=topp,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
        messages=[
         {
            "role": "user",
            "content": prompt
            }
        ]
    )
    generated_text = completion.choices[0].message.content

    return(generated_text)

#Use this to directly access OpenAI's models
def generate_results_openai(prompt, model='gpt-4o-global', max_new_tokens=512, topp=1.0, temperature=0.0, presence_penalty=0.0, frequency_penalty=0.0):

    response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_new_tokens,  # max_new_tokens is equivalent to max_tokens in this context
            top_p=topp,
            temperature=temperature,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty
        )
    generated_text = response.choices[0].message.content

    return(generated_text)

def generate_results_google_gemini(prompt,model='gemini-1.5-flash',temperature=0.0):

    model = genai.GenerativeModel(model)
    gen_config = genai.GenerationConfig(temperature=temperature,response_mime_type="application/json")
    model_response = model.generate_content(prompt,generation_config=gen_config)
    answer_txt = model_response.candidates[0].content.parts[0].text

    return(answer_txt)

def get_model_type(model):
    #USE_MODEL="titan" or "azure_openai" or "google_gemini" or "ollama" or "llama31" or "anthropic"
    modelToType = { "amazon.titan-tg1-large": "titan",
                    "mistral.mistral-large-2407-v1:0": "mistral",
                    "meta.llama3-1-405b-instruct-v1:0": "llama31",
                    "meta.llama3-1-70b-instruct-v1:0": "llama31",
                    "meta.llama3-1-8b-instruct-v1:0": "llama31",
                    "anthropic.claude-3-sonnet-20240229-v1:0": "anthropic",
                    "anthropic.claude-3-5-sonnet-20240620-v1:0": "anthropic",
                    "anthropic.claude-3-opus-20240229-v1:0": "anthropic",
                    "gpt-4o-global": "azure_openai",
                    "gpt-4o-regional": "azure_openai",
                    "gpt-4o-mini": "azure_openai",
                    "gpt-4": "azure_openai",
                    "gpt-4-32k": "azure_openai",
                    "gpt-35-turbo-16k": "azure_openai",
                    "gemini-1.5-flash": "google_gemini",
                    "gemini-1.5-pro": "google_gemini" }

    if model in modelToType:
        return(modelToType[model])
    else:
        return("ollama")

