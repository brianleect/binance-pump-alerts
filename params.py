# Main params
intervals = ['1s','5s','15s', '30s', '1m','15m','30m','1h','3h','6h']
outlier_param = {'1s':0.02,'5s':0.05,'15s':0.06,'30s':0.08,'1m':0.1,'5m':0.10,'15m':0.15,'30m':0.20,'1h':0.30,'3h':0.4,'6h':0.5}
pairs_of_interest = ['USDT'] # Other options include 'BTC' , 'ETH'

# Used for telegram bot updates
token = ''  # Insert token obtained from @BotFather here
chat_id = 0 # Insert Chat ID
tpdpa_chat_id = 0 # Insert Chat ID for top pump dump alert, if left at 0 it'll send to chat_id

# Useful Params
EXTRACT_INTERVAL = '1s'  # Interval between each price extract

# Alert Interval Params
HARD_ALERT_INTERVAL_ENABLED = True # If set to true, if '5m' is triggered, any interval >= '5m' will rest for '5m' before triggering
MIN_ALERT_INTERVAL = '5m' # Minimum interval between each Alert  # Only will be utlized when HARD_ALERT_INTERVAL is False. 

# Optional Watchlist only mode
watchlist = []  # E.g. ['ADAUSDT', 'ETHUSDT'] # Note that if watchlist has pairs, ONLY pairs in watchlist will be monitored

# Feature params
FUTURE_ENABLED=False # Determine whether to look at future markets
DUMP_ENABLED = True # Determine whether to look at DUMP

# Top Pump & Dump Feature Params
TOP_PUMP_ENABLED = True # Set to false if not interested in top pump info
TOP_DUMP_ENABLED = True # Set to false if not interested in top dump info
ADDITIONAL_STATS_ENABLED = True # Set to false if not interested in net movement of coins
VIEW_NUMBER = 5 # Top X amount of coins shown, adjust to show more or less within the timeframe
TDPA_INTERVALS = ['3h'] # Intervals for top pump and dump to be sent, Ensure its in interval + outlier_param as well

# Visual Params
PUMP_EMOJI = '\U0001F7E2' #	🟢 or '\U0001F4B9' 💹 
DUMP_EMOJI = '\U0001F534' # 🔴 or '\U0001F4C9' 📉
TDPA_EMOJI = '\U0001F3C6' # 🏆

# Debug Params (Avoid touching it if there's no issues)
PRINT_DEBUG = True # If false we do not print messages
RESET_INTERVAL = '12h' # Interval for clearing array to prevent MEM ERROR can handle up to 12h+ depending on system
GET_PRICE_FAIL_INTERVAL = '1s' # In the case of get price fail, this is the time delay before re-attempt
SEND_TELEGRAM_FAIL_INTERVAL = '1s' # If telegram message fails to send, this is the time delay before re-attempt
TDPA_INITIAL_BUFFER = '5m'
CHECK_NEW_LISTINGS_ENABLED = True # Set to false for debugging only