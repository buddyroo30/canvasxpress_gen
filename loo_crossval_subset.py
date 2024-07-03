import siteminder
import json
import sys
import utils

init_result_file = "loo_crossval_results.txt"

with open(init_result_file) as f:
    lines_list = f.readlines()

lines_list = [x.strip() for x in lines_list]

fewShotCt = 0
similarityScores = []
exactMatchCt = 0
subsetCt = 0
minSimilarityScore = 100.0

while len(lines_list) > 0:
    if lines_list[0].strip() == '***SUMMARY***':
        break
    fewShotQuest = lines_list.pop(0).strip().removeprefix("FEW SHOT QUESTION:").strip()
    fewShotDatafileContents = lines_list.pop(0).strip().removeprefix("FEW SHOT DATAFILE_CONTENTS:").strip()
    fewShotAnswer = lines_list.pop(0).strip().removeprefix("FEW SHOT ANSWER:").strip()
    fewShotAnswerObj = json.loads(fewShotAnswer)
    llmGeneratedResp = lines_list.pop(0).strip().removeprefix("LLM GENERATED RESPONSE:").strip()
    llmGeneratedRespObj = json.loads(llmGeneratedResp)
    if 'config' not in llmGeneratedRespObj and 'configJSONTxt' in llmGeneratedRespObj:
        llmGeneratedRespObj['config'] = json.loads(llmGeneratedRespObj['configJSONTxt'])
    if 'config' in llmGeneratedRespObj:
        llmGeneratedAnswerObj = llmGeneratedRespObj['config']
    else:
        print("NO CONFIG: " + str(llmGeneratedResp))
        
    similarityScore = lines_list.pop(0).strip().removeprefix("SIMILARITY SCORE:").strip()

    fewShotAnswerObj = utils.convert_boolean_dict_values(fewShotAnswerObj)
    llmGeneratedAnswerObj = utils.convert_boolean_dict_values(llmGeneratedAnswerObj)
    recomputedSimilarityScore = utils.json_similarity(fewShotAnswerObj,llmGeneratedAnswerObj)
    if recomputedSimilarityScore < minSimilarityScore:
        minSimilarityScore = recomputedSimilarityScore

    answerIsSubset = "False"
    if utils.is_subset(fewShotAnswerObj,llmGeneratedAnswerObj):
        answerIsSubset = "True"
        subsetCt = subsetCt + 1

    print("FEW SHOT QUESTION: " + fewShotQuest)
    print("FEW SHOT DATAFILE_CONTENTS: " + fewShotDatafileContents)
    print("FEW SHOT ANSWER: " + fewShotAnswer)
    print("FEW SHOT ANSWER PRETTY:")
    print(json.dumps(fewShotAnswerObj,indent=2,sort_keys=True))
    print("LLM GENERATED RESPONSE: " + llmGeneratedResp)
    print("LLM ANSWER PRETTY:")
    print(json.dumps(llmGeneratedAnswerObj,indent=2,sort_keys=True))
    print("SIMILARITY SCORE: " + similarityScore)
    print("RECOMPUTED SIMILARITY SCORE: " + str(recomputedSimilarityScore))
    print("TRUE ANSWER IS SUBSET OF LLM GENERATED ANSWER: " + answerIsSubset)

    similarityScores.append(recomputedSimilarityScore)
    if recomputedSimilarityScore >= 100.0:
        exactMatchCt = exactMatchCt + 1
    fewShotCt = fewShotCt + 1

avgSimilarityScore = sum(similarityScores) / len(similarityScores)
percentExactMatch = exactMatchCt / float(len(similarityScores))
percentSubsetMatch = subsetCt / fewShotCt

print("***SUMMARY***")
print("NUMBER OF FEW SHOTS: " + str(fewShotCt))
print("NUMBER OF EXACT MATCHES: " + str(exactMatchCt))
print("PERCENT EXACT MATCHES: " + str(percentExactMatch))
print("NUMBER OF SUBSET MATCHES: " + str(subsetCt))
print("PERCENT SUBSET MATCHES: " + str(percentSubsetMatch))
print("AVERAGE SIMILARITY SCORE: " + str(avgSimilarityScore))
print("MINIMUM SIMILARITY SCORE: " + str(minSimilarityScore))


