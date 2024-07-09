import siteminder
import json
import sys
import utils
import math
import time

QUERIES_PER_MINUTE = 15
SLEEP_TIME = math.ceil(60 / QUERIES_PER_MINUTE) + 1

USE_SITEMINDER=False

login_resp = None

if USE_SITEMINDER:
    un,pw = siteminder.user_input_creds()
    login_resp = siteminder.login(un,pw)
    if not login_resp['success']:
        print("Error: " + login_resp['msg'])
        sys.exit()

#Run this inside the container running the get_few_shots and ask services
base_url = "http://localhost:5000/"

get_all_few_shots_url = base_url + "get_few_shots?num=all&format=json"
ask_url = base_url + "ask"

if USE_SITEMINDER:
    fetch_resp = siteminder.sm_fetch(get_all_few_shots_url,cdict=login_resp['cdict'])
else:
    fetch_resp = siteminder.fetch(get_all_few_shots_url)
time.sleep(SLEEP_TIME)
fetch_json_txt = fetch_resp['text']
allFewShotsList = json.loads(fetch_json_txt)

totalFewShotCt = len(allFewShotsList)
similarityScores = []
exactMatchCt = 0
subsetCt = 0
minSimilarityScore = 100.0

for curFewShotObj in allFewShotsList:
    question = curFewShotObj['English Text']
    headers = curFewShotObj['Headers/Column Names']
    datafile_contents = '[' + headers + ']'
    answer = curFewShotObj['Answer']
    answerObj = json.loads(answer)
    print("FEW SHOT QUESTION: " + question)
    print("FEW SHOT DATAFILE_CONTENTS: " + datafile_contents)
    print("FEW SHOT ANSWER: " + answer)
    print("FEW SHOT ANSWER PRETTY:")
    print(json.dumps(answerObj,indent=2,sort_keys=True))

    postData = { 'datafile_contents': datafile_contents,
                 'model': 'gemini-1.5-flash',
                 'topp': 1,
                 'temperature': 0,
                 'presence_penalty': 0,
                 'frequency_penalty': 0,
                 'max_new_tokens': 1250,
                 'prompt': question,
                 'filter_prompt_from_few_shots': True }
    if USE_SITEMINDER:
        ask_resp = siteminder.sm_fetch(ask_url,cdict=login_resp['cdict'],postData=postData)
    else:
        ask_resp = siteminder.fetch(ask_url,postData=postData)
    if not ask_resp['success'] or 'text' not in ask_resp:
        print("ERROR RESPONSE: " + ask_resp['msg'])
        time.sleep(SLEEP_TIME)
        continue
    ask_json_txt = ask_resp['text']
    askJsonObj = None
    try:
        askJsonObj = json.loads(ask_json_txt)
    except Exception as e:
        print("ERROR DECODING RESPONSE AS JSON: " + str(e) + ", RESPONSE TEXT: " + ask_json_txt)
        time.sleep(SLEEP_TIME)
        continue        
    jsonSimilarityScore = 0.0
    answerIsSubset = "Unknown"
    if askJsonObj['success'] and 'config' in askJsonObj:
        jsonSimilarityScore = utils.json_similarity(answerObj,askJsonObj['config'])
        if utils.is_subset(answerObj,askJsonObj['config']):
            answerIsSubset = "True"
            subsetCt = subsetCt + 1
        else:
            answerIsSubset = "False"
    if jsonSimilarityScore < minSimilarityScore:
        minSimilarityScore = jsonSimilarityScore
    print("LLM GENERATED RESPONSE: " + ask_json_txt)
    if askJsonObj['success'] and 'config' in askJsonObj:
        print("LLM ANSWER PRETTY:")
        print(json.dumps(askJsonObj['config'],indent=2,sort_keys=True))
    print("SIMILARITY SCORE: " + str(jsonSimilarityScore))
    print("TRUE ANSWER IS SUBSET OF LLM GENERATED ANSWER: " + answerIsSubset)
    similarityScores.append(jsonSimilarityScore)
    if jsonSimilarityScore >= 100.0:
        exactMatchCt = exactMatchCt + 1
    time.sleep(SLEEP_TIME)


avgSimilarityScore = sum(similarityScores) / len(similarityScores)
percentExactMatch = exactMatchCt / len(similarityScores)
percentSubsetMatch = subsetCt / len(similarityScores)

print("***SUMMARY***")
print("NUMBER OF FEW SHOTS TESTED SUCCESSFULLY: " + str(len(similarityScores)))
print("NUMBER OF EXACT MATCHES: " + str(exactMatchCt))
print("PERCENT EXACT MATCHES: " + str(percentExactMatch))
print("NUMBER OF SUBSET MATCHES: " + str(subsetCt))
print("PERCENT SUBSET MATCHES: " + str(percentSubsetMatch))
print("AVERAGE SIMILARITY SCORE: " + str(avgSimilarityScore))
print("MINIMUM SIMILARITY SCORE: " + str(minSimilarityScore))

##Args to /ask:
#datafile_upload: (binary) --- or alternatively pass datafile_contents as row of rows, e.g. [['header1','header2',...],[1,2,....]]
#model: gpt-4-32k
#topp: 1
#temperature: 0
#presence_penalty: 0
#frequency_penalty: 0
#max_new_tokens: 1250
#prompt: boxplot of len on x axis grouped by dose

