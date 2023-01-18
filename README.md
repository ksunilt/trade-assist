Built With - 
  Python3

Prerequisites - 
1. Telegram API
2. Fyers broker API

Objective : The objective of this program is to get the perform swing trading stragegy with an automated approach with no manual intervention. 

The app has below features :
1.	Generates SGX Nifty status report to know the market trend in advance. 
2.	Fully automated login process to get the token for the trading session.
3.	Pre-open market data report to Identify the Gapup and Gapdown stocks for the day.
4.	Identify the holding stocks and place stop loss orders based on Heikin Ashi chart and also refer favourite stocks list to find buying opportunity. 
5.	The app can identify and generate the data points like SuperTrend, Simple Moving Average based on Daily OHLC data for the stocks. Buy orders will be placed with SMA_low crossover SMA_high and quantity is determined based on price action method or candle patterns. 
6.	Fund allocation is handled on a predefined percentage based on the candlestick pattern. 
7.	Sends trade event notifications and trade reports to the telegram app so that the user is aware of the ongoing events and status of the orders placed. 


Function Usage :

Fyers_auth.py
Fyers auth is to authenticate your access with fyers broker and this needs to be run before the trading session preferably before 9:AM IST. and save the access token in the token file which is valid for the current day. 

- generate_auth_token:
    The function is to generate authorisation token from your fyers app.
    You will be redirected to the fyers using browser where you have to put you login and paswd.
    
- generate_access_token:
    The function uses the Authorisation token from fyers and get the access token and calls write_token_file function to write the token in txt file.

- fyers_connect:
    Function to read the token from .txt file and connect to fyers app.
    This function can be used to called by other parent functions to perform some action in fyers.

- validate_login:
    Connect to fyers api to validate the connection.

- get_quotes:
    Function to get the quotes for the stock listed in the file from fyers.



sgx_nifty.py
At 08:30 AM we run the sgx nifty to find sgx value is negative or positive. This is to forcast the NIFTY direction for the current day. 
- fetch_sgx:
    The function uses beautifulsoup to scrap sgxnifty to get current day values. 
    Notificaiton will be sent to the telegram user about the positive and negative trends.  



pre_open_report_generation.py - 
This generates a excel report at 09:10 AM after the pre-auction and before the trading session at 09:15 AM. This helps in finding out the GAPUP and GAPDOWN stocks based on the IEP value. 
- Class NSEIndia:
- get_pre_open_market_data:
    The Class is used to connect to NSE India to fetch the Pre-Open Market. 
    The function get_pre_open_market_data will fetch NIFTY 50 (Also you can opt for NIFTY, BANKNIFTY, FNO)
    Saves csv and excel file in the report folder. 
    Sends a notification to the telegram. 
    
- holidays: (WORK IN PROGRESS)
    The function is used to get the trading and clearing holiday dates for the current year. 

- find_stock_to_trade:
    function to find the top gapup and gapdown stocks, within defined price range to trade. And sends notification to telegram.



awsome_strategy.py - 
- find_trade: (WORK IN PROGRESS)
    The function is used to generate the BUY and SELL signal for the stock. 
    The function will connect to fyers api to get the OHLC of the stock and keep updating the DataFrame. 
    It uses Ta-lib to find the (Simple Moving Average) SMA5 and SMA34 days similar to Awsome Oscillator. 
    It uses Ta-lib to find RSI14.
    It uses pandas-ta to find SuperTrend 7,3 and all these data points will be concatenated with the dataframe. 
    
    Example below - 
    <img width="1408" alt="image" src="https://user-images.githubusercontent.com/55142193/172527237-d97d378e-adba-40a5-8ea3-cdbd6a24f3ec.png">

    
- placeOrder: (WORK IN PROGRESS)
    The function will be called by the find_trade to place the orders in fyers based on the BUY/SELL signal. 
   
