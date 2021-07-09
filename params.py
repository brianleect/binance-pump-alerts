intervals = ['1s', '5s', '15s', '30s', '1m']
outlier_param = {'1s':0.01,'5s':0.03,'15s':0.05,'30s':0.06,'1m':0.07,'5m':0.10}
pairs_of_interest = ['USDT']
watchlist = []  # E.g. ['ADAUSDT', 'ETHUSDT']
FUTURE_ENABLED=False
DUMP_ENABLED = False
MIN_ALERT_INTERVAL = '15s'
RESET_INTERVAL = '3h'

# Used for telegram bot updates
token = ''  # Insert token obtained from @BotFather here
chat_id = 0  # Refer to chatid