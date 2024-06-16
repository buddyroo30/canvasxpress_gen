from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename
import csv
import os
import re
import datetime
import time
import json
import utils
import llm_logging
import urllib.parse
import boto3
from tabulate import tabulate
from AESCipher import AESCipher
from FlagEmbedding import BGEM3FlagModel
from pymilvus import MilvusClient
from pymilvus.model.hybrid import BGEM3EmbeddingFunction
import numpy as np
import tiktoken
from dotenv import load_dotenv

load_dotenv()

code_release = "https://biogit.pri.bms.com/smitha26/LLM-testing"
LOGCHATS=False

USE_MODEL="openai" #"titan" or "openai"

import openai
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

app = Flask(__name__)
app.config['SECRET_KEY'] = utils.random_password(16)
app.config['UPLOAD_FOLDER'] = "/tmp"
aes = AESCipher(app.config['SECRET_KEY'])

def getMilvusClient():
    if 'MILVUS_CLIENT' not in app.config:
        fewShotDbLoc = "/root/.cache/canvasxpress_llm.db"
        app.config['MILVUS_CLIENT'] = MilvusClient(fewShotDbLoc)
    return(app.config['MILVUS_CLIENT'])

SMVAL=True
validatedCookies = {}

#See here: https://pythonise.com/series/learning-flask/python-before-after-request
#Do SiteMinder authentication before all requests to get bmsid of current user. Returning
#None means allow the request to go forward and get processed, otherwise display/
#enact what is returned without processing the actual request.
@app.before_request
def before_request_func():

    req_ep = ''
    if not utils.empty(request.endpoint):
        req_ep = request.endpoint
    print('In before_request_func, endpoint: ' + req_ep)

    if SMVAL:
        curSmValidationVals = utils.getSiteMinderUser(request, validatedCookies)
        if curSmValidationVals is None or utils.empty(curSmValidationVals['User']):
            return redirect(utils.getSMRedirectUrl(request))
        else:
            return None
    else:
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dev')
def dev():
    return render_template('llm.html')

@app.route('/userinfo',methods=['GET','POST'])
def userinfo():

    curUserInfo = {}
    if SMVAL:
        curSmValidationVals = utils.getSiteMinderUser(request, validatedCookies)
        curUserInfo['uid'] = curSmValidationVals['User']
        curUserInfo['bmsid'] = curSmValidationVals['bmsid']
    else:
        curUserInfo['uid'] = 'NA'
        curUserInfo['bmsid'] = 'NA'

    retValsJson = json.dumps(curUserInfo)

    return(retValsJson)


@app.route('/getenv',methods=['GET','POST'])
def getenv():

    allEnvTxt = ""
    for name, value in os.environ.items():
        allEnvTxt = allEnvTxt + "{0}: {1}".format(name, value) + "\n"
    return("<plaintext>" + allEnvTxt + "</plaintext>")

def getFewShots(prompt,numFewShots=25):

    queries = [prompt]

    query_embeddings = bge_m3_ef.encode_queries(queries)
    #collection_name="few_shot_examples",
    #collection_name="canvasxpress_docs",

    milvusClient = getMilvusClient()
    res = milvusClient.search(
        collection_name="few_shot_examples",
        data=[query_embeddings["dense"][0]],
        limit=numFewShots,
        output_fields=["config", "configEnglish", "headers", "id"],
    )
    #English Text:...; Headers/Column Names: ..., Answer: ...
    #See here for where got below to get the hits: https://github.com/milvus-io/pymilvus/blob/master/examples/milvus_client/simple.py#L68
    fewShotTxt = ""
    for hits in res:
        for hit in hits:
            curConfig = hit['entity']['config'].replace("\n"," ")
            curEnglishConfig = hit['entity']['configEnglish'].replace("\n", " ")
            curHeadersColumnNames = hit['entity']['headers'].replace("\n", " ")
            fewShotTxt = fewShotTxt + f"English Text: {curEnglishConfig}; Headers/Column Names: {curHeadersColumnNames}, Answer: {curConfig}" + "\n"

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

def parse_file(filename):
    with open(filename, 'r') as f:
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        reader = csv.reader(f, dialect)
        return [row for row in reader]

@app.route('/ask',methods=['GET','POST'])
def ask():

    datafilename = None
    datafile_contents = []
    headerRow = []
    if 'datafile_upload' in request.files and request.files['datafile_upload'].filename != '':
        datafile = request.files['datafile_upload']
        datafilename = secure_filename(datafile.filename)
        upload_filepath = os.path.join(app.config['UPLOAD_FOLDER'], datafilename)
        datafile.save(upload_filepath)
        datafile_contents = parse_file(upload_filepath)
    else:
        errResp = { 'text': "Error: you must upload a data file to visualize", 'success': False, 'config_generated_flag': False, }
        return(json.dumps(errResp))

    if len(datafile_contents) > 0:
        headerRow = datafile_contents[0]

    version = request.values.get('version') # PROD, DEVTEST, etc.
    prompt = request.values.get('prompt')
    orig_prompt = prompt
    model = request.values.get('model')
    max_new_tokens = request.values.get('max_new_tokens')
    topp = request.values.get('topp')
    temperature = request.values.get('temperature')
    presence_penalty = request.values.get('presence_penalty')
    frequency_penalty = request.values.get('frequency_penalty')
    curDatetime = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

    if utils.empty(prompt):
        errResp = { 'text': "Error: you must provide a description of the visualization you want", 'success': False, 'config_generated_flag': False, }
        return(json.dumps(errResp))

    start = time.time()

    if utils.empty(version):
        version = 'UNKNOWN'

    if utils.empty(model):
        model = 'gpt-4-32k'

    if utils.empty(max_new_tokens):
        max_new_tokens = 1024

    if utils.empty(topp):
        topp = 1.0

    if utils.empty(temperature):
        temperature = 0.0

    if utils.empty(presence_penalty):
        presence_penalty = 0.0

    if utils.empty(frequency_penalty):
        frequency_penalty = 0.0

    resp = {}

    if prompt == 'Thumbs down':
        resp = { 'success': True,
                 'text': 'Thank-you for giving negative feedback, we will use it to improve future performance.',
                 'config_generated_flag': False,
                 'prompt': orig_prompt,
                 'datetime': curDatetime }
    elif prompt == 'Thumbs up':
        resp = { 'success': True,
                 'text': 'Thank-you for giving positive feedback, we will use it to improve future performance.',
                 'config_generated_flag': False,
                 'prompt': orig_prompt,
                 'datetime': curDatetime }
    elif prompt == 'Help':
        resp = { 'success': True,
                 'text': 'You can ask me for help with accessing the NGS360 database. You can search structured data by asking things like Can you give me a list of matching normal-tumor samples for the study CA209-214 or Which individuals in CA209-214 have both RNAseq and WES data?',
                 'config_generated_flag': False,
                 'prompt': orig_prompt,
                 'datetime': curDatetime }
    else:

        fewShotTxt = getFewShots(prompt,numFewShots=25)
        prompt = generate_prompt(prompt,str(headerRow), schema_info_file="/root/.cache/schema.txt",prompt_file="prompt.md",few_shot_examples_string=fewShotTxt)

        generated_text = "NOTHINGYET"
        if USE_MODEL == "titan":
            generated_text = generate_results_titan(prompt,model='amazon.titan-tg1-large', max_token_count=int(max_new_tokens), topp=float(topp), temperature=float(temperature))
        elif USE_MODEL == "openai":
            generated_text = generate_results_openai(prompt, model=model, max_new_tokens=int(max_new_tokens),topp=float(topp),temperature=float(temperature),presence_penalty=float(presence_penalty),frequency_penalty=float(frequency_penalty))
        if utils.empty(generated_text) or generated_text.strip() == "''":
            errResp = { 'text': "Error: No configuration was generated by the LLM, please try again.", 'success': False, 'config_generated_flag': False, }
            return(json.dumps(errResp))
        configObj = {}
        try:
            configObj = json.loads(generated_text)
        except Exception as e:
            errResp = { 'text': "Error converting LLM generated config into JSON object: " + str(e) + ", raw result from LLM: " + generated_text, 'success': False, 'config_generated_flag': False, }
            return(json.dumps(errResp))
        end = time.time()
        llm_time_taken = end - start
        print(f'Took {llm_time_taken} secs for LLM to generate results')

        resp = { 'success': True,
                 'config': configObj,
                 'configJSONTxt': generated_text,
                 'datafilename': datafilename,
                 'data': datafile_contents,
                 'config_generated_flag': True,
                 'total_time_taken': llm_time_taken,
                 'prompt': orig_prompt,
                 'header': headerRow,
                 'datetime': curDatetime }

    retValsJson = json.dumps(resp)

    if LOGCHATS:
        llm_logging.log_chatinfo(code_release,version,"user","id",retValsJson)

    return(retValsJson)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)


#ChatGPT/GPT-4 output looks like:
#{
#  "choices": [
#    {
#      "finish_reason": "stop",
#      "index": 0,
#      "message": {
#        "content": "As an AI language model, I don't have personal beliefs or opinions. However, according to Buddhist tradition, Bodhi-Dharma left for the east to spread the teachings of Buddhism and to find a suitable place to meditate and attain enlightenment. He is believed to have traveled from India to China, where he established the Shaolin Temple and taught Zen Buddhism.",
#        "role": "assistant"
#      }
#    }
#  ],
#  "created": 1682431166,
#  "id": "chatcmpl-79DUUocMn0fjDWQfd3MZdbg1RNucn",
#  "model": "gpt-35-turbo",
#  "object": "chat.completion",
#  "usage": {
#    "completion_tokens": 72,
#    "prompt_tokens": 19,
#    "total_tokens": 91
#  }
#}
