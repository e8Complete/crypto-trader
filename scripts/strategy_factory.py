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
from sentiment_analysis.google_trends.google_trends import GoogleTrends
from sentiment_analysis.reddit.reddit import Reddit
from sentiment_analysis.twitter.twitter import Twitter



class StrategyFactory:
    @staticmethod
    def create_strategy(name, **params):
        if name == 'ADX':
            return ADX(**params)
        elif name == 'BollingerBands':
            return BollingerBands(**params)
        elif name == 'DoubleTopBottom':
            return DoubleTopBottom(**params)
        elif name == 'EWT':
            return EWT(**params)
        elif name == 'FibonacciRetracements':
            return FibonacciRetracements(**params)
        elif name == 'HeadAndShoulders':
            return HeadAndShoulders(**params)
        elif name == 'IchimokuCloud':
            return IchimokuCloud(**params)
        elif name == 'MACD':
            return MACD(**params)
        elif name == 'OBA':
            return OBA(**params)
        elif name == 'OBV':
            return OBV(**params)
        elif name == 'RSI':
            return RSI(**params)
        elif name == 'StochasticOscillator':
            return StochasticOscillator(**params)
        elif name == 'Supertrend':
            return Supertrend(**params)
        elif name == 'Triangle':
            return Triangle(**params)
        elif name == 'VWAP':
            return VWAP(**params)
        elif name == 'GoogleTrends':
            return GoogleTrends(**params)
        elif name == 'Reddit':
            return Reddit(**params)
        elif name == 'Twitter':
            return Twitter(**params)
        else:
            raise ValueError(f'Unknown strategy: {name}')
