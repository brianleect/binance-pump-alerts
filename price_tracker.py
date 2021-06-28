import requests
import time

def getPrices():
    url = 'https://api.binance.com/api/v3/ticker/price'
    data = requests.get(url).json()
    return data

data = getPrices()
full_data = []
intervals = ['1s', '5s', '15s', '30s', '1m','15m']
pairs_of_interest = ['USDT','BTC']

# Initialize full_data
for asset in data:
    tmp_dict = {}
    tmp_dict['symbol'] = asset['symbol']
    tmp_dict['price'] = [] # Initialize empty price array

    for interval in intervals:
        tmp_dict[interval] = 0
    
    full_data.append(tmp_dict)

def searchSymbol(symbol_name):
    for asset in full_data:
        if asset['symbol'] == symbol_name: return asset

def getPercentageChange(asset_dict):

    data_length = len(asset_dict['price'])

    intervals = ['1s', '5s', '15s', '30s', '1m','15m']
    outlier_param = {'1s':0.01,'5s':0.01,'15s':0.01,'30s':0.01,'1m':0.01,'15m':0.10}

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

            if change >= outlier_param[inter]: print("Abnormal movement detected:",asset_dict['symbol'],'/ Change:',change,'/ Interval:',inter) # Possibly send telegram msg instead
    
    return asset_dict


count=0
while True:
    count+=1
    #if count == 10: break
    print("Extracting after 1s")
    start_time = time.time()
    data = getPrices()

    for asset in data:
        symbol = asset['symbol']
        sym_data = searchSymbol(symbol)
        sym_data['price'].append(float(asset['price']))
        sym_data = getPercentageChange(sym_data)

    # Check for outlier movement of percentages


    # Get market avg?

    print("Time taken to extract and append:",time.time()-start_time)
    while time.time() - start_time < 1: pass # Loop until 1s has passed to getPrices again

print(full_data)