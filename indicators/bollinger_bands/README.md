# Bollinger Bands
These are bands that surround a simple moving average of price movements. They are calculated by adding or subtracting a standard deviation from the moving average. They can help measure volatility and identify overbought or oversold conditions when prices touch or exceed the upper or lower band.


Bollinger Bands are a technical analysis tool that consist of a moving average (typically a simple moving average) and an upper and lower band that are calculated based on the standard deviation of the moving average. The upper band is calculated by adding two standard deviations to the moving average, and the lower band is calculated by subtracting two standard deviations from the moving average.

To use Bollinger Bands to generate buy/sell/hold signals, you can use the following approach:

1. Calculate the moving average of the price data over a specified period of time (e.g. 20 days).
2. Calculate the standard deviation of the price data over the same period of time.
3. Calculate the upper band and lower band by adding/subtracting two standard deviations from the moving average.
4. Determine the current position of the price relative to the bands.
5. Generate signals based on the position of the price relative to the bands.


## Usage

```sh
python3 boll_bands.py -C [closing_prices] -w [window_size] -n [num_std] [--use_mock]
```

Alternatively, use the `--use_mock` flag to generate a dataset of random prices for testing.

```sh
python boll_bands.py --use_mock
```

Where, 
- closing_prices: A comma-separated list of closing prices. e.g., `100.21,101.31,99.45,98.21,...`
- window_size: An integer to define the window size for rolling mean. Default is `20`.
- num_std: A number to specify the standard deviation. Default is `2`.
- use_mock: An optional argument, if specified program will run a mock example.
