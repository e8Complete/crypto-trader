import os
import time
import argparse
import pandas as pd
from utils.contants import Constants
from utils.logger import setup_logger
from binance.client import Client
from indicators.relative_strength_index.rsi import RSI


class TradingAPI(Client):
    def __init__(self, args, logger=None):
        self.logger = logger if logger else setup_logger(__name__)
        if args.symbols:
            self.symbols = args.symbols.split(',')
        else:
            self.symbols = Constants.DEFAULT_SYMBOLS
        if args.kline_interval:
            self.kline_interval = args.kline_interval
        else:
            self.kline_interval = Constants.KLINE_INTERVALS['5m']
        if args.kline_start:
            self.kline_start = args.kline_start
        else:
            self.kline_start = Constants.KLINE_START_STRING_EXAMPLES[1]
        if args.dont_run_testnet:
            self.testnet = not args.dont_run_testnet 
        else:
            self.testnet = True
        self.data = {}

    def run(self):
        init_time = time.perf_counter()
        self.logger.info("Initializing Trading API...")
        self.logger.info("Using symbols: %s" % ", ".join(self.symbols))
        self.client = Client(os.environ.get('BINANCE_KEY'),
                             os.environ.get('BINANCE_SECRET'),
                             testnet=self.testnet)
        self.rsi_api = RSI()
        self.logger.info("Fetching historical price data...")
        for sym in self.symbols:
            self.logger.info("Loading % price data..." % sym)
            try:
                self.data[sym] = {}
                bars = self.client.get_historical_klines(sym,
                                                         self.kline_interval,
                                                         self.kline_start)
                self.data[sym]["klines"] = bars
            except Exception as e:
                self.logger.error("Failed to fetch price data for %. Skipping" % sym)
                continue
            self.logger.info("Fetching % closing prices..." % sym)
            closing_prices = [float(kline[4]) for kline in bars]
            self.data[sym]["closing_price"] = closing_prices
            period_length = len(closing_prices)  # TODO: Maybe set this to something else
            rsi = self.rsi_api.calculate_rsi(closing_prices, period_length)
            self.data[sym]['rsi'] = rsi
            rsi_signals = self.rsi_api.decide_buy_sell_signals(rsi)
            self.data[sym]['rsi_signal'] = rsi_signals[-1]
            
            
        app_shutdown = time.perf_counter()
        total_time = app_shutdown - init_time
        self.logger.info("Total time for app run: %.2f seconds" % total_time)
    
    def convert_to_dataframe(self, symbol):
        self.logger.info("Converting data for % to dataframe..." % symbol)
        df = pd.DataFrame(self.data[symbol]["klines"],
                          columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignored'])
        df = df.drop(columns=['close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignored'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Binance Trading Bot API")
    parser.add_argument('-s', '--symbols', type=str,
                        help='Single symbol or comma separated list of symbols',
                        required=False)
    parser.add_argument('-p', '--period', type=str,
                        help='Binance API secret',
                        required=False)
    parser.add_argument('-k', '--kline_interval', type=str,
                        help='Set the kline interval. For more info, see: https://python-binance.readthedocs.io/en/latest/constants.html',
                        default=Constants.KLINE_INTERVALS['5m'],
                        choices=Constants.KLINE_INTERVALS.keys(),
                        required=False)
    parser.add_argument('--kline_start',
                        help='Set the kline start string. See choises for more examples',
                        default=Constants.KLINE_START_STRING_EXAMPLES[1],
                        choices=Constants.KLINE_START_STRING_EXAMPLES,
                        required=False)
    parser.add_argument('--dont_run_testnet',
                        action='store_true', default=False,
                        help='The API will run on the testnet by default. Add this argument to run on the real network.',
                        required=False)
    args = parser.parse_args()

    api = TradingAPI(args)
    api.run()
