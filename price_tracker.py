import requests
import time
from params import outlier_param, intervals, watchlist, pairs_of_interest, token, chat_id, FUTURE_ENABLED
import telegram as telegram
from time import sleep

try:
    bot = telegram.Bot(token=token)

    def send_message(message):
        bot.send_message(chat_id=chat_id,text=message)
except Exception as e:
    print("Error initializing telegram bot")
    print(e)
    quit()

# Choose whether we look at spot prices or future prices
if FUTURE_ENABLED: url = 'https://fapi.binance.com/fapi/v1/ticker/price'
else: url = 'https://api.binance.com/api/v3/ticker/price'

def getPrices():
    while True:
        try:
            data = requests.get(url).json()
            return data
        except Exception as e:
            print("Error:",e)
            print("Retrying in 1s")
            sleep(1) # Keeps trying every 0.5s 

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
        unit = inter[-1]
        if unit == 's': unit = 1
        elif unit == 'm': unit = 60
        elif unit == 'h': unit = 3600

        data_points = int(inter[:-1]) * unit
        if data_points+1 > data_length: 
            asset_dict[inter] = 0
        else: 
            
            change = round((asset_dict['price'][-1] - asset_dict['price'][-1-data_points]) / asset_dict['price'][-1],5)
            #print("Success Change:",asset_dict['symbol'],change)
            asset_dict[inter] = change

            if change >= outlier_param[inter]: 
                print("ALERT:",asset_dict['symbol'],'/ Change:',change,'/ Price:',asset_dict['price'][-1],'Interval:',inter) # Possibly send telegram msg instead
                
                while True:
                    try:
                        send_message("ALERT: "+asset_dict['symbol']+' / Change: '+str(change)+' / Price: '+str(asset_dict['price'][-1]) + ' / Interval: '+str(inter)) # Possibly send telegram msg instead
                        break
                    except:
                        print("Telegram bot error")
                        sleep(0.5)
    return asset_dict


count=0
while True:
    count+=1
    print("Extracting after 1s")
    start_time = time.time()
    data = getPrices()

    for asset in full_data:
        symbol = asset['symbol']
        sym_data = searchSymbol(symbol,data)
        asset['price'].append(float(sym_data['price']))
        asset = getPercentageChange(asset)

    # Check for outlier movement of percentages


    # Get market avg?

    print("Time taken to extract and append:",time.time()-start_time)
    while time.time() - start_time < 1:
        sleep(1-time.time()+start_time) # Sleeps for the remainder of 1s
        pass # Loop until 1s has passed to getPrices again

print(full_data)