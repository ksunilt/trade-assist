Built With - 
  Python3


Prerequisites - 
1. Telegram API
2. Fyers broker API


Technologies/modules used :
1.	Pandas, Numpy, Math, TA-lib and pandas_ta – to generate datapoints like Simple Moving Average, ATR, spread and trend of the market etc to generate buy signal. 
2.	Html2image, - to convert html to image and send it via telegram. 
3.	Beautifulsoup, yaml and requests – for web scrapping and to send request for generating reports. 
4.	Fyers Broker api to perform actual trading activity and telegram api to send notification on events and reports. 


Objective : 
    The objective of this program is to get the perform swing trading stragegy with an automated approach with no manual intervention. 

The app has below features :
1.	Generates SGX Nifty status report to know the market trend in advance. 
2.	Fully automated login process to get the token for the trading session.
3.	Pre-open market data report to Identify the Gapup and Gapdown stocks for the day.
4.	Identify the holding stocks and place stop loss orders based on Heikin Ashi chart and also refer favourite stocks list to find buying opportunity. 
5.	The app can identify and generate the data points like SuperTrend, Simple Moving Average based on Daily OHLC data for the stocks. Buy orders will be placed with SMA_low crossover SMA_high and quantity is determined based on price action method or candle patterns. 
6.	Fund allocation is handled on a predefined percentage based on the candlestick pattern. 
7.	Sends trade event notifications and trade reports to the telegram app so that the user is aware of the ongoing events and status of the orders placed. 


::: File Usage :::

File name : authendication/fyers_authentication.py
    - This is a automated login approach. It helps in generating the auth token on every day basis which is valid for the current trading session. This script will be executed as per the schedule on a daily basis and creates a token file that will be used by all the api functions in the trading events. The file fyers_login_crontab.py will be executed by the crontab as per the schedule. All the login details to be provided in the configuration file. 


File name : pretrade/pre_open_market/pre_open_report_generation.py
    - This script is responsible to generate the pre-open market data from NSE site to find out the top gap-up and gap-down stocks. Reports can be generated to multiple segments like FNO, BANKNIFTY or EQUITY cash. The report is scheduled by a cronjob and will be executed as per the schedule and should be scheduled immediately after the auction market and before the actual trading session ie,. 9:10 AM IST. 
    
    
File name : sgx_nifty.py
    - SGX reports is responsible to geenrate the SGX Nifty status on daily basis and send out the reports to the user. It help the user to predict the tend in the current market to know if the market is going to be negative or positive. The report will be executed by the cronjob as per the schedule. 
    

File name : ref_fav_stock.json
    - The file has a list of favriote stocks that you wish to trade on. 
    
File name : INTRA_strategy.py
    - This file is the main file that will be executing the trading activity. 
    
File name : fyers_trade_utility.py
    - This file has all the functions necessary to perform the swing trading and each functions will be called by the main file. 
    
File name : telegram_utility.py
    - This file contains functions that is required to send telegram messages and notifications to the end user. 
    
Application Flow --
1. Scheduled SGX report will be generated at 8:30 AM IST.
2. Fyers login process will kickstart at 8:45 AM IST to get the auth token which is valid for 24 hours. 
3. Pre-open market report will be executed as per the schedule at 9:10 to find the gapup and gapdown stocks. 
4. Strategy will be executed at 9:30 AM IST to find the buying opportunity. 
    - Lists out the holdings and place stop loss for the holding stock. SL Price will be determinded based on the existing porfit and candle stock pattern. 
    - Checks the Fund balance and if there is no enough fund, then the program terminates. 
    - Generate OHLC data for all the stocks in holdings and in favriote stocks. OHLC will be converted into Heikin Ashi to reduec the noise in candles. 
    - Generates datasets for the stock SMA long, SMA short, stock trend, ART.
    - Based on the candle pattern and price action determines the BUY signal. 
    - Quantity is determinded based on the candle patterns. 
    - Fund will be allocated based on the predefined percentaged which is again based on the candle pattern. 
    - Limit price is determinded based on the previous day low. 
    - If a stock has a buy signal then limit orders are placed and order status are checked in a loop untill its filled. 
    - Stocks that are not elegible for buy will be appended to a list that will be pick up again aftr a specific interval to find the buy signals. 
    - Position, holdings, pnl Report will be generated and sent to end user for the current day.  
  
  
Example of Dataset : 
  ![image](https://user-images.githubusercontent.com/55142193/213401932-4a61591d-ffe4-4558-a1bc-86afae2e8772.png)


Example of BUY logic :
  ![image](https://user-images.githubusercontent.com/55142193/213402231-75a2e26a-bd77-4a37-8f4a-a596101dfa62.png)


