# Binance-pump-alerts

Simple application which gets price data from binance API and sends telegram message based on parameters set used to detect pumps in Binance.

Working demo telegram channel: https://t.me/binance_pump_alerts (Hosted on AWS ec2 running latest version 24/7)

![image](https://user-images.githubusercontent.com/63389110/128601355-4be90b36-5e54-4be6-bf85-00fc395645de.png)

## Usage

1. In command line run `pip install -r requirements.txt` while located at folder with code.
2. Get telegram bot token from @botfather https://t.me/BotFather
3. Get telegram chatId from @get_id_bot https://telegram.me/get_id_bot (Alternatively channel id can be used as well which is shown in demo)
4. Add pairs to watch into watchlist or leave it empty to monitor all tickers on binance
5. Run "pumpAlerts.py" with command `python pumpAlerts.py`


### Mandatory Params

1. TelegramToken: Telegram bot telegramToken obtained from @BotFather
2. TelegramChatId: Bot will send message to this id, it can be a group or channel as well. To get personal telegramChatId, get it from @get_id_bot


## Main Customizable Params

1. chartIntervals: Can be modified to consider other timeframes, follow the format of 's' for second, 'm' for minute, 'h' for hour
2. Outlier param: (0.01 -> 1% , 0.10 -> 10%), modify accordingly based on needs. Avoid setting it too low to avoid noise
3. extractInterval: Default '1s' , interval at which we get the price information from Binance
4. Pairs of interest: Default is USDT (Other options include BTC, ETH etc)


### Alert Interval Params

1. hardAlertIntervalEnabled: (Main) Prevents triggering of same interval for the timeframe of the interval. E.g. '5m' triggers. Will not trigger intervals >= '5m' for 5 minutes. Other intervals < '5m' such as '1s' , '5s' will continue being triggered.
2. HardAlertMin: (Legacy) Set hardAlertIntervalEnabled to false to enable this. Does not trigger another alert within same pair for the specified duration


### Optional features to enable

1. Watchlist: Default if left empty it'll look at ALL symbols after filtering by pairs of interest. If pairs are added to watchlist, program will **only track the pairs specified**.
2. FuturesEnabled: If true program will monitor **future** market else it will monitor **spot** market.
3. DumpEnabled: If true program will alert on **DUMP** as well.

#### Top Pump & Dump Params

1. TopPumpEnabled: If true program will send top X pumps at defined interval
2. TopDumpEnabled: If true program will send top X dumps at defined interval (Together with pump information if enabled)
3. ViewNumber: Top X amount of coins shown, adjust to show more or less within the timeframe
4. TelegramAlertChatId: Insert Chat ID for top pump dump alert, if left at 0 it'll send to telegramChatId
   For params not indicated above, refer to comments besides parameter for its use.

#### Debug Params (Avoid modifying if possible)
1. Debug: Default 'False', only enable for debugging. Logging set to info level message and above
2. ResetInterval: Default '12h', clears the array used to store data points to prevent MEM ERROR
3. priceRetryInterval: Default '1s' # In the case of get price fail, this is the time delay before re-attempt
4. telegramRetryInterval: Default '1s' # If telegram message fails to send, this is the time delay before re-attempt
5. tdpaInitialBuffer: Default '5m' # Initial buffer before we trigger TDPA. Prevents all 0% output due to lack of data points
6. checkNewListingEnabled: True # Disables checking and adding of new listing pairs. 


---

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
12. Docker Integration (Thanks to @patbaumgartner)
13. Logging Integration (Thanks to @patbaumgartner)
