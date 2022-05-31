import datetime

import pandas as pd
from telegram_service.fyers_auth_v2 import read_token_file

from datetime import date
import numpy as np
import pandas_ta as ta
from fyers_api import fyersModel
import talib as talib
import matplotlib.pyplot as plt
from matplotlib import style
from config.config import getAppConfig
from datetime import datetime
import os

client_id = <CLIENT_ID_HERE>
secret_key = <SECRET_KEY_HERE>
redirect_uri = <REDIRECT_URL_HERE>
response_type = 'code'
grant_type = 'authorization_code'

def placeOrder(script, order):
    if order == "BUY":
        # appConfig = getAppConfig()
        client_id = <CLIENT_ID_HERE>
        secret_key = <SECRET_KEY_HERE>
        redirect_uri = <REDIRECT_URL_HERE>
        response_type = 'code'
        grant_type = 'authorization_code'

        fyers = fyersModel.FyersModel(client_id=client_id, token=read_token_file(), log_path=os.getcwd())
        print(fyers.get_profile())
        data = {
            "symbol": script,
            "qty": 1,
            "type": 2,
            "side": 1,
            "productType": "INTRADAY",
            "limitPrice": 0,
            "stopPrice": 0,
            "validity": "DAY",
            "disclosedQty": 0,
            "offlineOrder": "False",
            "stopLoss": 0,
            "takeProfit": 0
        }
        order = fyers.place_order(data=data)
        print(order)
        print(f"Buy order placed for {script} at time: {getTime()}")
    else:
        # appConfig = getAppConfig()
        client_id = <CLIENT_ID_HERE>
        secret_key = <SECRET_KEY_HERE>
        redirect_uri = <REDIRECT_URI_HERE>
        response_type = 'code'
        grant_type = 'authorization_code'
        fyers = fyersModel.FyersModel(client_id=client_id, token=read_token_file(), log_path=os.getcwd())
        data = {
            "symbol":script,
            "qty": 1,
            "type": 2,
            "side": -1,
            "productType": "INTRADAY",
            "limitPrice": 0,
            "stopPrice": 0,
            "validity": "DAY",
            "disclosedQty": 0,
            "offlineOrder": "False",
            "stopLoss": 0,
            "takeProfit": 0
        }
        order = fyers.place_order(data=data)
        print(order)
        print(f"Sell order placed for {script} at time: {getTime():>20}")

def getTime():
    return datetime.datetime.now().strftime('%Y-%m-%d')

def find_position():
    sgx_input_file = '/pretrade/sgx_report/find_side.csv'
    sgx_df = pd.read_csv(sgx_input_file)
    sgx_today = sgx_df.iloc[[-1]]
    sgx_side = sgx_today['side'].values[0]

    if sgx_side == "SELL":
        print("We are selling today. ")
        print("Calling pretrade function to find Sell stocks ...")
        print("getting gap_down/up_stocks")
    else:
        print("WE are buying today. ")
        print("Calling pretrade function to find Buy stocks...")
        print("getting gap_up/down_stocks")

def stock_analysis():

    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', None)

    # API paramaters.
    client_id = <CLIENT_ID_HERE>
    token = read_token_file()
    log_path = 'sk_bot/strategy/awsome_strategy/'

    # API to get stock details.
    data = {
        "symbol": "NSE:JSWSTEEL-EQ",
        "resolution": "3",
        "date_format": "1",
        "range_from": "2022-05-11",
        "range_to": "2022-05-17",
        "cont_flag": "1"
    }
    fyers = fyersModel.FyersModel(client_id=client_id, token=token, log_path=log_path)
    history_response = fyers.history(data)

    # to convert json response to df.
    history_candles = history_response['candles']
    df = pd.DataFrame.from_dict(data=history_candles)
    df.columns = ["timestamp", "open", "high", "low", "close", "volume"]
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

    # to find SMA_5
    df['SMA5'] = talib.SMA(df['close'],timeperiod=5)

    # to find SMA_34
    df['SMA34'] = talib.SMA(df['close'],timeperiod=34)

    # to find RSI_14
    df['RSI_14'] = talib.RSI(df['close'],timeperiod=14)

    # to find Supertrend.
    supertrend = ta.supertrend(df['high'], df['low'], df['close'], 7, 3)

    # to combine Supertrend output with the existing df.
    df = pd.concat([df, supertrend], axis=1, join='inner')

    # to convert UTC timestamp to IST timestamp.
    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
    df['timestamp'] = df['timestamp'].astype(str).str[:-6]

    # to check the SPREAD of SMA5 and SMA34. And round up with 2 decimals float number.
    df['SMA_SPREAD'] = df['SMA5'] - df['SMA34']
    df['SMA_SPREAD'] = df['SMA_SPREAD'].round(decimals = 2)


    # to check Supertrend Buy or Sell.
    df['SUPERTREND'] = np.where(df['SUPERTd_7_3.0'] == 1, "BUY", "SELL")

    # BUY/SELL decision making.
    # BUY/SELL based on SMA crossover.
    df['SMA_Crossover'] = np.where(df['SMA5'] > df['SMA34'], "BUY", "SELL")

    # SMA trend to know if its positive or negative.
    # current sma minus previous row sma.
    curr_spread = df.iloc[-1]['SMA_SPREAD']
    prev_spread = df.iloc[-2]['SMA_SPREAD']
    df['SMA_Trend'] = df['SMA_SPREAD'].gt(df['SMA_SPREAD'].shift(-1, fill_value=-1))
    # to check the Final Buy or Sell.
    # df['FINAL_BUY'] = np.where((df['SUPERTREND'] == "BUY") & (df['SMA_COMPARE'] == "BUY"), "BUY", "0")
    # df['FINAL_SELL'] = np.where((df['SUPERTREND'] == "SELL") & (df['SMA_COMPARE'] == "SELL"), "SELL", "0")

    # to roundup SMA SPREAD.
    # df['SMA_ROUNDUP'] = df.SMA_SPREAD.astype(float).round()
    # df['SPREAD_ROLL_MAX'] = df['SMA_ROUNDUP'].rolling(3).max()
    # df['super_final'] = np.where(df['SPREAD_ROLL_MAX'] == df['SMA_ROUNDUP'], "hold", "0")

    # Data Cleanup.
    df.drop(['SUPERTl_7_3.0', 'SUPERTs_7_3.0', 'SUPERTREND'], axis =1, inplace = True)

    # to print df.
    print(df)


    # to save to excel file.
    df.to_excel("/sk_bot/strategy/awsome_strategy/data_JSWSTEEL_revised.xlsx")

def trade_placement():
    today = datetime.today()
    current_date = today.strftime("%d:%m:%Y")
    orb_start_time = current_date + " 01:00:00" # this should be 09:30:00 trade start time.
    current_time = today.strftime("%d-%m-%Y %H:%M:%S")
    print("ORB Strategy started...")

    if orb_start_time > current_time:
        df = pd.read_excel("/sk_bot/strategy/awsome_strategy/data_TATAMOTORS.xlsx")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', None)
        print(df)

        if not df.empty:
            curr_timestamp = df.iloc[-1]['timestamp']
            curr_open = int(df.iloc[-1]['open'])
            curr_high = int(df.iloc[-1]['high'])
            curr_low = int(df.iloc[-1]['low'])
            curr_close = int(df.iloc[-1]['close'])
            curr_SMA5 = int(df.iloc[-1]['SMA5'])
            curr_SMA34 = int(df.iloc[-1]['SMA34'])
            curr_RSI_14 = int(df.iloc[-1]['RSI_14'])
            # curr_supertrend = df.iloc[-1]['SUPERTREND']
            curr_spread = df.iloc[-1]['SMA_SPREAD']
            curr_crossover = df.iloc[-1]['SMA_Crossover']
            prev_spread = df.iloc[-2]['SMA_SPREAD']
            prev_crossover = df.iloc[-2]['SMA_Crossover']
            curr_trades = []

            print("===================================")
            print("curr_spread: " ,curr_spread)
            print("curr_crossover: " ,curr_crossover)
            print("prev_spread: " ,prev_spread)
            print("prev_crossover: " ,prev_crossover)
            print("curr_trades: " ,curr_trades)
            print("===================================")

            if not curr_trades and curr_crossover == 'BUY':
                print("Function to place BUY order...")
                curr_trades.append("LONG")
                print("curr_trades is updated with :", curr_trades)

            elif 'LONG' in curr_trades and curr_crossover == 'SELL' and curr_crossover == prev_crossover:
                print("Function to place SELL order...")
                curr_trades.append("LONGCLOSE")
                print("curr_trades is updated with :", curr_trades)

            elif sma_crossover1 == sma_crossover2:
                print("we are holding it")
                print(curr_trades)

        # FINAL_BUY = df.iloc[-1]['FINAL_BUY']
            # FINAL_SELL = df.iloc[-1]['FINAL_SELL']
            # SMA_DIFF = df.iloc[-1]

            # buy_traded_stock = []
            sell_traded_stock = []

            # verison1 of calculation.
            # if FINAL_BUY == "BUY" and FINAL_SELL == 0:
            #     print("we are Selling")
            # #     place the order here.
            # # send msg to telegram for now.
            # if SUPERTREND == "SELL" and SMA_SPREAD > 0:
            #     print("we are Buy")

            # verison1 of calculation.
            # if


    # else:
    #     print("df is empty")


# VWAP requires the DataFrame index to be a DatetimeIndex.
    # Replace "datetime" with the appropriate column from your DataFrame
    # df.set_index(pd.DatetimeIndex(df["timestamp"]), inplace=True)
    # df = df.dropna()
    # df.reset_index(drop=True)
    # df.ta.supertrend(period=7, multiplier=3, append=True)
    # print(df)




    # df[['SMA5','SMA35']].plot(figsize=(8,8))
    # plt.show()
    # print(df.tail(10))
    #
    # print(df.index[2:])




# DND - do not delete below lines.
print(find_position())
# stock_analysis()
# print(getTime())
# placeOrder(script="NSE:JSWSTEEL-EQ", order="SELL")
# trade_placement()
