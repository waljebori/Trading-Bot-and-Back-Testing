#Creating a local cache of EMA values and storing into a JSON file
#https://www.reddit.com/r/algotrading/comments/l6p1mb/trouble_with_ema_calculation/   Useful link
#Libraries
import urllib.parse
import hashlib
import hmac
import requests
import time
from time import sleep
from datetime import datetime
from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
import statistics
import json
#######################################################################################################
#APIkey
api_key = '' #Add these
api_secret = '' #Add these
client = Client(api_key, api_secret, tld='us')
#######################################################################################################
#Variable initializations
#"25 Sep, 2019" is the earliest date available for USDT and USD
klines = client.get_historical_klines("BTCUSD", Client.KLINE_INTERVAL_15MINUTE, "25 Sep, 2019")#Return all klines
EMA_values_dict = dict()
final_dict = dict()
close_prices = list()
period = 20
alpha = 2.0 / (period+1)
i = 0
#######################################################################################################
#Creating a list of all the closing prices and a dictionary with index as key and open timestamp as value
for candle in klines:
    close_prices.append(float(candle[4]))
    #EMA_values_dict[candle[0]] = float(candle[4]) #dictionary with unix opentime as key and close time as value
    EMA_values_dict[i] = list()
    EMA_values_dict[i].append(int(candle[0]))
    i+=1


#Using simple moving average of first period for first EMA value, since EMA values depend on prior EMA value
first_period_values = close_prices[0:period]
SMA_as_first_EMA = statistics.mean(first_period_values)


#Adding the EMA values to the dictionary
for i in range(len(close_prices)-1):
    if i<period:
        currEMA = 0
    elif i == period:
        currEMA = SMA_as_first_EMA
    else:
        currEMA = alpha*close_prices[i] + (1.0-alpha)*currEMA
    #print(str(currEMA))
    EMA_values_dict[i+1].append(currEMA) #Timing was off when comparing values to binance EMA values, i+1 offsets that

EMA_values_dict[0].append(0) #Since loop above starts at 1


#Convert the dictionary key to the timestamp, not an arbitrary index
for key, value in EMA_values_dict.items():
    final_dict[value[0]] = value[1] #Timestamp is the key, ema value is the value

#Outputting dictionary to a JSON file for future access
with open("15min_20EMA_25sep2019.json", "w") as outfile:
    json.dump(final_dict, outfile)

#This program has been tested for accuracy, EMA values are accurate within a few cents for BTC/USD

#Notes/initial planning
#1. Create Dictionary
#2. Add timestamp as key, associated EMA as value
#3. Use SMA for first EMA, since calculation is recursive
#Start with one month data, then test for accuracy. If accuracy ok, use 3 years for all backtesting scenarios
#Data sourcing options: Calculations using binance klines, not Alpha Vantage
#Will my own calculations be accurate? Is Alpha Vantage accurate?
########Compare my calculations with the binance chart values
#Data storing options: JSON file, not CSV
#Accuracy, simplicity, cost are factors to consider
#Import data/file as a dictionary in first few lines of backtesting.py
#timestamp is the key, EMA value is the value. Perhaps add datetime for own reference
#Option 1) Create a local copy of EMA price data. Unix timestamp in one column, ema price in the other
#Option 2) Calculate EMA data live in backtesting using the imported klines
#Option 3) Alpha Vantage
