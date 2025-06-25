import json
import sys
import re


bads_fixed_file = "loo_crossval_resultsBAD_fixed.txt"

def parse_records(file_path):
    records = []
    record = {}
    multi_line_field = None
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('FEW SHOT QUESTION:'):
                if record:
                    records.append(record)
                record = {}
                multi_line_field = None
 #           if ':' in line:
            if re.match(r'^[A-Z ]+:',line):
                if multi_line_field:
                    record[multi_line_field] = ' '.join(record[multi_line_field].replace('\n',' ').replace('\r',' ').split())
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                if key in ['FEW SHOT ANSWER PRETTY', 'FIXED FEW SHOT ANSWER PRETTY', 'LLM ANSWER PRETTY']:
                    multi_line_field = key
                    record[key] = value if value else ''
                else:
                    record[key] = value
            elif multi_line_field:
                record[multi_line_field] += line
    if record:
        records.append(record)
    return records

fixedRecs = parse_records(bads_fixed_file)
hashedFixedRecs = {}
for curRec in fixedRecs:
    fewShotQuestOrig = curRec['FEW SHOT QUESTION']
    if fewShotQuestOrig not in hashedFixedRecs:
        hashedFixedRecs[fewShotQuestOrig] = curRec
    else:
        print("Duplicates detected, please fix: " + fewShotQuestOrig)
        sys.exit()

with open("canvasxpress-lmm-gpt4.json", "r") as f:
    cxExamplesJsonTxt = f.read()
    cxExamples = json.loads(cxExamplesJsonTxt)
    for i in range(len(cxExamples['Questions'])):
        curRec = cxExamples['Questions'][i]
        isaacEnglishTxt = curRec['Question']
        gpt4EnglishTxt = curRec['QuestionGPT4']
        configObj = curRec["Answer"]
        if isaacEnglishTxt in hashedFixedRecs:
            fixRec = hashedFixedRecs[isaacEnglishTxt]
            fixedFewShotQuestion = fixRec['FIXED FEW SHOT QUESTION']
            fixedAnswer = fixRec['FIXED FEW SHOT ANSWER PRETTY']
            curRec['Question'] = fixedFewShotQuestion
            curRec['Answer'] = json.loads(fixedAnswer)
        if gpt4EnglishTxt in hashedFixedRecs:
            fixRec = hashedFixedRecs[gpt4EnglishTxt]
            fixedFewShotQuestion = fixRec['FIXED FEW SHOT QUESTION']
            fixedAnswer = fixRec['FIXED FEW SHOT ANSWER PRETTY']
            curRec['Question'] = fixedFewShotQuestion
            curRec['Answer'] = json.loads(fixedAnswer)

print(json.dumps(cxExamples,indent=2))
        





