import requests
import time
from params import TOP_DUMP_ENABLED, VIEW_NUMBER, outlier_param, intervals, watchlist, pairs_of_interest, token, chat_id, FUTURE_ENABLED,\
     DUMP_ENABLED, MIN_ALERT_INTERVAL, RESET_INTERVAL, PRINT_DEBUG, EXTRACT_INTERVAL, GET_PRICE_FAIL_INTERVAL,\
     SEND_TELEGRAM_FAIL_INTERVAL, TOP_PUMP_DUMP_ALERT_INTERVAL, TOP_PUMP_ENABLED, TOP_DUMP_ENABLED
from time import sleep
import telegram as telegram

# Initialize telegram bot
try:
    bot = telegram.Bot(token=token)
except Exception as e:
    print("Error initializing telegram bot")
    print(e)
    quit()

def durationToSeconds(str_dur):
    unit = str_dur[-1]
    if unit == 's': unit = 1
    elif unit == 'm': unit = 60
    elif unit == 'h': unit = 3600

    return  int(str_dur[:-1]) * unit

def send_message(message):
    while True:
        try:
            bot.send_message(chat_id=chat_id,text=message)
            break
        except:
            print("Retrying to send tele message in",SEND_TELEGRAM_FAIL_INTERVAL,"s")
            sleep(SEND_TELEGRAM_FAIL_INTERVAL)

MIN_ALERT_INTERVAL = durationToSeconds(MIN_ALERT_INTERVAL)
EXTRACT_INTERVAL = durationToSeconds((EXTRACT_INTERVAL))
GET_PRICE_FAIL_INTERVAL = durationToSeconds(GET_PRICE_FAIL_INTERVAL)
SEND_TELEGRAM_FAIL_INTERVAL = durationToSeconds(SEND_TELEGRAM_FAIL_INTERVAL)


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
            print("Retrying in",GET_PRICE_FAIL_INTERVAL,"s")
            sleep(GET_PRICE_FAIL_INTERVAL) # Keeps trying every 0.5s 

def searchSymbol(symbol_name, data):
    for asset in data:
        if asset['symbol'] == symbol_name: return asset

def getPercentageChange(asset_dict):

    data_length = len(asset_dict['price'])

    for inter in intervals:
        data_points = int(durationToSeconds(inter) / EXTRACT_INTERVAL)

        if data_points+1 > data_length: break
        elif time.time() - asset_dict['last_triggered'] < MIN_ALERT_INTERVAL: break # Skip checking for period since last triggered
        else: 
            change = round((asset_dict['price'][-1] - asset_dict['price'][-1-data_points]) / asset_dict['price'][-1],5)
            asset_dict[inter] = change # Stores change for the interval into asset dict (Used for top pump/dumps)

            if change >= outlier_param[inter]:
                asset_dict['last_triggered'] = time.time() #W Updates last triggered time
                if PRINT_DEBUG: print("PUMP:",asset_dict['symbol'],'/ Change:',round(change*100,2),'/% Price:',asset_dict['price'][-1],'Interval:',inter) # Possibly send telegram msg instead
                send_message("PUMP: "+asset_dict['symbol']+' / Change: '+str(round(change*100,2))+'% / Price: '+str(asset_dict['price'][-1]) + ' / Interval: '+str(inter)) # Possibly send telegram msg instead
                # Note that we don't need to break as we have updated 'last_triggered' parameter which will skip the remaining intervals
            
            elif DUMP_ENABLED and -change >= outlier_param[inter]:
                asset_dict['last_triggered'] = time.time()
                if PRINT_DEBUG: print("DUMP:",asset_dict['symbol'],'/ Change:',round(change*100,2),'% / Price:',asset_dict['price'][-1],'Interval:',inter) # Possibly send telegram msg instead
                send_message("DUMP: "+asset_dict['symbol']+' / Change: '+str(round(change*100,2))+'% / Price: '+str(asset_dict['price'][-1]) + ' / Interval: '+str(inter)) # Possibly send telegram msg instead

    return asset_dict

def topPumpDump(last_trigger_pd,full_asset):
    if time.time() > last_trigger_pd + durationToSeconds(TOP_PUMP_DUMP_ALERT_INTERVAL) + 1:
        msg = ''
        msg += 'Interval: ' + TOP_PUMP_DUMP_ALERT_INTERVAL + '\n\n'
        if TOP_PUMP_ENABLED:
            pump_sorted_list = sorted(full_asset, key = lambda i: i[TOP_PUMP_DUMP_ALERT_INTERVAL],reverse=True)[0:VIEW_NUMBER]
            msg += 'Top ' + str(VIEW_NUMBER) + ' PUMP\n'
            print("Top",VIEW_NUMBER,"PUMP")
            for asset in pump_sorted_list: 
                print(asset['symbol'],':',asset[TOP_PUMP_DUMP_ALERT_INTERVAL])
                msg += str(asset['symbol']) + ': ' + str(round(asset[TOP_PUMP_DUMP_ALERT_INTERVAL]*100,2)) + '%\n'

            msg += '\n'

        if TOP_DUMP_ENABLED:
            dump_sorted_list = sorted(full_asset, key = lambda i: i[TOP_PUMP_DUMP_ALERT_INTERVAL])[0:VIEW_NUMBER]
            print("Top",VIEW_NUMBER,"DUMP")
            msg += 'Top ' + str(VIEW_NUMBER) + ' DUMP\n'
            for asset in dump_sorted_list: 
                print(asset['symbol'],':',asset[TOP_PUMP_DUMP_ALERT_INTERVAL])
                msg += str(asset['symbol']) + ': ' + str(round(asset[TOP_PUMP_DUMP_ALERT_INTERVAL]*100,2)) + '%\n'

        send_message(msg)
        
        return time.time()
    else: return last_trigger_pd



