from bittrex import Bittrex
from exceptions import API_Timeout
import requests
import time
import config
import logging
import random

def createFileLogger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler('log.csv')
    formatter = logging.Formatter('%(asctime)s,%(message)s', 
                                  datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


class Trader(Bittrex):
    def __init__(self):
        Bittrex.__init__(self, config.api_key, config.api_secret)
        self.fileLogger = createFileLogger()
        self.status = "setting up"
        self.fileLogger.info(self.status)

    def fileLog(self, msg):
        logMsg = ','.join(map(str, msg))
        self.fileLogger.info(logMsg)
    
    def updateCSV(self):
        '''Enter the variables you want to log, starting with self.status'''
        self.fileLog([self.status,
                      self.r1, 
                      self.r2, 
                      self.r3,
                      self.data])

    def handle_resp(self, resp):
        if resp['success']:
            return resp['result']
        else:
            raise API_Timeout
            #return resp['message']

    def shut_down(self, msg):
        self.status = "shutting down: " + msg
        self.fileLogger.info(self.status)

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
        self.trading_routine()
        self.updateCSV()
        time.sleep(sleepTime)

    def trading_routine(self):
        self.status = "In trading rountine"
        print(self.status)
        # enter trading routine here
        # update variables: for example r1, r2, r3, data
        self.r1 = random.randint(1,5)
        self.r2 = random.randint(1,5)
        self.r3 = random.randint(1,5)
        self.data = "dummy data"
        #self.data = self.GET_TICKER('USDT-BTC')
        

if __name__ == '__main__':
    t1 = Trader()
    while True:
        try:
            t1.task1(sleepTime=1)
        except API_Timeout:
            t1.shut_down("API Timeout")
            break
        except KeyboardInterrupt:
            t1.shut_down("Keyboard Interrupt")
            break