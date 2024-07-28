import time
import calendar
from flask import request, redirect
import requests
import re
import json
import string
import sys

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
        matches = re.search('^([^=]+)=(.+)$', curLine)
        if matches:
            respValsHash[matches.group(1)] = matches.group(2)

    UserDN = respValsHash['UserDN']
    if not empty(UserDN):
        UserDNVals = UserDN.split(",")
        for curVal in UserDNVals:
            matches = re.search('^([^=]+)=(.+)$', curVal)
            if matches and matches.group(1) == 'bmsid':
                respValsHash['bmsid'] = matches.group(2)

    if 'bmsid' not in respValsHash:
        SMUSERDN = respValsHash['UserDN']
        if not empty(SMUSERDN):
            SMUSERDNVals = UserDN.split(",")
            for curVal in SMUSERDNVals:
                matches = re.search('^([^=]+)=(.+)$', curVal)
                if matches and matches.group(1) == 'bmsid':
                    respValsHash['bmsid'] = matches.group(2)

    respValsHash['epochsecs'] = calendar.timegm(time.gmtime())
    validatedCookies[smSession] = respValsHash

    return(respValsHash)

