import requests
import time
import telegram as telegram
from params import outlier_param, intervals, watchlist, pairs_of_interest, token, chat_id, FUTURE_ENABLED,\
     DUMP_ENABLED, RESET_INTERVAL, PRINT_DEBUG, EXTRACT_INTERVAL, GET_PRICE_FAIL_INTERVAL,\
     SEND_TELEGRAM_FAIL_INTERVAL, TOP_PUMP_DUMP_ALERT_INTERVAL, TOP_PUMP_ENABLED, VIEW_NUMBER, TDPA_INTERVALS
from functions import durationToSeconds, getPrices, send_message, searchSymbol, getPercentageChange, topPumpDump
from time import sleep
import datetime

init_dt = datetime.datetime.now()
init_time = time.time()
EXTRACT_INTERVAL = durationToSeconds((EXTRACT_INTERVAL))

print("Extract interval:",EXTRACT_INTERVAL)

data = getPrices()
full_data = []

# Initialize full_data
for asset in data:
    symbol = asset['symbol']

    if len(watchlist) > 0: # Meaning watchlist has variables
        if symbol not in watchlist: continue
    else: # If watchlist is empty we take general variables
        if (('UP' in symbol) or ('DOWN' in symbol) or ('BULL' in symbol) or ('BEAR' in symbol)) and ("SUPER" not in symbol):
            print("Ignoring:",symbol)
            continue # Remove leveraged tokens
        if symbol[-4:] not in pairs_of_interest and symbol[-3:] not in pairs_of_interest: continue # Should focus on usdt pairs to reduce noise

    tmp_dict = {}
    tmp_dict['symbol'] = asset['symbol']
    tmp_dict['price'] = [] # Initialize empty price array
    tmp_dict['lt_dict'] = {}

    print("Added symbol:",symbol)
    for interval in intervals:
        tmp_dict[interval] = 0
        tmp_dict['lt_dict'][interval] = time.time()
    full_data.append(tmp_dict)

print("Following",len(full_data),"pairs")

def checkTimeSinceReset(): # Used to solve MEM ERROR bug
    global init_time
    global full_data
    if time.time() - init_time > durationToSeconds(RESET_INTERVAL): # Clear arrays every 3 hours
        print('Emptying data to prevent mem error') # Logs to console only, reduces spam
        for asset in full_data:
            asset['price'] = [] # Empty price array

        init_time = time.time()

count=0
send_message("Bot has started")

tpda_last_trigger = {}
for inter in TDPA_INTERVALS: tpda_last_trigger[inter] = time.time()
 
while True:
    count+=1
    if PRINT_DEBUG: print("Extracting after",EXTRACT_INTERVAL,'s')
    start_time = time.time()
    data = getPrices()

    checkTimeSinceReset() # Clears logs if pass a certain time
    
    for asset in full_data:
        symbol = asset['symbol']
        sym_data = searchSymbol(symbol,data)
        asset['price'].append(float(sym_data['price']))
        asset = getPercentageChange(asset)

    
    topPumpDump(tpda_last_trigger,full_data) # Triggers check for top_pump_dump

    if PRINT_DEBUG: print("Extract time:",time.time()-start_time,'/ Time ran:',datetime.datetime.now()-init_dt)
    while time.time() - start_time < EXTRACT_INTERVAL:
        sleep(EXTRACT_INTERVAL-time.time()+start_time) # Sleeps for the remainder of 1s
        pass # Loop until 1s has passed to getPrices again