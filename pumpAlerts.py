import sys, os
import datetime
import requests
import time
import yaml

from telegram import Bot
from time import sleep


def durationToSeconds(duration):
    unit = duration[-1]
    if unit == "s":
        unit = 1
    elif unit == "m":
        unit = 60
    elif unit == "h":
        unit = 3600

    return int(duration[:-1]) * unit


def sendMessage(message, isTPDA=False):
    if isTPDA:
        if config["telegramAlertChatId"] == 0:
            chatId = config["telegramChatId"]
        else:
            chatId = config["telegramAlertChatId"]
    else:
        chatId = config["telegramChatId"]

    while True:
        try:
            bot.send_message(chat_id=chatId, text=message)
            break
        except:
            print(
                "Retrying to send tele message in",
                config["telegramRetryInterval"],
                "s",
            )
            sleep(config["telegramRetryInterval"])


def searchSymbol(symbol_name, data):
    for asset in data:
        if asset["symbol"] == symbol_name:
            return asset


def getPrices():
    while True:
        try:
            data = requests.get(url).json()
            return data
        except Exception as e:
            print("Error: ", e)
            print("Retrying in", config["priceRetryInterval"], "s")
            sleep(config["priceRetryInterval"])  # Keeps trying every 0.5s


def getPercentageChange(asset_dict):

    data_length = len(asset_dict["price"])

    for inter in config["chartIntervals"]:
        data_points = int(durationToSeconds(inter) / config["extractInterval"])

        if data_points + 1 > data_length:
            break
        elif not config["hardAlertIntervalEnabled"] and (
            time.time() - asset_dict["last_triggered"] < config["hardAlertMin"]
        ):
            break  # Skip checking for period since last triggered
        elif config["hardAlertIntervalEnabled"] and (
            time.time() - asset_dict["lt_dict"][inter] < durationToSeconds(inter)
        ):  # Check for hardAlertIntervalEnabled
            print("Duration insufficient", asset_dict["symbol"], inter)
            break  # Skip checking for period since last triggered
        else:
            change = round(
                (asset_dict["price"][-1] - asset_dict["price"][-1 - data_points])
                / asset_dict["price"][-1],
                5,
            )
            lt_change = round(
                (asset_dict["price"][-1] - asset_dict["lt_price"])
                / asset_dict["price"][-1],
                5,
            )  # Gets % change from last alert trigger
            asset_dict[
                inter
            ] = change  # Stores change for the interval into asset dict (Used for top pump/dumps)

            if (
                abs(change) >= config["outlierParams"][inter]
                and abs(lt_change) >= config["outlierParams"][inter]
            ):
                asset_dict["lt_price"] = asset_dict["price"][
                    -1
                ]  # Updates last triggerd price
                asset_dict[
                    "last_triggered"
                ] = (
                    time.time()
                )  # Updates last triggered time for config['hardAlertMin']
                asset_dict["lt_dict"][
                    inter
                ] = time.time()  # Updates last triggered time for HARD_ALERT_INTERVAL

                if change > 0:
                    if config["debug"]:
                        print(
                            "PUMP: ",
                            asset_dict["symbol"],
                            "/ Change: ",
                            round(change * 100, 2),
                            "/% Price: ",
                            asset_dict["price"][-1],
                            "Interval: ",
                            inter,
                        )
                    sendMessage(
                        config["pumpEmoji"]
                        + " Interval: "
                        + str(inter)
                        + " - "
                        + asset_dict["symbol"]
                        + " / Change: "
                        + str(round(change * 100, 2))
                        + "% / Price: "
                        + str(asset_dict["price"][-1])
                    )
                elif config["dumpEnabled"]:
                    if config["debug"]:
                        print(
                            "DUMP: ",
                            asset_dict["symbol"],
                            "/ Change: ",
                            round(change * 100, 2),
                            "% / Price: ",
                            asset_dict["price"][-1],
                            "Interval: ",
                            inter,
                        )
                    sendMessage(
                        config["dumpEmoji"]
                        + " Interval: "
                        + str(inter)
                        + " - "
                        + asset_dict["symbol"]
                        + " / Change: "
                        + str(round(change * 100, 2))
                        + "% / Price: "
                        + str(asset_dict["price"][-1])
                    )
                # Note that we don't need to break as we have updated 'lt_dict' parameter which will skip the remaining config['chartIntervals']
                return asset_dict  # Prevents continuation of checking other config['chartIntervals']
    return asset_dict


def getAdditionalStatistics(full_asset, inter):  # Net Up, Down & Full Asset
    sum_change = 0
    up = 0
    down = 0
    for asset in full_asset:
        if asset[inter] > 0:
            up += 1
        elif asset[inter] < 0:
            down += 1

        sum_change += asset[inter]
    msg = ""
    avg_change = round((sum_change * 100) / len(full_asset), 2)
    msg += "Average Change: " + str(avg_change) + "%" + "\n"
    msg += (
        config["pumpEmoji"]
        + " "
        + str(up)
        + " / "
        + config["dumpEmoji"]
        + " "
        + str(down)
    )
    return msg


def topPumpDump(last_trigger_pd, full_asset):
    for inter in last_trigger_pd:
        if time.time() > last_trigger_pd[inter] + durationToSeconds(inter) + 8:
            msg = config["tdpaEmoji"]
            msg += " Interval: " + inter + "\n\n"
            if config["topPumpEnabled"]:
                pump_sorted_list = sorted(
                    full_asset, key=lambda i: i[inter], reverse=True
                )[0 : config["viewNumber"]]
                msg += "Top " + str(config["viewNumber"]) + " PUMP\n"
                print("Top", config["viewNumber"], "PUMP")
                for asset in pump_sorted_list:
                    print(asset["symbol"], ": ", asset[inter])
                    msg += (
                        str(asset["symbol"])
                        + ": "
                        + str(round(asset[inter] * 100, 2))
                        + "%\n"
                    )
                msg += "\n"
            if config["dumpEnabled"]:
                dump_sorted_list = sorted(full_asset, key=lambda i: i[inter])[
                    0 : config["viewNumber"]
                ]
                print("Top", config["viewNumber"], "DUMP")
                msg += "Top " + str(config["viewNumber"]) + " DUMP\n"
                for asset in dump_sorted_list:
                    print(asset["symbol"], ": ", asset[inter])
                    msg += (
                        str(asset["symbol"])
                        + ": "
                        + str(round(asset[inter] * 100, 2))
                        + "%\n"
                    )
            if config["additionalStatsEnabled"]:
                msg += "\n" + getAdditionalStatistics(full_asset, inter)
            sendMessage(msg, isTPDA=True)

            last_trigger_pd[inter] = time.time()  # Update time for trigger
    else:
        return last_trigger_pd


def checkTimeSinceReset():  # Used to solve MEM ERROR bug
    global init_time
    global full_data
    if time.time() - init_time > durationToSeconds(
        config["resetInterval"]
    ):  # Clear arrays every 3 hours
        print(
            "Emptying data to prevent mem error"
        )  # Logs to console only, reduces spam
        for asset in full_data:
            asset["price"] = []  # Empty price array
        init_time = time.time()


def checkNewListings(data_t):
    global full_data
    global init_data

    if len(init_data) != len(data_t):

        if len(init_data) > len(data_t):
            return  # If init_data has more than data_t we just ignore it

        init_symbols = [asset["symbol"] for asset in init_data]
        symbols_to_add = [
            asset["symbol"] for asset in data_t if asset["symbol"] not in init_symbols
        ]

        msg = config["newListingEmoji"] + " New Listings" + "\n\n"
        msg += (
            str(len(data_t) - len(init_data))
            + " new pairs found, adding to monitored list"
            + "\n\n"
        )
        msg += "Pairs\n"

        for symbol in symbols_to_add:

            if (
                symbol[-4:] not in config["pairsOfInterest"]
                and symbol[-3:] not in config["pairsOfInterest"]
            ):
                msg += (
                    config["dumpEmoji"] + " Ignore: " + symbol + " \n"
                )  # Ignores pairs not specified
                continue
            tmp_dict = {}
            tmp_dict["symbol"] = symbol
            tmp_dict["price"] = []  # Initialize empty price array
            tmp_dict["lt_dict"] = {}  # Used for HARD_ALERT_INTERVAL
            tmp_dict["last_triggered"] = time.time()  # Used for config['hardAlertMin']
            tmp_dict["lt_price"] = 0  # Last triggered price for alert

            print("Added symbol: ", symbol)
            msg += config["pumpEmoji"] + " Add: " + symbol + "\n"

            for interval in config["chartIntervals"]:
                tmp_dict[interval] = 0
                tmp_dict["lt_dict"][interval] = time.time()
            full_data.append(tmp_dict)
        sendMessage(msg)  # Sends combined message
        init_data = data_t[:]  # Updates init data


# Read config
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
yaml_file = open(os.path.join(__location__, "config.yml"), "r")
config = yaml.load(yaml_file, Loader=yaml.FullLoader)

if config["debug"]:
    print("Config: ", config)

# Initialize telegram bot
try:
    bot = Bot(token=config["telegramToken"])
except Exception as e:
    print("Error initializing Telegram bot")
    print(e)
    quit()

init_dateTime = datetime.datetime.now()
init_time = time.time()

config["extractInterval"] = durationToSeconds(config["extractInterval"])
config["priceRetryInterval"] = durationToSeconds(config["priceRetryInterval"])
config["telegramRetryInterval"] = durationToSeconds(config["telegramRetryInterval"])
config["hardAlertMin"] = durationToSeconds(config["hardAlertMin"])
config["tdpaInitialBuffer"] = durationToSeconds(config["tdpaInitialBuffer"])

if not config["hardAlertIntervalEnabled"]:
    print("config['hardAlertMin']: ", config["hardAlertMin"])
else:
    print("Hard Alert Interval is being used")

print("Extract interval: ", config["extractInterval"])

# Choose whether we look at spot prices or future prices
if config["futuresEnabled"]:
    url = "https://fapi.binance.com/fapi/v1/ticker/price"
else:
    url = "https://api.binance.com/api/v3/ticker/price"

data = getPrices()
init_data = data[:]  # Used for checking for new listings
full_data = []

# Initialize full_data
for asset in init_data:
    symbol = asset["symbol"]

    if (
        "watchlist" in config and len(config["watchlist"]) > 0
    ):  # Meaning config['watchlist'] has variables
        if symbol not in config["watchlist"]:
            continue
    else:  # If config['watchlist'] is empty we take general variables
        if (
            ("UP" in symbol)
            or ("DOWN" in symbol)
            or ("BULL" in symbol)
            or ("BEAR" in symbol)
        ) and ("SUPER" not in symbol):
            print("Ignoring: ", symbol)
            continue  # Remove leveraged config['telegramToken']s
        if (
            symbol[-4:] not in config["pairsOfInterest"]
            and symbol[-3:] not in config["pairsOfInterest"]
        ):
            continue  # Should focus on usdt pairs to reduce noise
    tmp_dict = {}
    tmp_dict["symbol"] = asset["symbol"]
    tmp_dict["price"] = []  # Initialize empty price array
    tmp_dict["lt_dict"] = {}  # Used for HARD_ALERT_INTERVAL
    tmp_dict["last_triggered"] = time.time()  # Used for config['hardAlertMin']
    tmp_dict["lt_price"] = 0  # Last triggered price for alert

    print("Added symbol: ", symbol)
    for interval in config["chartIntervals"]:
        tmp_dict[interval] = 0
        tmp_dict["lt_dict"][interval] = time.time()
    full_data.append(tmp_dict)

print("Following", len(full_data), "pairs")

sendMessage(config["botEmoji"] + " Bot has started")

tpda_last_trigger = {}
for inter in config["tdpaIntervals"]:
    tpda_last_trigger[inter] = (
        time.time() + config["tdpaInitialBuffer"]
    )  # Set TDPA interval
print("TDPA Initial Buffer: ", config["tdpaInitialBuffer"], "seconds")

while True:
    if config["debug"]:
        print("Extracting after", config["extractInterval"], "s")
    start_time = time.time()
    data = getPrices()

    if config["checkNewListingEnabled"]:
        checkNewListings(data)
    checkTimeSinceReset()  # Clears logs if pass a certain time

    for asset in full_data:
        symbol = asset["symbol"]
        sym_data = searchSymbol(symbol, data)
        asset["price"].append(float(sym_data["price"]))
        asset = getPercentageChange(asset)
    topPumpDump(tpda_last_trigger, full_data)  # Triggers check for top_pump_dump

    if config["debug"]:
        print(
            "Extract time: ",
            time.time() - start_time,
            "/ Time ran: ",
            datetime.datetime.now() - init_dateTime,
        )
    while time.time() - start_time < config["extractInterval"]:
        sleep(
            config["extractInterval"] - time.time() + start_time
        )  # Sleeps for the remainder of 1s
        pass  # Loop until 1s has passed to getPrices again
