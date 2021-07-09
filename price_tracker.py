import requests
import time
from params import outlier_param, intervals, watchlist, pairs_of_interest, token, chat_id, FUTURE_ENABLED, DUMP_ENABLED, MIN_ALERT_INTERVAL, RESET_INTERVAL, PRINT_DEBUG
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
COOLDOWN = durationToSeconds(MIN_ALERT_INTERVAL)
print("Cooldown:",COOLDOWN)

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
if FUTURE_ENABLED: url = 'https://fapi.binance.com/fapi/v1/ticker/price'
else: url = 'https://api.binance.com/api/v3/ticker/price'

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
    tmp_dict['last_triggered'] = time.time()

    print("Added symbol:",symbol)
    for interval in intervals:
        tmp_dict[interval] = 0
    
    full_data.append(tmp_dict)

print("Following",len(full_data),"pairs")

def searchSymbol(symbol_name, data):
    for asset in data:
        if asset['symbol'] == symbol_name: return asset

def getPercentageChange(asset_dict):

    data_length = len(asset_dict['price'])

    for inter in intervals:
        data_points = durationToSeconds(inter)

        if data_points+1 > data_length: asset_dict[inter] = 0 # Set change to 0% due to insufficient data
        elif time.time() - asset_dict['last_triggered'] < COOLDOWN:
            send_message("(TEST) Skipping " +asset_dict['symbol']+ " as on cooldown")
            break # Skip checking for period since last triggered
        else: 
            change = round((asset_dict['price'][-1] - asset_dict['price'][-1-data_points]) / asset_dict['price'][-1],5)
            asset_dict[inter] = change # Saves % change

            if change >= outlier_param[inter]:
                asset_dict['last_triggered'] = time.time() # Updates last triggered time
                print("PUMP:",asset_dict['symbol'],'/ Change:',round(change*100,2),'/% Price:',asset_dict['price'][-1],'Interval:',inter) # Possibly send telegram msg instead
                send_message("PUMP: "+asset_dict['symbol']+' / Change: '+str(round(change*100,2))+'% / Price: '+str(asset_dict['price'][-1]) + ' / Interval: '+str(inter)) # Possibly send telegram msg instead
                # Note that we don't need to break as we have updated 'last_triggered' parameter which will skip the remaining intervals
            
            elif DUMP_ENABLED and -change >= outlier_param[inter]:
                asset_dict['last_triggered'] = time.time()
                print("DUMP:",asset_dict['symbol'],'/ Change:',round(change*100,2),'% / Price:',asset_dict['price'][-1],'Interval:',inter) # Possibly send telegram msg instead
                send_message("PUMP: "+asset_dict['symbol']+' / Change: '+str(round(change*100,2))+'% / Price: '+str(asset_dict['price'][-1]) + ' / Interval: '+str(inter)) # Possibly send telegram msg instead

    return asset_dict

def checkTimeSinceReset(): # Used to solve MEM ERROR bug
    global init_time
    global full_data
    if time.time() - init_time > durationToSeconds(RESET_INTERVAL): # Clear arrays every 3 hours
        send_message('Emptying data to prevent mem error')
        for asset in full_data:
            asset['price'] = [] # Empty price array

        init_time = time.time()

count=0
while True:
    count+=1
    if PRINT_DEBUG: print("Extracting after 1s")
    start_time = time.time()
    data = getPrices()

    checkTimeSinceReset() # Clears logs if pass a certain time
    
    for asset in full_data:
        symbol = asset['symbol']
        sym_data = searchSymbol(symbol,data)
        asset['price'].append(float(sym_data['price']))
        asset = getPercentageChange(asset)

    if PRINT_DEBUG: print("Time taken to extract and append:",time.time()-start_time)
    while time.time() - start_time < 1:
        sleep(1-time.time()+start_time) # Sleeps for the remainder of 1s
        pass # Loop until 1s has passed to getPrices again