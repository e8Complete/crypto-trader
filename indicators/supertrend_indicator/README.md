# Supertrend indicator

The Supertrend, created by Olivier Seban, is a versatile trend following indicator used by traders. It is simple to use and gives accurate buy and sell signals especially in a trending market. Trading signals are generated using two indicator lines: an upward sloping line for uptrends, and a downward sloping line for downtrends. The indicator is relatively easy to read:

- When the Supertrend indicator line is green (below price), the prevailing trend is uptrend.
- When the Supertrend indicator line is red (above price), the prevailing trend is downtrend.

Related sources: <br/>
https://www.youtube.com/watch?v=GKNVmb82IfE <br/>
https://blog.elearnmarkets.com/supertrend-indicator-strategy-trading/ <br/>
https://tradingfuel.com/supertrend-indicator-formula-and-calculation/ <br/>


This python script provides the functionality of the Supertrend indicator used in trading. The Supertrend is a trend following indicator that is plotted on the price chart and aids in determining the direction of the price movement. It uses two parameters, a multiplier and a lookback period. 

Internally, it calculates the average true range (ATR) of the price and uses it, along with the given multiplier, to calculate upper and lower bands around the price. Depending on certain conditions, the Supertrend changes its position from above to below the price (or vice versa), thus indicating a trend reversal.

## Usage

```
python supertrend.py --high_prices 110,120,130 --low_prices 90,100,110 --closing_prices 100,110,120
```

Alternatively, use the `--use_mock` flag to generate a dataset of random prices for testing.

```sh
python supertrend.py --use_mock
```


### Parameters:

- -C/--closing_prices: Comma-separated list of closing prices (required unless --use_mock is specified)
- -H/--high_prices: Comma-separated list of high prices (required unless --use_mock is specified)
- -L/--low_prices: Comma-separated list of low prices (required unless --use_mock is specified)
- --lookback: The number of periods used for the ATR calculation. Defaults to 10.
- --multiplier: The factor by which the ATR is multiplied to calculate the bands of the Supertrend line. Defaults to 3.
- --use_mock: Instead of using input data, generates random prices and uses them for the calculations.


## Output

This script outputs the buy/sell/hold signal based on the Supertrend indicator. It also provides detailed logging information for every step of the calculation.