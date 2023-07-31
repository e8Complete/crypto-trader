# Triangle
This pattern consists of two converging trendlines that form a triangular shape. It signals a continuation of the existing trend when prices break out of the triangle in the same direction.


This script, named `triangle.py`, is designed to leverage technical analysis principles to guide cryptocurrency trading. Specifically, it uses the "Triangle" pattern, a popular indicator amongst traders, to decide whether to send a buy, sell, or hold signal for a given cryptocurrency.

The Triangle pattern is identified using the talib library's CDLMORNINGSTAR function, which incorporates opening prices, closing prices, highest prices, and lowest prices within a given day. If a consistent pattern is found amongst these data points, a trading decision is made.

The script is compatible with Python 3.5, and logs activity for user review and debugging.

## Usage

Run the script using the following command:

`python3 triangle.py` 

There are four inputs: opening prices (`-O`), closing prices (`-C`), highest prices (`-H`), and lowest prices (`-L`). Values should be passed as comma-separated strings. For example:

`python3 triangle.py -O "100,200,300" -C "150,250,350" -H "200,300,400" -L "50,150,250"`

Alternatively, use the `--use_mock` flag to generate a dataset of random prices for testing.

```sh
python triangle.py --use_mock
```

## Understanding the Outputs

The script outputs two main things: the Triangle pattern, and the buy/sell/hold signal.

The Triangle pattern is a printout of the talib function's output, a complex calculation based on the inputted highs, lows, opens, and closes.

The signal, on the other hand, is easier to understand. A `BUY_SIGNAL` means that it is a good time to purchase the given cryptocurrency, a `SELL_SIGNAL` means it is a good time to sell, and a `HOLD_SIGNAL` means the trader should wait for a more clear indicator.