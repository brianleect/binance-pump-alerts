from time import sleep
import time
import datetime
from binance import ThreadedWebsocketManager
from key import api_key, api_secret

def main():

    sym_1 = 'BUSD'
    sym_2 = 'USDT'
    symbol = sym_1 + sym_2

    twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    # start is required to initialise its internal loop
    twm.start()

    def handle_socket_message(msg):
        #print(f"message type: {msg['e']}")
        print(msg)
    
    buy_price = 1
    def triggerBuy(capital):
        print("Buy triggered\nCapital:",capital)
        quantity = capital / buy_price

        # Insert buy

    def triggerSell(token_quant):
        print("Sell triggered\nTokens:",token_quant)
        pass
        # Insert client sell by limit? based on TP
        

    def handle_user_socket_message(msg):
        print("Received:",time.time())
        print(msg)
        if msg['e'] == 'outboundAccountPosition':
            for asset in msg['B']:
                if asset['a'] == 'USDT' and int(float(asset['f'])) >= 200: triggerBuy(int(float(asset['f'])))
                elif asset['a'] == sym_1 and int(float(asset['f'])) >= 10: triggerSell(int(float(asset['f'])))

    #twm.start_kline_socket(callback=handle_socket_message, symbol=symbol)

    # multiple sockets can be started
    #twm.start_depth_socket(callback=handle_socket_message, symbol=symbol)

    # or a multiplex socket can be started like this
    # see Binance docs for stream names
    streams = ['klayusdt@miniTicker', 'klayusdt@aggTrade']
    twm.start_multiplex_socket(callback=handle_socket_message, streams=streams)
    user_stream = twm.start_user_socket(callback=handle_user_socket_message)

    # Implement getting of support line

    #twm.join()

    sleep(600)
    print("Time's up")
    twm.stop()



if __name__ == "__main__":
   main()