import siteminder
import json
import sys
import utils

un,pw = siteminder.user_input_creds()
login_resp = siteminder.login(un,pw)
if not login_resp['success']:
    print("Error: " + login_resp['msg'])
    sys.exit()

base_url = "http://ip-172-25-132-16.rdcloud.bms.com:5008/"

get_all_few_shots_url = base_url + "get_few_shots?num=all&format=json"
ask_url = base_url + "ask"

fetch_resp = siteminder.sm_fetch(get_all_few_shots_url,cdict=login_resp['cdict'])
fetch_json_txt = fetch_resp['text']
allFewShotsList = json.loads(fetch_json_txt)

totalFewShotCt = len(allFewShotsList)
similarityScores = []
exactMatchCt = 0

for curFewShotObj in allFewShotsList:
    question = curFewShotObj['English Text']
    headers = curFewShotObj['Headers/Column Names']
    datafile_contents = '[' + headers + ']'
    answer = curFewShotObj['Answer']
    answerObj = json.loads(answer)
    print("FEW SHOT QUESTION: " + question)
    print("FEW SHOT DATAFILE_CONTENTS: " + datafile_contents)
    print("FEW SHOT ANSWER: " + answer)

    postData = { 'datafile_contents': datafile_contents,
                 'model': 'gpt-4-32k',
                 'topp': 1,
                 'temperature': 0,
                 'presence_penalty': 0,
                 'frequency_penalty': 0,
                 'max_new_tokens': 1250,
                 'prompt': question,
                 'filter_prompt_from_few_shots': True }
    ask_resp = siteminder.sm_fetch(ask_url,cdict=login_resp['cdict'],postData=postData)
    ask_json_txt = ask_resp['text']
    askJsonObj = json.loads(ask_json_txt)
    jsonSimilarityScore = 0.0
    if askJsonObj['success'] and 'config' in askJsonObj:
        jsonSimilarityScore = utils.json_similarity(answerObj,askJsonObj['config'])
    print("LLM GENERATED RESPONSE: " + ask_json_txt)
    print("SIMILARITY SCORE: " + str(jsonSimilarityScore))
    similarityScores.append(jsonSimilarityScore)
    if jsonSimilarityScore >= 100.0:
        exactMatchCt = exactMatchCt + 1

avgSimilarityScore = sum(similarityScores) / len(similarityScores)
percentExactMatch = exactMatchCt / float(len(similarityScores))

print("***SUMMARY***")
print("NUMBER OF FEW SHOTS: " + str(totalFewShotCt))
print("NUMBER OF EXACT MATCHES: " + str(exactMatchCt))
print("PERCENT EXACT MATCHES: " + str(percentExactMatch))
print("AVERAGE SIMILARITY SCORE: " + str(avgSimilarityScore))

##Args to /ask:
#datafile_upload: (binary) --- or alternatively pass datafile_contents as row of rows, e.g. [['header1','header2',...],[1,2,....]]
#model: gpt-4-32k
#topp: 1
#temperature: 0
#presence_penalty: 0
#frequency_penalty: 0
#max_new_tokens: 1250
#prompt: boxplot of len on x axis grouped by dose

