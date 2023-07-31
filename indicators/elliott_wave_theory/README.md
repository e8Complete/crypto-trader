# Elliott Wave Theory
This is a technical analysis approach that looks for patterns in market cycles and uses them to forecast future price movements.


Calculates the (default) 20-day and (default) 50-day moving averages and the (default) 14-day RSI using the TA-Lib library, and identifies the waves and Elliott Wave patterns using a simple set of rules# Elliott Wave Theory Python Script

This script is a Python implementation of the Elliott Wave Theory, which is a technical analysis approach employed to track market cycles and future price movements. It relies on patterns to provide predictions on prices' future paths. 

At its core, the script identifies wave patterns and applies a set of simple rules to determine these patterns. It also calculates the 20-day and 50-day moving averages and the 14-day RSI (Relative Strength Index) using the TA-Lib library, both built-in values but can be adjusted according to needs.

## Features

- Calculates the 20-day and 50-day moving averages.
- Determines the 14-day RSI.
- Identifies market cycle wave patterns.

## Requirements

- Python 3.5 or above
- TA-Lib Python library
- numpy
- random
- indicators.relative_strength_index.rsi

## How to Use

1. Clone the repository to your local machine.
2. Make sure you have all the required Python packages installed.
3. You can try the script with mock data by using the argument `--use_mock`.
4. If you want to provide closing prices data, use the `-C` argument followed by your comma-separated list of closing prices.
5. Modify the period length by using `-n` argument followed by an integer representing the length period.
6. Adjust time period for moving average 1 and 2 using `-t1` and `-t2` respectively followed by the number of days.

Example running the script with custom arguments:

```bash
python3 ewt.py -C "127.2, 126.5, 129.8, 133.5" -n 14 -t1 15 -t2 30
```

Alternatively, use the `--use_mock` flag to generate a dataset of random prices for testing.

```sh
python ewt.py --use_mock
```
