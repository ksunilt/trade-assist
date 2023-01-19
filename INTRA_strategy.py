from utility.fyers_trade_utility import *
from utility.telegram_utility import send_tele_msg
import datetime
import threading
from time import sleep
from threading import *
import pandas as pd


def swing_strategy(symbol):
    print("\n\n============================================================== STOCK REPORT ==============================================================")
    report = fyers_get_datasets(strategy="SWING", symbol=symbol, data_resolution="1D", days=200)


    print("=============================== BUY/SELL Logic ===============================")
    buy_signal = find_swing_trades(df=report, symbol=symbol, trading_strength=trading_strength)
    print("buy_signal is ====> ", buy_signal)
    # buy_signal = ('NSE:ZOMATO-EQ', 8, 561, 'BUY', 30)
    # ('NSE:ZOMATO-EQ', 8, 561, 'BUY', 30)

    if buy_signal == "NOACTION":
        no_action_stocks.append(symbol)

    elif buy_signal != "NOACTION":
        symbol = buy_signal[0]
        # allocated_qty = buy_signal[0]
        allocated_qty = 1
        print("allocated_qty hardcoded to : %s for testing. " %(allocated_qty))
        allocated_fund = buy_signal[2]
        side = buy_signal[3]
        percent = buy_signal[4]
        limitPrice = buy_signal[5]
        print(symbol, allocated_qty, allocated_fund, side, percent, limitPrice)
        # return symbol, allocated_qty, allocated_fund, side, percent, limitPrice
        order_resp = fyers_place_order(symbol=symbol, qty=allocated_qty, type="LO", side=side, productType="CNC", stopPrice=0, limitPrice=limitPrice)
        print("order_resp is ====> ", order_resp)
        # ('NSE:ZOMATO-EQ', '122120252634')

        if order_resp != None:
            symbol = order_resp[0]
            order_id = order_resp[1]
            order_status = fyers_get_order_status(order_id=order_id)
            print("order_status is ====> ", order_status)
            # ('122120252634', 'Filled', 'NSE:ZOMATO-EQ', '02 Dec 2022 11:57:33', 1, 'TRADE CONFIRMED', 0.0, 64.0, 'BUY')





if __name__ == "__main__":
    # to read configuration.
    config_main = '../trade-assist/config/config_main.yml'
    with open(config_main, 'r') as config_main:
        cfg = yaml.load(config_main, Loader=SafeLoader)


    # to parse configuration.
    fav_stock = cfg['trading_strategy']['fav_stock']
    fav_stock_file = cfg['trading_strategy']['fav_stock_file']
    stock_report_path = cfg['trading_strategy']['stock_report_path']

    # to validate login.
    print("\n====================================== LOGIN VALIDATION ======================================\n")
    login_validation = fyers_login()
    if login_validation['code'] != 200:
        count = 0
        while count < 3:
            message = "MESSAGE: LOGIN -> Trade-Assist Login Validation is Failure\nRerunning the login job..."
            sleep(10)
            print(fyers_login())
            count += 1
            sleep(10)
            break
    elif login_validation['code'] == 200:
        message = "MESSAGE: LOGIN -> Trade-Assist Login Validation is GREEN"
        send_tele_msg(message=message)
        sleep(10)
        pass

    print("\n====================================== FUND BALANCE ======================================\n")
    # to fetch fund balance from fyers.
    fund_balance = fyers_get_funds()
    message = "MESSAGE: FUND -> Balance is %s" %(fund_balance)
    send_tele_msg(message=message)

    print("\n====================================== HOLDING REPORT ======================================\n")
    # to fetch holdings reports.
    holdings_df = fyers_get_report("holdings")


    # to add additional columns for holdings report.
    message = "MESSAGE: Holdings -> generating holdings report...[This is reading from csv file. ]"
    send_tele_msg(message=message)
    holdings_df['curr_points'] = round(holdings_df['ltp'] - holdings_df['cost_Price'])
    holdings_df['expected_points'] = round(holdings_df['cost_Price'] / 100 * 10)
    holdings_df['stop_loss'] = np.where(holdings_df['curr_points'] > holdings_df['expected_points'], "YES", "NO")
    # print(holdings_df)


    message = "MESSAGE: Holdings SL -> Finding SL Trades for holding report..."
    send_tele_msg(message=message)
    holdings_sl_df = holdings_df.loc[holdings_df['stop_loss'] == "YES"]
    print(holdings_sl_df)


    curr_date = date.today().strftime("%d%m%Y")
    holdings_df.to_csv("../trade-assist/reference_data/holdings_report/holdings_" + curr_date + ".csv", index=True)
    holdings_list = holdings_df['Current_Holdings'].tolist()
    holdings_list = [*set(holdings_list)]
    message = "\nMESSAGE: Holdings List -> %s" %(holdings_list)
    send_tele_msg(message=message)

    print("\n============================================================================ PLACING SL ORDERS FOR HOLDING STOCKS ============================================================================\n")
    # sl_result_list = []
    # no_sl_result_list = []
    if not holdings_sl_df.empty:
        sl_table = holdings_sl_df.groupby(by='Current_Holdings').sum(numeric_only=True)
        sl_table = sl_table.filter(items=["Current_Holdings", "quantity"], axis=1)
        sl_dict = sl_table.to_dict()

        for sl_stocks in sl_dict.values():
            sl_result_list = []
            sl_result_dict = {}

            for hld_stock, quantity in sl_stocks.items():
                fyers_place_sl_order_resp = fyers_place_sl_order(df=holdings_sl_df, sl_stock=hld_stock, quantity=quantity, previous_low=-2)
                # print("fyers_place_sl_order_resp  is ---> ", fyers_place_sl_order_resp)
                print("\n=============================================================================\n")

                if type(fyers_place_sl_order_resp) == list:
                    for holdings in range(len(fyers_place_sl_order_resp)):
                        symbol = fyers_place_sl_order_resp[holdings]['symbol']
                        status = fyers_place_sl_order_resp[holdings]['status']
                        sl_result_dict = {**sl_result_dict, symbol: status}
                        sl_result_list.append(sl_result_dict)
            print("sl_result_dict is ======> ", sl_result_dict)
            print("******************************************************************** SL ORDER EXECUTION SUMMARY ***********************************************************************")
            for key, value in sl_result_dict.items():
                k = key
                v = value
                message = "SL Order for %s is %s" %(k, v)
                send_tele_msg(message=message)


    # working on stocks in radar fuction.
    print("\n============================================================================ DATASETS FOR RADAR STOCKS ============================================================================\n")
    radar_response = get_stocks_in_radar(holdings=holdings_list)

    threads = []
    no_action_stocks = []
    for stock in radar_response:
        # print("\n============================================================================ STOCK ANALYSIS and ORDER PLACEMENT ============================================================================\n")
        swing_strategy(symbol=stock)

    fyers_get_report(report="positions")
    fyers_get_report(report="holdings")
    fyers_get_report(report="pnl")


