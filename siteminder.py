# Based on Mark Russo's smlogin.py

import sys
import re
import requests
import getpass

# Login page
smlogin = 'https://smusath.net.bms.com/siteminderagent/forms/login.fcc'

# SiteMinder target page
smtarget = 'HTTPS://smwinath.bms.com/redirect/redirector.asp?ORIGTARGET=http%3a%2f%2fsiteminder%2ebms%2ecom%2f'

# Match login failure page
failRegex = re.compile(r'.*<html.*AUTHENTICATION\s*FAILED.*</html.*', re.S)

# Match fetch failure page
fetch_failRegex = re.compile(r'.*<title>BMS: SiteMinder ADSSO</title>.*', re.S)

# Disable SSL warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def user_input_creds():
    un = input('Enter username: ')
    pw = getpass.getpass('Enter password: ')

    return(un,pw)

def login(un, pw):
    # Assemble POST data
    data = {
     'USER': un,
     'PASSWORD': pw, 
     'SMAUTHREASON': '0', 
     'TARGET': smtarget
    }
    
    # Do request
    r = requests.post(smlogin, data=data, verify=False)
    
    # Test for auth failure or stale token
    if failRegex.match(r.text):
        msg = 'Authentication failed or token stale'
        return {'success':False, 'msg':msg}
    
    # Recreate cookies string from response
    cstring = ';'.join(["{}={}".format(k,v) for k,v in r.cookies.items() if k in ['SMSESSION', 'SMIDENTITY']])
    # Create cookie dict for use in followup requests
    cdict = {}
    for k,v in r.cookies.items():
        if k in ['SMSESSION', 'SMIDENTITY']:
            cdict[k] = v
    
    return {'success':True, 'cstring':cstring, 'cdict': cdict}

def sm_fetch(url,cdict=None,cstring=None,postData=None):

    if cstring is None and cdict is None:
        return({'success': False, 'msg': 'Error: you must pass in cookies as either dict or cookies string'})

    if cstring is not None:
        # Create a dictionary from the cookie string
        cdict = {
                    cookie.split("=")[0].strip(): cookie.split("=")[1].strip()
                    for cookie in cstring.split(";")
                }

    response = None
    if postData is None:
        response = requests.get(url,cookies=cdict, verify=False)
    else:
        response = requests.post(url, data=postData, cookies=cdict, verify=False)

    # Test for auth failure or stale token
    if fetch_failRegex.match(response.text):
        msg = 'Authentication failed or token stale'
        return({'success':False, 'msg':msg})

    return({ 'success': True, 'text': response.text, 'response': response })

#If no SiteMinder, you can just use this to GET/POST
def fetch(url,postData=None):

    response = None
    try:
        if postData is None:
            response = requests.get(url)
        else:
            response = requests.post(url, data=postData)
    except Exception as e:
        return({ 'success': False, 'msg': str(e)})

    return({ 'success': True, 'text': response.text, 'response': response })
