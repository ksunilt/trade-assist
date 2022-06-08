'''
The file will have all the functions to get the data from NSE.
author: ksunilt
'''

import requests
import pandas as pd
import datetime
import os.path
import yaml
from yaml.loader import SafeLoader
import json
import time

import utility.trade_utility
# from utility.trade_utility import send_tele_json, send_tele_msg

# to setup the work table!.
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)

# to read the configuration file.
config_main = '/sk_bot/config/config_main.yml'
with open(config_main, 'r') as config_main:
    cfg = yaml.load(config_main, Loader=SafeLoader)

nse_url = cfg['pom']['nse_url']
pom_dir = cfg['pom']['pom_reports_dir']
pom_file = cfg['pom']['pom_file']
curr_date = datetime.date.today().strftime("%d%m%Y")
pom_csv_file_name = pom_dir + pom_file + curr_date + '.csv'  # filename is 'POM_NSE_DDMMYYY'
pom_xls_file_name = pom_dir + pom_file + curr_date + '.xlsx'
pre_market_key = cfg['pom']['pre_market_key']

class NSEIndia:

    # Create a session with NSE India.
    def __init__(self):
        self.headers = <Mozilla_USER_AGENT_HERE>
        self.session = requests.Session()
        self.session.get(url=nse_url, headers=self.headers)

    # This function is used to get Pre-Open Market data from NSE India, into a excel report.
    def get_pre_open_market_data(self, key):
        """
        function to connect to NSE India after pre-open session and save data in csv and xls format.
        :param key: the pre-market data that you want to download.
        :return: data will be saved in csv and xlsx file.
        """
        pre_market_key = {"NIFTY 50":"NIFTY","BANK NIFTY":"BANKNIFTY","FNO":"FO"}
        data = self.session.get(f"https://www.nseindia.com/api/market-data-pre-open?key={pre_market_key[key]}", headers=self.headers).json()["data"]

        new_data = []
        for i in data:
            new_data.append(i["metadata"])
        df = pd.DataFrame(new_data)

        # to create pre-open market data file.
        df.to_csv(pom_csv_file_name)
        df.to_excel(pom_xls_file_name)
        utility.trade_utility.send_tele_msg(msg="NSE Pre-Open Market data files created for today in csv and xlsx format.")

    def holidays(self):
        """
        function to find the trading holiday.
        :return: dataframe.
        """
        holiday = ["clearing","trading"]
        key = "trading"
        data = self.session.get(f'https://www.nseindia.com/api/holiday-master?type={holiday[holiday.index(key)]}', headers=self.headers).json()
        df = pd.DataFrame(list(data.values())[0])
        return df


def find_stock_to_trade():
    """
    function to find the top gapup and gapdown stocks, within defined price range to trade. And sends notification to telegram.
    :return: Gapup and Gapdown stock in json file.
    """
    print("Analysis will start in 10 seconds. ")
    time.sleep(10)
    # To make df fit to screen.
    # pd.set_option('display.max_columns', None)
    # pd.set_option('display.max_rows', None)
    # pd.set_option('display.width', None)

    # load configuration.
    upper_limit = cfg['pom']['stock_price_range']['upper_limit']
    lower_limit = cfg['pom']['stock_price_range']['lower_limit']
    top_stock = cfg['pom']['number_of_stock_to_trade']
    output_dir = cfg['pom']['pom_reports_dir']
    gapup_file = cfg['pom']['json_output_file']['gapup_file']
    gapdown_file = cfg['pom']['json_output_file']['gapdown_file']

    input_file_dir = cfg['pom']['pom_reports_dir']
    input_file = cfg['pom']['input_file']['file_name']
    curr_date = datetime.date.today().strftime("%d%m%Y")
    pom_csv_file_name = input_file_dir + input_file + curr_date + '.csv'

    # Read the input file created by 'get_pre_open_market_data'.
    pom_df = pd.read_csv(pom_csv_file_name)

    # Select stocks between price range.
    pom_df = pom_df[(pom_df['iep'] >= upper_limit) & (pom_df['iep'] <= lower_limit)]

    # Sort the values and select the top stock and save it in json file.
    pom_df.sort_values(by=['pChange'], inplace=True, ascending=False)
    gapup_df = pom_df[['symbol','change','pChange','previousClose','iep']].head(top_stock)
    gapdown_df = pom_df[['symbol','change','pChange','previousClose','iep']].tail(top_stock)

    # to create gapup_file in json.
    gapup_df.to_json(gapup_file, orient = 'records', compression = 'infer', index = 'true')
    print("Gap-up stock json file is created at", gapup_file)

    # to create gapdown_file in json.
    gapdown_df.to_json(gapdown_file, orient = 'records', compression = 'infer', index = 'true')
    print("Gap-down stock json file is created at", gapdown_file)

    # Send Gapup/Gapdown notification to telegram user.
    utility.trade_utility.send_tele_json(gapup_file)
    utility.trade_utility.send_tele_json(gapdown_file)


# nse = NSEIndia() # to create class.
# nse.get_pre_open_market_data(key="NIFTY 50") # to call Pre Open Market data function.
# find_stock_to_trade() # to find the gap-up and gap-down stocks.
# print(nse.holidays()) # to call holidays function.

