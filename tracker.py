import requests
import time

start= time.time()
response = requests.get("https://api.binance.com/api/v3/ticker/bookTicker?symbol=TORNUSDT")
data = response.json()

print(data)
print("Time taken:",time.time()-start)