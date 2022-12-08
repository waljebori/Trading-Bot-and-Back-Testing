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
api_key = 
api_secret =
client = Client(api_key, api_secret, tld='us')
#######################################################################################################
#Variable initializations
#"25 Sep, 2019" is the earliest date available for USDT and USD
klines = client.get_historical_klines("BTCUSD", Client.KLINE_INTERVAL_15MINUTE, "25 Sep, 2019")#Return all klines
#print(type(klines)) #confirmed type is list


with open("15MinuteKLineCache250919_031222.json", "w") as outfile:
    json.dump(klines, outfile)
