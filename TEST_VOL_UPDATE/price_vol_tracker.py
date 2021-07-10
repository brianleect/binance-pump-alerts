import requests
import time
from volume_test_param import outlier_param, intervals, watchlist, pairs_of_interest, token, chat_id, FUTURE_ENABLED, DUMP_ENABLED, MIN_ALERT_INTERVAL, RESET_INTERVAL, PRINT_DEBUG, EXTRACT_INTERVAL
import telegram as telegram
from time import sleep

def durationToSeconds(str_dur):
    unit = str_dur[-1]
    if unit == 's': unit = 1
    elif unit == 'm': unit = 60
    elif unit == 'h': unit = 3600

    return  int(str_dur[:-1]) * unit

def getPrices():
    while True:
        try:
            data = requests.get(url).json()
            return data
        except Exception as e:
            print("Error:",e)
            print("Retrying in 1s")
            sleep(1) # Keeps trying every 0.5s 

init_time = time.time()
MIN_ALERT_INTERVAL = durationToSeconds(MIN_ALERT_INTERVAL)
EXTRACT_INTERVAL = durationToSeconds(EXTRACT_INTERVAL)
print("Cooldown:",MIN_ALERT_INTERVAL)

try:
    bot = telegram.Bot(token=token)

    def send_message(message):
        while True:
            try:
                bot.send_message(chat_id=chat_id,text=message)
                break
            except:
                print("Telegram bot error")
                sleep(0.5)
except Exception as e:
    print("Error initializing telegram bot")
    print(e)
    quit()

# Choose whether we look at spot prices or future prices
if FUTURE_ENABLED: url = 'https://fapi.binance.com/fapi/v1/ticker/24hr'
else: url = 'https://api.binance.com/api/v3/ticker/24hr'

data = getPrices()
full_data = []

# Initialize full_data
for asset in data:
    symbol = asset['symbol']

    if len(watchlist) > 0: # Meaning watchlist has variables
        if symbol not in watchlist: continue
    else: # If watchlist is empty we take general variables
        if float(asset['lastPrice']) == 0:  # Possible delisted symbols e.g. BCCUSDT
            print("Delisted:",symbol)
            continue
        if (('UP' in symbol) or ('DOWN' in symbol) or ('BULL' in symbol) or ('BEAR' in symbol)) and ("SUPER" not in symbol):
            print("Ignoring:",symbol)
            continue # Remove leveraged tokens
        if symbol[-4:] not in pairs_of_interest and symbol[-3:] not in pairs_of_interest: continue # Should focus on usdt pairs to reduce noise

    tmp_dict = {}
    tmp_dict['symbol'] = asset['symbol']
    tmp_dict['price'] = [] # Initialize empty price array
    tmp_dict['volume'] = [] # Initialize empty volume array
    tmp_dict['last_triggered'] = time.time()

    print("Added symbol:",symbol)
    full_data.append(tmp_dict)

print("Following",len(full_data),"pairs")

def searchSymbol(symbol_name, data):
    for asset in data:
        if asset['symbol'] == symbol_name: return asset

def getPercentageChange(asset_dict):

    data_length = len(asset_dict['price'])

    for inter in intervals:
        data_points = int(durationToSeconds(inter) / EXTRACT_INTERVAL)

        if data_points*2+1 > data_length: break # Skip unless sufficient data points, *2 for the volume comparison with previous interval
        elif time.time() - asset_dict['last_triggered'] < MIN_ALERT_INTERVAL: break # Skip checking for period since last triggered
        else: 
            change = round((asset_dict['price'][-1] - asset_dict['price'][-1-data_points]) / asset_dict['price'][-1],5)
            
            change_vol = asset_dict['volume'][-1] - asset_dict['volume'][-1-data_points]
            prev_change_vol = asset_dict['volume'][-1-data_points] - asset_dict['volume'][-1-2*data_points]

            if change_vol == 0 or prev_change_vol == 0 : change_vol_percent = 0
            else: change_vol_percent = round(((change_vol-prev_change_vol)/prev_change_vol)*100,2)

            if change >= outlier_param[inter]:
                asset_dict['last_triggered'] = time.time() # Updates last triggered time
                print("PUMP:",asset_dict['symbol'],'/ Change:',round(change*100,2),'/% Price:',asset_dict['price'][-1],'Interval:',inter) # Possibly send telegram msg instead
                send_message("PUMP: "+asset_dict['symbol']+' / Change: '+str(round(change*100,2))+'% / Price: '+str(asset_dict['price'][-1]) \
                    +' / Volume Change: '+str(change_vol_percent)+ '%' + ' / Interval: '+str(inter))
                # Note that we don't need to break as we have updated 'last_triggered' parameter which will skip the remaining intervals if an alert is triggered
            
            elif DUMP_ENABLED and -change >= outlier_param[inter]:
                asset_dict['last_triggered'] = time.time()
                print("DUMP:",asset_dict['symbol'],'/ Change:',round(change*100,2),'% / Price:',asset_dict['price'][-1],'Interval:',inter) # Possibly send telegram msg instead
                send_message("DUMP: "+asset_dict['symbol']+' / Change: '+str(round(change*100,2))+'% / Price: '+str(asset_dict['price'][-1]) \
                    +' / Volume Change: '+str(change_vol_percent)+ '%' + ' / Interval: '+str(inter))

def checkTimeSinceReset(): # Used to solve MEM ERROR bug
    global init_time
    global full_data
    if time.time() - init_time > durationToSeconds(RESET_INTERVAL): # Clear arrays every 3 hours
        send_message('Emptying data to prevent mem error')
        for asset in full_data:
            asset['price'] = [] # Empty price array
            asset['volume'] = [] # Empty volume array

        init_time = time.time()

count=0

while True:
    count+=1
    if PRINT_DEBUG: print("Extracting after",EXTRACT_INTERVAL,"s")
    start_time = time.time()
    data = getPrices()

    checkTimeSinceReset() # Clears logs if pass a certain time

    for asset in full_data:
        symbol = asset['symbol']
        sym_data = searchSymbol(symbol,data)
        if float(sym_data['lastPrice']) == 0: # Bug fix for possiblly delisted pairs, E.g. BCC
            #if PRINT_DEBUG: print("[Delist] Ignoring:",symbol)
            continue 
        asset['price'].append(float(sym_data['lastPrice']))
        asset['volume'].append(float(sym_data['quoteVolume']))
        getPercentageChange(asset)

    if PRINT_DEBUG: print("Time taken to extract and append:",time.time()-start_time)
    while time.time() - start_time < EXTRACT_INTERVAL:
        sleep(EXTRACT_INTERVAL-time.time()+start_time) # Sleeps for the remainder of 1s
        pass # Loop until 1s has passed to getPrices again