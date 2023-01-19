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
# import datetime
from datetime import datetime, timedelta, date
# from datetime import datetime, date
from html2image import Html2Image
from time import sleep
# import warnings
# warnings.filterwarnings("ignore")
import math
from authentication import *
from authentication.fyers_login_crontab import *

import os
import time
from utility.telegram_utility import send_tele_msg, send_tele_image

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)

# to read the configuration file.
config_main = '../trade-assist/config/config_main.yml'
with open(config_main, 'r') as config_main:
    cfg = yaml.load(config_main, Loader=SafeLoader)

# Configuration Assignment
client_id = cfg['auth']['client_id']
log_path = cfg['auth']['strategy_logs']
fyers = fyersModel.FyersModel(client_id=client_id, token=read_t_file(), log_path=log_path)
fav_stock = cfg['trading_strategy']['fav_stock']
fav_stock_file = cfg['trading_strategy']['fav_stock_file']
stock_report = cfg['trading_strategy']['stock_report_path']
trading_strength = cfg['trading_strategy']['trading_strength']


# Reference Data
ref_hld_stock = []
ref_hld_res = []
fund_available = None


# [this is working fine]
def fyers_get_funds():
    '''
    Function is used to check the available fund balance in account for equity.
    And will append "ref_hld_stock" in "Reference Data".

    :return: float value of available balance.SMA_Trend
    :plan:  - need to make it run after the daily login and validation.
            - always run this function after the daily login. so there is no change of token expiry message.
            - add retry option in case if we don't get 200 response code.
            - telegram notification in case of less/no funds.
    '''
    funds_response = fyers.funds()
    funds_response_msg = funds_response.get('message')
    funds_response_code = funds_response.get('code')

    if funds_response_code != 200:
        # print("ERROR : You have  got unexpected response code. Message:", funds_response_msg)
        message = "ERROR : You have got unexpected response code: " + funds_response_msg
        send_tele_msg(message=message)
    else:
        # print("funds_response is : ----> ", funds_response)
        fund_balance = funds_response['fund_limit'][-1]['equityAmount']
        fund_balance = 50000            # Testing: fund balance hardcoded, comment it out before production use.
        if fund_balance < 1000:
            messsage = "No enough fund in account. Fund balance: %s is less than threshold" %(fund_balance)
            send_tele_msg(message=messsage)
            exit_program(code="x", message="Due to low fund balance")
        else:
            return fund_balance


# [this is working fine]
def read_fav_stock(filename):
    fav_stock_list = []
    with open(filename, "r") as f:
        output = f.read()
        output = json.loads(output)
        output = output[0]
        output = output['symbol']
        for symbol in output:
            fav_stock_list.append(symbol)
        return fav_stock_list


# [this is working fine]
def round_up_price(price):
    if "." in str(price):
        whole = str(math.floor(price))
        decimal = int(str(price).split(".")[-1])
        decimal = str(decimal - (decimal % 5))
        rounded_price = (float(whole + "." + decimal))
        return rounded_price


# [this is working fine]
def get_ohlc_to_check_sl(symbol, data_resolution, days=60):
    ohlc_df = get_ohlc(stock=symbol, data_resolution=data_resolution, days=days)
    intraday_ha_chart_df = get_heikin_ashi(df=ohlc_df)
    return intraday_ha_chart_df


# [this is working fine]
def fyers_place_sl_order(df, sl_stock, quantity, previous_low):
    sl_result_list = []
    no_sl_result_list = []
    sl_not_applicable = []
    dataset_issue = []
    ha_table = get_ohlc_to_check_sl(symbol=sl_stock, data_resolution="1D", days=30)
    print(ha_table.tail(3))

    curr_date = datetime.today().strftime("%Y-%m-%d")
    last_row = ha_table['timestamp'].iloc[-1].strftime("%Y-%m-%d")

    if last_row == curr_date:                      
        stopPrice = float(ha_table['low'].iloc[previous_low])
        print("previous low is ====>", stopPrice)
        stopPrice = round_up_price(price=stopPrice)
        ltp = fyers_get_stock_quote(symbol=sl_stock)
        print("ltp is ====>", ltp)
        curr_profit = float(df['pl'].loc[df['Current_Holdings'] == sl_stock])

        if ltp > stopPrice:
            msg = "SL ORDER PLACED"
            message = "\n - MESSAGE: %s - \nSymbol: %s \nltp: %s \nstopPrice: %s \ncurr_profit: %s" %(msg, sl_stock, ltp, stopPrice, curr_profit)
            send_tele_msg(message=message)
            sl_place_order_resp = fyers_place_order(symbol=sl_stock, qty=quantity, type="SLM", side="SELL", productType="CNC", stopPrice=stopPrice, limitPrice=0)
            sl_place_order_resp = {'s': 'ok', 'code': 1101, 'message': 'Order Submitted Successfully. Your Order Ref. No.122122062654', 'id': '122122062654'}

            response_code = sl_place_order_resp.get('code')
            order_id = sl_place_order_resp.get('id')
            order_message = sl_place_order_resp.get('message')

            if response_code == 1101:
                # print("SL Order is placed....")
                status = "CONFIRMED"
                keys = ["symbol", "ltp", "curr_profit", "stopPrice", "order_id", "order_message", "status"]
                values = [sl_stock, ltp, curr_profit, stopPrice, order_id, order_message, status]
                sl_result_dict = dict(zip(keys, values))
                sl_result_list.append(sl_result_dict)
                if len(sl_result_list) > 0 and status == "CONFIRMED":
                    msg = "SL ORDER CONFIRMED"
                    for each_dict in sl_result_list:
                        message = "\n - MESSAGE: %s - \nSymbol: %s \nltp: %s \nstopPrice: %s\norder_id: %s\norder_message: %s\n" %(msg, each_dict['symbol'], each_dict['ltp'], each_dict['stopPrice'], each_dict['order_id'], each_dict['order_message'])
                        send_tele_msg(message=message)
                        print("sl_result_list is ====> ", sl_result_list)
                        return sl_result_list

            else:
                status = "rejected"
                keys = ["symbol", "ltp", "curr_profit", "stopPrice", "order_id", "order_message", "status"]
                values = [sl_stock, ltp, curr_profit, stopPrice, order_id, order_message, status]
                no_sl_result_dict = dict(zip(keys, values))
                no_sl_result_list.append(no_sl_result_dict)
                if len(no_sl_result_list) > 0:
                    msg = "SL ORDER REJECTED"
                    for each_dict in no_sl_result_list:
                        message = "\n - MESSAGE: %s - \nSymbol: %s \nltp: %s \nstopPrice: %s\norder_message: %s\n" %(msg, each_dict['symbol'], each_dict['ltp'], each_dict['stopPrice'], each_dict['order_message'])
                        send_tele_msg(message=message)
                        return no_sl_result_list

        else:
            msg = "SL NOT APPLICABLE"
            status = "NA"
            error_message = "stopPrice: %s is higher than the ltp: %s" %(stopPrice, ltp)
            keys = ["symbol", "ltp", "stopPrice", "curr_profit", "error_message", "status"]
            values = [sl_stock, ltp, stopPrice, curr_profit, error_message, status]
            sl_result_dict = dict(zip(keys, values))
            sl_not_applicable.append(sl_result_dict)
            message = "\n - MESSAGE: %s \nSymbol: %s \nltp: %s \nstopPrice: %s \nerror_message: %s \n" %(msg, sl_stock, ltp, stopPrice, error_message)
            send_tele_msg(message=message)
            return sl_not_applicable
    else:
        msg = "DATASET ISSUE"
        status = "NA"
        error_message = "Latest data received is for %s" %(last_row)
        keys = ["symbol", "error_message", "status"]
        values = [sl_stock, error_message, status]
        sl_result_dict = dict(zip(keys, values))
        dataset_issue.append(sl_result_dict)
        message = "\n - MESSAGE: %s - \nSymbol: %s \nerror_message: %s \n" %(msg, sl_stock, error_message)
        send_tele_msg(message=message)
        return dataset_issue


# [this is working fine]
def fyers_get_datasets(strategy, symbol, data_resolution, days):
    if strategy == "SWING":
        if type(symbol) is str:
            # for each_symbol in symbol:
            ohlc_df = get_ohlc(stock=symbol, data_resolution=data_resolution, days=days)
            intraday_ha_chart_df = get_heikin_ashi(df=ohlc_df)
            intraday_ha_dp_chart_df = get_datapoints(df=intraday_ha_chart_df, sma_green=5, sma_red=15, rolling_candle=2)
            intraday_shape = intraday_ha_dp_chart_df.shape
            ohlc_shape = ohlc_df.shape
            ohlc_df.drop(ohlc_df.index[:(ohlc_shape[0] - intraday_shape[0])], inplace=True)
            ohlc_df.reset_index(inplace = True, drop = True)
            ohlc_df.drop(['timestamp'], axis=1, inplace=True)
            df = pd.concat([intraday_ha_dp_chart_df, ohlc_df], axis=1, join='inner')
            return df


# [this is working fine]
def get_ohlc(stock, data_resolution, days):
    print("OHLC for stock ::::::::: ", stock)
    """
    to get ohlc data to df.
    :param stock: the stock name should be in NSE:JPASSOCIAT-EQ format.
    :return: ohlc df
    """
    range_from = (datetime.now() - timedelta(days=1*days)).strftime("%Y-%m-%d")
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

    history_response = fyers.history(data)
    print("history_response is ====> ", history_response)
    if history_response['s'] == "ok" and type(history_response['candles']) == list:
        df = pd.DataFrame.from_dict(data=history_response['candles'])
        df.columns = ["timestamp", "open", "high", "low", "close", "volume"]
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.drop(['volume'], axis=1, inplace=True)
        return df
    else:
        err_message = history_response['message']
        message = "MESSAGE: %s" %(err_message)
        send_tele_msg(message=message)
        exit_program(code=" ", message=message)


# [this is working fine]
def get_heikin_ashi(df):
    df = df
    pd.options.mode.chained_assignment = None
    HAdf = df[['timestamp', 'open', 'high', 'low', 'close']]
    HAdf['close'] = round(((df['open'] + df['high'] + df['low'] + df['close'])/4), 2)
    for i in range(len(df)):
        if i == 0:
            HAdf.iat[0, 1] = (df['open'].iloc[0] + df['close'].iloc[0])/2
        else:
            HAdf.iat[i, 1] = (HAdf.iat[i-1, 1] + HAdf.iat[i-1, 4])/2
    HAdf['high'] = HAdf.loc[:, ['open', 'close']].join(df['high']).max(axis=1)
    HAdf['low'] = HAdf.loc[:, ['open', 'close']].join(df['low']).min(axis=1)
    HA_columns = ['open', 'high', 'low', 'close']
    HAdf[HA_columns] = HAdf[HA_columns].round(2)
    return HAdf


# [this is working fine]
def get_datapoints(df, sma_green, sma_red, rolling_candle):
    '''
    function to create below datapoints:win_type
        1. sma_8
        2. sma_4
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

    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', None)

    # called by df['candle'] to find the RED or GREEN Candle.
    def find_candle(df):
        if df['close'] < df['open']:
            return "RED"
        else:
            return "GREEN"

    df['ha_ohlc4'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4

    # to find SMA_green
    df['sma_green'] = talib.SMA(df['ha_ohlc4'], timeperiod=sma_green)

    # to find SMA_red
    df['sma_red'] = talib.SMA(df['ha_ohlc4'], timeperiod=sma_red)

    # to find Supertrend.
    supertrend = ta.supertrend(df['high'], df['low'], df['close'], 3, 3)
    df = pd.concat([df, supertrend], axis=1, join='inner')

    # to convert UTC timestamp to IST timestamp.
    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
    df['timestamp'] = df['timestamp'].astype(str).str[:-6]

    # to find the max value from low columns to get the limit price for current day trading.
    df['limit_price'] = df.low.rolling(rolling_candle, win_type=None).min()          # removing this for now. closed="left"

    # to check the SPREAD of sma_green and sma_red. And round up with 2 decimals float number.
    df['SMA_SPREAD'] = df['sma_green'] - df['sma_red']
    df = df.dropna(subset=['SMA_SPREAD'])
    # df['SMA_SPREAD'] = df['SMA_SPREAD'].round(decimals=0).astype(int)

    # to check Supertrend Buy or Sell.
    df['SUPERTREND'] = np.where(df['SUPERTd_3_3.0'] == 1, "BUY", "SELL")

    # calls the candle function to find the RED or GREEN Candle.
    df['candle'] = df.apply(find_candle, axis=1)

    def sma_trend(df):
        if (df['sma_green'] > df['sma_red'] or df['sma_green'] < df['sma_red']) and -1.00 <= df['SMA_SPREAD'] <= 1.00:
            return "Sideways"
        elif df['sma_green'] > df['sma_red']:
            return "Uptrend"
        elif df['sma_green'] < df['sma_red']:
            return "Downtrend"

    df['sma_trend'] = df.apply(sma_trend, axis=1)

    # to clean up the data. Required columns can be re-enabled back again when needed.
    df.drop(['SUPERTl_3_3.0', 'SUPERTd_3_3.0', 'SUPERTs_3_3.0'], axis=1, inplace=True)

    # to round up with 2 decimal value for all the columns in the df.
    columns = ['open', 'high', 'low', 'close', 'ha_ohlc4', 'sma_green', 'sma_red', 'SMA_SPREAD', 'SUPERT_3_3.0']
    df[columns] = df[columns].round(2)
    df = df.rename(columns={'open': 'ha_open', 'high': 'ha_high', 'low': 'ha_low', 'close': 'ha_close', 'SUPERT_3_3.0': 'st_limit_price'})
    df.reset_index(inplace=True, drop=True)
    return df


def fyers_find_limit_price(df, symbol):
    sma_red = round_up_price(price=df['sma_red'].iloc[-1])
    prv_low = round_up_price(price=df['ha_low'].iloc[-2])
    print("sma_red is ===>", sma_red)
    print("prv_low is ===>", prv_low)
    return sma_red if sma_red < prv_low else prv_low


def find_swing_trades(df, symbol, trading_strength):
    # trading_quantity = []
    print("Symbol is =====> ", symbol)
    if trading_strength == "HIGH":
        print("\nExecuting Candlestick Pattern check: 3g2r")
        print("Expected Trend Pattern: ")
        expected_ha_3g2r = np.array([["GREEN"], ["GREEN"], ["GREEN"], ["RED"], ["RED"]])
        for x in expected_ha_3g2r: print(x, end=' ')
        print("\nCurrent Candlestick Trend: ")
        tail_arr = df[["candle"]].to_numpy()
        tail_arr = tail_arr[-5:]
        for x in tail_arr:
            print(x, end=' ')
        comparison = tail_arr == expected_ha_3g2r
        pattern = comparison.all()
        print("=", pattern)

        if pattern == True:
            percent = 5
            allocation = fyers_get_allocation(symbol=symbol, fund=round(int(fyers_get_funds())), percent=percent)
            allocated_qty = round(allocation[0])
            # trading_quantity.append(allocated_qty)
            # trading_quantity = sum(trading_quantity)
            # print("trading_quantity is ====>", trading_quantity)
            allocated_fund = round(allocation[1])
            side = "BUY"
            limit_price = fyers_find_limit_price(df=df, symbol=symbol)
            return symbol, allocated_qty, allocated_fund, side, percent, limit_price

    if (trading_strength == "LOW") | (trading_strength == "HIGH"):
        print("\nExecuting Candlestick Pattern check: 2g3r")
        print("Expected Trend Pattern: ")
        expected_ha_2g3r = np.array([["GREEN"], ["GREEN"], ["RED"], ["RED"], ["RED"]])
        for x in expected_ha_2g3r: print(x, end=' ')
        print("\nCurrent Candlestick Trend: ")
        tail_arr = df[["candle"]].to_numpy()
        tail_arr = tail_arr[-5:]
        for x in tail_arr:
            print(x, end=' ')
        comparison = tail_arr == expected_ha_2g3r
        pattern = comparison.all()
        print("=", pattern)

        if pattern == True:
            percent = 10
            allocation = fyers_get_allocation(symbol=symbol, fund=round(int(fyers_get_funds())), percent=percent)
            allocated_qty = round(allocation[0])
            # trading_quantity.append(allocated_qty)
            # trading_quantity = sum(trading_quantity)
            # print("trading_quantity is ====>", trading_quantity)
            allocated_fund = round(allocation[1])
            side = "BUY"
            limit_price = fyers_find_limit_price(df=df, symbol=symbol)
            return symbol, allocated_qty, allocated_fund, side, percent, limit_price

    if pattern == False:
        return "NOACTION"



# [this is working fine]
def fyers_place_order(symbol, qty, type, side, productType, stopPrice=0, limitPrice=0):
    side = 1 if side == "BUY" else -1
    if type == "MO":
        type = 2
    if type == "LO":
        type = 1
    if type == "SLM":
        type = 3

    data = {
        "symbol": symbol,
        "qty": qty,       # REMEMBER to change this to variable "qty".
        "type": type,      # 2 represents market order and 1 means limit order.
        "side": side,      # REMEMBER to change this to variable "side".
        "productType": productType,
        "limitPrice": limitPrice,     #fyers_get_quote(symbol=symbol)
        "stopPrice": stopPrice,
        "validity": "DAY",
        "disclosedQty": 0,
        "offlineOrder": "False",
        "stopLoss": 0,
        "takeProfit": 0
    }
    print(data)
    response_code = place_order_res['code']
    response_message = place_order_res['message']
    order_id = place_order_res.get('id', int)
    if response_code == -174 or response_code == -392 or response_code == -99:
        print("Exiting program due to: ", response_message)
        exit_program(code=response_code, message=response_message)     # should not exit if order fails due to invalid limitprice or due to less fund. instead it should close only the thread.
        return symbol, order_id

    elif order_id is not None and response_code == 1101:
        side = "Buy" if side == 1 else "Sell"
        type = "MarketOrder" if type == 2 else "LimitOrder"
        message = "%s Placed : %s order for the stock %s with %s quantity." %(type, side, symbol, qty)
        send_tele_msg(message=message)
        return symbol, order_id


# [this is working fine]
def fyers_get_order_status(order_id):
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

    data = {"order_id": order_id}

    order_status_code = order_status_res.get('code')
    order_status_msg = order_status_res.get('message')

    while order_status_code != 200:
        trade_wait = 30
        send_tele_msg(message="ERROR: Unexpected response: " + order_status_msg)
        time.sleep(trade_wait)
        if order_status_code == 200:
            break

    order_id = order_status_res['orderBook'][0]['id']
    order_status = order_status_res['orderBook'][0]['status']
    if order_status == 2:
        order_status = "Filled"
    elif order_status == 5:
        order_status = "Rejected"
    elif order_status == 6:
        order_status = "Pending"
    if order_status == 2:
        order_status = "Cancelled"

    order_symbol = order_status_res.get('orderBook')[0]['symbol']
    order_datetime = order_status_res['orderBook'][0]['orderDateTime']
    order_qty = order_status_res['orderBook'][0]['qty']
    order_message = order_status_res['orderBook'][0]['message']
    order_limitPrice = order_status_res['orderBook'][0]['limitPrice']
    order_tradedPrice = order_status_res['orderBook'][0]['tradedPrice']
    order_side = order_status_res['orderBook'][0]['side']
    order_side = "BUY" if order_side == 1 else "SELL"

    return order_id, order_status, order_symbol, order_datetime, order_qty, order_message, order_limitPrice, order_tradedPrice, order_side


# [this is working fine]
def exit_program(code, message):
    '''
    code: 1101, message: Order Submitted Successfully.
    code: -174, message: System is not connected to NSE Equity market
    code: -392, message: Price should be in multiples of tick size.
    code: -8, message: Your token has expired. Please generate a token
    :param code: code you received from the place order function
    :param message: message you received from the place order function
    :return: sends notification and terminates the program with reason.
    '''
    if code == -174 or code == -392 or code == -8 or code == -99:
        send_tele_msg(message="EXITING PROGRAM: " + message)
        quit()
    elif code == "x":
        send_tele_msg(message="EXITING PROGRAM: "+ message)
        quit()


# [this is working fine]
def fyers_get_allocation(symbol, fund, percent):
    quote = fyers_get_stock_quote(symbol=symbol)
    allocated_fund = (fund / 100) * percent
    qty = allocated_fund / quote
    qty = round(int(qty))
    return qty, allocated_fund


# [this is working fine]
def fyers_get_stock_quote(symbol):
    data = {
        "symbols": symbol
    }
    stock_quote = fyers.quotes(data=data)
    stock_quote = stock_quote.get('d')[0]['v']['lp']
    return stock_quote


# [this is working fine]
def fyers_get_report(report):
    if report == "positions":
        fyers_position_resp = fyers.positions()
        print("fyers_position_resp is : ", fyers_position_resp)

        if fyers_position_resp['code'] != 200:
            message = "Error in response: %s" %(fyers_position_resp['message'])
            send_tele_msg(message=message)
        else:
            if not fyers_position_resp['netPositions']:
                message = "Position Report: There is no trades for today."
                send_tele_msg(message=message)
            else:
                net_position = fyers_position_resp['netPositions']
                position_list = []

                # to parse position response.
                for position in net_position:
                    symbol = position['symbol']
                    qty = position['qty']
                    side = "BUY" if position['side'] == 1 else "SELL"
                    pl = position['pl']
                    buyQty = position['buyQty']
                    sellQty = position['sellQty']
                    buyAvg = position['buyAvg']
                    sellAvg = position['sellAvg']
                    ltp = position['ltp']

                    key = ["Today's position", 'qty', 'side', 'buyQty', 'buyAvg', 'sellQty', 'sellAvg', 'ltp', 'pl']
                    value = [symbol, qty, side, buyQty, buyAvg, sellQty, sellAvg, ltp, pl ]
                    position = dict(zip(key, value))
                    position_list.append(position)

                # to convert position json response to dataframe object.
                df = pd.DataFrame.from_dict(position_list)

                try:
                    # to covert dataframe to html object.
                    hti = Html2Image()
                    html = df.to_html()
                    # text_file = open("/Users/sunilkumar/ksunilt/trading_bot/trade-assist/index.html", "w")
                    # text_file.write(html)
                    # text_file.close()
                    css = 'body {background: lightblue}'
                    # css = """
                    # <style>
                    #     table, td, th {
                    #         border: 1px solid;
                    #         padding: 15px;
                    #     }
                    #     table {
                    #         border-collapse: collapse;
                    #         text-align: center;
                    #     }
                    #     th, td {
                    #         padding: 8px;
                    #     }
                    # </style>"""

                    # to take screenshot of the table and sent to user via telegram.
                    hti.screenshot(html_str=html, css_str=css, save_as='positions_table.png', size=(550, 150))
                    ImageFile = '../trade-assist/strategy/positions_table.png'
                    send_tele_image(ImageFile=ImageFile)
                except Exception:
                    pass
                return df

    elif report == "holdings":
        fyers_holdings_resp = fyers.holdings()
        print("fyers_holdings_resp is : ", fyers_holdings_resp)
        if fyers_holdings_resp['code'] != 200:
            message = "Error in response: %s" %(fyers_holdings_resp['message'])
            send_tele_msg(message=message)
        else:
            if not fyers_holdings_resp['holdings']:
                message = "Holdings Report: There is no current holdings."
                send_tele_msg(message=message)
            else:
                net_holdings = fyers_holdings_resp['holdings']
                holdings_list = []

                # to parse holdings response.
                for holdings in net_holdings:
                    symbol = holdings['symbol']
                    holdingType = holdings['holdingType']
                    quantity = holdings['quantity']
                    costPrice = holdings['costPrice']
                    marketVal = holdings['marketVal']
                    pl = holdings['pl']
                    ltp = holdings['ltp']

                    key = ['Current_Holdings', 'holding_Type', 'quantity', 'cost_Price', 'market_Val', 'pl', 'ltp']
                    value = [symbol, holdingType, quantity, costPrice, marketVal, pl, ltp,]
                    holdings = dict(zip(key, value))
                    holdings_list.append(holdings)

                # to convert holdings json response to dataframe object.
                df = pd.DataFrame.from_dict(holdings_list)

                try:
                    # to covert dataframe to html object.
                    hti = Html2Image()
                    html = df.to_html()
                    css = 'body {background: lightblue}'

                    # to take screenshot of the table and sent to user via telegram.
                    hti.screenshot(html_str=html, css_str=css, save_as='holdings_table.png', size=(600, 150))
                    ImageFile = '../trade-assist/strategy/holdings_table.png'
                    send_tele_image(ImageFile=ImageFile)
                except Exception:
                    pass
                return df

    elif report == "pnl":
        total_pnl = []
        fyers_position_resp = fyers.positions()

        fyers_holdings_resp = fyers.holdings()

        pnl_list = []
        if fyers_position_resp['code'] != 200 and fyers_holdings_resp['code'] != 200:
            message = "Error in response: %s" %(fyers_holdings_resp['message'])
            send_tele_msg(message=message)
        else:
            print(fyers_position_resp['overall']['count_total'])
            if fyers_position_resp['overall']['count_total'] == 0:
                message = "PNL Report: There is no positions for today."
                send_tele_msg(message=message)
            else:
                position_pnl = fyers_position_resp['overall']['pl_total']
                pnl_list.append(position_pnl)

            if not fyers_holdings_resp['holdings']:
                print("There is no current holdings.")
            else:
                overall_holdings = fyers_holdings_resp['overall']
                total_investment = overall_holdings['total_investment']
                total_current_value = overall_holdings['total_current_value']
                holdings_pnl = overall_holdings['total_pl']
                pnl_perc = overall_holdings['pnl_perc']
                pnl_list.append(holdings_pnl)

        pnl = round(sum(pnl_list))
        key = ['position_pnl', 'holdings_pnl', 'total_pnl', 'total_investment', 'total_current_value', 'holdings_pnl', 'holdings_pnl_perc']
        value = [position_pnl, holdings_pnl, pnl, total_investment, total_current_value, holdings_pnl, pnl_perc]
        pnl_report = dict(zip(key, value))
        send_tele_msg(message=pnl_report)



# to read the favourite stock from reference data
def get_stocks_in_radar(holdings):
    holdings_list = holdings
    if fav_stock == "ENABLED":
        fav_stock_list = read_fav_stock(filename=fav_stock_file)
        stock_list = list(set(holdings_list + fav_stock_list))
        message = "MESSAGE: FAV STOCK ===> ENABLED\nStocks in Radar ===> %s" %(stock_list)
        send_tele_msg(message=message)
        return stock_list
    elif fav_stock == "DISABLED":
        message = "MESSAGE: FAV STOCK ===> DISABLED\nStocks in Radar ===> %s" %(holdings_list)
        send_tele_msg(message=message)
        return holdings_list
