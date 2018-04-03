from bittrex.bittrex import Bittrex
import requests
import time
import config
import logging

def createLogger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    filehandler = logging.FileHandler('log.log')
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)
    return logger

class Trader(Bittrex):
    def __init__(self):
        Bittrex.__init__(self, config.api_key, config.api_secret)
        self.logger = createLogger()
        self.logger.info("New Trader Created")
    
    def handle_resp(self, resp):
        
        if resp['success']:
            msg = str(resp['result'])[:100]
            self.logger.info(msg)
            return resp['result']
        else:
            msg = str(resp['result'])[:100]
            self.logger.info(msg)
            return resp['message']

    def GET_BALANCES(self):
        return self.handle_resp(self.get_balances())
    
    def GET_CURRENCIES(self):
        return self.handle_resp(self.get_currencies())
    
    def GET_TICKER(self, market):
        return self.handle_resp(self.get_ticker(market))

    def LIMIT_BUY(self, market, quantity, rate):
        return self.handle_resp(self.buy_limit(market, quantity, rate))
   
    def LIMIT_SELL(self, market, quantity, rate):
        return self.handle_resp(self.sell_limit(market, quantity, rate))
    
    def GET_OPEN_ORDERS(self, market=None):
        return self.handle_resp(self.get_open_orders(market=market))
    
    def CANCEL_ORDER(self, uuid):
        return self.handle_resp(self.cancel(uuid))
    
    def GET_ORDER(self, uuid):
        return self.handle_resp(self.get_order(uuid))
    
    def GET_ORDER_BOOK(self, market, type):
        return self.handle_resp(self.get_orderbook(market, depth_type=type))

    def trade_asset(self, order, market, quantity, rate, pause_sec, check_times, filled_trigger):
        if order == "sell":
            order_uuid = self.LIMIT_SELL(market, quantity, rate)
        elif order == "buy":
            order_uuid = self.LIMIT_BUY(market, quantity, rate)
        if "uuid" not in order_uuid:
            self.logger.warn(order_uuid)
            return -1
        counter = 0
        
        while True:
            if counter > 0:
                time.sleep(pause_sec)
                self.logger.info("Waiting: {}".format(counter))
            order_details = self.GET_ORDER(order_uuid["uuid"])
            remain_amt = order_details["QuantityRemaining"]
            filled_pct = 1 - (remain_amt / quantity)
            counter +=1
            if not (counter < check_times and filled_pct < filled_trigger):
                break
        if remain_amt > 0:
            cancel = self.CANCEL_ORDER(order_uuid["uuid"])
            if cancel != None:
                self.logger.warn(cancel)
                return -2
            self.logger.info("remaining order cancelled")
        return order_details

    def buy_asset(self, market, quantity, buy_rate, pause_sec, check_times, filled_trigger):
        return self.trade_asset("buy", market, quantity, buy_rate, 
                                pause_sec, check_times, filled_trigger)

    def sell_asset(self, market, quantity, sell_rate, pause_sec, check_times, filled_trigger):
        return self.trade_asset("sell", market, quantity, sell_rate, 
                                pause_sec, check_times, filled_trigger)
    
    def task1(self, sleepTime):
        # enter repetative task here
        print(self.GET_TICKER("USDT-BTC"))
        time.sleep(sleepTime)

if __name__ == '__main__':
    t1 = Trader()
    while True:
        t1.task1(sleepTime=5)
        