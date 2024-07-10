import json
import sys

with open("canvasxpress-lmm-gpt4.json", "r") as f:
    cxExamplesJsonTxt = f.read()
    cxExamples = json.loads(cxExamplesJsonTxt)

totalCt = 0
fieldCounts = {}

for curRec in cxExamples['Questions']:
    totalCt = totalCt + 1
    curConfig = curRec['Answer']
    for curConfigField in curConfig:
        if curConfigField not in fieldCounts:
            fieldCounts[curConfigField] = 0
        fieldCounts[curConfigField] = fieldCounts[curConfigField] + 1

sortedFields = sorted(fieldCounts.items(), key=lambda x: x[1], reverse=True)
rowCt = 1
print("\tFieldName\tOccurrenceCount\tOccurrencePercentage")
for curFieldInfo in sortedFields:
    fieldName = curFieldInfo[0]
    fieldCount = curFieldInfo[1]
    docPct = round(fieldCount / totalCt, 2)
    print(f"{rowCt}\t{fieldName}\t{fieldCount}\t{docPct}")
    rowCt = rowCt + 1
