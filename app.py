from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename
import os
import re
import datetime
import time
import json
import utils
import llm
#import llm_logging
import urllib.parse
import boto3
from tabulate import tabulate
from AESCipher import AESCipher
import numpy as np

code_release = "https://biogit.pri.bms.com/smitha26/LLM-testing"
LOGCHATS=False

google_api_key = os.environ.get("GOOGLE_API_KEY")

app = Flask(__name__)
app.config['SECRET_KEY'] = utils.random_password(16)
app.config['UPLOAD_FOLDER'] = "/tmp"
aes = AESCipher(app.config['SECRET_KEY'])

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

@app.route('/get_few_shots',methods=['GET','POST'])
def get_few_shots():

    prompt = request.values.get('prompt')
    if prompt is not None:
        prompt = prompt.strip()
    num = request.values.get('num')
    format = request.values.get('format')
    filter_prompt = request.values.get('filter_prompt')

    if format != 'text' and format != 'json':
        format = 'text'

    milvusClient = llm.getMilvusClient(app)
    if num == 'all':
        resTxt = llm.getAllFewShots(milvusClient, format=format)
    else:
        if not utils.empty(filter_prompt) and filter_prompt == 'True':
            filter_prompt = True
        else:
            filter_prompt = False
        resTxt = llm.getFewShots(milvusClient, prompt,numFewShots=int(num),filterPrompt=filter_prompt,format=format)

    return(resTxt)

@app.route('/ask',methods=['GET','POST'])
def ask():

    datafilename = None
    datafile_contents = []
    headerRow = []
    in_datafile_contents = request.values.get('datafile_contents')
    in_header = request.values.get('header')
    if not utils.empty(in_datafile_contents):
        datafile_contents = json.loads(in_datafile_contents)
    elif not utils.empty(in_header):
        datafile_contents = json.loads(in_header)
    elif 'datafile_upload' in request.files and request.files['datafile_upload'].filename != '':
        datafile = request.files['datafile_upload']
        datafilename = secure_filename(datafile.filename)
        upload_filepath = os.path.join(app.config['UPLOAD_FOLDER'], datafilename)
        datafile.save(upload_filepath)
        datafile_contents = utils.parse_file(upload_filepath)
    else:
        errResp = { 'text': "Error: you must upload a data file to visualize or pass in a header", 'success': False, 'config_generated_flag': False, }
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
    filter_prompt_from_few_shots = request.values.get('filter_prompt_from_few_shots')
    config_only = request.values.get('config_only')
    target = request.values.get('target')
    client = request.values.get('client')
    callback = request.values.get('callback')
    num_few_shots = request.values.get('num_few_shots')
    curDatetime = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

    if utils.empty(num_few_shots):
        num_few_shots = 25
    else:
        num_few_shots = int(num_few_shots)

    if not utils.empty(filter_prompt_from_few_shots) and filter_prompt_from_few_shots == 'True':
        filter_prompt_from_few_shots = True
    else:
        filter_prompt_from_few_shots = False

    if not utils.empty(config_only) and config_only == 'True':
        config_only = True
    else:
        config_only = False

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

    USE_MODEL = llm.get_model_type(model)
    print("USE_MODEL = " + USE_MODEL + ", model = " + model)

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
                 'text': 'You can generate visualizations by describing them in plain English, e.g. boxplot with legend at top right, and uploading a file of data to graph.',
                 'config_generated_flag': False,
                 'prompt': orig_prompt,
                 'datetime': curDatetime }
    else:

        milvusClient = llm.getMilvusClient(app)
        fewShotTxt = llm.getFewShots(milvusClient, prompt,numFewShots=num_few_shots,filterPrompt=filter_prompt_from_few_shots)
        prompt = llm.generate_prompt(prompt,str(headerRow), schema_info_file="schema.txt",prompt_file="prompt.md",few_shot_examples_string=fewShotTxt)

        generated_text = "NOTHINGYET"
        if USE_MODEL == "titan":
            generated_text = llm.generate_results_titan(prompt,model=model, max_token_count=int(max_new_tokens), topp=float(topp), temperature=float(temperature))
        elif USE_MODEL == "mistral":
            generated_text = llm.generate_results_mistral(prompt,model=model,max_token_count=int(max_new_tokens),topp=float(topp),temperature=float(temperature))
        elif USE_MODEL == "llama31":
            generated_text = llm.generate_results_llama31(prompt,model=model, max_token_count=int(max_new_tokens), topp=float(topp), temperature=float(temperature))
        elif USE_MODEL == "anthropic":
            generated_text = llm.generate_results_anthropic(prompt, model=model, max_token_count=int(max_new_tokens), topp=float(topp), temperature=float(temperature))
        elif USE_MODEL == "openai":
            generated_text = llm.generate_results_openai(prompt, model=model, max_new_tokens=int(max_new_tokens),topp=float(topp),temperature=float(temperature),presence_penalty=float(presence_penalty),frequency_penalty=float(frequency_penalty))
        elif USE_MODEL == 'google_gemini':
            generated_text = llm.generate_results_google_gemini(prompt,model=model,temperature=float(temperature))
        elif USE_MODEL == 'ollama':
            generated_text = llm.generate_results_ollama(prompt,model=model)
        if utils.empty(generated_text) or generated_text.strip() == "''":
            errResp = { 'text': "Error: No configuration was generated by the LLM, please try again.", 'success': False, 'config_generated_flag': False, }
            return(json.dumps(errResp))
        print("RAW generated_text:\n" + generated_text)
        configObj = {}
        generated_text = utils.clean_llm_response_text(generated_text)
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
                 'config_generated_flag': True,
                 'total_time_taken': llm_time_taken,
                 'prompt': orig_prompt,
                 'datetime': curDatetime }

        if not config_only:
            resp['datafilename'] = datafilename
            resp['data'] = datafile_contents
            resp['header'] = headerRow

    if not utils.empty(target):
        resp['target'] = target
    if not utils.empty(client):
        resp['client'] = client
    retValsJson = json.dumps(resp)

    if LOGCHATS:
        llm_logging.log_chatinfo(code_release,version,"user","id",retValsJson)

    if not utils.empty(callback):
        #jsonp response
        callbackStr = callback + "(" + retValsJson + ")"
        return(callbackStr)
    else:
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
