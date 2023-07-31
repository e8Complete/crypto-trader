# Double Top/Bottom Crypto Trading Pattern Detection

This Python script helps crypto traders detect Double Top/Bottom patterns in closing prices to generate buy or sell signals. Double Top/Bottom patterns consist of two peaks or bottoms at approximately the same price level and are considered powerful indicators of price reversals in trading. This script uses these patterns to signal a likely reversal from an uptrend to a downtrend (Double Top), or from a downtrend to an uptrend (Double Bottom) when prices break through the respective resistance or support levels.

## Usage

To run the script, use the command below:

```bash
python dtb.py -C <closing_prices> [--use_mock]
```

- `-C, --closing_prices`: This is a comma-separated list of closing prices that you pass to the script. Please ensure that these numeric values are comma-separated without spaces. (required unless `--use_mock` is used)

- `--use_mock`: Run script with a mock dataset of 100 random values between 100 and 200.


## Functionality

This script includes several classes and functions, including:

- `DoubleTopBottom(BaseIndicator)`: This class works to calculate Double Top and Bottom patterns. It includes methods to identify double tops and bottoms and to determine trading signals based on these patterns.

- `calculate(self, **data)`: This method calculates the double top and bottom patterns.

- `check_double_top(self, closes)`: This method checks for a double top in a list of closing prices.

- `check_double_bottom(self, closes)`: This method checks for a double bottom in a list of closing prices.

- `decide_signal(self, **data)`: This method decides the trading signals based on the assessed patterns.