from fyers_trade_utility import *
from telegram_utility import send_tele_msg


ref_hld_stock = []
ref_hld_res = []
fund_available = None
ref_qty = None

if __name__ == "__main__":
    # to get the current holding stock details.
    ref_hld_stock.append(fyers_get_holdings())
    print("Holding stock: ", ref_hld_stock)
    try:
        msg = ", ".join(ref_hld_stock)
        send_tele_msg(msg="Holding stock: " + msg)
    except Exception as e:
        print("Error found in holdings function", e)


    # to get the fund details.
    funds = fyers_get_funds()
    print("Fund balance: ", funds)
    try:
        msg = str(funds)
        send_tele_msg(msg="Fund balance: " + msg)
    except Exception as e:
        print("Error found in holdings function", e)


    if len(ref_hld_stock) > 0:
        trade_wait = 20          # should this be configurable ? check accordingly.

        # for each symbol in holding stock
        for stock in ref_hld_stock:
            holding_symbol_ohlc = get_ohlc(stock=stock, data_resolution="60", days=60)
            holding_symbol_HA = find_heikin_ashi(df=holding_symbol_ohlc)
            symbol_datapoints = get_datapoints(df=holding_symbol_HA, show_rows=20, sma_yellow=4, sma_red=2, rolling_candle=3)     # for day_chart=sma 15/5 hourly_chart=SMA 3/2


            place_order_res = fyers_place_order(symbol=stock, df=symbol_datapoints)      # REMINDER - add this paramater to the function after testing. df=symbol_datapoints.
            print("place_order_res is -->", place_order_res)        # output is ('NSE:ZOMATO-EQ', 61, None, '122082997824')
            ordered_symbol = place_order_res[0]
            limit_price = place_order_res[1]
            side = place_order_res[2]
            order_id = place_order_res[3]

            order_status_res = fyers_order_status(order_id)
            print("order_status_res is -->", order_status_res)      # output is ('122082997824', 2, 'NSE:ZOMATO-EQ', '16-Sep-2022 14:03:01', 5, 10, 'BUY')
            ref file to capture order and trade details.
            ref_order_capture = "/Users/sunilkumar/ksunilt/trading_bot/sk_bot/refrence_data/ref_order_capture.txt"
            ref_trade_capture = '/Users/sunilkumar/ksunilt/trading_bot/sk_bot/refrence_data/ref_trade_capture.json'
            ref_qty_capture = '/Users/sunilkumar/ksunilt/trading_bot/sk_bot/refrence_data/ref_qty_capture.txt'
            when we get the response from the order placement. print response from fyers_place_order. 3 items.
            if place_order_res is not None:
                print(place_order_res)      # what if order id is null. need to handle as per the message
            
                order_id = place_order_res[0]
                print(order_id)
                time.sleep(trade_wait)
            
                order_status_res = fyers_order_status(id=order_id)
                print("order_status_res is first : ", order_status_res)
                print("order_status_res is ---->", order_status_res)
                print("order_status_res[1] is ----> ", order_status_res[1])
                
                if order_status_res[1] == 6:
                    while order_status_res[1] == 6:
                        print("Order is still pending.. checking status again for order id :", order_id)
                        order_status_res = fyers_order_status(id=order_id)
                        print("order_status_res is pending : ", order_status_res)
                        time.sleep(trade_wait)
                        if order_status_res[1] != 6:
                            break
                if order_status_res[1] == 2:
                    print("order_status_res is filled : ", order_status_res)


                    print("Order is filled")
                    print("ref_qty from swing strategy:", ref_qty)
                    ref_qty = order_status_res[3]
                    print("ref_qty from swing strategy:", ref_qty)
                elif order_status_res[1] == 5:
                    print("Order is rejected")
                elif order_status_res[1] == 1:
                    print("order_status_res is cancelled : ", order_status_res)
                    print("Order is cancelled")


    position_res = fyers_position()
    print(position_res)     # symbol, net_qty, profit, avg_price

    pnl = fyers_get_pnl(stk='NSE:ZOMATO-EQ')
    print(pnl)


