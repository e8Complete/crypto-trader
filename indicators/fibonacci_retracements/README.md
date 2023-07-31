# Fibonacci Retracements: 

These are horizontal lines that divide a price movement into different ratios based on the Fibonacci sequence. They can help identify support and resistance levels where prices may bounce back or break through during a correction or retracement.


The calculate_fib_levels function in the Fibonacci retracements module returns three Fibonacci retracement levels, which are the 38.2%, 50%, and 61.8% levels. These levels are commonly used in technical analysis to identify potential levels of support and resistance in the market.

In terms of determining a buy, sell, or hold signal based on these levels, it would depend on the specific trading strategy being employed.

For example, a trader who is using Fibonacci retracements as part of a swing trading strategy may look for a bullish signal to buy when the price retraces to the 38.2% or 50% retracement level and then resumes its upward trend. Conversely, they may look for a bearish signal to sell when the price retraces to the 61.8% level and then continues to move downwards.

However, it is important to note that Fibonacci retracements are just one tool in a trader's toolbox and should be used in conjunction with other indicators and analysis to make informed trading decisions.

## Usage

This script needs closing prices, high prices and low prices of any asset to calculate Fibonacci retracement levels and generate BUY, SELL or HOLD signals. You can provide these as a comma-separated list. Additionally, it allows you to specify your preferred Fibonacci levels. 

```
python fib_ret.py -C <closing_prices> -H <high_prices> -L <low_prices> -l <fib_levels>
```

Use the argument `--use_mock` to run a mock example.

## Example

For example, if the closing prices are "100, 102, 105", high prices are "101, 103, 106" and low prices are "99, 101, 103", the command would be:

```
python fib_ret.py -C "100, 102, 105" -H "101, 103, 106" -L "99, 101, 103"
```

## Module

This script contains two core methods:

- `calculate()` calculates the Fibonacci Retracement levels based on supplied high and low prices.
- `decide_signal()` takes decision on buying, selling or holding the asset based on the calculated Fibonacci levels and the closing prices. 

## Strategy

The buy or sell signal is decided based on these levels. We consider a BUY signal if the last closing price is less than or equal to the 38.2% Fibonacci level. It's a SELL signal if it's greater than or equal to 61.8%, else it's a HOLD signal.
