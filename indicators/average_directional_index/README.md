# Average Directional Index (ADX) - Python Script

The Average Directional Index (ADX) is an indicator designed to quantify the strength of a trend. This Python script calculates the ADX based on given high, low and closing price data and provides potential buy, sell, or hold signals.

## Indicator Logic

This script relies on TA-Lib, a widely-used software library that provides tools for technical analysis of financial markets. It measures the strength and direction of a price trend by calculating the difference between two directional indicators: +DI (shows positive price movement) and -DI (shows negative price movement). The ADX line is derived from these two indicators. A high ADX value indicates a strong trend (either upwards or downwards), while a low value suggests a weak or sideways trend.

## Dependencies

1. Python 3.5+
2. TA-Lib
3. Numpy
4. Logger

## Usage

To execute the script, pass in comma separated lists of high, low, and close prices as arguments. It returns the calculated ADX and a signal (buy, sell or hold).

```
python adx.py [-H HIGH_PRICES] [-L LOW_PRICES] [-C CLOSE_PRICES] [--use_mock] [--timeperiod TIMEPERIOD]
```

Where:
- `-H, --high_prices`: Comma-separated list of highest prices. (e.g., "10.0,11.0,10.5")
- `-L, --low_prices`: Comma-separated list of lowest prices. (e.g., "9.0,9.5,9.8")
- `-C, --close_prices`: Comma-separated list of closing prices. (e.g., "9.5,10.0,10.2")
- `--use_mock`: Add this argument to generate and run the script with random mock data.
- `--timeperiod`: Specify time period for the ADX calculation. Default is 14.

Alternatively, use the `--use_mock` flag to generate a dataset of random prices for testing.

```
python adx.py --use_mock
```


## Output

The script outputs the calculated ADX value along with the chosen signal: either `buy`, `sell`, or `hold`.
