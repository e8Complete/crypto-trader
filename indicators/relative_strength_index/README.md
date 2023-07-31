# Relative Strength Index (RSI)
This indicator measures the strength and potential reversal points of a price trend by comparing the magnitude of recent gains and losses over a period of time. A high RSI value indicates overbought conditions (possible sell signal), while a low RSI value indicates oversold conditions (possible buy signal).


The calculate_rsi function that takes in an array of prices and a period length n (default value is 14), and returns an array of RSI values. This function uses the Wilder's RSI formula to calculate RSI values for each price in the input array.


In order to use the RSI indicator to determine a buy or sell signal for the current period, you would typically calculate the RSI values for the previous n periods (where n is the period length you choose, e.g. 14) and then use the RSI value for the current period to generate a buy or sell signal.

For example, if you have daily closing prices for a specific symbol, you could calculate the RSI values for the previous 14 days (not including today) using the calculate_rsi function, and then use the RSI value for yesterday's closing price (the last period) to generate a buy or sell signal.

If yesterday's RSI value was above 70, it would indicate overbought conditions and a possible sell signal. If yesterday's RSI value was below 30, it would indicate oversold conditions and a possible buy signal. If yesterday's RSI value was between 30 and 70, there would be no clear buy or sell signal based on the RSI indicator alone.

Of course, it's important to note that the RSI indicator is just one tool among many that traders use to analyze market trends and identify potential trade opportunities. It's always a good idea to use multiple indicators and analysis methods to make informed trading decisions.


## Usage
  
Use the script from the command line as follows: 

```bash
python3 rsi.py -C "127.2, 126.5, 129.8, 133.5" -n 14
```

The above command assumes you provide closing prices as a string `-C` argument and that it is followed by a comma-separated list of closing prices. You can define the period length using the `-n` argument followed by an integer.

Running the script without any arguments defaults to a period length of 14 (RSI typically suggests this period length) and generates RSI values for the sample data provided. 

Alternatively, use the `--use_mock` flag to generate a dataset of random prices for testing.

```sh
python rsi.py --use_mock
```
