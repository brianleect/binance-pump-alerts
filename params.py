intervals = ['1s','5s','15s', '30s', '1m']
outlier_param = {'1s':0.02,'5s':0.03,'15s':0.06,'30s':0.08,'1m':0.1,'5m':0.10}
pairs_of_interest = ['USDT'] # Other options include 'BTC' , 'ETH'
watchlist = []  # E.g. ['ADAUSDT', 'ETHUSDT'] # Note that if watchlist has pairs, ONLY pairs in watchlist will be monitored

FUTURE_ENABLED=False # Determine whether to look at future markets
DUMP_ENABLED = True # Determine whether to look at DUMP
MIN_ALERT_INTERVAL = '15s' # Minimum interval between alerts for SAME pair
EXTRACT_INTERVAL = '1s' # Minimum interval is 2s but reccommend for 5s and above due to 10054 errors. 

# Debug Params (Avoid touching it if there's no issues)
PRINT_DEBUG = True # If false we do not print messages
RESET_INTERVAL = '3h' # Interval for clearing array to prevent MEM ERROR
GET_PRICE_FAIL_INTERVAL = '1s' # In the case of get price fail, this is the time delay before re-attempt
SEND_TELEGRAM_FAIL_INTERVAL = '1s' # If telegram message fails to send, this is the time delay before re-attempt

# Used for telegram bot updates
token = ''  # Insert token obtained from @BotFather here
chat_id = 0 # Insert chat id