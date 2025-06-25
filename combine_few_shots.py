import sqlite3
import json
import os
import sys
import requests
import re
import time
import tiktoken
from dotenv import load_dotenv

load_dotenv()
    
def combineFewShots(fewShotsJsonFile1,fewShotsJsonFile2):

    with open(fewShotsJsonFile1, "r") as f:
        fewShotsJsonTxt1 = f.read()
        fewShotsJson1 = json.loads(fewShotsJsonTxt1)

    with open(fewShotsJsonFile2, "r") as f:
        fewShotsJsonTxt2 = f.read()
        fewShotsJson2 = json.loads(fewShotsJsonTxt2)

    fewShotsToAdd = []
    for row2 in fewShotsJson2['Questions']:
        configObj2 = row2['Answer']
        uniqueFlag = True
        for row1 in fewShotsJson1['Questions']:
            configObj1 = row1['Answer']
            if configObj1 == configObj2:
                uniqueFlag = False
                break
        if uniqueFlag:
            fewShotsToAdd.append(row2)

    fewShotsJson1['Questions'].extend(fewShotsToAdd)

    for curRow in fewShotsJson1['Questions']:
        if 'QuestionGPT4' in curRow:
            gpt4QuestTxt = curRow['QuestionGPT4']
            curRow['QuestionGPT4o'] = gpt4QuestTxt
            del(curRow['QuestionGPT4'])
        if not 'Header' in curRow:
            curRow['Header'] = fewShotsJson1['data'][0]

    print(json.dumps(fewShotsJson1,indent=2))

f1 = "all_few_shots.json"
f2 = "all_few_shots_dev.json"

combineFewShots(f1,f2)
