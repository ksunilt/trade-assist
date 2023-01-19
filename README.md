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


::: File Usage :::

File name : authendication/fyers_authentication.py
    - This is a automated login approach. It helps in generating the auth token on every day basis which is valid for the current trading session. This script will be executed as per the schedule on a daily basis and creates a token file that will be used by all the api functions in the trading events. The file fyers_login_crontab.py will be executed by the crontab as per the schedule. All the login details to be provided in the configuration file. 


File name : pretrade/pre_open_market/pre_open_report_generation.py
    - This script is responsible to generate the pre-open market data from NSE site to find out the top gap-up and gap-down stocks. Reports can be generated to multiple segments like FNO, BANKNIFTY or EQUITY cash. The report is scheduled by a cronjob and will be executed as per the schedule and should be scheduled immediately after the auction market and before the actual trading session ie,. 9:10 AM IST. 
    
    
File name : pretrade/sgx_report/sgx_nifty.py
    - SGX reports is responsible to geenrate the SGX Nifty status on daily basis and send out the reports to the user. It help the user to predict the tend in the current market to know if the market is going to be negative or positive. The report will be executed by the cronjob as per the schedule. 
    

File name : reference_data/ref_fav_stock.json
    - The file has a list of favriote stocks that you wish to trade on. 
    
File name : strategy/INTRA_strategy.py
    - This file is the main file that will be executing the trading activity. 
    
File name : utility/fyers_trade_utility.py
    - This file has all the functions necessary to perform the swing trading and each functions will be called by the main file. 
    
File name : utility/telegram_utility.py
    
