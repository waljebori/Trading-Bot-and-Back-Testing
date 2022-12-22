#Rules of strategy https://www.best-trading-platforms.com/trading-platform-futures-forex-cfd-stocks-nanotrader/inventory-retracement-bar-irb

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
#3. Analyze the results to see if you can find any similar themes, consider skipping short candles
#4. Create an "Overwritten signals" dictionary that stores the old data when a new signal is found before the entry is hit
#### Store the old signal time, the old entry price, the new signal time, and the new signal price
#5. Skip candles where the high-low is less than 50 (or another number)
#6. Change the signal function to also return the entry, PT, and SL. Makes this more versatile for other strategies
#7. Continously refine the optimization parameters
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
import sqlite3
#######################################################################################################
#######################################################################################################
#APIkey
api_key =
api_secret =

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
#######################################################################################################
#######################################################################################################
#Optional local copy of klines to use instead of getting data live from API. API won't be needed

#Don't forget to delete klines = in the variable initializations section
# file3 = json.load(open("15MinuteKLineCache250919_031222.json")) #Goes through December 3, 2022
# file3string = json.dumps(file3)
# all_klines = json.loads(file3string)
#
# start_date = "01/01/2022" #"%d/%m/%Y"
# end_date = "29/11/2022"   #"%d/%m/%Y"
# start_time_timestamp = int(time.mktime(datetime.strptime(start_date, "%d/%m/%Y").timetuple()))*1000
# end_time_timestamp = int(time.mktime(datetime.strptime(end_date, "%d/%m/%Y").timetuple()))*1000
#
# start_timestamp_index, final_start_timestamp_index = 0, 0
# end_timestamp_index, final_end_timestamp_index = 0, 0
#
# for candle in all_klines:
#     if candle[0] == start_time_timestamp:
#         final_start_timestamp_index = start_timestamp_index
#     elif candle[0] == end_time_timestamp:
#         final_end_timestamp_index = end_timestamp_index
#     else:
#         start_timestamp_index += 1
#         end_timestamp_index += 1
#
# klines = list()
# klines = all_klines[final_start_timestamp_index:final_end_timestamp_index] #Returns klines for the desired dates by using timestamp indicies
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
    global min_EMA_change
    global num_candles_for_slope
    min15_time_difference = 900000 #15 minutes in milliseconds
    slope_sum = 0
    slope_start_time = candle_open_time - num_candles_for_slope*min15_time_difference
    mid_point_EMA_value = (minute15_20EMA_dict[str(slope_start_time)] + minute15_20EMA_dict[str(candle_open_time)])/2

    #Calculating the average difference in EMA on a candle-by-candle basis
    for timestamp in range(slope_start_time, candle_open_time, min15_time_difference):
        slope_sum += minute15_20EMA_dict[str(timestamp)] - minute15_20EMA_dict[str(timestamp - min15_time_difference)]
    average_slope = (slope_sum/num_candles_for_slope)*(mid_point_EMA_value/17000) #percent basis

    if average_slope>min_EMA_change:
        return 1
    else:
        return 0

def skipping_doji_candles(candle):
    #global minimum_range
    if float(candle[2]) - float(candle[3]) < minimum_range: #high - low
        return 0
    else: return 1

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

#Returns list of results: number of hits, win rate, GOA. Perhaps average win and loss percentages?
def gather_data(optimization_parameters):
    global repetition_check_open_time
    results_dictionary = dict() #{tradenumber/index(key): [IRB_time, entry_time, entry_price, sell_price, sell_time]}
    trade_number = 0
    repetition_check_open_time = 0
    current_candle_time = 0
    wins, losses, draws = 0,0,0
    minimum_range = 100.0
    #######################################################################################################
    #Parameters being optimized
    maximum_percent_loss = optimization_parameters[0]
    risk_reward_ratio = optimization_parameters[1]
    global num_candles_for_slope
    num_candles_for_slope = optimization_parameters[2]
    global min_EMA_change
    min_EMA_change = optimization_parameters[3]
    global minimum_consecutive_increasing_candles
    minimum_consecutive_increasing_candles = optimization_parameters[4]
    entry_offset = optimization_parameters[5]  #Parameter exists only in this function
    stop_loss_offset = optimization_parameters[6] #Parameter exists only in this function
    #######################################################################################################

    for candle in klines:
        if candle[0] < current_candle_time: continue #if candle has already been iterated through, skip it
        elif signal(candle) == 1: #Signal is met, set parameters, search for entry to be hit

            #Setting order parameters
            entry_price = float(candle[2]) + entry_offset
            IRB_time = candle[0]
            #timestamp_20_candles_later = IRB_time + 20*15*60*1000 #results not improved
            results_dictionary[trade_number] = list()
            results_dictionary[trade_number].append(IRB_time) #0
            SL = float(candle[3]) - stop_loss_offset #IRB low
            if (entry_price - SL) < minimum_range: #SL is too close to the entry, meaning candle is too short
                SL = entry_price - minimum_range - entry_offset #Reducing the stop-loss

            percent_risk = SL/entry_price
            if percent_risk < maximum_percent_loss:
                SL = entry_price * maximum_percent_loss
            PT = entry_price + (entry_price - SL)*risk_reward_ratio

            #Searching for entry candle after IRB appears, also searching for new IRBs
            for candle in klines:
                if candle[0] < IRB_time: #skipping candles that came before the signal
                    continue
                #elif candle[0] > timestamp_20_candles_later: #Per strategy rules, entry must be hit within 20 candles
                #    break   #Commenting out, didn't seem to improve results at all
                elif float(candle[2]) > float(entry_price): #The entry was hit
                    current_candle_time = candle[0]
                    results_dictionary[trade_number].append(current_candle_time) #1. entry candle timestamp
                    results_dictionary[trade_number].append(entry_price) #2

                    for candle in klines: #Searching for PT or SL after entry is hit
                        if candle[0] < current_candle_time: #skipping candles that come before entry candle
                            continue

                        elif float(candle[2])>PT and float(candle[3])<SL: #PT and SL both hit in one candle
                            results_dictionary[trade_number].append(0.01) #3. To identify candle in data
                            results_dictionary[trade_number].append(946702800000) #3. Y2K to identify candle
                            current_candle_time = candle[0]
                            trade_number += 1
                            draws += 1
                            break

                        elif float(candle[2])>PT: #Profit Target is hit
                            sell_price = PT
                            sell_time = candle[0]
                            results_dictionary[trade_number].append(float(sell_price)) #3
                            results_dictionary[trade_number].append(sell_time) #4
                            current_candle_time = candle[0]
                            percent_gain_or_loss = round(((float(sell_price)/float(entry_price))-1)*100,2)
                            results_dictionary[trade_number].append(percent_gain_or_loss) #5
                            trade_number += 1
                            wins += 1
                            break

                        elif float(candle[3])<SL: #Stop-loss is hit
                            sell_price = SL
                            sell_time = candle[0]
                            results_dictionary[trade_number].append(float(sell_price)) #3
                            results_dictionary[trade_number].append(sell_time) #4
                            current_candle_time = candle[0]
                            percent_gain_or_loss = round(((float(sell_price)/float(entry_price))-1)*100,3)
                            results_dictionary[trade_number].append(percent_gain_or_loss) #5
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
                            SL = entry_price - minimum_range - entry_offset
                        percent_risk = entry_price/SL
                        if percent_risk > maximum_percent_loss:
                            SL = entry_price - entry_price*maximum_percent_loss
                        PT = entry_price + (entry_price - SL)*risk_reward_ratio
                        current_candle_time = candle[0]
        else: continue #no IRB


    final_results = list()
    num_hits = (wins+losses+draws)
    if num_hits == 0:
        num_hits = 1
    win_rate = round(wins/(num_hits-int(draws/2))*100,2)
    final_results.append(num_hits)
    final_results.append(win_rate)

    #print(results_dictionary)

    starting_amount = 1000
    for key,value in results_dictionary.items():
        while len(value)<6:
            value.append(0)
        starting_amount *= (value[5]/100+1) #percent win/loss

    final_amount = round(starting_amount,2)
    final_results.append(final_amount)
    return final_results
    #return list of results. Should return number of hits, win rate, GOA. Perhaps average win and loss percentages?


#Static Variable Initializations
klines = client.get_historical_klines("BTCUSD", Client.KLINE_INTERVAL_15MINUTE, "29 Nov, 2021", "29 Nov, 2022")
global repetition_check_open_time
minimum_range = 100.0  #minimum difference between candle high and low: skipping_doji_candles(candle)
IRB_percent_limit = 0.45

optimization_parameters = [0]*7
test_optimization_parameters = [0.985, 1.65, 10, 10, 0, 30, 30]
#print(gather_data(test_optimization_parameters)) #error was that maximum_percent_loss was set to 1

# start_time = time.time()
# gather_data(test_optimization_parameters)
# end_time = time.time()
# time_of_function = start_time - end_time
# print("--- %s seconds to run one test---" % (time.time() - start_time))
# quit()


conn = sqlite3.connect('BackTestingResults.sqlite')
cur = conn.cursor()
commit_index = 0
cur.execute('DROP TABLE IF EXISTS BT29Nov21_29Nov22')
cur.execute('''CREATE TABLE BT29Nov21_29Nov22
    (id     INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    maximum_risk FLOAT,
    risk_reward_ratio FLOAT,
    num_candles_for_slope INTEGER,
    minimum_EMA_change INTEGER,
    minimum_consecutive_increasing_candles INTEGER,
    entry_offset INTEGER,
    stop_loss_offset INTEGER,
    total_hits INTEGER,
    win_rate FLOAT,
    account_balance FLOAT)
    ''')


#Optimization Parameters #14 hours for 10,000 tests with 5 seconds per test
for max_risk in range(950,991,5):
    optimization_parameters[0] = max_risk/1000

    for RRratio in range(105,210,15):
        optimization_parameters[1] = RRratio/100

        for num_candles in range(10,60,7): #6*5*5*4*4*4
            optimization_parameters[2] = num_candles

            for min_EMA_change_loop in range(1,40,5):  #gather_data function stops working in this loop for some reason
                optimization_parameters[3] = min_EMA_change_loop #Issue likely with min_EMA_change

                for min_consec_candles in range(0,40,10):
                    optimization_parameters[4] = min_consec_candles

                    for entry_addition in range(0,40,10):
                        optimization_parameters[5] = entry_addition

                        for SL_subtraction in range(0,40,10): #the final loop, output here
                            optimization_parameters[6] = SL_subtraction

                            final_output_results = gather_data(optimization_parameters)
                            total_hits, win_rate, account_balance = final_output_results[0], final_output_results[1], final_output_results[2]
                            #print(total_hits, win_rate, account_balance)

                            cur.execute('''INSERT OR REPLACE INTO BT29Nov21_29Nov22
                                (maximum_risk, risk_reward_ratio, num_candles_for_slope, minimum_EMA_change, minimum_consecutive_increasing_candles, entry_offset, stop_loss_offset, total_hits, win_rate, account_balance)
                                VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )''',
                                (max_risk/10, RRratio/100, num_candles, min_EMA_change_loop, min_consec_candles, entry_addition, SL_subtraction, total_hits, win_rate, account_balance) )

                            commit_index += 1
                            if commit_index % 100 == 0:
                                conn.commit()
                            if commit_index % 100 == 0:
                                print("Test # ", commit_index)

                            #add feature that lets you pause the tests, and have them pick up where they stopped
                            #search how to get a loop to jump to a certain point in the execution
conn.commit()
cur.close()






############################
