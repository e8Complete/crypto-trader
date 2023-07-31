# Head And Shoulders

This pattern consists of three peaks , with the middle peak being higher than the other two. It signals a reversal from an uptrend to a downtrend when prices break below the neckline that connects the lows between the peaks.

## Usage

Run this script from the command-line as follows:

```shell
python3.5 head_n_shoulders.py --opening_prices=price1,price2,price3,... 
--closing_prices=price1,price2,price3,... 
--high_prices=price1,price2,price3,... 
--low_prices=price1,price2,price3,... 
--window_size=5
```
Where:

- `opening_prices`, `closing_prices`, `high_prices`, `low_prices` are comma-separated lists of float values representing the opening, closing, high and low market prices respectively. These are required arguments unless `--use_mock` is specified.
- `window_size` is an integer representing how many data points before and after a specific point will be used for detecting peaks and valleys in the data. Default value is `5`.

If you'd like to run the script with mock data, use the `--use_mock` flag:

```shell
python3.5 head_n_shoulders.py --window_size=5 --use_mock
```

## Output

The script will print buy, sell, and hold signals to the console. Buy signals indicate a potential uptrend, thus a good time to buy. Sell signals indicate a potential downtrend, meaning it could be a good time to sell. Hold signals indicate no clear trend change detected, suggesting it might be safer to hold off buying or selling.