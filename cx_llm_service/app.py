from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename
import os
import re
import datetime
import time
import json
import urllib.parse
from dotenv import load_dotenv
import requests
import utils

load_dotenv()

SERVICE_URL = os.environ.get("SERVICE_URL")

app = Flask(__name__)

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

@app.route('/ask_proxy',methods=['GET','POST'])
def ask_proxy():

#        var src = t.llmServiceURL + "?service=ask&target=" + t.target + "&client=" + x + "&config=" + c + "&prompt=" + i.value + "&header=" + h;

    service = request.values.get('service')
    target = request.values.get('target')
    client = request.values.get('client')
    config = request.values.get('config')
    prompt = request.values.get('prompt')
    header = request.values.get('header')

    p = config.split(',')

    postParams = {
        "config_only" : "True",
        "model" : p[0],
        "topp" : p[1],
        "temperature" : p[2],
        "presence_penalty" : p[3],
        "frequency_penalty" : p[4],
        "max_new_tokens" : p[5],
        "prompt" : prompt,
        "datafile_contents" : header
    }

    cdict = {}
    if SMVAL:
        for k,v in request.cookies.items():
            if k in ['SMSESSION', 'SMIDENTITY']:
                cdict[k] = v

    resp = requests.post(SERVICE_URL + service,cookies=cdict,data=postParams)
    #note: add target and client values to resp.content json before returning, CanvasXpress needs those values

    respJsonTxt = resp.content.decode("utf-8")
    respObj = json.loads(respJsonTxt)
    respObj['target'] = target
    respObj['client'] = client
    respJsonTxt = json.dumps(respObj)

    return 'CanvasXpress.callbackLLM(' + respJsonTxt + ')'

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)