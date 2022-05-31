import datetime
import pandas as pd
import numpy as np
import os
import requests
import yaml
from datetime import date
from datetime import datetime
from bs4 import BeautifulSoup
from yaml.loader import SafeLoader


# Read the main app configuration to be used inside the functions.
config_main = '/sk_bot/config/config_main.yml'
with open(config_main, 'r') as config_main:
    cfg = yaml.load(config_main, Loader=SafeLoader)

# Send sgx status to telegram to TradeAssist
def send_telegram_msg(status, day, sgx, change, points):
    message = f"SGX Status as on {day} \n\nSGX is {status} today !! \nSGX Nifty: {sgx}. \nSGX points: {points}. \nPercentage Change: {change}"
    url = 'https://api.telegram.org/bot<TOKEN_HERE>/sendMessage?chat_id=<CHAT_ID_HERE>&text="{}"'.format(message)
    requests.get(url)

def fetch_sgx():
    # Configuration details.
    sgx_url = cfg['sgx']['sgx_url']
    csv_file = cfg['sgx']['sgx_tracker_file_name_csv']
    xlsx_file = cfg['sgx']['sgx_tracker_file_name_xlsx']
    sgx_tracker_path = cfg['sgx']['sgx_tracker_file_path']
    sgx_tracker = sgx_tracker_path + csv_file
    sgx_tracker_xlsx = sgx_tracker_path + xlsx_file

    # pdb.set_trace()
    # Fetch sgx value from sgx nifty site.
    get_sgx_page = requests.get(sgx_url)
    soup = BeautifulSoup(get_sgx_page.text, 'html.parser')
    sgx_nifty_table = soup.find('table', {'class': 'main-table bold'})

    # Convert sgx to dataframe.
    sgx_df = pd.read_html(str(sgx_nifty_table))[0]

    # Add timestamp to the existing dataframe.
    current_time = date.today()
    sgx_df.insert(0, "datetime", [current_time], True)

    # Add sgx_report value to csv file.
    sgx_df.to_csv(sgx_tracker, mode='a', index=False, header=False)

    # Convert percentage column to float.
    read_sgx_df = pd.read_csv(sgx_tracker)
    # read_sgx_df['SIDE'] = np.where(read_sgx_df['change_percentage'] > 1, "Negative", "Positive")
    read_sgx_df['change_percentage'] = read_sgx_df['change_percentage'].str.rstrip('%').astype('float')

    # Create xlsx file to easy readable.
    read_sgx_df.to_excel(sgx_tracker_xlsx, index = None, header = True)

    # Find the latest row as today's SGX value.
    sgx_today = read_sgx_df.iloc[[-1]]

    # Assign each values from latest row.
    today = datetime.today()
    current_date = today.strftime("%Y-%m-%d")
    sgx_timestamp = sgx_today.iloc[-1]['timestamp']
    sgx_last_trade = sgx_today.iloc[-1]['last_trade']
    sgx_change = sgx_today.iloc[-1]['change']
    sgx_change_percentage = sgx_today.iloc[-1]['change_percentage']

    # Condition to find sgx status based on the above values.
    if sgx_timestamp == current_date:
        output_file = cfg['sgx']['sgx_json_file']
        if sgx_change_percentage > 0:
            print("SGX is Positive")
            sgx_today.to_json(output_file, orient='records', compression='infer', index='true')
            send_telegram_msg(status='Positive',
                              day=current_date,
                              sgx=sgx_last_trade,
                              change=sgx_change_percentage,
                              points=sgx_change)
        else:
            print("SGX is Negative")
            sgx_today.to_json(output_file, orient='records', compression='infer', index='true')
            send_telegram_msg(status='Negative',
                              day=current_date,
                              sgx=sgx_last_trade,
                              change=sgx_change_percentage,
                              points=sgx_change)

    # Confirmation of sgx_report value updated.
    # print("sgx tracker appended successfully to.", sgx_tracker, "at", current_time)
    # sgx = sgx_df.to_json(orient='records')
    return

    # def send_msg_to_telegram():
    #     get_pre_market_data()



fetch_sgx()
