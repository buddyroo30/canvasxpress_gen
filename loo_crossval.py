import siteminder
import json
import sys
import utils
import math
import statistics
import time

num_few_shots_to_test = [0,5,10,15,20,25,30]
models_to_test = ["mistral.mistral-large-2407-v1:0","anthropic.claude-3-opus-20240229-v1:0",
                  "anthropic.claude-3-5-sonnet-20240620-v1:0","gpt-4o-global","gpt-4-32k",
                  "meta.llama3-1-405b-instruct-v1:0","meta.llama3-1-70b-instruct-v1:0","meta.llama3-1-8b-instruct-v1:0"]

#num_few_shots_to_test = [10]
#models_to_test = ["mistral.mistral-large-2407-v1:0"]

all_f = open("all_results.txt", "w")
sum_f = open("summary_results.txt", "w")
sum_result_header = ["Model","Num Few Shots", "Num Examples Tested", "Num Exact Matches", "Exact MatchPerc","Num Subset Matches",
                    "Subset Match Perc","Avg Similarity Score", "Med Similarity Score", "Max Similarity Score", "Min Similarity Score"]
sum_f.write("\t".join(sum_result_header) + "\n")

DO_SLEEP=False
QUERIES_PER_MINUTE = 15
SLEEP_TIME = math.ceil(60 / QUERIES_PER_MINUTE) + 1

def sleep_for_llm():
    if DO_SLEEP:
        time.sleep(SLEEP_TIME)

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
sleep_for_llm()
fetch_json_txt = fetch_resp['text']
allFewShotsList = json.loads(fetch_json_txt)

def do_one_test(model,num_few_shots):
    similarityScores = []
    exactMatchCt = 0
    subsetCt = 0
    minSimilarityScore = 100.0
    maxSimilarityScore = 0.0

    all_f.write(f"--- MODEL {model}, NUM_FEW_SHOTS {num_few_shots}---" + "\n")

    for curFewShotObj in allFewShotsList:
        question = curFewShotObj['English Text']
        headers = curFewShotObj['Headers/Column Names']
        datafile_contents = '[' + headers + ']'
        answer = curFewShotObj['Answer']
        answerObj = json.loads(answer)
        all_f.write("FEW SHOT QUESTION: " + question + "\n")
        all_f.write("FEW SHOT DATAFILE_CONTENTS: " + datafile_contents + "\n")
        all_f.write("FEW SHOT ANSWER: " + answer + "\n")
        all_f.write("FEW SHOT ANSWER PRETTY:" + "\n")
        all_f.write(json.dumps(answerObj,indent=2,sort_keys=True)  + "\n")

        postData = { 'datafile_contents': datafile_contents,
                    #'model': 'meta.llama3-1-405b-instruct-v1:0',
                    #'model': 'gpt-4o-global',
                    'model': model,
                    'topp': 1.0,
                    'temperature': 0.0,
                    'presence_penalty': 0,
                    'frequency_penalty': 0,
                    'max_new_tokens': 1250,
                    'prompt': question,
                    'num_few_shots': num_few_shots,
                    'filter_prompt_from_few_shots': True }
        if USE_SITEMINDER:
            ask_resp = siteminder.sm_fetch(ask_url,cdict=login_resp['cdict'],postData=postData)
        else:
            ask_resp = siteminder.fetch(ask_url,postData=postData)
        if not ask_resp['success'] or 'text' not in ask_resp:
            all_f.write("ERROR RESPONSE: " + ask_resp['msg'] + "\n")
            sleep_for_llm()
            continue
        ask_json_txt = ask_resp['text']
        askJsonObj = None
        try:
            askJsonObj = json.loads(ask_json_txt)
        except Exception as e:
            all_f.write("ERROR DECODING RESPONSE AS JSON: " + str(e) + ", RESPONSE TEXT: " + ask_json_txt + "\n")
            sleep_for_llm()
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
        if jsonSimilarityScore > maxSimilarityScore:
            maxSimilarityScore = jsonSimilarityScore
        all_f.write("LLM GENERATED RESPONSE: " + ask_json_txt + "\n")
        if askJsonObj['success'] and 'config' in askJsonObj:
            all_f.write("LLM ANSWER PRETTY:" + "\n")
            all_f.write(json.dumps(askJsonObj['config'],indent=2,sort_keys=True) + "\n")
        all_f.write("SIMILARITY SCORE: " + str(jsonSimilarityScore) + "\n")
        all_f.write("TRUE ANSWER IS SUBSET OF LLM GENERATED ANSWER: " + answerIsSubset + "\n")
        similarityScores.append(jsonSimilarityScore)
        if jsonSimilarityScore >= 100.0:
            exactMatchCt = exactMatchCt + 1
        sleep_for_llm()

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

    sum_result = [str(model),str(num_few_shots),str(len(similarityScores)),str(exactMatchCt),str(percentExactMatch),str(subsetCt),str(percentSubsetMatch),
                  str(avgSimilarityScore),str(medSimilarityScore),str(maxSimilarityScore),str(minSimilarityScore)]
    sum_f.write("\t".join(sum_result) + "\n")

for model in models_to_test:
    for num_few_shots in num_few_shots_to_test:
        do_one_test(model,num_few_shots)

all_f.close()
sum_f.close()

##Args to /ask:
#datafile_upload: (binary) --- or alternatively pass datafile_contents as row of rows, e.g. [['header1','header2',...],[1,2,....]]
#model: gpt-4-32k
#topp: 1
#temperature: 0
#presence_penalty: 0
#frequency_penalty: 0
#max_new_tokens: 1250
#prompt: boxplot of len on x axis grouped by dose

