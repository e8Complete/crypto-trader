import os
from binance.client import Client

class Constants():
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

    HOLD_SIGNAL = "hold"
    BUY_SIGNAL = "buy"
    SELL_SIGNAL = "sell"

    DEFAULT_SYMBOLS = ['BTCUSDT']

    KLINE_INTERVALS = {
        '1m': Client.KLINE_INTERVAL_1MINUTE,
        '3m': Client.KLINE_INTERVAL_3MINUTE,
        '5m': Client.KLINE_INTERVAL_5MINUTE,
        '15m': Client.KLINE_INTERVAL_15MINUTE,
        '30m': Client.KLINE_INTERVAL_30MINUTE,
        '1h': Client.KLINE_INTERVAL_1HOUR,
        '2h': Client.KLINE_INTERVAL_2HOUR,
        '4h': Client.KLINE_INTERVAL_4HOUR,
        '6h': Client.KLINE_INTERVAL_6HOUR,
        '8h': Client.KLINE_INTERVAL_8HOUR,
        '12h': Client.KLINE_INTERVAL_12HOUR,
        '1d': Client.KLINE_INTERVAL_1DAY,
        '3d': Client.KLINE_INTERVAL_3DAY,
        '1w': Client.KLINE_INTERVAL_1WEEK,
        '1M': Client.KLINE_INTERVAL_1MONTH,
    }

    KLINE_START_STRING_EXAMPLES = ['30 minutes ago UTC',
                                   '1 day ago UTC',
                                   '1 month ago UTC',
                                   '30 days ago',
                                   ["1 Dec, 2017", "1 Jan, 2018"], #  klines for the last month of 2017
                                   '1 Jan, 2017', # Since NEOBTC was listed
                                   ]
    
    RSI_SELL_THRESHOLD = 70
    RSI_BUY_THRESHOLD = 30