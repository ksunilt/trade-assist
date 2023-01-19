import os
from urllib.parse import urlparse, parse_qs
from fyers_api import fyersModel, accessToken
from utility.telegram_utility import send_tele_msg
from yaml.loader import SafeLoader

import requests
import sys
import yaml

config_main = '../trade-assist/config/config_main.yml'
with open(config_main, 'r') as config_main:
    cfg = yaml.load(config_main, Loader=SafeLoader)

# below items to be added to config_main and should be picking it from there.
username = cfg['auth']['username'] # fyers_id
password = cfg['auth']['password']  # fyers_password
pin = cfg['auth']['pin']  # your integer pin
client_id = cfg['auth']['client_id']  # "L9NY****W-100" (Client_id here refers to APP_ID of the created app)
secret_key = cfg['auth']['secret_key']  # app_secret key which you got after creating the app
redirect_uri = cfg['auth']['redirect_uri']  # redircet_uri you entered while creating APP.

app_id = client_id[:-4]  # '##########'
auth_logs = cfg['auth']['auth_logs']

# to read the token file.
def read_t_file():
    with open("../trade-assist/authentication/tokenf.txt", "r") as f:
        token = f.read()
    return token

# to write the token to the token file and will be valid till 12 PM
def write_file(token):
    with open("../trade-assist/authentication/tokenf.txt", "w") as f:
        f.write(token)


def setup():
    session = accessToken.SessionModel(
        client_id=client_id,
        secret_key=secret_key,
        redirect_uri=redirect_uri,
        response_type="code",
        grant_type="authorization_code"
    )

    headers = {
        "accept": "application/json",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
        "accept-language": "en-US,en;q=0.9",
    }

    s = requests.Session()
    s.headers.update(headers)

    data1 = f'{{"fy_id":"{username}","password":"{password}","app_id":"2","imei":"","recaptcha_token":""}}'
    r1 = s.post("https://api.fyers.in/vagator/v1/login", data=data1)
    # print("this is data1 ==>", data1)
    # print("this is r1 ==>", r1)
    assert r1.status_code == 200, f"Error in r1:\n {r1.json()}"

    request_key = r1.json()["request_key"]

    data2 = f'{{"request_key":"{request_key}","identity_type":"pin","identifier":"{pin}","recaptcha_token":""}}'
    r2 = s.post("https://api.fyers.in/vagator/v1/verify_pin", data=data2)
    # print("this is data2 ==>", data2)
    # print("this is r2 ==>", r2)
    assert r2.status_code == 200, f"Error in r2:\n {r2.json()}"

    headers = {"authorization": f"Bearer {r2.json()['data']['access_token']}", "content-type": "application/json; charset=UTF-8"}
    data3 = f'{{"fyers_id":"{username}","app_id":"{app_id}","redirect_uri":"{redirect_uri}","appType":"100","code_challenge":"","state":"abcdefg","scope":"","nonce":"","response_type":"code","create_cookie":true}}'
    r3 = s.post("https://api.fyers.in/api/v2/token", headers=headers, data=data3)

    assert r3.status_code == 308, f"Error in r3:\n {r3.json()}"

    parsed = urlparse(r3.json()["Url"])
    auth_code = parse_qs(parsed.query)["auth_code"][0]
    session.set_token(auth_code)
    response = session.generate_token()
    token = response["access_token"]
    write_file(token)

    message = "Got the access token!!!"
    send_tele_msg(message=message)

    fyers = fyersModel.FyersModel(client_id=client_id, token=token, log_path=auth_logs)
    fyers_profile = fyers.get_profile()
    if fyers_profile.get('code') == 200:
        data = fyers_profile['data']
        msg = ("Login validation is PASSED")
        send_tele_msg(message=msg)
        for key, val in data.items():
            print(key, ":",val)
    else:
        message = "Login validation FAILED."
        send_tele_msg(message=message)


def fyers_login():
    try:
        token = read_t_file()
    except FileNotFoundError:
        setup()
        sys.exit()
    fyers = fyersModel.FyersModel(client_id=client_id, token=token, log_path=auth_logs)
    response = fyers.get_profile()
    # print("response is ====>", response)
    if "error" in response["s"] or "error" in response["message"] or "expired" in response["message"]:
        setup()
        return response
    else:
        message = "You already have a access token!"
        send_tele_msg(message=message)
        passwd_expiry = response['data']['pwd_to_expire']
        if passwd_expiry < 5:
            print(f"Please change the password. Will be expired in {passwd_expiry} days")
            return response

if __name__ == "__main__":
    fyers_login()
