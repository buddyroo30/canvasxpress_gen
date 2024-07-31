import ldap
import time
import calendar
from flask import request, redirect
import requests
import re
import mysql.connector
from itertools import combinations
import json
import secrets
import string
import sys
import csv

LDAP_BASE_SEARCH='ou=people,o=bms.com'
LDAP_URL='ldap://smusdir.bms.com'
LDAP_ROOT_DN='o=bms.com'

redirect_url = "http://smusath.net.bms.com/rdproxy/redirect.cgi"
validate_url = "http://smusath.net.bms.com/rdproxy/validate.cgi"

def empty(str):
    """
    Return True if the str is None or composed of only whitespace, False otherwise
    """

    if str is None:
        return True
    if str.strip() == "":
        return True
    return False

def remove_backtick_text(text):
    index = text.find('```')
    if index != -1:
        text = text[:index]
    return text

#See here: https://pynative.com/python-generate-random-string/#h-generate-a-secure-random-string-and-password
def random_password(len):
    password = ''.join((secrets.choice(string.ascii_letters + string.digits + string.punctuation) for i in range(len)))
    return(password)

def ldapConnect():
    """
    Connect to an Ldap server.
    """

    ldap_url = LDAP_URL

    con = ldap.initialize(ldap_url)
    con.simple_bind_s()
    return con

def parse_file(filename):
    with open(filename, 'r') as f:
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        reader = csv.reader(f, dialect)
        return [row for row in reader]

def queryLdapForUid(uid,con):
    """
    Execute an Ldap query for an input BMS user id.
    Return associated cn, uid, bmsid, and email address
    """

    if con is None:
        con = ldapConnect()

    base_dn = LDAP_BASE_SEARCH
    filter_str = f"(|(uid={uid}*))"
    attrs = ['cn', 'uid', 'bmsid', 'mail', 'bmsentaccountstatus']

    try:
        results = con.search_ext_s(base_dn, ldap.SCOPE_SUBTREE, filter_str, attrs)
    except ldap.LDAPError:
        return []

    res = [{ 'cn': result[1]['cn'][0].decode('utf-8'),
             'uid': result[1]['uid'][0].decode('utf-8'),
             'bmsid': result[1]['bmsid'][0].decode('utf-8'),
             'mail': result[1]['mail'][0].decode('utf-8'),
             'bmsacountstatus': result[1]['bmsentaccountstatus'][0].decode('utf-8') } for result in results]

    return res

def getSMRedirectUrl(request):

    #See here for getting parts of url in Flask: https://stackoverflow.com/questions/15974730/how-do-i-get-the-different-parts-of-a-flask-requests-url
    #See here for quote: https://stackoverflow.com/questions/1695183/how-to-percent-encode-url-parameters-in-python
    location = redirect_url + '?url=' + requests.utils.quote(request.url)

    return(location)

#Returning None means 'pass', i.e. allow the user access to the
#requested resource. Otherwise returns a "access denied" message that
#can get displayed to the user. This version goes directly against
#the SiteMinder validation services and not indirectly through
#an intermediate service (so use this if you are directly on the
#BMS network).
def getSiteMinderUser(request, validatedCookies):

    if not 'SMSESSION' in request.cookies:
        return(None)

    #Remove expired cookies from the validatedCookies dict
    currentEpochSecs = calendar.timegm(time.gmtime())
    delCookies = {}
    for curSmSession, assocVals in validatedCookies.items():
        initTtlSecs = int(assocVals['TTL'])
        initEpochSecs = int(assocVals['epochsecs'])
        secsDiff = currentEpochSecs - initEpochSecs
        remainingTtlSecs = initTtlSecs - secsDiff
        if remainingTtlSecs <= 0:
            delCookies[curSmSession] = True

    for curSmSession, assocVal in delCookies.items():
        del validatedCookies[curSmSession]

    smSession = request.cookies['SMSESSION']

    if smSession in validatedCookies:
        validatedCookieVals = validatedCookies[smSession]
        return(validatedCookieVals)

    validateResp = requests.get(validate_url,cookies={ 'SMSESSION': smSession })
    respLines = validateResp.text.splitlines()

    if respLines[0] != 'Success':
        return(None)

    respValsHash = {}
    for curLine in respLines:
        matches = re.search('^([^\=]+)=(.+)$', curLine)
        if matches:
            respValsHash[matches.group(1)] = matches.group(2)

    UserDN = respValsHash['UserDN']
    if not empty(UserDN):
        UserDNVals = UserDN.split(",")
        for curVal in UserDNVals:
            matches = re.search('^([^\=]+)=(.+)$', curVal)
            if matches and matches.group(1) == 'bmsid':
                respValsHash['bmsid'] = matches.group(2)

    if 'bmsid' not in respValsHash:
        SMUSERDN = respValsHash['UserDN']
        if not empty(SMUSERDN):
            SMUSERDNVals = UserDN.split(",")
            for curVal in SMUSERDNVals:
                matches = re.search('^([^\=]+)=(.+)$', curVal)
                if matches and matches.group(1) == 'bmsid':
                    respValsHash['bmsid'] = matches.group(2)

    respValsHash['epochsecs'] = calendar.timegm(time.gmtime())
    validatedCookies[smSession] = respValsHash

    return(respValsHash)

#json1 and json2 are each Dict
def json_similarity(json1, json2):

    if type(json1) != type(json2):
        return 0

    if isinstance(json1, dict):
        keys1 = set(json1.keys())
        keys2 = set(json2.keys())
        common_keys = keys1 & keys2
        total_keys = keys1 | keys2

        if not total_keys:
            return 100

        similarity = (len(common_keys) / len(total_keys)) * 100

        for key in common_keys:
            similarity += json_similarity(json1[key], json2[key])

        return similarity / (len(total_keys) + 1)

    elif isinstance(json1, list):
        len1 = len(json1)
        len2 = len(json2)
        total_len = max(len1, len2)

        if not total_len:
            return 100

        overlap = 0
        for item in json1:
            if item in json2:
                overlap += 1

        return (overlap / total_len) * 100

    else:
        if isinstance(json1,str) and isinstance(json2,str):
            json1_copy = json1.replace("\n", " ").strip()
            json2_copy = json2.replace("\n", " ").strip()
            if json1_copy == json2_copy:
                return 100
            else:
                return 0
        elif json1 == json2:
            return 100
        else:
            return 0

#Here is a Python3 function that uses recursion to check if one JSON object (json1) is a subset of another (json2):
def is_subset(json1, json2):
    if isinstance(json1, dict) and isinstance(json2, dict):
        for key in json1:
            if key not in json2:
                return False
            if not is_subset(json1[key], json2[key]):
                return False
        return True
    elif isinstance(json1, list) and isinstance(json2, list):
        if len(json1) > len(json2):
            return False
        for item in json1:
            if item not in json2:
                return False
        return True
    else:
        if isinstance(json1,str) and isinstance(json2,str):
            json1_copy = json1.replace("\n", " ").strip()
            json2_copy = json2.replace("\n", " ").strip()
            return json1_copy == json2_copy
        else:
            return json1 == json2

def convert_boolean_dict_values(d):
    for k, v in d.items():
        if isinstance(v, dict):
            convert_boolean_dict_values(v)
        elif isinstance(v, list):
            for i in range(len(v)):
                if isinstance(v[i], dict):
                    convert_boolean_dict_values(v[i])
                elif v[i] == "true":
                    v[i] = True
                elif v[i] == "false":
                    v[i] = False
        else:
            if v == "true":
                d[k] = True
            elif v == "false":
                d[k] = False
    return d
