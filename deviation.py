class PairInstrument:
    def __init__(self):
        self.eth = 0
        self.btc = 0
        self.old_eth = 0
        self.old_btc = 0
        self.deviation = 0
        self.percent_d = 0
        self.timer = 0
        self.expected_ratio = 6751/616
        self.real_ratio = 6751/616
        self.ratio_of_ratio = 0
        self.calc_f_trigger = False
        self.delta_eth = 0
        self.delta_btc = 0
        self.change_price_percent = 0

        self.oldest_eth_trigger = True
        self.oldest_eth = 0

    def get_eth(self, eth):
        self.eth = eth

    def get_btc(self, btc):
        self.btc = btc

    def make_oldest_eth(self):
        if self.oldest_eth_trigger:
            self.oldest_eth == self.eth
            self.oldest_eth_trigger = False
            
    def timer_tick(self):
        self.timer += 1
        if self.timer == 3600:
            self.timer == 0
            self.change_price_percent = ((self.eth - self.oldest_eth) / self.oldest_eth) * 100
            self.oldest_eth_trigger = True
            if self.change_price_percent >= 1 or self.change_price_percent <= -1:
                print("Deviation is", self.percent_d)
    
    def time_calc(self):
        if self.timer % 10 == 0:
            if self.calc_f_trigger == True:
                self.delta_eth = self.old_eth - self.eth
                self.delta_btc = self.old_btc - self.btc
                self.real_ratio = round(self.delta_btc / (self.delta_eth + 0.00000000000000001), 8)

            self.ratio_of_ratio = round(self.real_ratio / (self.expected_ratio + 0.00000000000000001), 8)

            
            self.deviation = round(self.deviation + (round(self.real_ratio, 1) - round(self.expected_ratio, 1)), 1)
            if self.timer % 100 == 0:
                self.deviation = 0

            
            self.percent_d = round(((self.real_ratio - self.expected_ratio - 0.00000000000000001) / (self.expected_ratio + 0.00000000000000001)) * 100, 3)
             
            self.old_eth = self.eth
            self.old_btc = self.btc
            self.calc_f_trigger = True


        

from binance import AsyncClient, BinanceSocketManager
import asyncio
import time

class Session():
    
    def __init__(self):
        self.api =    "key"
        self.secret = "secret"
        self.pair = PairInstrument()
        self.client = AsyncClient()

    async def __fetch_lastprices(self):
        fut_btc_usdt = round(float((await self.client.futures_ticker(symbol='BTCUSDT'))['lastPrice']), 1)
        self.pair.get_btc(fut_btc_usdt)
        fut_eth_usdt = round(float((await self.client.futures_ticker(symbol='ETHUSDT'))['lastPrice']), 2)
        self.pair.get_eth(fut_eth_usdt)

    async def start(self):
        self.client = await AsyncClient.create(self.api, self.secret)
        
        while True:
            await self.__fetch_lastprices()
            self.pair.time_calc()
            self.pair.make_oldest_eth()
            self.pair.timer_tick()
            print("+++++++++++++++++++++++++++++++++++++++++++")
            print("ETH:", self.pair.eth)
            print("BTC:", self.pair.btc)
            print("Timer:", self.pair.timer)
            print("Real ratio:", self.pair.real_ratio)
            print("Ratio of ratio:", self.pair.ratio_of_ratio)
            print("Deviation:", self.pair.deviation)
            print("Deviation (%):", self.pair.percent_d) 
            print("+++++++++++++++++++++++++++++++++++++++++++")
            time.sleep(1)

# - в противоположную + в одну

if __name__ == "__main__":
    s = Session()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(s.start())