import pandas as pd
import numpy as np
import yaml
from yaml.loader import SafeLoader
from authentication.fyers_authentication import read_t_file
from utility.telegram_utility import read_file
from fyers_api import fyersModel
import talib as talib
import pandas_ta as ta
import json
import datetime
from datetime import date
import os
import time
from telegram_utility import send_tele_msg


pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)

# to read the configuration file.
config_main = '/Users/sunilkumar/ksunilt/trading_bot/sk_bot/config/config_main.yml'
with open(config_main, 'r') as config_main:
    cfg = yaml.load(config_main, Loader=SafeLoader)

periods = cfg['trade']['daily_candle_drawdown_period'] - 1

# Reference Data
ref_hld_stock = []
ref_hld_res = []
fund_available = None

# print("we are at starting point.")
# print(ref_hld_stock)
# print(fund_available)


def fyers_get_holdings():
    '''
    Function is to get the number of holding stocks.
    And will append the list "ref_hld_stock" from "Reference Data"

    :return: float value of the fund balance.
    :plan:  - Need to add retry logic in case of bad response code.
            - run this func after getting the funds and before the trading session.
            - telegram notification to let the user know about the holding stocks.
            - one more functin to check if the holding stock is the current day gapup or gapdown stock.
            - holding good response - {'s': 'ok', 'code': 200, 'message': '', 'holdings': [{'holdingType': 'HLD', 'quantity': 1, 'costPrice': 1.55, 'marketVal': 3.75, 'remainingQuantity': 1, 'pl': 2.2, 'ltp': 3.75, 'id': 1, 'fyToken': 101000000011460, 'exchange': 10, 'symbol': 'NSE:JPASSOCIAT-EQ'}, {'holdingType': 'HLD', 'quantity': 1, 'costPrice': 192.6, 'marketVal': 149.7, 'remainingQuantity': 1, 'pl': -42.9, 'ltp': 149.7, 'id': 2, 'fyToken': 10100000003812, 'exchange': 10, '
            ': 'NSE:ZEEL-EQ'}], 'overall': {'count_total': 2, 'total_investment': 194.15, 'total_current_value': 153.45, 'total_pl': -40.7, 'pnl_perc': -10.48}}
           - use count from the hld_res to validate the number of stoks in holding. need to make sure that data set will happen for all those trades.
    '''
    client_id = '<client_id>'
    log_path = '<log_path>'
    fyers = fyersModel.FyersModel(client_id=client_id, token=read_t_file(), log_path=log_path)
    hld_res = fyers.holdings()
    # print(hld_res)
    # hld_res = {'s': 'ok', 'code': 200, 'message': '', 'holdings': [{'holdingType': 'HLD', 'quantity': 1, 'costPrice': 1.55, 'marketVal': 3.75, 'remainingQuantity': 1, 'pl': 2.2, 'ltp': 3.75, 'id': 1, 'fyToken': 101000000011460, 'exchange': 10, 'symbol': 'NSE:SBIN-EQ'}, {'holdingType': 'HLD', 'quantity': 1, 'costPrice': 192.6, 'marketVal': 149.7, 'remainingQuantity': 1, 'pl': -42.9, 'ltp': 149.7, 'id': 2, 'fyToken': 10100000003812, 'exchange': 10, 'symbol': 'NSE:ZEEL-EQ'}], 'overall': {'count_total': 2, 'total_investment': 194.15, 'total_current_value': 153.45, 'total_pl': -40.7, 'pnl_perc': -10.48}}        # (comment-out to multiple stock function)
    # hld_res = {'s': 'ok', 'code': 200, 'message': '', 'holdings': [{'holdingType': 'HLD', 'quantity': 2, 'costPrice': 192.6, 'marketVal': 149.7, 'remainingQuantity': 1, 'pl': -42.9, 'ltp': 149.7, 'id': 2, 'fyToken': 10100000003812, 'exchange': 10, 'symbol': 'NSE:ZOMATO-EQ'}], 'overall': {'count_total': 2, 'total_investment': 194.15, 'total_current_value': 153.45, 'total_pl': -40.7, 'pnl_perc': -10.48}}                         # (comment-out dummy to test single stock function)
    hld_res_code = hld_res.get('code')
    if hld_res_code != 200:
        holdings_response_msg = hld_res.get('message')
        # print("ERROR : You have got unexpected response code. Message:", holdings_response_msg)
        msg = "ERROR : You have got unexpected response code: " + holdings_response_msg
        send_tele_msg(msg=msg)
    else:
        hld_overall = hld_res.get('overall')
        hld_count = hld_overall['count_total']
        if hld_count > 0:
            hld_list = hld_res.get('holdings')
            for each_hld in hld_list:
                hld_stock_symbol = each_hld.get('symbol')
                # ref_hld_stock.append(hld_stock_symbol)
                # hld_stock = [*set(ref_hld_stock)]  # to remove duplicates from the list
                return hld_stock_symbol


def fyers_get_funds():
    '''
    Function is used to check the available fund balance in account for equity.
    And will append "ref_hld_stock" in "Reference Data".

    :return: float value of available balance.
    :plan:  - need to make it run after the daily login and validation.
            - always run this function after the daily login. so there is no change of token expiry message.
            - add retry option in case if we gont get 200 response code.
            - telegram notification in case of less/no funds.
    '''
    client_id = '<client_id>'
    log_path = '<log_path>'
    fyers = fyersModel.FyersModel(client_id=client_id, token=read_t_file(), log_path=log_path)
    funds_response = fyers.funds()
    funds_response_msg = funds_response.get('message')
    funds_response_code = funds_response.get('code')
    # funds_response_code = 403                                             # (comment-out to test the function)
    # print("funds_response_code is =========>", funds_response_code)       # (comment-out to test the function)
    if funds_response_code != 200:
        # print("ERROR : You have got unexpected response code. Message:", funds_response_msg)
        msg = "ERROR : You have got unexpected response code: " + funds_response_msg
        send_tele_msg(msg=msg)
    else:
        # print("funds_response is : ----> ", funds_response)
        fund_limit = funds_response['fund_limit']
        for each_limit in fund_limit:
            for limit_dict in each_limit.values():
                if '10' in str(limit_dict):
                    avl_bal_dict = funds_response.get('fund_limit')[9]
                    fund_balance = avl_bal_dict['equityAmount']
                    return fund_balance


def get_ohlc(stock, data_resolution, days):
    """
    to get ohlc data to df.
    :param stock: the stock name should be in NSE:JPASSOCIAT-EQ format.
    :return: ohlc df
    """
    # paramaters.
    stock = stock
    data_resolution = data_resolution
    days = days
    print("stock: ", stock)
    client_id = '<client_id>'
    token = read_t_file()
    log_path = '<log_path>'
    range_from = (datetime.datetime.now() - datetime.timedelta(days=1*days)).strftime("%Y-%m-%d")
    range_to = date.today().strftime("%Y-%m-%d")

    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', None)

    data = {
        "symbol": stock,
        "resolution": data_resolution,
        "date_format": "1",
        "range_from": range_from,
        "range_to": range_to,
        "cont_flag": "1"
    }
    fyers = fyersModel.FyersModel(client_id=client_id, token=token, log_path=log_path)
    history_response = fyers.history(data)
    history_res_msg = history_response.get('message')
    # print(history_res_msg)
    if history_res_msg != None:
        send_tele_msg(msg="Error in OHLC extract: " + history_res_msg)

    # to convert json response to df.
    history_candles = history_response['candles']
    df = pd.DataFrame.from_dict(data=history_candles)
    df.columns = ["timestamp", "open", "high", "low", "close", "volume"]
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    # print("OHLC Data : ")
    # print(df.tail())
    return df


def find_heikin_ashi(df):
    df = df
    pd.options.mode.chained_assignment = None
    HAdf = df[['timestamp', 'open', 'high', 'low', 'close']]
    HAdf['close'] = round(((df['open'] + df['high'] + df['low'] + df['close'])/4), 2)
    for i in range(len(df)):
        if i == 0:
            HAdf.iat[0, 1] = (df['open'].iloc[0] + df['close'].iloc[0])/2
        else:
            HAdf.iat[i, 1] = (HAdf.iat[i-1, 1] + HAdf.iat[i-1, 4])/2
    HAdf['high'] = HAdf.loc[:,['open', 'close']].join(df['high']).max(axis=1)
    HAdf['low'] = HAdf.loc[:,['open', 'close']].join(df['low']).min(axis=1)
    HA_columns = ['open', 'high', 'low', 'close']
    HAdf[HA_columns] = HAdf[HA_columns].round(2)
    # print("Heikin Ashi Data : ")
    # print(HAdf.tail())
    return HAdf


def get_datapoints(df, show_rows, sma_yellow, sma_red, rolling_candle):
    '''
    function to create below datapoints:
        1. sma_red
        2. sma_yellow
        3. RSI14
        4. SMA_SPREAD
        5. SMA_Trend
        6. Candle_type
        7. tM1_candle
        8. buy_more_distance
        9. find_buy
        10. tM1_SMA_SPREAD
        11. exit_all
    :param df: dataframe created by Heikin Ashi function.
    :param days: the latest number of days the datapoints to be created.
    :return: Datapoints for the holding stock for the number of latest trading day. (day in case of daily candle. and data depends on frequency)
    '''

    show_rows = show_rows
    df = df
    sma_yellow = sma_yellow
    sma_red = sma_red
    rolling_candle = rolling_candle
    # report_dir = '/Users/sunilkumar/ksunilt/trading_bot/sk_bot/strategy/awsome_strategy/reports/'
    # report_name = "report"
    # report_name = stock + ".xlsx"       # add logic to use pop the list in every fetch of ohlc.

    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', None)

    # called by df['candle_type'] to find the RED or GREEN Candle.
    def candle(df):
        if df['close'] < df['open']:
            return "RED"
        else:
            return "GREEN"

    # to find the buy opportunity.
    def find_buy(df):   # this function is still under testing --- > thsi shoudl go. 2021-08-26 05:30:00
        if df['SMA_Trend'] == 'DOWNTREND' and df['candle_type'] == "RED" and df['tM1_candle'] == 0.0:
            return "BUYMORE"
        elif df['sma_yellow'] < df['sma_red'] and df['candle_type'] == "RED":
            return "sell"

    # to find the Increasing or Decreasing trend.
    def SMA_SPREAD_trend(df):
        if abs(df['SMA_SPREAD']) > abs(df['tM1_SMA_SPREAD']):
            return "increasing"
        else:
            return "decreasing"

    # to find the exit point based on SMA spread trend for last three candles.
    # "last three candles" is hardcoded and this needs to be configurable.
    def exit_all(df):
        if df['SMA_Trend'] == "UPTREND":
            if df['t-2_SMA_SPREAD_trend'] == "decreasing":
                if df['SMA_SPREAD_trend'] == df['tM1_SMA_SPREAD_trend'] and df['tM1_SMA_SPREAD_trend'] == df['t-2_SMA_SPREAD_trend']:
                    return "exit all"


    # to find SMA_yellow
    df['sma_yellow'] = talib.SMA(df['close'],timeperiod=sma_yellow)

    # to find SMA_red
    df['sma_red'] = talib.SMA(df['close'],timeperiod=sma_red)

    # to find RSI_14
    df['RSI_14'] = talib.RSI(df['close'],timeperiod=14)

    # to find Supertrend.
    supertrend = ta.supertrend(df['high'], df['low'], df['close'], 7, 3)
    # to combine Supertrend output with the existing df.
    df = pd.concat([df, supertrend], axis=1, join='inner')

    # to convert UTC timestamp to IST timestamp.
    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
    df['timestamp'] = df['timestamp'].astype(str).str[:-6]

    # to check the SPREAD of sma_red and sma_yellow. And round up with 2 decimals float number.
    df['SMA_SPREAD'] = df['sma_red'] - df['sma_yellow']
    df['SMA_SPREAD'] = df['SMA_SPREAD'].round(decimals=2)

    # to check Supertrend Buy or Sell.
    df['SUPERTREND'] = np.where(df['SUPERTd_7_3.0'] == 1, "BUY", "SELL")

    # BUY/SELL decision making based on SMA crossover.
    df['SMA_Trend'] = np.where(df['sma_red'] > df['sma_yellow'], "UPTREND", "DOWNTREND")

    # # to keep only the latest few days data to rest of the processing.
    # df = df.tail(days)

    # calls the candle function to find the RED or GREEN Candle.
    df['candle_type'] = df.apply(candle, axis=1)

    # to find numeric version for candle_type. RED=0 and GREEN=1
    df['candle_type_num'] = np.where(df['candle_type'] == "RED", 0, 1)
    df['tM1_candle'] = df['candle_type_num'].shift(1)

    # to find distance from low to sma_red.
    df['buy_more_distance'] = df['low'] - df['sma_red']

    # calls find_buy func to find more and more buying opportunity which helps in averaging price.
    df['find_buy'] = df.apply(find_buy, axis=1)

    # to shift the SMA SPREAD column so that this column will help to find SMA Trend.
    # how many shift of candle is determined from the configuration file.
    df['tM1_SMA_SPREAD'] = df['SMA_SPREAD'].shift(periods=periods)

    # call SMA_SPREAD_trend func to find the spread trend if its increasing or decreasing.
    df['SMA_SPREAD_trend'] = df.apply(SMA_SPREAD_trend, axis=1)

    # the below two columns is created to find the continuous down/up trend for last 3 days.
    df['tM1_SMA_SPREAD_trend'] = df['SMA_SPREAD_trend'].shift(1)
    df['t-2_SMA_SPREAD_trend'] = df['SMA_SPREAD_trend'].shift(2)

    # to find the exit point based on last 3 days sma candle trend.
    df['exit_all'] = df.apply(exit_all, axis=1)

    # to find the diff of open and low.
    df['open_low_diff'] = df['open'] - df['low']

    # to find the day of the week based on date.
    # df['day'] = df.apply(day, axis=1)

    # to find the max value from low columns to get the limit price for current day trading.
    df['limit_price'] = df.low.rolling(rolling_candle, win_type=None).min()          # removing this for now. closed="left"

    # to clean up the data. Required columns can be reenabled back again when needed.
    df.drop(['SUPERTl_7_3.0', 'SUPERT_7_3.0', 'SUPERTd_7_3.0', 'SUPERTs_7_3.0', 'SUPERTREND'], axis =1, inplace = True)
    df = df.dropna(subset=['tM1_SMA_SPREAD']).reset_index(drop=True)

    # to round up with 2 decimal value.
    columns = ['open', 'high', 'low', 'close', 'sma_red', 'sma_yellow', 'RSI_14', 'SMA_SPREAD', 'buy_more_distance']
    df[columns] = df[columns].round(2)

    # to save to excel file.
    # df.to_excel(report_dir + "OHLC_" + report_name, sheet_name='candle')
    # print("Dataset generated and report saved to: ", report_dir + "OHLC_" + report_name)

    # to print latest few lines from df.
    df = df.tail(show_rows)
    df.reset_index(inplace=True, drop=True)
    # print(df.dtypes)
    print(df)
    return df


def getTime():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def check_previous_trade():
    ref_trade_capture = "/../sk_bot/refrence_data/ref_trade_capture.json"
    with open(ref_trade_capture, 'r') as prev_trade:
        curr_trade = prev_trade.read()
        print(curr_trade)

def find_qty(df):
    df = df
    limit_price = round(df.iloc[-1]['limit_price'])
    ref_trade_capture = "/../sk_bot/refrence_data/ref_trade_capture.json"

    if os.stat(ref_trade_capture).st_size == 0:
        funds = fyers_get_funds()
        funds = funds * 0.05      # thsi 5% shoudl be picked up from the config file.
        print("qty from find_qty function is : -->", funds)
        funds = limit_price / round(funds)
        qty = round(funds)
        if qty < 5:            # shoudl be configiratble as min start qty.
            qty = 5
            print("qty from find_qty function is : -->", qty)
            return qty
        else:
            return qty
    else:
        with open(ref_trade_capture, 'r') as prev_trade:
            prev_trade = prev_trade.read()
            prev_trade = json.loads(prev_trade)
            print("prev_trade --->", prev_trade)
            if prev_trade['date'] < date.today().strftime("%d-%b-%Y"):
                funds = fyers_get_funds()
                qty_percent = prev_trade['qty_percent'] * 2    # this 2 can be made configurable.
                funds = funds * qty_percent
                qty = funds / limit_price
                qty = round(qty)
                print(qty)
                if qty < 5:            # shoudl be configiratble as min start qty.
                    qty = 5
                    print("qty from find_qty function is : -->", qty)
                    return qty
                else:
                    return qty


def find_side(df):
    '''
    function is to find order side, if its buy or sell.
    :param df:
    :return:
    '''
    if df.iloc[-2]['find_buy'] == "BUYMORE":
        side = 1
        return side
    else:
        # side = -1
        side = 1        # used for testing purpose, hard coded as buy.
        return side

def find_limit_price(df):
    limitPrice = round(df.iloc[-1]['limit_price'])

    print("limitPrice from find_limit_price function is ", limitPrice)
    return limitPrice


def exit_program(code, message):
    '''
    code: 1101, message: Order Submitted Successfully.
    code: -174, message: System is not connected to NSE Equity market
    code: -392, message: Price should be in multiples of tick size.
    :param code: code you received from the place order function
    :param message: message you received from the place order function
    :return: sends notification and terminates the program with reason.
    '''
    code = code
    message = message
    if code == -174 or code == -392:
        send_tele_msg(msg="EXITING PROGRAM : " + message)
        quit()
    # elif code == -392:   no need to exit the program for this reason. need to add reasonse as n when we get more codes.
    #     send_tele_msg(msg="EXITING PROGRAM : " + message)
    #     quit()
        return message

def fyers_place_order(symbol, df):
    '''
    function to place order. The function is only to find the buy opportunity in the downtreand stock. and not concentrating on the exit of the order for now.
    :param symbol: symbol will be picked up from the holding stock.
    :return: places the order.
    Plan : 1. add a loop of 1hours for the BUYMORE so that you can use hourly sma to find effective buy opportunity.
        2. add more logic to find qty and limit price.
        3.
    '''
    symbol = symbol
    df = df
    find_buy = df.iloc[-1]['find_buy']

    # Based on the datasets, this func finds the buymore opportunity and place the buy order.
    if find_buy == "BUYMORE":                    # note : change this to "BUYMORE" . None is used for testing.
        qty = find_qty(df=df)
        side = find_side(df=df)
        # limitPrice = df.iloc[-1]['limit_price']
        limitPrice = find_limit_price(df=df)
        # limitPrice = limit_price_validation(symbol=symbol, limit_price=limitPrice)    # this is on hold.
        print("******** order placing paramaters ********")
        print("symbol is : ", symbol)
        print("find_buy is : ", find_buy)
        print("qty is : ", qty)
        print("side is : ", side)
        print("limitPrice is : ", limitPrice)
        print("******** ******** ******** ******** ********")
        # appConfig = getAppConfig()
        client_id = '<client_id'
        log_path = '<log_path>'
        fyers = fyersModel.FyersModel(client_id=client_id, token=read_t_file(), log_path=log_path)
        data = {
            "symbol": symbol,
            "qty": qty,       # REMEMBER to change this to variable "qty".
            "type": 1,
            "side": side,      # REMEMBER to change this to variable "side".
            "productType": "CNC",
            "limitPrice": limitPrice,      # REMEMBER to change this to variable "limitPrice".
            "stopPrice": 0,
            "validity": "DAY",
            "disclosedQty": 0,
            "offlineOrder": "False",
            "stopLoss": 0,
            "takeProfit": 0
        }
        place_order_response = fyers.place_order(data=data)                 # comment-out for testing.
        
        response_code = place_order_response['code']
        response_message = place_order_response['message']
        order_id = place_order_response.get('id', int)

        if order_id == '' and (response_code == -174 or response_code == -392):
            print("Exiting program due to: ", response_message)
            exit_program(code=response_code, message=response_message)
            return symbol, limitPrice, find_buy, order_id

        elif order_id is not None and response_code == 1101:
            send_tele_msg(msg=" Order placed for " + symbol + " placed for Rs." + str(limitPrice))
            return symbol, limitPrice, find_buy, order_id


def get_ref_file(file, data, action):
    if action == "update":
        temp_dict = {}
        print(temp_dict)
        print(type(data))
        json_data = json.dumps(data)
        print(json_data)
        print(type(json_data))
        with open(file, 'w') as f:
            f.write(json_data)
            f.close()
    elif action == "read":
        with open(file, 'r') as f:
            data = f.read()
            print(type(data))
            datass = json.loads(data)
            print("data is ---->---->", datass)
            print(type(datass))
            return datass




def fyers_order_status(id):
    '''
    Possible Values	Description
    1	 -->   Cancelled
    2	 -->   Traded / Filled
    3	 -->   For future use
    4	 -->   Transit
    5	 -->   Rejected
    6	 -->   Pending

    :param id:
    :return:
    '''
    id = id
    client_id = '<client_id>'
    log_path = '<log_path>'
    fyers = fyersModel.FyersModel(client_id=client_id, token=read_t_file(), log_path=log_path)
    data = {"id": id}

    order_status_res = fyers.orderbook(data=data)
    order_status_code = order_status_res.get('code')
    order_status_msg = order_status_res.get('message')

    while order_status_code != 200:
        trade_wait = 30
        print("ERROR: Unexpected response, checking status after ", str(trade_wait), "minutes..", order_status_msg)
        send_tele_msg(msg="ERROR: Unexpected response: " + order_status_msg)
        time.sleep(trade_wait)
        if order_status_code == 200:
            break

    order_id = order_status_res['orderBook'][0]['id']
    order_status = order_status_res['orderBook'][0]['status']
    order_symbol = order_status_res.get('orderBook')[0]['symbol']
    order_datetime = order_status_res['orderBook'][0]['orderDateTime']
    order_qty = order_status_res['orderBook'][0]['qty']
    order_qty_pct = 10
    side = "BUY"

    while order_status == 6:    # Pending.
        print("Order is still pending.. checking status again for order id : ----> ", order_id)
        send_tele_msg(msg="Order is still pending.. checking status again for order id : ----> " + order_id)
        trade_wait = 20         # make this configurable.
        time.sleep(trade_wait)
        if order_status == 2:
            break

    if order_status == 2:   # Filled
        print("Order is Filled for the order id: ----> ", order_id)
        send_tele_msg(msg="Order is Filled." + order_id + order_symbol)
        ref_trade_capture = '/Users/sunilkumar/ksunilt/trading_bot/sk_bot/refrence_data/ref_trade_capture.json'

        key = ['order_id', 'order_status', 'order_symbol', 'order_datetime', 'order_qty', 'order_qty_pct', 'side']
        value = [order_id, order_status, order_symbol, order_datetime, order_qty, order_qty_pct, side]
        curr_trade = dict(zip(key, value))
        print("curr_trade is : ----> ", curr_trade)

        if os.stat(ref_trade_capture).st_size == 0:
            curr_trade['trade_count'] = 1
            # print("curr_trade is :", curr_trade)
            with open(ref_trade_capture, 'w') as f:
                temp_list = []
                temp_list.append(curr_trade)
                json.dump(temp_list, f, indent=2)
                print("created trade capture file.")

        elif os.stat(ref_trade_capture).st_size != 0:
            with open(ref_trade_capture, 'r+') as f:
                prv_trades = json.load(f)
                prv_trades_count = len(prv_trades)
                if prv_trades_count > 0:
                    curr_trade['trade_count'] = prv_trades_count + 1
                    print(curr_trade)
                f.close()

            with open(ref_trade_capture, 'w') as f:
                f.truncate(0)
                prv_trades.append(curr_trade)
                json.dump(prv_trades, f, indent=2)
                print("updated trade capture file.")


        return order_id, order_status, order_symbol, order_datetime, order_qty, order_qty_pct, side



def fyers_position():
    # id = id
    # data = {"id": id}
    client_id = '<client_id>'
    log_path = '<log_path>'
    fyers = fyersModel.FyersModel(client_id=client_id, token=read_t_file(), log_path=log_path)
    fyers_position_res = fyers.positions()

    if fyers_position_res['code'] == 200:
        if type(fyers_position_res['netPositions']) == list:
            for item in fyers_position_res['netPositions']:
                symbol = item['symbol']
                net_qty = item['netQty']
                avg_price = item['avgPrice']
                return symbol, net_qty, avg_price


def fyers_get_pnl(stk):
    stk = stk
    client_id = '<client_id>'
    log_path = '<log_path>'
    fyers = fyersModel.FyersModel(client_id=client_id, token=read_t_file(), log_path=log_path)
    hld_res = fyers.holdings()
    hld_res_code = hld_res.get('code')
    if hld_res_code != 200:
        holdings_response_msg = hld_res.get('message')
        print("ERROR : You have got unexpected response code. Message:", holdings_response_msg)
    else:
        hld = hld_res.get('holdings')
        if len(hld) > 0:
            stk_qty = []
            stk_pnl = []
            for each_hld in hld:
                symbol = each_hld.get('symbol')
                quantity = each_hld.get('quantity')
                pl = each_hld.get('pl')
                if symbol == stk:
                    stk_qty.append(quantity)
                    stock_quantity = 0
                    for qty in range(0, len(stk_qty)):
                        stock_quantity = stock_quantity + stk_qty[qty]
                    stk_pnl.append(pl)
                    stock_pnl = 0
                    for pnl in range(0, len(stk_pnl)):
                        stock_pnl = stock_pnl + stk_pnl[pnl]
            return stock_quantity, stock_pnl

def get_order_book():
    '''

    :return:
    '''
    client_id = '<client_id>'
    log_path = '<log_path>'
    fyers = fyersModel.FyersModel(client_id=client_id, token=read_t_file(), log_path=log_path)
    orderbook_res = fyers.orderbook()
    orderbook_code = orderbook_res['code']
    orderbook_msg = orderbook_res['message']
    if orderbook_code != 200:
        print("ERROR : You have got unexpected response code. Message:", orderbook_msg)
        # need to handle the situation here. may be retry thrice.
    else:
        orderbook_list = orderbook_res['orderBook']
        print(len(orderbook_list))
        print(type(orderbook_list))
        print(orderbook_list)
        for each_order in orderbook_list:
            orderDateTime = each_order.get('orderDateTime')
            id = each_order.get('id')
            side = each_order.get('side')
            instrument = each_order.get('instrument')
            productType = each_order.get('productType')
            status = each_order.get('status')
            qty = each_order.get('qty')
            remainingQuantity = each_order.get('remainingQuantity')
            filledQty = each_order.get('filledQty')
            limitPrice = each_order.get('limitPrice')
            message = each_order.get('message')
            symbol = each_order.get('symbol')

def fyers_order_cancel(id):
    id = id
    client_id = '<client_id>'
    log_path = '<log_path>'
    fyers = fyersModel.FyersModel(client_id=client_id, token=read_t_file(), log_path=log_path)
    data = {"id":'808058117761'}

    order_cancel_res = fyers.cancel_order(data)
    print(order_cancel_res)
    # order_cancel_res = {'s': 'ok','code': 1103,'message': 'Successfully cancelled order', 'id': '808058117761'}
    # print(order_cancel_res)

