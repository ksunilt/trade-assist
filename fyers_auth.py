from fyers_api import fyersModel
from fyers_api import accessToken
import webbrowser
import json
import pdb
import ast


def read_token_file():
    """
    Function to read the access token. 
    :return: reads the access token and share it with the parent function. 
    """
    with open('/sk_bot/telegram_service/tokenf.txt', 'r') as f:
        token = f.read()
    return token

def write_token_file(access_token):
    """
    :param access_token: Access token from fyers. 
    :return: gets the access token from fyers and write it in txt file. 
    """
    with open('/sk_bot/telegram_service/tokenf.txt', 'w') as f:
        f.write(access_token).close()

def generate_auth_token():
    """
    The function is to generate authorisation token from your fyers app.
    You will be redirected to the fyers using browser where you have to put you login and paswd. 
    :return: redirect you to the app url (redirect_uri that you have configured while creating the app in fyers broker.) to get the auth token.
    :roadmap: 1. need to read from the config file.
            2. need to fully automate by not using the internet browser.
    """
    client_id = '<CLIENT_ID_HERE>'
    secret_key = '<SECRET_KEY_HERE>'
    redirect_uri = '<REDIRECT_URI_HERE>'
    appSession = accessToken.SessionModel(client_id=client_id, secret_key=secret_key, redirect_uri=redirect_uri, response_type='code', grant_type='authorization_code')
    response = appSession.generate_authcode()
    print(response)
    webbrowser.open(response, new=1)


def generate_access_token():
    """
    The function uses the Authorisation token from fyers and get the access token and calls write_token_file function to write the token in txt file.
    :return: get access token by calling write_token_file function.
    :roadmap: 1. need to read from the config file. 
            2. need more automation here to get the non url version. 
    """
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
    """
    Function to read the token from .txt file and connect to fyers app.
    This function can be used to called by other parent functions to perform some action in fyers.
    :return: connects to fyers api.
    :roadmap: 1. need to read from config file.
            2. need to have a validation for the app connection and send confirmation/failure message to the user via telegram. 
    """
    client_id = '<CLIENT_ID_HERE>'
    token = read_token_file()
    log_path = '/sk_bot/logs/fyers_auth_logs/'
    fyers = fyersModel.FyersModel(client_id=client_id, token=token, log_path=log_path)
    return fyers


def validate_login():
    """
    Connect to fyers api to validate the connection. 
    :return: user profile.
    :roadmap: 1. need to use config file. 
            2. need to put a validation on the password last change value. 
    """
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
    """
    Function is called by parent function to read the file from the path.  
    :param filename: any txt file name that you wanted to read.   
    :param path: the path where the file exist. 
    :return: list datatype.  
    """
    filePath = path + filename
    with open(filePath, 'r') as f:
        fav_stock = f.read()
        fav_stock_response = ast.literal_eval(fav_stock)
        return fav_stock_response

def get_quotes():
    """
    Function to get the quotes for the stock listed in the file from fyers.
    :return: quote price.
    """
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

            
# print(generate_auth_token.__doc__)    # using doc string for the function. 
# generate_auth_token()
# generate_access_token()
# validate_login()
# print(read_input_file('fav_stocks.txt'))
# get_quotes() #python dict

# fyers_connect()

# fav_stock = '/Users/sunilkumar/ksunilt/trading_bot/sk_bot/config/fav_stocks.txt'


