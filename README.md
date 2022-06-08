Built With - 
  Python3

Prerequisites - 
1. Telegram API
2. Fyers broker API

Objective - 
- The objective of this program is to get the trading datapoint that helps you to know if the current day trend of the market if its Positive or Negative. 
- The program also helps in finding out the Gapup and Gapdown stocks from NSE India for the current day and trade on generate BUY and SELL signals for the stocks. 
- All the status will be communicated to the use via Telegram API. 

-- Function Usage --

Fyers_auth.py
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







Awsome Strategy - 
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
   
