#!/usr/bin/env python3.5

import os
import time
import argparse
import pandas as pd
import numpy as np
from utilities.constants import Constants
from utilities.logger import setup_logger
from utilities.utils import get_timestamp
from binance.client import Client
from indicators.average_directional_index.adx import ADX
from indicators.bollinger_bands.boll_bands import BollingerBands
from indicators.double_top_bottom.dtb import DoubleTopBottom
from indicators.elliott_wave_theory.ewt import EWT
from indicators.fibonacci_retracements.fib_ret import FibonacciRetracements
from indicators.head_and_shoulders.head_n_shoulders import HeadAndShoulders
from indicators.ichimoku_cloud.ichimoku import IchimokuCloud
from indicators.macd.macd import MACD
from indicators.order_book_analysis.oba import OBA
from indicators.on_balance_volume.obv import OBV
from indicators.relative_strength_index.rsi import RSI
from indicators.stochastic_oscillator.stoc_osc import StochasticOscillator
from indicators.supertrend_indicator.supertrend import Supertrend
from indicators.triangle.triangle import Triangle
from indicators.volume_weighted_average_price.vwap import VWAP
from sentiment_analysis.twitter.twitter import Twitter

class TradingAPI(Client):
    def __init__(self, args, timestamp=get_timestamp()):
        self.timestamp = timestamp
        if args.dont_run_testnet:
            self.testnet = not args.dont_run_testnet 
        else:
            self.testnet = True
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=self.testnet,
                                   timestamp=self.timestamp,
                                   )
        self.logger.info("Timestamp: {}".format(self.timestamp))
        self.logger.info("Testnet: {}".format(self.testnet))

        if args.symbols:
            self.symbols = args.symbols.split(',')
        else:
            self.symbols = Constants.DEFAULT_SYMBOLS
        self.logger.info("Using symbols: {}".format(", ".join(self.symbols)))
        if args.kline_interval:
            self.kline_interval = args.kline_interval
        else:
            self.kline_interval = Constants.KLINE_INTERVALS['5m']
        self.logger.info("Kline interval: {}".format(self.kline_interval))
        if args.kline_start:
            self.kline_start = args.kline_start
        else:
            self.kline_start = Constants.KLINE_START_STRING_EXAMPLES[1]
        self.logger.info("Kline start: {}".format(self.kline_start))
        self.data = {}
        self.logger.info("Initializing trading APIs...")
        self.client = Client(os.environ.get('BINANCE_KEY'),
                        os.environ.get('BINANCE_SECRET'),
                        testnet=self.testnet)
        # Indicator APIs
        self.adx_api = ADX(is_test=self.testnet, timestamp=self.timestamp)
        self.bb_api = BollingerBands(is_test=self.testnet, timestamp=self.timestamp)
        self.dtb_api = DoubleTopBottom(is_test=self.testnet, timestamp=self.timestamp)
        self.ewt_api = EWT(is_test=self.testnet, timestamp=self.timestamp)
        self.fib_api = FibonacciRetracements(is_test=self.testnet, timestamp=self.timestamp)
        self.head_n_shoulders_api = HeadAndShoulders(is_test=self.testnet, timestamp=self.timestamp)
        self.ichimoku_api = IchimokuCloud(is_test=self.testnet, timestamp=self.timestamp)
        self.macd_api = MACD(is_test=self.testnet, timestamp=self.timestamp)
        self.oba_api = OBA(is_test=self.testnet, timestamp=self.timestamp)
        self.obv_api = OBV(is_test=self.testnet, timestamp=self.timestamp)
        self.rsi_api = RSI(is_test=self.testnet, timestamp=self.timestamp)
        self.stoc_osc_api = StochasticOscillator(is_test=self.testnet, timestamp=self.timestamp)
        self.st_api = Supertrend(is_test=self.testnet, timestamp=self.timestamp)
        self.triangle_api = Triangle(is_test=self.testnet, timestamp=self.timestamp)
        self.vwap_api = VWAP(is_test=self.testnet, timestamp=self.timestamp)
        # Sentiment APIs
        try:
            self.twitter_api = Twitter(is_test=self.testnet, timestamp=self.timestamp)
            self.use_twitter = True
        except Exception as e:
            self.logger.info("Failed to initialize Twitter API: {}".format(e))
            self.use_twitter = False

    def run(self):
        init_time = time.perf_counter()
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
                self.logger.error("Failed to fetch price data for '%'. Skipping" % sym)
                continue
            
            df = self.convert_to_dataframe(self.data[sym]["klines"])
            start_index = 0 
            end_index = len(df) - 1

            self.logger.info("Fetching {} opening prices...".format(sym))
            opening_prices = df['open']
            opening_price = df.iloc[start_index]['open']
            self.logger.info("{} opening price: {}".format(sym, opening_price))
            self.data[sym]["opening_prices"] = opening_prices
            self.data[sym]["opening_price"] = opening_price

            self.logger.info("Fetching {} high prices...".format(sym))
            high_prices = df['high']
            # To get highest price over a specific period: high_prices.rolling(period_length).max().iloc[-1]
            highest_price = high_prices.max()
            self.logger.info("{} highest price: {}".format(sym, highest_price))
            self.data[sym]["high_prices"] = high_prices
            self.data[sym]["highest_price"] = highest_price
            
            self.logger.info("Fetching {} low prices...".format(sym))
            low_prices = df['low']
            lowest_price = low_prices.min()
            self.logger.info("{} lowest price: {}".format(sym, lowest_price))
            self.data[sym]["low_prices"] = low_prices
            self.data[sym]["lowest_price"] = lowest_price

            self.logger.info("Fetching {} closing prices...".format(sym))
            closing_prices = df['close']
            closing_price = closing_prices.iloc[-1]
            self.data[sym]["closing_prices"] = closing_prices
            self.logger.info("Latest {} closing price for interval: {}".format(sym, closing_price))
            self.data[sym]["closing_prices"] = closing_prices
            self.data[sym]["closing_price"] = closing_price

            # This should be the same as the lat closing price
            self.logger.info("Fetching {} current price...".format(sym))
            current_price = self.client.get_symbol_ticker(sym)["price"]
            self.logger.info("Current {} price: {}".format(sym, current_price))
            self.data[sym]["current_price"] = current_price

            self.logger.info("Fetching {} volumes...".format(sym))
            volumes = df['volume']
            self.data[sym]["volumes"] = volumes

            self.logger.info("Fetching {} order book...".format(sym))
            order_book = self.client.get_order_book(symbol=sym, limit=Constants.DEFAULT_ORDERBOOK_DEPTH)
            self.data[sym]["order_book"] = order_book

            # TODO:
            # Run indicators in threads
            # Make arguments to choose which indicators to use or not use

            # RSI
            rsi = self.rsi_api.calculate_rsi(closing_prices, period_length)
            self.data[sym]['rsi'] = rsi
            rsi_signals = self.rsi_api.decide_buy_sell_hold_signals(rsi)
            self.data[sym]['rsi_signal'] = rsi_signals[-1]
            
            # Fibonacci Retracements
            fib_ret_signal = self.fib_api.decide_buy_sell_hold_signals(closing_prices, df)
            self.data[sym]['fibonacci_retracements'] = fib_ret_signal
            
            # MACD
            macd_line, macd_signal_line, macd_histogram = self.macd_api.calculate_macd(closing_prices)
            self.data[sym]['macd_line'] = macd_line
            self.data[sym]['macd_signal_line']= macd_signal_line
            self.data[sym]['macd_histogram'] = macd_histogram
            macd_signal = self.macd_api.decide_buy_sell_hold_signals(macd_line, macd_signal_line)
            self.data[sym]['macd_signal'] = macd_signal
            
            # Bollinger Bands
            upper_band, middle_band, lower_band = self.bb_api.bollinger_bands(closing_prices)
            self.data[sym]['bollinger_middle_band'] = middle_band
            self.data[sym]['bollinger_upper_band'] = upper_band
            self.data[sym]['bollinger_lower_band'] = lower_band
            bb_signal = self.bb_api.decide_buy_sell_hold_signals(closing_prices, upper_band, middle_band, lower_band)
            self.data[sym]['bollinger_bands_signal'] = bb_signal
            
            # Stochastic Oscillator
            K, D = self.stoc_osc_api.stochastic_oscillator(high_prices, low_prices, closing_prices)
            self.data[sym]['stochastic_oscillator_k'] = K
            self.data[sym]['stochastic_oscillator_d'] = D
            
            # ADX
            adx = self.adx_api.calculate_adx(high, low, close)
            self.data[sym]['adx'] = adx
            adx_signal = self.adx_api.decide_buy_sell_hold_signals(adx)
            self.data[sym]['adx_signal'] = adx_signal
            
            # OBV
            obv = self.obv_api.calculate_obv()
            self.data[sym]['obv'] = obv
            obv_signal = self.obv_api.decide_buy_sell_hold_signals(obv)
            self.data[sym]['obv_signal'] = obv_signal
            
            # Head and shoulders
            cdl_head_shoulders, cdl_head_shoulders_inverted = self.head_n_shoulders_api.caclulate_head_and_shoulders(opening_prices, high_price, low_price, closing_price)
            h_n_s_signal = self.head_n_shoulders_api.decide_buy_sell_hold_signals(cdl_head_shoulders, cdl_head_shoulders_inverted)
            self.data[sym]['head_shoulders_cdl'] = cdl_head_shoulders
            self.data[sym]['head_shoulders_cdl_inverted'] = cdl_head_shoulders_inverted
            self.data[sym]['head_shoulders_cdl_signal'] = h_n_s_signal

            # Triangle
            triangle_pattern = self.triangle_api.get_triangle_pattern(opening_prices, high_prices, low_prices, closing_prices)
            triangle_signal = self.triangle_api.decide_buy_sell_hold_signals(triangle_pattern)
            self.data[sym]['triangle_pattern'] = triangle_pattern
            self.data[sym]['triangle_signal'] = triangle_signal

            # Double Top/Bottom
            double_top = self.dtb_api.check_double_top(closing_prices)
            double_bottom = self.dtb_api.check_double_bottom(closing_prices)
            dtb_signal = self.dtb_api.decide_buy_sell_hold_signals(double_top, double_bottom)
            self.data[sym]['dtb_double_top'] = double_top
            self.data[sym]['dtb_double_bottom'] = double_bottom
            self.data[sym]['dtb_signal'] = dtb_signal

            # Supertrend
            st = self.st_api.calculate_supertrend(high_prices, low_prices, closing_prices)
            st_signal = self.st_api.decide_buy_sell_hold_signals(st, closing_prices)
            self.data[sym]['supertrend'] = st
            self.data[sym]['supertrend_signal'] = st_signal

            # IchimokuCloud
            (tenkan_sen,
            kijun_sen,
            senkou_span_a,
            senkou_span_b) = self.ichimoku_api.calculate_ichimoku_values(high_prices, low_prices)
            ichimoku_signal = self.ichimoku_api.decide_buy_sell_hold_signals(senkou_span_a, senkou_span_b, current_price)
            self.data[sym]['ichimoku_tenkan_sen'] = tenkan_sen
            self.data[sym]['ichimoku_kijun_sen'] = kijun_sen
            self.data[sym]['ichimoku_senkou_span_a'] = senkou_span_a
            self.data[sym]['ichimoku_senkou_span_b'] = senkou_span_b
            self.data[sym]['ichimoku_signal'] = ichimoku_signal

            # VWAP
            vwap = self.vwap_api.calculate_vwap(volumes, closing_prices)
            vwap_signal = self.vwap_api.decide_buy_sell_hold_signals(vwap, current_price)
            self.data[sym]['vwap'] = vwap
            self.data[sym]['vwap_signal'] = vwap_signal

            # Elliott Wave Theory
            ewt_pattern = self.ewt_api.identify_wave_patterns(args.closing_prices)
            sma1 = self.ewt_api.get_moving_average(20)  # 20 day moving average
            sma2 = self.ewt_api.get_moving_average(50)  # 50 day moving average
            ewt_signal = self.ewt_api.decide_buy_sell_hold_signals(args.closing_prices, ewt_pattern, rsi, sma1, sma2)
            self.data[sym]['ewt_pattern'] = ewt_pattern
            self.data[sym]['ewt_sma1'] = sma1
            self.data[sym]['ewt_timeperiod1'] = 20
            self.data[sym]['ewt_sma2'] = sma2
            self.data[sym]['ewt_timeperiod2'] = 50
            self.data[sym]['ewt_signal'] = ewt_signal

            # Order Book Analysis
            oba_signal = self.oba_api.decide_buy_sell_hold_signals(order_book)
            self.data[sym]['oba_signal'] = oba_signal

            # Twitter sentiment
            if self.use_twitter:
                # TODO: Consider increasing DEFAULT_TWEET_COUNT if it is working well, make it an argument
                public_tweets = self.twitter_api.fetch_public_tweets(sym, Constants.DEFAULT_TWEET_COUNT)
                avg_sentiment = self.twitter_api.get_sentiment_scores(public_tweets)
                # twitter_gpt_sentiment = self.twitter_api.get_gpt_sentiment(public_tweets)
                self.data[sym]['twitter_{}'.format(sym)] = avg_sentiment
                for topic in Constants.SYMBOL_TOPICS[sym]:
                    public_tweets = self.twitter_api.fetch_public_tweets(topic, Constants.DEFAULT_TWEET_COUNT)
                    avg_sentiment = self.twitter_api.get_sentiment_scores(public_tweets)
                    # twitter_gpt_sentiment = self.twitter_api.get_gpt_sentiment(public_tweets)
                    self.data[sym]['twitter_{}'.format(topic)] = avg_sentiment
            
            # Get Reddit sentiment

            # Get Google Trends
            
            # Get Bing's latest market news signal


            # Finally use GPT to evaluate the signals and perform final trading decision


        app_shutdown = time.perf_counter()
        total_time = app_shutdown - init_time
        self.logger.info("Total time for app run: %.2f seconds" % total_time)
    
    def convert_to_dataframe(self, klines):
        self.logger.info("Converting data to dataframe...")
        df = pd.DataFrame(klines,
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
