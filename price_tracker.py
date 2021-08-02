import requests
import time
import telegram as telegram
from params import outlier_param, intervals, watchlist, pairs_of_interest, token, chat_id, FUTURE_ENABLED,\
     DUMP_ENABLED, RESET_INTERVAL, PRINT_DEBUG, EXTRACT_INTERVAL, GET_PRICE_FAIL_INTERVAL,\
     SEND_TELEGRAM_FAIL_INTERVAL, TOP_PUMP_ENABLED, VIEW_NUMBER, TDPA_INTERVALS, HARD_ALERT_INTERVAL_ENABLED, MIN_ALERT_INTERVAL
from functions import durationToSeconds, getPrices, send_message, searchSymbol, getPercentageChange, topPumpDump
from time import sleep
import datetime

init_dt = datetime.datetime.now()
init_time = time.time()
EXTRACT_INTERVAL = durationToSeconds((EXTRACT_INTERVAL))

if not HARD_ALERT_INTERVAL_ENABLED: print("Min_Alert_Interval:",MIN_ALERT_INTERVAL)
else: print("Hard Alert Interval is being used")
print("Extract interval:",EXTRACT_INTERVAL)

data = getPrices()
init_data = data[:] # Used for checking for new listings
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
    tmp_dict['lt_dict'] = {} # Used for HARD_ALERT_INTERVAL
    tmp_dict['last_triggered'] = time.time() # Used for MIN_ALERT_INTERVAL

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

def checkNewListings(data_t):
    global full_data
    global init_data

    if len(init_data) != len(data_t):
        send_message(str(len(data_t)-len(init_data))+" new pairs found, adding to monitored list")

        init_symbols = [asset['symbol'] for asset in init_data]
        symbols_to_add = [asset['symbol'] for asset in data_t if asset['symbol'] not in init_symbols ]
        
        for symbol in symbols_to_add:

            if symbol[-4:] not in pairs_of_interest and symbol[-3:] not in pairs_of_interest: 
                send_message("(New Listing) Ignoring: "+symbol+" as not in pair of interest") # Ignores pairs not specified
                continue 

            tmp_dict = {}
            tmp_dict['symbol'] = symbol
            tmp_dict['price'] = [] # Initialize empty price array
            tmp_dict['lt_dict'] = {} # Used for HARD_ALERT_INTERVAL
            tmp_dict['last_triggered'] = time.time() # Used for MIN_ALERT_INTERVAL

            print("Added symbol:",symbol)
            send_message("Added symbol: "+symbol)

            for interval in intervals:
                tmp_dict[interval] = 0
                tmp_dict['lt_dict'][interval] = time.time()
            
            full_data.append(tmp_dict)

        init_data = data_t[:] # Updates init data 

count=0
send_message("Bot has started")

tpda_last_trigger = {}
for inter in TDPA_INTERVALS: tpda_last_trigger[inter] = time.time() # Set TDPA interval
 
while True:
    count+=1
    if PRINT_DEBUG: print("Extracting after",EXTRACT_INTERVAL,'s')
    start_time = time.time()
    data = getPrices()

    checkNewListings(data)
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