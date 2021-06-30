# binance-price-tracker

Simple application which gets price data from binance API and sends notification based on parameters set for % change.

Working demo telegram channel: https://t.me/binance_pump_alerts

## Usage

1. In command line run ```pip install -r requirements.txt``` while located at folder with code.
2. Get telegram bot token from @botfather https://t.me/BotFather
3. Get telegram chat_id from @get_id_bot https://telegram.me/get_id_bot (Alternatively channel id can be used as well which is shown in demo)
4. Add pairs to watch into watchlist or leave it empty to monitor all tickers on binance
5. Run "price_tracker.py" with command ```python price_tracker.py```

## Further explanation on parameters file
1. Intervals: Can be modified to consider other timeframes, follow the format of 's' for second, 'm' for minute, 'h' for hour
2. Outlier param: (0.01 -> 1% , 0.10 -> 10%), modify accordingly based on needs. Avoid setting it too low or there might be quite a bit of spam.
3. Pairs of interest: Default is USDT and BTC, 
4. Watchlist: Default if left empty it'll look at ALL symbols after filtering by pairs of interest. If pairs are added to watchlist, program will **only track the pairs specified**.
5. Token: Telegram bot token obtained from @BotFather
6. Chat_id: Bot will send message to this id, it can be a group or channel as well. To get personal chat_id, get it from @get_id_bot

## Todo
1. Integrate with binance API to make trades on pumps
2. Possibly improve on efficiency for storing data points
3. Integrate with listing-predictor to monitor movements for potential listings

## Completed features
1. Telegram integration
2. Update every 1s
3. Adjustable parameters for % based on intervals
4. Watchlist feature
