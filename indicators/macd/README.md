# Moving Average Convergence Divergence (MACD)

This indicator consists of two moving averages that show the relationship between two different time periods of price movements. The MACD line is calculated by subtracting the longer-term moving average from the shorter-term moving average, while the signal line is a smoothed version of the MACD line. The MACD histogram shows the difference between the MACD line and the signal line. A positive MACD histogram indicates bullish momentum (possible buy signal), while a negative MACD histogram indicates bearish momentum (possible sell signal).


The MACD line is calculated by subtracting the 26-period exponential moving average (EMA) from the 12-period EMA. The signal line, which is a 9-period EMA of the MACD line, is then plotted on top of the MACD line.

A decision to buy or sell can be made when the MACD line crosses above or below the signal line, respectively. If the MACD line crosses above the signal line, it is considered a bullish signal and may suggest a buying opportunity. Conversely, if the MACD line crosses below the signal line, it is considered a bearish signal and may suggest a selling opportunity.

However, it is important to note that no single indicator or signal is foolproof, and traders should use multiple indicators and technical analysis tools to make informed trading decisions. It is also important to consider other factors such as market conditions, news events, and risk management strategies.


Related sources: <br/>
https://www.investopedia.com/terms/m/macd.asp <br/>
https://www.youtube.com/watch?v=W78Xg_pnJ1A <br/>
https://www.youtube.com/watch?v=rf_EQvubKlk <br/>



## Usage

Run the script from the command line using the following command:

```bash
python macd.py --closing_prices 200,210,200,230,240
```

or run a mock example:

```bash
python macd.py --use_mock
```

### Arguments

The script supports the following arguments:

- `-C` or `--closing_prices`: A comma-separated list of closing prices. Required `False`.
- `-f` or `--fast_period`: Set the fast period for MACD calculation. The default is `12`. Required `False`.
- `-sl` or `--slow_period`: Set the slow period for MACD calculation. The default is `26`. Required `False`.
- `-sig` or `--signal_period`: Set the signal period for MACD calculation. The default is `9`. Required `False`.
- `--use_mock`: Add this argument to run a mock example. The default is `False`. Required `False`.
