# Binance Pump Alerts

BPA is a simple application which gets the price data from Binance Spot or Futures API and sends Telegram messages based on parameters set used to detect pumps and dumps on the Binance Exchange.

[Demo Telegram Channel](https://t.me/binance_pump_alerts) hosted on AWS ec2 running the 'Base Stable Version' release 24/7.

![image](https://user-images.githubusercontent.com/63389110/128601355-4be90b36-5e54-4be6-bf85-00fc395645de.png)

## Manual Setup

1. On the command-line, run the command `pip install -r requirements.txt` while located at folder with code.
1. Create a new telegram bot token from [@botfather](https://t.me/BotFather).
1. Get telegram `chat_id` from [@get_id_bot](https://telegram.me/get_id_bot).
   - Alternatively, a `channel_id` can be used as well.
1. Add pairs to watch into the watchlist or leave it empty to monitor all tickers on Binance.
1. Run the script with the command `python pumpAlerts.py`.

## Docker Setup

1. Use environment variables in the `docker-compse.yml` file to provide your config.
   - See `entrypoint.sh` for environment variable names and the config possibilities.
   - You can also use a `.env` file during development.
   - If changing the config parameters, you have to make sure that search and replace will place the right parameter in the `config.yml`
   - Emojis are more tricky therefore defining it with some tricks e.g. `PUMP_EMOJI="! \"\\\\U0001F4B9\""`
1. On the command line run `docker-compose up -d --build` to create and run the docker image/container.

## Configuration

### Mandatory Params

1. `telegramToken`: The token obtained from[@botfather](https://t.me/BotFather).
2. `telegramChatId`: The bot will send the messages to this `chat_id`. It can be a group or channel as well.

## Main Customizable Params

1. `chartIntervals`: Can be modified to consider other timeframes, follow the format of 's' for seconds, 'm' for minutes, 'h' for hours.
1. `outlierIntervals`: (0.01 -> 1% , 0.1 -> 10%), modify accordingly based on needs. Avoid setting it too low to avoid noise.
1. `extractInterval`: Default is `1s`, Interval at which we retrieve the price information from Binance.
1. `pairsOfInterest`: Default is _USDT_. Other options include BUSD, BTC, ETH etc.
1. `topReportIntervals`: Default is `1h`,`3h`and `6h` Intervals for top pump and dump reports to be sent, ensure it is in chartIntervals + outlierIntervals as well.

### Optional features to enable

1. `watchlist`: Default if left empty it'll look at ALL symbols after filtering by pairs of interest. If pairs are added to the watchlist, the application will _only track the pairs specified_.
1. `dumpEnabled`: If `True`, the application will alert on dumps as well.

#### Top Pump & Dump Params

1. `topPumpEnabled`: If `True`, the application will send the Top X pumps at the defined interval.
1. `topDumpEnabled`: If `True`, the application will send the Top X dumps at the defined interval.
   - Together with pump information, if enabled.
1. `noOfReportedCoins`: Top X amount of coins shown, adjust to show more or less within the timeframe.
1. `telegramAlertChatId`: Insert the alert chat_id for top pump dump alert, if left at `0`, it'll send messages to the telegram `chat_Id`.
   For params not indicated above, refer to comments besides parameter for its use.

#### Debug Params (Avoid modifying if possible!)

1. `debug`: Default is `False`. Please, only enable for debugging purposes. Default logging set to info level.
1. `resetInterval`: Default `12h`. It clears the array used to store data price points to prevent memory issues.
1. `priceRetryInterval`: Default `5s`. In the case of get price fail, this is the time delay before re-attempt
1. `checkNewListingEnabled`: Default `True`. Enables checking and adding of new listing pairs.

## Todo

1. Integrate with Binance API to make trades on pumps.
1. Integrate with Binance Websocket API to get volume information.
1. Integrate with listing-predictor to monitor movements for potential listings.

## Completed features

1. Telegram integration
1. Price update every 1s
1. Adjustable alert % param (outliers)
1. Watchlist feature
1. Monitor future markets
1. Optional alert on dumps
1. Customizable minimum alert interval for spam prevention
1. Option to disable print debugs on extraction
1. [Test] Volume Change Updates (TEST_VOL version)
1. Allows long period of running without memory issues
1. Send periodic Top X Pump & Dump reports
1. Docker integration (Thanks to [@patbaumgartner](https://github.com/patbaumgartner))
1. Logging integration (Thanks to [@patbaumgartner](https://github.com/patbaumgartner))
1. Major Refactoring and cleanup (Thanks to [@patbaumgartner](https://github.com/patbaumgartner))
