import sqlite3
import json
import os
import requests
import re
import time


def clean_datasets():
    cxDatasets = None
    cleaned_cxDatasets = []
    with open("datasets.json", "r") as f:
        cxDatasetsJsonTxt = f.read()
        cxDatasets = json.loads(cxDatasetsJsonTxt)

    for curRec in cxDatasets:
        if curRec['config'].strip() == "" or curRec['config'].strip() == '{}':
            continue
        else:
            cleaned_cxDatasets.append(curRec)

    print(json.dumps(cleaned_cxDatasets))

clean_datasets()


