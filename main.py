import math
from datetime import datetime
import requests
import jwt
from flask import Flask, request
import time
import json
from bs4 import BeautifulSoup

access_token = 'none'
generated_at = 1

app = Flask(__name__)

# python -m flask run  - terminal command to start the program running.


def encode(user, expires, jti, aud):
    private_key = "<private key> "

    public_key = "<public key>"

    encoded = jwt.encode({"iss": "<IRS Client ID>", "sub": user,
                          "aud": aud,
                          "exp": expires,
                          "jti": jti
                          }, private_key, algorithm="RS256", headers={"kid": "<kid>"})
    return encoded


def time_gen():
    seconds = datetime.now().timestamp()
    seconds += 900  # adds 15 minutes to use for expiration time.
    seconds = math.trunc(seconds)
    return seconds


@app.post('/token-gen')
def token_gen():
    access = token_generation(aud="https://api.www4.irs.gov/auth/oauth/v2/token", user="IRS user ID")
    return access


def token_generation(aud, user):
    expires = time_gen()
    global generated_at
    generated_at = expires
    jti = expires + 1
    user_assertion = encode(user, expires, jti, aud)
    jti = jti + 1

    client_assertion = encode("<IRS Client ID>", expires, jti, aud)

    header = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(aud, headers=header, data={"grant_type": 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                                                        "assertion": user_assertion,
                                                        "client_assertion_type": "urn:ietf:params:oauth:client"
                                                                                 "-assertion-type:jwt-bearer",
                                                        "client_assertion": client_assertion
                                                        })
    token = ''
    match response.ok:  # checks code < 200 = True, > 200 = False
        case True:
            data = response.json()
            token = data["access_token"]
            global access_token
            access_token = token
        case False:
            token = {response.status_code: response.text}
    return token


@app.post('/actr-dev')
def actr_call_dev():
    member_request = request.get_json()
    print(member_request)
    current = datetime.now().timestamp()
    current = math.trunc(current)
    if current > generated_at:
        token = token_generation(aud="https://api.alt.www4.irs.gov/auth/oauth/v2/token", user=member_request["user"])
        print('new token' + token)
    else:
        global access_token
        token = access_token
        print(token)
    if isinstance(token, str):
        del member_request["user"]
        response = requests.post("https://api.alt.www4.irs.gov/esrv/api/tds/request/caf",
                                 headers={"authorization": "bearer " + token},
                                 json=member_request)
        test = {'test': response.text}
        transaction = caf_request_dev(token, member_request)
        transactions = {'transactions': transaction, "html": test}
    else:
        transactions = token  # if the returned value of the token is a dictionary, there was an error in the
        # call. The error is returned to the caller of this api.
    return transactions


@app.post('/actr-prod')
def actr_call():
    member_request = request.get_json()
    current = datetime.now().timestamp()
    current = math.trunc(current)
    if current > generated_at:
        token = token_generation(aud="https://api.www4.irs.gov/auth/oauth/v2/token", user=member_request["user"])
    else:
        global access_token
        token = access_token
        # print(token)
    if isinstance(token, str):
        del member_request["user"]
        transactions = caf_request_prod(token, member_request)
    else:
        transactions = token  # if the returned value of the token is a dictionary, there was an error in the
        # call. The error is returned to the caller of this api.
    return transactions


def caf_request_dev(token, body):
    response = requests.post("https://api.alt.www4.irs.gov/esrv/api/tds/request/caf",
                             headers={"authorization": "bearer " + token},
                             json=body)
    print(response.status_code)
    print(response.ok)  # prints true/false
    parsed = ''
    match response.ok:  # checks code < 200 = True, > 200 = False
        case True:
            parsed = actr_html_parsing_dev(response.text)
        case False:
            parsed = response.text
    return parsed


def caf_request_prod(token, body):
    response = requests.post("https://api.www4.irs.gov/esrv/api/tds/request/caf",
                             headers={"authorization": "bearer " + token},
                             json=body)
    # print(response.ok)
    parsed = ''
    match response.ok:
        case True:
            parsed = actr_html_parsing(response.text)
        case False:
            parsed = response.text
    # parsed = actr_html_parsing(response.text, 'output.json')
    return parsed


@app.route('/main')
def home():
    app.logger.info("from route handler")
    app.logger.warning('test')
    return 'JWT Creator'


def actr_html_parsing(html_file):
    soup = BeautifulSoup(html_file, features='html.parser')
    data = {}
    for tag in soup.find_all(summary=
                             "Transactions           table. Note: Row 2 is formatting only. n/a is used for "
                             "Supplemental"
                             " info or No           tax return filed. Check the Explanation of Transaction column for "
                             "more details."
                             ): # This tag is used to find the table in the returned HTML transacript with the account
                                # transactions. Parses them and stores a json version to be returned to the caller.
        data_line = 1
        for row in tag.find_all('tr'):
            data[data_line] = {}
            i = 0
            for value in row.find_all('td'):
                match i:
                    case 0:
                        data[data_line]['Code'] = value.text
                    case 1:
                        data[data_line]['Explanation'] = value.text
                    case 2:
                        data[data_line]['Cycle'] = value.text
                    case 3:
                        data[data_line]['Date'] = value.text
                    case 4:
                        data[data_line]['Amount'] = value.text
                i += 1
            data_line += 1
    return data


def actr_html_parsing_dev(html_file):
    soup = BeautifulSoup(html_file, features='html.parser')
    data = {}
    for tag in soup.find_all(summary=
                             'Transactions table. Note: Row 2 is formatting only. n/a is used for Supplemental info '
                             'or No tax return filed. Check the Explanation of Transaction column for more details.'
                             ):

        for row in tag.find_all('tr'):
            code = row.text[:3]
            data[code] = {}  # what if there are duplicate codes?
            i = 0
            for value in row.find_all('td'):
                match i:
                    case 0:
                        data[code]['Code'] = value.text
                    case 1:
                        data[code]['Explanation'] = value.text
                    case 2:
                        data[code]['Cycle'] = value.text
                    case 3:
                        data[code]['Date'] = value.text
                    case 4:
                        data[code]['Amount'] = value.text
                i += 1
    return data


if __name__ == "__main__":
    app.run()
