#https://algotrading101.com/learn/binance-python-api-guide/    Extremely Valuable Resource
#https://python-tradingview-ta.readthedocs.io/en/latest/usage.html Import live TA data
#https://www.youtube.com/watch?v=3WIcaCMJoqA  YouTube video related to above
#The important thing here is that the data is accurate, constant/reliable, and fast to access.
# Deploy the strategy locally and monitor for issues for 1 week. Consider connecting with cloud server

#Most recent progress
#1. Rough draft basically completed, time to begin back-testing.
#2. How will I backtest? Will I use this program and/or a similar one? Or on PineScript or another software?


#To-be-developed:
#1. Function to determine if a candle is an IRB.  Reset IRB to 0 and wait 15 minutes (1 more candle) before testing again
#2. A signal function that tests for all the trade parameters and returns true only if all criteria are met
### Perhaps set signal as a global variable so it can be reset when a buy/sell function is executed
#3. Backtest before developing below functions, as you might not need all of them. Only ones with good results
#A) Function to determine if 1 hr 50 EMA is below 15 min 20 EMA
#B) Function to test if ADX above 30
#C) Function to find slope of EMAs
#4. Trailng stop-loss/rising profitTarget. PT based on TA perhaps
#5. Automated emails/alerts when a trade is entered with appropriate info

#Notes/To keep in mind:
#1. Maybe define minimum/maximum range between PT and SL for potentially large candles
#2. Perhaps use bitcoin balance to define if buy orders should be placed or not, instead of open orders Steps 4,6
#5. profit_target = IRB_high + (IRB_high - IRB_low)*1.5
#6. Quantity needs to be added to  buy order in Step 2. Use full USDT balance
#7. Consider using USD instead of USDT. USDT is not safe
#8. Add symbol and quantity as function parameters
#9. #The signal function needs to reset to zero after it is called

#################################################################################################
#Libraries
import urllib.parse
import hashlib
import hmac
#import base64
import requests
import time
from time import sleep
from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
#######################################################################################################
#APIkey
api_key = ''#Add these
api_secret = ''#Add these
client = Client(api_key, api_secret, tld='us')
#######################################################################################################

#Playground to run only a few lines
#######################################################################################################
#Test 1
# x=client.get_open_orders() #No open orders returns an empty list
# print(x)
# if x == []:
#     print("Equal to empty list") #This test was successful
# print("test")

#Test 2
# candle = client.get_klines(symbol='BTCUSDT', interval=Client.KLINE_INTERVAL_15MINUTE)
# print(candle[-1]) #returns 12 different parameters, search the below link for "1499040000000,// Open time"
# #https://github.com/binance-us/binance-us-api-docs/blob/master/rest-api.md#klinecandlestick-data
# most_recent_candle = candle[-1]


# quit()
# ffjnddkndjkdj #gibberish
# print("Test 2, I should not be seeing this")
#######################################################################################################


#Functions
#######################################################################################################
def place_buy_limit_order(order_symbol, order_quantity, order_price): #Consider adding all order parameters as function variables
#Order Parameters
#Side: BUY or SELL
#Type: LIMIT, MARKET, STOP_LOSS_LIMIT, TAKE_PROFIT_LIMIT, LIMIT_MAKER
#timeInForce:
    try:
        buy_limit = client.create_order(
            symbol=order_symbol,
            side='BUY',
            type='LIMIT',
            timeInForce='GTC',
            quantity=order_quantity,
            price=order_price)
        print("Buy limit order of {} {} succesfully placed".format(order_quantity, order_symbol)) #make quantity a function var
        return buy_limit

    except Exception as e:
        # error handling goes here
        print(e)
    except BinanceOrderException as e:
        # error handling goes here
        print(e)

def place_oco_sell_order(order_symbol, order_quantity, order_profit_target, order_stop_price, order_stop_sell_price):
    try:
        oco_sell_order = client.create_oco_order(
        symbol=order_symbol,
        side='SELL',
        quantity=order_quantity,
        price=order_profit_target,
        stopPrice=order_stop_price,
        stopLimitPrice=order_stop_sell_price,
        stopLimitTimeInForce='GTC')
        print("OCO sell order for {} {} succesfully placed with PT of {} and SL of {}".format(order_quantity, order_symbol, order_profit_target, order_stop_sell_price))
        return oco_sell_order

    except Exception as e: # error handling goes here
        print(e)
    except BinanceOrderException as e:
        print(e)

def get_changed_rounded_price(symbol_1, change_factor):

    if change_factor<0.01 or change_factor>1.99:
        print("Error, percentage is out of bounds. Use a number between 0.01 and 1.99")
        return None
    else: pass
    #btc_price_object = client.get_symbol_ticker(symbol="BTCUSDT")
    #print(btc_price_object["price"])
    symbol_price_object = client.get_symbol_ticker(symbol=symbol_1)
    symbol_price_string = symbol_price_object["price"] #This is the last traded price
    significant_figures = len(symbol_price_string.split('.')[1])-1
    #print(symbol_price_string, significant_figures)
    symbol_price_float = float(symbol_price_string)
    if symbol_1 == "BTCUSDT":
        symbol_changed = round(symbol_price_float*change_factor, 2)
    else:
        symbol_changed = round(symbol_price_float*change_factor, significant_figures)
    #print("price is", symbol_changed)
    return symbol_changed #make percentage change optional, set default to 1

def scan_for_IRB():
    return None #Returns either true or false. Must return 0 if the same IRB is called a second time
    candle = client.get_klines(symbol='BTCUSDT', interval=Client.KLINE_INTERVAL_15MINUTE) #call short timeframe to speed up algo maybe
#Needs to be tested more for consistency
    #print(candle[-1]) #returns 12 different parameters, search the below link for "1499040000000,// Open time"
    #https://github.com/binance-us/binance-us-api-docs/blob/master/rest-api.md#klinecandlestick-data
    most_recent_candle = candle[-1] #Verified to be true
    candle_open = most_recent_candle[1]
    candle_close = most_recent_candle[4]
    candle_high = most_recent_candle[2]
    candle_low = most_recent_candle[3]
    IRB_percent_limit = 0.45

    if most_recent_candle[0] == repetition_check_open_time: #Meaning this candle has already been checked
        return 0
    elif candle_high-max(candle_open, candle_close))/(candle_high-candle_low)>IRB_percent_limit:
        global IRB_high = candle_high
        global IRB_low = candle_low
        global repetition_check_open_time = most_recent_candle[0]
        return 1
    else:
        return 0
#Plan.
#1. Open web socket connection, or get most recent 15 minute candle from binance?
#2. Test if most recent candle is an IRB
#3. If it is, set parameters of global variables (IRB_high/entry price), IRB_low, profit_target, stop_loss)
#4. If not, return 0
#5. If the same IRB gets tested twice, return 0.
#   Perhaps we can compare the candle values used in the first test to those used in the second test







def signaltest(): #This function will take input from scan_for_IRB and the ADX/EMA slope functions to return
    pass          #either true or false
#######################################################################################################


#######################################################################################################
#Trade Parameters,
# entry = 17000
# profitTarget = 17200
# stopLoss = 16900
# IRB_candle_high = 17000 #This will be the price the buy order is placed at
#######################################################################################################


#######################################################################################################
#Function Calls for Testing
btc_99_percent = get_changed_rounded_price('BTCUSDT', 0.99)
btc_plus1_percent = get_changed_rounded_price('BTCUSDT', 1.01)
#sell_order_1 = place_oco_sell_order('BTCUSDT', 0.002, btc_plus1_percent, btc_99_percent, btc_99_percent)
bnb_99_percent = get_changed_rounded_price('BNBBTC', 0.99)
#print(bnb_99_percent)
buy_order_1 = place_buy_limit_order('BNBBTC', 0.01, bnb_99_percent)
print(buy_order_1)
print("Going to sleep, orders will cancel soon")
sleep(3)
cancel_buy = client.cancel_order(symbol='BNBBTC', orderId=buy_order_1['orderId'])
#cancel_sell = client.cancel_order(symbol='BTCUSDT', orderId=sell_order_1['orderId']) #doesn't work, figure out why
#######################################################################################################


#######################################################################################################
#Playing around to test API and its different endpoints
depth = client.get_order_book(symbol='BNBBTC')
RLC_balance = client.get_asset_balance(asset='RLC')
info = client.get_symbol_info('BTCUSDT') #checks to see if pair supports stop_limit order





#######################################################################################################
#High level plan/walk through
#1. Search for signal. IRBs come through every 15 minutes, if not modified
#2. Signal activated, place buy order
#3. If new IRB shows and order still open, cancel and place new order at new IRB high
#4. If order goes through, turn off signal searching and/or don't allow new buy orders.
#5. Place OCO sell order with PT & SL
#6. Once sell order executes, turn signal searching back on.
#7. Repeat
#######################################################################################################



#######################################################################################################
#High-level plan in code
while True:
#Step 1/2. Place signal function here perhaps. Perhaps use the sleep function so it isn't always searching and
######## using processing power. Perhaps also place the signal function at the bottom and/or elsewhere also
    while client.get_open_orders() == []:
        signal = signaltest()
        if signal == 0:
            sleep(900) #waits 15 minutes to retest the signal function/find an IRB
            continue
        elif signal == 1:
            signal = 0
            quantity = client.get_asset_balance(asset='USD') #We will be placing buy orders with all our USD
            entry = IRB_candle_high
            buy_order_1 = place_buy_limit_order('BTCUSDT', quantity, entry) #Opens order, breaks us out of loop
            break
#Step 1/2. Done. Order has now been placed


#Step 3. If new IRB and first order still unfilled, replace first order with new IRB_high, reset signal
#wait 15 minutes for new signal here maybe, or until the order executes
    minimum_fill_percent = 0.8 #If order is 80% placed, this loop won't execute and we move on to sell order
    i = 0 #loop index

    while buy_order_1['executedQty'] < minimum_fill_percent * buy_order_1['origQty']:
        if i == 0 and buy_order_1['executedQty'] > 0.2 * buy_order_1['origQty']:
            sleep(60) #if loop is being executed for the first time, wait 60 and recheck if order went through
            i = i + 1
            #Perhaps I can include an email alert here, so I can know what's up
            continue
        signal = signaltest() #The signal function needs to reset to zero after it is called
        if signal == 1 and client.get_open_orders() != []: #Change BTC_balance to %-based?
            cancel = client.cancel_order(symbol='BTCUSDT', orderId=buy_order_1['orderId'])
            quantity = client.get_asset_balance(asset='USD') #We will be placing buy order with remaining USD
            buy_order_1 = place_buy_limit_order('BTCUSDT', quantity, IRB_candle_high)
            signal = 0
        elif signal == 0:
            sleep(30) #Waiting for order to execute before checking loop condition again
            continue

    sleep(90) #Waiting 1.5 minutes for final 20% to execute before placing sell order
    #Cancel all open orders to clean house before sell order goes through.
#This is just a precaution, there shouldn't be any open orders
#open_orders = client.get_open_orders(symbol='BNBBTC')
#result = client.cancel_order(symbol='BNBBTC', orderId='orderId')


#Questions:
#Are we running an all or nothing model, or will we run multiple orders at once?
#Should partial fills be handled manually?
#How long should we wait from initial fill to final fill before alternative action
#Will a partially filled order mess with my sell order?
#Answers:
#Run the all or nothing model for now, don't waste too much time on these corner-cases. Fix them after deployment
#We can handle them manually/ignore them temporarily for the interest of time. Deploy ASAP
#Step 3. Done


#Step 4/5. Place OCO sell order with PT and SL once bitcoin is purchased. Don't allow new orders when OCO open
    risk_reward_ratio = 1.5
    profit_target = IRB_high + (IRB_high - IRB_low)*risk_reward_ratio
    stop_loss = IRB_low
    stop_loss_sell_price = stop_loss - 25 #Selling $25 less than the trigger. Optimize during backtesting


    sell_order_1 = place_oco_sell_order('BTCUSDT', quantity, profit_target, stop_loss, stop_loss_sell_price) #use round function)
    while client.get_open_orders() != [] and BTC_balance > 0.001:
        continue #We will wait for the entire sell order to execute then restart the process
#Use all or nothing here, and perhaps keep it that way. The order will sell regardless
#Step 4/5. Done

#Step 6. #Perhpas this entire cycle can execute in just one iteration of the loop. The loop only gets iterated
#when the cycle is complete. Conditional executed and while loops are what keep it moving forward through
#the larger iteration
    Continue
#Step 6. done
#All done





#######################################################################################################
#Note)
# This is what buy_order_1 returns
#{'symbol': 'BNBBTC', 'orderId': 131013810, 'orderListId': -1, 'clientOrderId': 'H6DZe5mmEHcZiFOduSJ4EG',
#'transactTime': 1668565491684, 'price': '0.01632350', 'origQty': '0.01000000', 'executedQty': '0.00000000',
#'cummulativeQuoteQty': '0.00000000', 'status': 'NEW', 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'BUY',
#'fills': []}
