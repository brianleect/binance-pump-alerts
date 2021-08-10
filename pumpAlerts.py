import colorlog, logging
import sys, os
import requests
import time
import yaml

from time import sleep
from sender import TelegramSender


def durationToSeconds(duration):
    unit = duration[-1]
    if unit == "s":
        unit = 1
    elif unit == "m":
        unit = 60
    elif unit == "h":
        unit = 3600

    return int(duration[:-1]) * unit


def exctractTickerData(symbol, assets):
    for asset in assets:
        if asset["symbol"] == symbol:
            return asset


def retrieveExchangeAssets(apiUrl, priceRetryIntervalInSeconds):
    while True:
        try:
            logger.debug(
                "Retrieving price information from the ticker. ApiUrl: %s.", apiUrl
            )
            return requests.get(apiUrl).json()
        except Exception as e:
            logger.error(
                "Issue occured while getting prices. Retrying in %ss. Error: %s.",
                priceRetryIntervalInSeconds,
                e,
                exc_info=True,
            )
            sleep(priceRetryIntervalInSeconds)


def isSymbolValid(symbol, watchlist, pairsOfInterest):
    # Filter symbols not in watchlist if set
    if len(watchlist) > 0:
        if symbol not in watchlist:
            logger.debug("Ignoring symbol not in watchlist: %s.", symbol)
            return False

    # Removing leverage symbols
    if (
        ("UP" in symbol)
        or ("DOWN" in symbol)
        or ("BULL" in symbol)
        or ("BEAR" in symbol)
    ) and ("SUPER" not in symbol):
        logger.debug("Ignoring leverage symbol: %s.", symbol)
        return False

    # Filter pairsOfInterest to reduce the noise. E.g. BUSD, USDT, ETH, BTC
    if symbol[-4:] not in pairsOfInterest and symbol[-3:] not in pairsOfInterest:
        logger.debug("Ignoring symbol not in pairsOfInterests: %s.", symbol)
        return False

    return True


def filterAndConvertAssets(exchangeAssets, watchlist, pairsOfInterest, chartIntervals):
    filteredAssets = []

    for exchangeAsset in exchangeAssets:
        symbol = exchangeAsset["symbol"]

        if isSymbolValid(symbol, watchlist, pairsOfInterest):
            filteredAssets.append(createNewAsset(symbol, chartIntervals))
            logger.info("Adding symbol: %s.", symbol)

    return filteredAssets


def createNewAsset(symbol, chartIntervals):
    asset = {}
    asset["symbol"] = symbol
    asset["price"] = []

    for interval in chartIntervals:
        asset[interval] = 0

    return asset


def updateAllMonitoredAssetsAndSendMessages(
    monitoredAssets,
    exchangeAssets,
    dumpEnabled,
    chartIntervals,
    extractIntervalInSeconds,
    outlierIntervals,
):
    for asset in monitoredAssets:
        exchangeAsset = exctractTickerData(asset["symbol"], exchangeAssets)
        asset["price"].append(float(exchangeAsset["price"]))
        asset = calculateAssetChangeAndSendMessage(
            asset,
            dumpEnabled,
            chartIntervals,
            extractIntervalInSeconds,
            outlierIntervals,
        )

    return monitoredAssets


def calculateAssetChangeAndSendMessage(
    asset,
    dumpEnabled,
    chartIntervals,
    extractIntervalInSeconds,
    outlierIntervals,
):
    assetLength = len(asset["price"])

    for interval in chartIntervals:

        dataPoints = int(
            chartIntervals[interval]["intervalInSeconds"] / extractIntervalInSeconds
        )

        # If data is not avalilable yet after restart for interval, stop here.
        if dataPoints >= assetLength:
            break

        # Gets change in % from last alert trigger
        priceDelta = asset["price"][-1] - asset["price"][-1 - dataPoints]
        change = priceDelta / asset["price"][-1]

        # Stores change for the interval into asset dict. Only used for top pump/dump report.
        asset[interval] = change

        if abs(change) >= outlierIntervals[interval]:

            if change > 0:
                telegram.sendPumpMessage(
                    interval,
                    asset["symbol"],
                    change,
                    asset["price"][-1],
                )

            if change < 0 and dumpEnabled:
                telegram.sendDumpMessage(
                    interval,
                    asset["symbol"],
                    change,
                    asset["price"][-1],
                )

    return asset


def resetPricesDataWhenDue(
    initialTimeInSeconds, currentTimeInSeconds, resetIntervalInSeconds, assets
):
    if currentTimeInSeconds - initialTimeInSeconds > resetIntervalInSeconds:
        logger.debug("Emptying price data to prevent memory errors.")
        telegram.sendGenericMessage("Emptying price data to prevent memory errors.")
        for asset in assets:
            asset["price"] = []

        initialTimeInSeconds = currentTimeInSeconds

    return initialTimeInSeconds


def checkAddNewAssetListings(
    initialAssets,
    filteredAssets,
    exchangeAssets,
    watchlist,
    pairsOfInterest,
    chartIntervals,
):

    if len(initialAssets) >= len(exchangeAssets):
        # If initialAssets has more than assets we just ignore it
        return filteredAssets

    initSymbols = [asset["symbol"] for asset in initialAssets]
    retrievedSymbolsToAdd = [
        exchangeAsset["symbol"]
        for exchangeAsset in exchangeAssets
        if exchangeAsset["symbol"] not in initSymbols
    ]

    filteredSymbolsToAdd = []
    for symbol in retrievedSymbolsToAdd:
        if isSymbolValid(symbol, watchlist, pairsOfInterest):
            filteredSymbolsToAdd.append(symbol)
            filteredAssets.append(createNewAsset(symbol, chartIntervals))

    # Sends combined message
    telegram.sendNewListingMessage(filteredSymbolsToAdd)

    return filteredAssets


def checkToSendTopPumpDumpStatisticsReport(
    assets,
    currentTimeInSeconds,
    topReportIntervals,
    topPumpEnabled,
    topDumpEnabled,
    additionalStatsEnabled,
    noOfReportedCoins,
):

    for interval in topReportIntervals:
        if (
            currentTimeInSeconds
            > topReportIntervals[interval]["startTime"]
            + topReportIntervals[interval]["intervalInSeconds"]
            + 8  # Magic number ;)
        ):
            # Update time for new trigger
            topReportIntervals[interval]["startTime"] = currentTimeInSeconds

            telegram.sendTopPumpDumpStatisticsReport(
                assets,
                interval,
                topPumpEnabled,
                topDumpEnabled,
                additionalStatsEnabled,
                noOfReportedCoins,
            )

        return topReportIntervals


# Read config
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
yaml_file = open(os.path.join(__location__, "config.yml"), "r", encoding="utf-8")
config = yaml.load(yaml_file, Loader=yaml.FullLoader)

# Define the log format
log_format = "[%(asctime)s] %(levelname)-8s %(name)-25s %(message)s"

bold_seq = "\033[1m"
colorlog_format = f"{bold_seq} " "%(log_color)s " f"{log_format}"
colorlog.basicConfig(
    # Define logging level according to the configuration
    level=logging.DEBUG if config["debug"] == True else logging.INFO,
    # Declare the object we created to format the log messages
    format=colorlog_format,
    # Declare handlers for the Console
    handlers=[logging.StreamHandler()],
)

# Define your own logger name
logger = logging.getLogger("binance-pump-alerts")

# Logg whole configuration during the startup
logger.debug("Config: %s", config)

initialTimeInSeconds = time.time()

telegram = TelegramSender(
    token=config["telegramToken"],
    retryInterval=durationToSeconds(config["telegramRetryInterval"]),
    chatId=config["telegramChatId"],
    alertChatId=config["telegramAlertChatId"]
    if "telegramAlertChatId" in config and config["telegramAlertChatId"] != 0
    else config["telegramChatId"],
    botEmoji=config["botEmoji"],
    pumpEmoji=config["pumpEmoji"],
    dumpEmoji=config["dumpEmoji"],
    tdpaEmoji=config["tdpaEmoji"],
    newListingEmoji=config["newListingEmoji"],
)

extractIntervalInSeconds = durationToSeconds(config["extractInterval"])
priceRetryIntervalInSeconds = durationToSeconds(config["priceRetryInterval"])
resetIntervalInSeconds = durationToSeconds(config["resetInterval"])

chartIntervals = {}
for interval in config["chartIntervals"]:
    chartIntervals[interval] = {}
    chartIntervals[interval]["intervalInSeconds"] = durationToSeconds(interval)

topReportIntervals = {}
for interval in config["tpdReportsIntervals"]:
    topReportIntervals[interval] = {}
    topReportIntervals[interval]["startTime"] = initialTimeInSeconds
    topReportIntervals[interval]["intervalInSeconds"] = durationToSeconds(interval)

initialAssets = retrieveExchangeAssets(config["apiUrl"], priceRetryIntervalInSeconds)

filteredAssets = filterAndConvertAssets(
    initialAssets,
    [] if "watchlist" not in config else config["watchlist"],
    config["pairsOfInterest"],
    config["chartIntervals"],
)

telegram.sendGenericMessage(
    "*Bot has started.* Following _{0}_ pairs.", len(filteredAssets)
)
if "telegramAlertChatId" in config and config["telegramAlertChatId"] != 0:
    telegram.sendGenericMessage(
        "*Bot has started.* Following _{0}_ pairs.",
        len(filteredAssets),
        isAlertChat=True,
    )

while True:
    startLoopTimeInSeconds = time.time()

    initialTimeInSeconds = resetPricesDataWhenDue(
        initialTimeInSeconds,
        startLoopTimeInSeconds,
        resetIntervalInSeconds,
        filteredAssets,
    )

    exchangeAssets = retrieveExchangeAssets(
        config["apiUrl"], priceRetryIntervalInSeconds
    )

    if config["checkNewListingEnabled"]:
        filteredAssets = checkAddNewAssetListings(
            initialAssets,
            filteredAssets,
            exchangeAssets,
            [] if "watchlist" not in config else config["watchlist"],
            config["pairsOfInterest"],
            config["chartIntervals"],
        )
        # Reset initial exchange asset
        initialAssets = exchangeAssets

    filteredAssets = updateAllMonitoredAssetsAndSendMessages(
        filteredAssets,
        exchangeAssets,
        config["dumpEnabled"],
        chartIntervals,
        extractIntervalInSeconds,
        config["outlierIntervals"],
    )

    topReportIntervals = checkToSendTopPumpDumpStatisticsReport(
        filteredAssets,
        startLoopTimeInSeconds,
        topReportIntervals,
        config["topPumpEnabled"],
        config["topDumpEnabled"],
        config["additionalStatsEnabled"],
        config["noOfReportedCoins"],
    )

    # Sleeps for the remainder of 1s
    sleep(startLoopTimeInSeconds + extractIntervalInSeconds - time.time())
