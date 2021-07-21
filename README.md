# Binance-pump-alerts

Simple application which gets price data from binance API and sends telegram message based on parameters set used to detect pumps in Binance.

Working demo telegram channel: https://t.me/binance_pump_alerts

## Usage

1. In command line run ```pip install -r requirements.txt``` while located at folder with code.
2. Get telegram bot token from @botfather https://t.me/BotFather
3. Get telegram chat_id from @get_id_bot https://telegram.me/get_id_bot (Alternatively channel id can be used as well which is shown in demo)
4. Add pairs to watch into watchlist or leave it empty to monitor all tickers on binance
5. Run "price_tracker.py" with command ```python price_tracker.py```

### (TEST_VOL VERSION) (Outputs change in volume relative to the previous interval)
1. Same usage, but minimum interval is 2s (Buggy partially working), recommended to use any interval >2s E.g. 5s instead. 

## Further explanation on parameters file
1. Intervals: Can be modified to consider other timeframes, follow the format of 's' for second, 'm' for minute, 'h' for hour
2. Outlier param: (0.01 -> 1% , 0.10 -> 10%), modify accordingly based on needs. Avoid setting it too low or there might be quite a bit of spam.
3. Pairs of interest: Default is USDT and BTC, 
4. Watchlist: Default if left empty it'll look at ALL symbols after filtering by pairs of interest. If pairs are added to watchlist, program will **only track the pairs specified**.
5. FUTURE_ENABLED: If true program will monitor **future** market else it will monitor **spot** market.
6. DUMP_ENABLED: If true program will alert on **DUMP** as well.
7. MIN_ALERT_INTERVAL: Default '15s' will not trigger another alert within same pair for the specified duration
8. RESET_INTERVAL: Default '3h', clears the array used to store data points to prevent MEM ERROR (Still testing), customizable as well
9. PRINT_DEBUG: Default 'True', sends extraction messages and duration
8. Token: Telegram bot token obtained from @BotFather
9. Chat_id: Bot will send message to this id, it can be a group or channel as well. To get personal chat_id, get it from @get_id_bot

For params not indicated above, refer to comments besides parameter for its use.

## Todo
1. Integrate with binance API to make trades on pumps
2. Integrate with listing-predictor to monitor movements for potential listings

## Completed features
1. Telegram integration
2. Price Update every 1s
3. Adjustable alert % param
4. Watchlist feature
5. Monitor future markets
6. Optional alert on dumps
7. Customizable minimum alert interval for spam prevention
8. Option to disable print debugs on extraction
9. [Test] Volume Change Updates (TEST_VOL version)
10. Allows long period of running without MEM ERROR
11. Send periodic Top X dumped / pumped coins
