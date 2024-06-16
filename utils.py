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

def generate_prompt(question, prompt_file="prompt.md", metadata_file="ngs_metrics_context.txt",few_shot_examples_file="few_shot_examples.txt"):
    with open(prompt_file, "r") as f:
        prompt = f.read()
    
    with open(metadata_file, "r") as f:
        table_metadata_string = f.read()

    with open(few_shot_examples_file, "r") as f:
        few_shot_examples_string = f.read()

    prompt = prompt.format(
        user_question=question, table_metadata_string=table_metadata_string,few_shot_examples=few_shot_examples_string
    )
    return prompt

def deconstruct_llmgen_result(llm_result):
    try:
        query_parts = llm_result.split(" ",2)
        query_type = query_parts[0]
        db_name = query_parts[1]
        actual_query = query_parts[2]
        return (True, query_type, db_name, actual_query)
    except Exception as e:
        return(False,"Error: " + str(e),False,False)

def ngs_metrics_query(sql_query, rowOfRows=False):
    #mysql --host=ngsp1.cbe7mtbvwi2d.us-east-1.rds.amazonaws.com --user=ngs_user --password=ngspass ngs_metrics
    try:
        mydb = mysql.connector.connect(
            host="ngsp1.cbe7mtbvwi2d.us-east-1.rds.amazonaws.com",
            user="ngsro",
            password="ngsro123",
            database="ngs_metrics"
        )

        mycursor = mydb.cursor()
        mycursor.execute(sql_query)
        #See here for converting to JSON output: https://stackoverflow.com/questions/43796423/python-converting-mysql-query-result-to-json
        row_headers=[x[0] for x in mycursor.description] #this will extract row headers
        if rowOfRows:
            row_headers.insert(0,'Row')
        myresult = mycursor.fetchall()
        json_data = []

        if rowOfRows:
            json_data.append(row_headers)

        rowCt = 1
        for x in myresult:
            if rowOfRows:
                x = ('R' + str(rowCt),) + x
                rowCt += 1
                json_data.append(x)
            else:
                json_data.append(dict(zip(row_headers,x)))
    except Exception as e:
        return({'success': False, 'msg': "Error executing SQL Query: " + str(e), 'rows': []})

    #print(json.dumps(json_data))
    return({'success': True,'rows': json_data})

def mysql_extract_limit(query):
  """Extracts the LIMIT clause value from a MySQL query.

  Args:
    query: The MySQL query.

  Returns:
    The LIMIT clause value (e.g. '23' for 'LIMIT 23'), or None if the LIMIT clause is not present.
  """

  match = re.search(r'LIMIT\s+(\d+)', query, re.IGNORECASE)
  if match:
    return match.group(1)
  else:
    return None

#Next 2 functions created by GPT-4 based on this question:
#Create a Python function to read a MySQL schema's tables and columns from the INFORMATION_SCHEMA table into a Dictionary of Dictionaries,
#keyed on table name with value another Dictionary keyed on column name with value column type. Use the mysql-connector-python package.
#Create another function that takes the result of the first function and prints out the schema in this format:
#table1: column1 (column1_type), column2 (column2_type), ... columnn (columnn_type)
#table2:column1 (column1_type), column2 (column2_type), ... columnn (columnn_type)
def read_schema_structure(host, user, password, database):
    # Connect to the MySQL server
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
    )

    # Query the INFORMATION_SCHEMA table to retrieve tables and columns for the provided schema
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_NAME, ORDINAL_POSITION
        """,
        (database,),
    )

    # Store the result in a dictionary of dictionaries
    schema = {}
    for table_name, column_name, column_type in cursor.fetchall():
        if table_name not in schema:
            schema[table_name] = {}
        schema[table_name][column_name] = column_type

    # Close the connection and cursor
    cursor.close()
    connection.close()

    return schema

def print_schema(schema):
    for table_name, columns in schema.items():
        print("---{}: ".format(table_name), end="")
        print( "[" +
            ", ".join(
                "{} ({})".format(column_name, column_type)
                for column_name, column_type in columns.items()
            )
            + "]"
        )

#Generated by GPT-4 based on this question:
#Write a Python function that for a given database name, queries the INFORMATION_SCHEMA table for that database and
#prints out all foreign key relationships. For each foreign key relationship found from table1.column1 to table2.column2,
#print out the foreign key relationship like this: ---table2.column2 is a foreign key of table1.column1.
#Use the mysql-connector-python package.
def print_foreign_key_relationships(host, user, password, database_name):
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database_name
    )
    cursor = connection.cursor()

    query = """
        SELECT kcu.TABLE_NAME, kcu.COLUMN_NAME, kcu.REFERENCED_TABLE_NAME, kcu.REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE as kcu
        WHERE kcu.REFERENCED_TABLE_SCHEMA = %s
          AND kcu.REFERENCED_TABLE_NAME IS NOT NULL;
    """

    cursor.execute(query, (database_name,))
    results = cursor.fetchall()

    for result in results:
        print("---{}.{} is a foreign key of {}.{}.".format(
            result[2], result[3], result[0], result[1]))

    cursor.close()
    connection.close()

#Generated by GPT-4 based on the request: Write a Python function that takes a list of values and returns True if they are all numeric values, for example "100", "2", "2.01", etc. and False otherwise.
def all_numeric(values):
    for value in values:
        if value is None:
            continue
        try:
            float(value)
        except ValueError:
            return False
    return True

#Got this (and slightly different version of read_schema_structure function above) by asking GPT-4:
#Create a Python function to read a MySQL schema's tables and columns from the INFORMATION_SCHEMA table into a Dictionary of
#Dictionaries, keyed on table name with value another Dictionary keyed on column name with value column type. Use the
#mysql-connector-python package.  Write another Python function that takes the result of the first function and considers all
#columns from different tables 2 at a time, call them table1.table1_column and table2.table2_column: if table1.table1_column and
#table2.table2_column have the same column type (and check that the column type is a non-numeric type) then load all values from
#each column into a list and determine if either list is a subset of the other. If table1.table1_column's values are a subset of
#table2.table2_column's values then print on a line "---table1.table1_column can join with table2.table2_column".
#If table2.table2_column's values are a subset of table1.table1_column's values then print on a line "---table2.table2_column can
#join with table1.table1_column". 
def find_joinable_columns(schema, database, user, password, host, minvals = 15):
    """Find joinable columns and print their conditions."""

    # Connect to the MySQL server
    cnx = mysql.connector.connect(user=user, password=password, host=host, database=database)
    cursor = cnx.cursor()

    # Compare all columns from different tables 2 at a time
    for table1, table1_columns in schema.items():
        for table2, table2_columns in schema.items():
            if table1 == table2:
                continue

            for col1, col1_type in table1_columns.items():
                for col2, col2_type in table2_columns.items():
                    if col1_type == col2_type and col1_type.lower() not in ['int', 'decimal', 'float', 'double', 'numeric', 'bigint', 'smallint', 'tinyint']:
                        # Load all values from the columns into lists
                        query1 = f"SELECT `{col1}` FROM `{table1}`"
                        query2 = f"SELECT `{col2}` FROM `{table2}`"
                        cursor.execute(query1)
                        col1_values = [val[0] for val in cursor.fetchall()]
                        if all_numeric(col1_values):
                            continue
                        col1_values_set = set(col1_values)
                        if len(col1_values_set) < minvals:
                            continue
                        cursor.execute(query2)
                        col2_values = [val[0] for val in cursor.fetchall()]
                        if all_numeric(col2_values):
                            continue
                        col2_values_set = set(col2_values)
                        if len(col2_values_set) < minvals:
                            continue

                        # Check if either list is a subset of the other
                        if col1_values_set.issubset(col2_values):
                            print(f"---{table1}.{col1} can join with {table2}.{col2}")
                        elif col2_values_set.issubset(col1_values):
                            print(f"---{table2}.{col2} can join with {table1}.{col1}")

    cursor.close()
    cnx.close()

#Result of asking GPT-4: Write a Python function to just print the base type of a given MySQL type. For example int(10) -> int, char(25) -> char, varchar(25) -> varchar
def get_base_type(mysql_type):
    base_type = ""
    for ch in mysql_type:
        if ch == '(':
            break
        base_type += ch
    return base_type

#Again, GPT-4 created this function based on this request:
#Write another function that takes the output of the first function and iterates through all tables and columns, and for
#non-numeric type columns prints out the top n most frequently occurring values in the column like this:
#Most frequent values in table1.column1: value1, value2, value3, value4, value5, ...
#Most frequent values in table2.column2: value1, value2, value3, value4, value5\n...
def print_topn_values(schema_information, user, password, host, database, n=5):
    connection = mysql.connector.connect(user=user, password=password, host=host, database=database)
    cursor = connection.cursor()

    for table, columns in schema_information.items():
        for column, column_type in columns.items():
            column_type_base = get_base_type(column_type)
            if column_type_base.lower() not in ['int', 'decimal', 'float', 'double', 'numeric', 'bigint', 'smallint', 'tinyint']:
                query = f"SELECT {column}, COUNT(*) as count FROM {table} WHERE {column} IS NOT NULL AND {column} != '' GROUP BY {column} ORDER BY COUNT(*) DESC LIMIT {n};"
                cursor.execute(query)
                top_n = cursor.fetchall()
                if len(top_n) > 0:
                    top_n_values = ', '.join([str(value[0]) for value in top_n])
                    print(f"---{table}.{column}: {top_n_values}")

    cursor.close()
    connection.close()

def printLLMContextForMySQLDatabase(user, password, host, database):

    schema_info = read_schema_structure(host, user, password, database)
    print(f"Below is detailed information about MySQL database '{database}' that you will use to convert an English language question into a corresponding SQL query to answer the question.")
    print("### Here is the schema in format 'table name: [column1_name (column1_type), column2_name (column2_type),...,columnN_name (columnN_type)]':")
    print_schema(schema_info)
    print("### Here are the foreign key relationships that can be joined on:")
    print_foreign_key_relationships(host, user, password, database)
    print("### Here are joinable non-numeric type columns based on a column's values being subsets of another column's values (however these are not explicit foreign keys):")
    find_joinable_columns(schema_info, database, user, password, host)
    print("### Here are the most frequent values in each non-numeric table.column:")
    print_topn_values(schema_info, user, password, host, database, n=8)
