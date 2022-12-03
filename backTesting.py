#Plan/walk-through
#1. Import the 15 minute candles for the timeperiod you are looking to backtest
#___ Use klines = client.get_historical_klines("BNBBTC", Client.KLINE_INTERVAL_1MINUTE, "1 day ago UTC")
#2. Test each candle to see if it meets the signal criteria
#3. Signal criteria is hit, set appropriate parameters and note timestamp
#4. Search following candles for entry. Also search for signal again. If signal is found again before entry,
### search for new entry target
#5. When entry is hit, check if PT or SL is hit and make note of prices.
#6. Dictionary parameters:{tradenumber/index (key), IRB_time, entry_time, entry price, sell price, sell time}
#7 Output information to SQL database for analysis
#################################################################################################
#################################################################################################

#To-be done:
#1. Add ADX as a signal parameter. ADX must be > 30
#2. Optimize maximum range between PT and SL for potentially large candles, see how results affected
#3. Hoffman wants the price to break within the next 20 bars according to the time frame used. Code this
#4. Loop over optimization parameters to maximize win rate and account Balance
#5. Store results and optimization parameters of automated tests in a SQL database for later analysis
#5. Analyze the losses to see if you can find any similar themes, consider skipping short candles
#6. Create an "Overwritten signals" dictionary that stores the old data when a new signal is found before the entry is hit
#### Store the old signal time, the old entry price, the new signal time, and the new signal price
#7. Create a local JSON file of all the candle data so API isn't hit so much. Edit program accordingly
#################################################################################################
#################################################################################################

#Libraries
import urllib.parse
import hashlib
import hmac
#import base64
import requests
import time
from time import sleep
from datetime import datetime
from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
import json
#######################################################################################################
#APIkey
api_key = ''#Add these
api_secret = ''#Add these
client = Client(api_key, api_secret, tld='us')
#######################################################################################################
#######################################################################################################
#Importing JSON files as dictionaries
#using the loadstring JSON method. This returns a dictionary that is stored in variable on left
file1 = json.load(open("15min_20EMA_25sep2019.json"))
file1string = json.dumps(file1) #json.dumps take a dictionary as input and returns a string as output.
minute15_20EMA_dict = json.loads(file1string) # json.loads take a string as input and returns a dictionary as output.

file2 = json.load(open("1hr_50EMA_25sep2019.json"))
file2string = json.dumps(file2)
hour1_50EMA_dict = json.loads(file2string)

#print(minute15_20EMA_dict[str(1664583300000)])
#print(hour1_50EMA_dict[1664583300000])
#######################################################################################################
#######################################################################################################
#Functions
def scan_for_IRB(candle):
#each candle is a list of 12 different parameters, search the below link for "1499040000000,// Open time"
#https://github.com/binance-us/binance-us-api-docs/blob/master/rest-api.md#klinecandlestick-data
    candle_open = float(candle[1])
    candle_close = float(candle[4])
    candle_high = float(candle[2])
    candle_low = float(candle[3])
    global IRB_percent_limit
    global repetition_check_open_time

    #Avoiding division by zero, this scenario happened and caused an error in a corner-case
    if candle_high == candle_low:
        candle_high += 0.01

    if candle[0] == repetition_check_open_time: #Meaning this candle has already been checked
        return 0
    elif (candle_high-max(candle_open, candle_close)) / (candle_high-candle_low) > IRB_percent_limit:
        repetition_check_open_time = candle[0]
        timestamp = int(int(repetition_check_open_time)/1000)
        #print("Found IRB!")
        #print(datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'))
        #print()
        return 1
    else:
        return 0

def EMA_comparison(candle_open_time):
#Testing to see if the 15 min 20 EMA is above the 1 hr 50 EMA, per strategy requirements
    hour1_base = 3600000 #1 hour in milliseconds
    if candle_open_time % hour1_base != 0:  #Not a 1 hour candle
        #convert the 15 minute timestamp to the closest 1 hour timestamp
        hour1_candle_time = str(int(hour1_base * round(candle_open_time/hour1_base)))
    else: hour1_candle_time = str(candle_open_time)

    #Comparing the EMA values using
    if float(minute15_20EMA_dict[str(candle_open_time)]) > float(hour1_50EMA_dict[hour1_candle_time]):
        return 1
    else:
        return 0

def EMA_slope_test(candle_open_time):
    global num_candles_for_slope
    global minimum_slope
    min15_time_difference = 900000 #15 minutes in milliseconds
    minimum_slope_for_one_candle = minimum_slope/num_candles_for_slope
    slope_sum = 0
    slope_start_time = candle_open_time - num_candles_for_slope*min15_time_difference

    #Calculating the average difference in EMA on a candle-by-candle basis
    for timestamp in range(slope_start_time, candle_open_time, min15_time_difference):
        slope_sum += minute15_20EMA_dict[str(timestamp)]
    average_slope = slope_sum/num_candles_for_slope

    if average_slope>minimum_slope_for_one_candle:
        return 1
    else:
        return 0

def EMA_positivity_check(candle_open_time):
#Making sure the last x consecutive candles' corresponding EMA values are increasing
    global minimum_consecutive_increasing_candles
    min15_time_difference = 900000 #15 minutes in milliseconds
    positivity_start_time = candle_open_time - minimum_consecutive_increasing_candles*min15_time_difference

    for timestamp in range(positivity_start_time, candle_open_time, min15_time_difference):
        if float(minute15_20EMA_dict[str(timestamp)]) < float(minute15_20EMA_dict[str(timestamp-min15_time_difference)]):
            return 0
        else:
            continue

    return 1

#This function will combine all the individual trade strategy requirements/functions and return a 1 or 0
def signal(candle):

    test1 = scan_for_IRB(candle)
    test2 = EMA_comparison(candle[0])
    test3 = EMA_slope_test(candle[0])
    test4 = EMA_positivity_check(candle[0])

    if (test1 == 1) and (test2 == 1) and (test3 == 1) and (test4 == 1):
        return 1
    else:
        return 0


#######################################################################################################
#######################################################################################################
#Variable Initializations
results_dictionary = dict() #{tradenumber/index(key): [IRB_time, entry_time, entry_price, sell_price, sell_time]}
trade_number = 0
global repetition_check_open_time
repetition_check_open_time = 0
current_candle_time = 0
wins, losses, draws = 0,0,0
percent_gains_and_losses = list()
klines = client.get_historical_klines("BTCUSD", Client.KLINE_INTERVAL_15MINUTE, "1 Sep, 2022", "28 Nov, 2022")
#######################################################################################################
#######################################################################################################
global num_candles_for_slope
global minimum_slope
global minimum_consecutive_increasing_candles
#Optimization Parameters
maximum_percent_loss = 0.99
risk_reward_ratio = 1.5
minimum_slope = 16045/15800
num_candles_for_slope = 40 #integers only
minimum_consecutive_increasing_candles = 5 #integers only
minimum_range = 100.0  #minimum difference between candle high and candle low
minimum_range_offset = 30.0
entry_offset = 15.19  #Placing the entry this high above the candle
IRB_percent_limit = 0.45
stop_loss_offset = 20.0
#Consider adding maximum range between PT and SL for potentially large candles, see how results affected



#######################################################################################################
#######################################################################################################
#Playground to run only a few lines of code
# i = 0
# print(len(klines))
# for candle in klines:
#     if i>50:
#         break
#     else:
#         print(i, candle)
#         i += 1
# quit()
# dknkcjdkj
#######################################################################################################
#######################################################################################################


#Looping over all imported candles, checking if signal is hit, adding trade parameters to dictionary
for candle in klines:
    if candle[0] < current_candle_time: continue #if candle has already been iterated through, skip it
    elif signal(candle) == 1: #Signal is met, set parameters, search for entry to be hit

        #Setting order parameters
        entry_price = float(candle[2]) + entry_offset
        IRB_time = candle[0]
        results_dictionary[trade_number] = list()
        results_dictionary[trade_number].append(IRB_time)
        SL = float(candle[3]) - stop_loss_offset #IRB low
        if (entry_price - SL) < minimum_range: #SL is too close to the entry, meaning candle is too short
            SL -= minimum_range_offset #Reducing the stop-loss

        percent_risk = SL/entry_price
        if percent_risk < maximum_percent_loss:
            SL = entry_price * maximum_percent_loss
        PT = entry_price + (entry_price - SL)*risk_reward_ratio

        #Searching for entry candle after IRB appears, also searching for new IRBs
        for candle in klines:
            if candle[0] < IRB_time: #skipping candles that came before the signal
                continue
            elif float(candle[2]) > float(entry_price): #The entry was hit
                current_candle_time = candle[0]
                results_dictionary[trade_number].append(current_candle_time) #entry candle timestamp
                results_dictionary[trade_number].append(entry_price)

                for candle in klines: #Searching for PT or SL after entry is hit
                    if candle[0] < current_candle_time: #skipping candles that come before entry candle
                        continue

                    elif float(candle[2])>PT and float(candle[3])<SL: #PT and SL both hit in one candle
                        results_dictionary[trade_number].append(0.01) #To identify candle in data
                        results_dictionary[trade_number].append(946702800000) #Y2K to identify candle
                        current_candle_time = candle[0]
                        trade_number += 1
                        draws += 1
                        break

                    elif float(candle[2])>PT: #Profit Target is hit
                        sell_price = PT
                        sell_time = candle[0]
                        results_dictionary[trade_number].append(float(sell_price))
                        results_dictionary[trade_number].append(sell_time)
                        current_candle_time = candle[0]
                        percent_gain_or_loss = round(((float(sell_price)/float(entry_price))-1)*100,2)
                        results_dictionary[trade_number].append(percent_gain_or_loss)
                        trade_number += 1
                        wins += 1
                        break

                    elif float(candle[3])<SL: #Stop-loss is hit
                        sell_price = SL
                        sell_time = candle[0]
                        results_dictionary[trade_number].append(float(sell_price))
                        results_dictionary[trade_number].append(sell_time)
                        current_candle_time = candle[0]
                        percent_gain_or_loss = round(((float(sell_price)/float(entry_price))-1)*100,3)
                        results_dictionary[trade_number].append(percent_gain_or_loss)
                        trade_number += 1
                        losses += 1
                        break

                    else: continue #SL and PT not hit yet
                break
            elif signal(candle) == 1: #another IRB appears before entry is hit, reset parameters, note time
                    entry_price = float(candle[2]) + entry_offset
                    IRB_time = candle[0] #Overwriting IRB time
                    results_dictionary[trade_number][0] = IRB_time #Overwriting IRB time in dictionary
                    SL = float(candle[3]) - stop_loss_offset
                    if (entry_price - SL) < minimum_range:
                        SL -= minimum_range_offset
                    percent_risk = entry_price/SL
                    if percent_risk > maximum_percent_loss:
                        SL = entry_price - entry_price*maximum_percent_loss
                    PT = entry_price + (entry_price - SL)*risk_reward_ratio
                    current_candle_time = candle[0]
    else: continue #no IRB


#Formatting, printing, and analyzing the results; Changing timestamps to dates, rounding, and corner-cases
win_rate = wins/(wins+losses+draws)*100
starting_amount = 1000

for key,value in results_dictionary.items():
    value[0] = datetime.fromtimestamp(int(value[0]/1000)).strftime('%Y-%m-%d %H:%M:%S')
    value[1] = datetime.fromtimestamp(int(value[1]/1000)).strftime('%Y-%m-%d %H:%M:%S')
    value[2] = round(float(value[2]), 2)
    if len(value)<4:
        value.append(0.01)
        value.append(946702800000) #Y2K
        value.append(1.00)
    value[3] = round(float(value[3]), 2)
    value[4] = datetime.fromtimestamp(int(value[4]/1000)).strftime('%Y-%m-%d %H:%M:%S')
    starting_amount *= (value[5]/100+1)
    print(value)

final_amount = round(starting_amount,2)

print("")
print("Risk/Reward: {}    Minimum Range: {}     Minimum Range Offset: {}     Entry Offset: {}       Candles for Slope: {}".format(risk_reward_ratio, minimum_range, minimum_range_offset, entry_offset, num_candles_for_slope))
print("Wins: {}    Losses: {}     Draws: {}     Win Rate: {}%      Account Balance: ${}".format(wins, losses, draws, round(win_rate,1), final_amount ) )
