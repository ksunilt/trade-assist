from fyers_api import fyersModel
from fyers_api import accessToken
import webbrowser
import json
import pdb
import ast

def read_token_file():
    with open('/sk_bot/telegram_service/tokenf.txt', 'r') as f:
        token = f.read()
    return token

def write_token_file(access_token):
    with open('/sk_bot/telegram_service/tokenf.txt', 'w') as f:
        f.write(access_token).close()

def generate_auth_token():
    client_id = '<CLIENT_ID_HERE>'
    secret_key = '<SECRET_KEY_HERE>'
    redirect_uri = '<REDIRECT_URI_HERE>'
    appSession = accessToken.SessionModel(client_id=client_id, secret_key=secret_key, redirect_uri=redirect_uri, response_type='code', grant_type='authorization_code')
    response = appSession.generate_authcode()
    print(response)
    webbrowser.open(response, new=1)


def generate_access_token():
    auth_code = '<AUTH_CODE_HERE>'
    client_id = '<CLIENT_ID_HERE>'
    secret_key = '<SECRET_KEY_HERE>'
    redirect_uri = '<CREDIRECT_URI_HERE>'
    appSession = accessToken.SessionModel(client_id=client_id, secret_key=secret_key, redirect_uri=redirect_uri, response_type='code', grant_type='authorization_code')
    appSession.set_token(auth_code)
    response = appSession.generate_token()
    try:
        access_token = response['access_token']
        write_token_file(access_token)
        print("Token file is updated with new access token...")
    except Exception as error:
        print(response['message'])


def fyers_connect():
    client_id = '<CLIENT_ID_HERE>'
    token = read_token_file()
    log_path = '/sk_bot/logs/fyers_auth_logs/'
    fyers = fyersModel.FyersModel(client_id=client_id, token=token, log_path=log_path)
    return fyers


def validate_login():
    fyers = fyers_connect()
    profile = fyers.get_profile()
    if profile.get('code') == 200:
        print("Login validation is PASSED.\n")
        data = profile['data']
        for key, val in data.items():
            print(key, ":",val)
    else:
        print("Login validation FAILED.")


def read_input_file(filename, path = '/sk_bot/config/'):
    filePath = path + filename
    with open(filePath, 'r') as f:
        fav_stock = f.read()
        fav_stock_response = ast.literal_eval(fav_stock)
        return fav_stock_response

def get_quotes():
    data = read_input_file('fav_stocks.txt')
    fyers = fyers_connect()
    quote = fyers.quotes(data)
    print(quote)
    ltp = quote['d'][0]['v']['lp']
    symbol = quote['d'][0]['n']
    print(ltp)
    print(symbol)
    for k, v in quote.items():
        while isinstance(v, dict):
            myprint(v)
        else:
            print("{0} : {1}".format(k, v))

# pdb.set_trace()
# generate_auth_token()
# generate_access_token()
# validate_login()
# print(read_input_file('fav_stocks.txt'))
# get_quotes() #python dict

# fyers_connect()

# fav_stock = '/Users/sunilkumar/ksunilt/trading_bot/sk_bot/config/fav_stocks.txt'


