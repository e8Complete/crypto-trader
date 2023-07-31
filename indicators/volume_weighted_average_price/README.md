# Volume Weighted Average Price (VWAP)
This indicator shows the average price of an asset over a specific time period, weighted by trading volume. If the latest price is higher than the VWAP, output a BUY signal. If it is lower, output a SELL signal. If the price is exactly the VWAP, output a HOLD signal

### Usage
The script is executed by running the following command:

```python
python vwap.py --closing_prices '100.1,200.2,300.3,400' --volumes '100,200,300,400'
```

Alternatively, use the `--use_mock` flag to generate a dataset of random prices for testing.

```sh
python vwap.py --use_mock
```

## Parameters
| Parameter | Description | Default Value | Example |
| ----------- | ----------- | -------- | ------- |
| -C, --closing_prices | A list of closing prices, separated by commas | None | 100.1,200.2,300.3,400 |
| -V, --volumes | A list of trading volumes, separated by commas | None | 100,200,300,400 |
| --use_mock | Use mock data. If this argument is present, the script will run with randomly generated values | False | --use_mock |

## Output
The script will output the calculated VWAP, followed by a buy/sell/hold signal based on the comparison with the last closing price.

## How It Works
1. Parse the input parameters. If `--use_mock` is set, generate random values. Otherwise, use the values passed in via `--closing_prices` and `--volumes`.
2. Calculate the VWAP using the formula `(Sum of (Price*Volume))/total volume`.
3. Compare the latest closing price with the VWAP. If the latest price is higher than the VWAP, output a BUY signal. If it is lower, output a SELL signal. If the price is exactly the VWAP, output a HOLD signal.
4. Print logs showing calculations, total volume, total value, calculation time, and the derived signal.

## Important Note
Ensure the trading volumes and closing prices passed to the script are of equal length and correspond correctly to each other. The script does not validate this.