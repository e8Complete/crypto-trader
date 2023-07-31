# Ichimoku Cloud
This is a technical indicator that provides a comprehensive overview of support and resistance levels, trend direction, momentum, and other key market factors.

- Tenkan-sen is the average of the highest high and lowest low over a specified period of time (usually 9 periods). It is often used to indicate short-term market momentum.
- Kijun-sen is the average of the highest high and lowest low over a longer period of time (usually 26 periods). It is often used to indicate longer-term market momentum.
- Senkou Span A is calculated as the average of the Tenkan-sen and Kijun-sen, plotted 26 periods ahead of the current price. It forms one edge of the Ichimoku Cloud and can be used to identify potential support and resistance levels.
- Senkou Span B is calculated as the average of the highest high and lowest low over the previous 52 periods, plotted 26 periods ahead of the current price. It forms the other edge of the Ichimoku Cloud and can also be used to identify potential support and resistance levels.

n1 is typically set to 9, which means that the Tenkan-sen line is calculated as the average of the highest high and lowest low over the previous 9 periods.

n2 is typically set to 26, which means that the Kijun-sen line is calculated as the average of the highest high and lowest low over the previous 26 periods.

tenkan_sen represents the short-term trend and is calculated as the average of the highest high and lowest low over the previous n1 periods. In the standard settings of the Ichimoku Cloud indicator, n1 is set to 9.

On the other hand, kijun_sen represents the medium-term trend and is calculated as the average of the highest high and lowest low over the previous n2 periods. In the standard settings of the Ichimoku Cloud indicator, n2 is set to 26.

Therefore, tenkan_sen and kijun_sen are calculated using different periods and are not always the same. However, they are both components of the Ichimoku Cloud indicator and are used together to help traders identify trend direction and potential areas of support and resistance.

a common convention is to set n2 to twice the Kijun-sen period, which means that in the standard settings of the Ichimoku Cloud indicator where n1=9 and n2=26, n2 would be set to 52. This is because the Senkou Span B component represents longer-term support and resistance levels, and using a value of twice the Kijun-sen period helps to capture this longer-term trend.


In general, when the price is above the Cloud, this indicates a bullish trend, while when the price is below the Cloud, this indicates a bearish trend. Traders may use various combinations of these values, along with other technical indicators, to make trading decisions.



## Setup and Usage

1. Make sure you have **python 3.5** or newer installed.
2. You would need several python packages, which you can install using pip:
   
    ```sh
    pip install os argparse time ta random pandas
    ```

3. Run the script from a command line, specifying required parameters:

    ```sh
    python ichimoku.py --high_prices HIGH_PRICES --low_prices LOW_PRICES --tenkan_sen_n1 TENKAN_SEN_N1 --kijun_sen_n2 KIJUN_SEN_N2 --senkou_span_b_n2 SENKOU_SPAN_B_N2
    ```

Be sure to replace `HIGH_PRICES`, `LOW_PRICES`, `TENKAN_SEN_N1`, `KIJUN_SEN_N2`, `SENKOU_SPAN_B_N2` with your desired high prices list, low prices list, tenkan sen period, kijun sen period and senkou span b period respectively.

**Note:** High and low prices should be comma-separated with no spaces.

Alternatively you can make use of the `use_mock` argument to run the script with mock high and low prices.

```sh
python ichimoku.py --use_mock
```

## Important Functions

- `calculate`: This function calculates the Ichimoku Cloud values - Tenkan Sen, Kijun Sen, Senkou Span A and Senkou Span B using the given high and low prices.

- `decide_signal`: This function uses the calculations to decide and return a buy, sell, or hold signal.

## Args

The script accepts command-line arguments for parameters:

- `--high_prices`: Comma-separated list of highest prices. Each price must be a floating point number.
- `--low_prices`: Comma-separated list of lowest prices. Each price must be a floating point number.
- `-H` or `--tenkan_sen_n1`: Number of periods for Tenkan Sen calculation. Default is 9.
- `-K` or `--kijun_sen_n2`: Number of periods for Kijun Sen calculation. Default is 26.
- `-S` or `--senkou_span_b_n2`: Number of periods for Senkou Span B calculation. Default is 52.
- `--use_mock`: Use this option to run the script with mock example prices.

---

For more details about the Ichimoku Cloud Indicator, please refer to this [link](http://Investopedia.com/terms/i/ichimoku).