from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager

api = "key"
secret = "secret"

client = Client(api, secret, testnet=True)

import pandas as pd
import pandas_ta as ta
import f

class PairInstrument:

    def __init__(self):
        self.fut_price_now = 0
        self.history_fut_prices = pd.DataFrame
        self.timer_m = 0
        self.timer_s = 0
        self.mark_price = 0
        self.instrument = 'OPUSDT'

    def get_history_data(self):
        delta = f.time_delta_hours(5)
        klines = client.futures_historical_klines(self.instrument, Client.KLINE_INTERVAL_1MINUTE, delta[0], delta[1])
        df = pd.DataFrame(klines, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df['Time'] = pd.to_datetime(df['Time'], unit='ms')
        df.set_index('Time', inplace=True)
        df = df.astype(float)
        df.ta.adjusted = True
        df.ta.datetime = "Time"
        df.ta.volume = "Volume"
        df.ta.high = "High"
        df.ta.low = "Low"
        df.ta.close = "Close"
        df.ta.ema(length=100, append=True)
        df.ta.macd(append=True)
        df['ATR']=ta.atr(df['High'], df['Low'], df['Close'], length=5)
        self.history_fut_prices = df

    def get_now_price(self):
        self.fut_price_now = round(float((client.futures_ticker(symbol=self.instrument))['lastPrice']), 4)

    def get_mark_price(self):
        self.mark_price = round(float((client.futures_mark_price(symbol=self.instrument))['markPrice']), 4)

    def get_orders(self):
        return client.get_open_orders(symbol=self.instrument)

    def timer_tick(self):
        self.timer_s += 1
        if self.timer_s == 60:
            self.timer_m += 1
            self.timer_s = 0


def accept_long(macd, ema, now_price, last_close, minute_time):
    if minute_time == 43 and now_price > last_close and macd[-2] > macd[-3] and macd[-3] < macd[-4]:# and now_price > ema[-2]:
        print("LONG!")
        return True
    else:
        return False
    
def accept_short(macd, ema, now_price, last_close, minute_time):
    if minute_time == 43 and now_price < last_close and macd[-2] < macd[-3] and macd[-3] > macd[-4]:# and now_price < ema[-2]:
        print("SHORT!")
        return True
    else:
        return False
    
def crossover(series1, series2, minute_time):
    if series1[-2] < series2[-2] and series1[-1] > series2[-1] and minute_time == 44:
        return True
    else:
        return False
    
def cross(series1, series2, minute_time):
    return crossover(series1, series2, minute_time) or crossover(series2, series1, minute_time)


def tp_accept_long(macd, ema, now_price, last_close, minute_time):
    if minute_time == 43 and now_price > last_close and macd[-2] > macd[-3] and macd[-3] > macd[-4] and macd[-4] < macd[-5]: #and now_price > ema[-2]:
        print("TP_LONG!")
        return True
    else:
        return False
    

def tp_accept_short(macd, ema, now_price, last_close, minute_time):
    if minute_time == 43 and now_price < last_close and macd[-2] < macd[-3] and macd[-3] < macd[-4] and macd[-4] > macd[-5]: #and now_price < ema[-2]:
        print("TP_SHORT!")
        return True
    else:
        return False

pair = PairInstrument()

class Trader:

    def __init__(self):
        self.pos = False
        self.long_or_short = "None"
        self.sl1 = 0
        self.tp1 = 0

    def strategy(self, history_fut_prices_MACD, history_fut_prices_EMA, fut_price_now, history_fut_prices_Close_last, timer_s, slatr, TPSLRatio, quantity):
        if accept_long(history_fut_prices_MACD, history_fut_prices_EMA, fut_price_now, history_fut_prices_Close_last, timer_s) and self.pos==False:
            self.sl1 = pair.history_fut_prices['Close'][-1] - slatr
            self.tp1 = pair.history_fut_prices['Close'][-1] + slatr*TPSLRatio
            order = client.futures_create_order(
                symbol=pair.instrument,
                side="BUY",
                type='MARKET',
                quantity=quantity
            )
            self.long_or_short = "Long"
            self.pos = True

        if self.pos == True and self.long_or_short == "Long" and (fut_price_now.__round__(8) <= self.sl1.__round__(8) or fut_price_now.__round__(8) >= self.tp1.__round__(8)):
            order = client.futures_create_order(
                symbol=pair.instrument,
                side="SELL",
                type='MARKET',
                quantity=quantity
            )
            self.long_or_short = "None"
            self.pos = False

        if accept_short(history_fut_prices_MACD, history_fut_prices_EMA, fut_price_now, history_fut_prices_Close_last, timer_s) and self.pos==False:
            self.sl1 = pair.history_fut_prices['Close'][-1] + slatr
            self.tp1 = pair.history_fut_prices['Close'][-1] - slatr*TPSLRatio
            order = client.futures_create_order(
                symbol=pair.instrument,
                side="SELL",
                type='MARKET',
                quantity=quantity
            )
            self.long_or_short = "Short"
            self.pos = True

        if self.pos == True and self.long_or_short == "Short" and (fut_price_now.__round__(8) >= self.sl1.__round__(8) or fut_price_now.__round__(8) <= self.tp1.__round__(8)):
            order = client.futures_create_order(
                symbol=pair.instrument,
                side="BUY",
                type='MARKET',
                quantity=quantity
            )
            self.long_or_short = "None"
            self.pos = False

        if self.pos == True and (self.long_or_short == "Short" or self.long_or_short == "Long") and (tp_accept_short(history_fut_prices_MACD, history_fut_prices_EMA, fut_price_now, history_fut_prices_Close_last, timer_s) or tp_accept_long(history_fut_prices_MACD, history_fut_prices_EMA, fut_price_now, history_fut_prices_Close_last, timer_s)):
            if self.long_or_short == "Short":
                order = client.futures_create_order(
                symbol=pair.instrument,
                side="BUY",
                type='MARKET',
                quantity=quantity
            ) 
            else:
                order = client.futures_create_order(
                symbol=pair.instrument,
                side="SELL",
                type='MARKET',
                quantity=quantity
            )
            self.long_or_short = "None"
            self.pos = False


bank = 300

trader = Trader()

import time

while True:

    print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
    pair.timer_tick()
    print("Minutes:", pair.timer_m)
    print("Seconds:", pair.timer_s)
    #if pair.timer % 10 == 0:
    pair.get_now_price()
    pair.get_history_data()
    slatr = 0.5 * pair.history_fut_prices['ATR'][-1]
    TPSLRatio = 7
    pair.get_mark_price()
    my_cash = 280
    quantity = round(280 / float(pair.mark_price), 4)
    quantity = (quantity/4).__round__(4)
    
    print("Seconds:", quantity)

    trader.strategy(
        history_fut_prices_MACD=pair.history_fut_prices['MACD_12_26_9'], 
        history_fut_prices_EMA=pair.history_fut_prices['EMA_100'], 
        fut_price_now=pair.fut_price_now, 
        history_fut_prices_Close_last=pair.history_fut_prices['Close'][-2], 
        timer_s=pair.timer_s, 
        slatr=slatr, 
        TPSLRatio=TPSLRatio, 
        quantity=quantity)

    print(pair.history_fut_prices.index[-2], pair.history_fut_prices['Close'][-2])
    print(pair.history_fut_prices.index[-1], pair.history_fut_prices['Close'][-1])
    print("Now price:", pair.fut_price_now)
    print("Mark price:", pair.mark_price)
    print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')


    #print("Количество открытых позиций: ", len(pair.get_orders()))

    time.sleep(1)

### ----------------------- ЗАПУСКАТЬ ПО ИСТЕЧЕНИЮ МИНУТКИ ----------------------- ###