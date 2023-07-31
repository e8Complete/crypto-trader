# On-Balance Volume (OBV)

This script helps in making Crypto trading decisions based on On-Balance Volume (OBV). OBV is an indicator that measures the cumulative trading volume of an asset. It adds the volume on days when prices close higher than their previous close and subtracts the volume on days when prices close lower than their previous close. It illustrates the buying and selling pressure behind price movements. A rising OBV line indicates bullish accumulation (possible buy signal), while a falling OBV line indicates bearish distribution (possible sell signal).

## Usage:

To run the script: 

```bash
python obv.py -C [closing_prices] -V [volume]
```

#### Sample Usage

```bash
python obv.py -C 100,200,150 -V 2000,4000,3000
```

In case you want to run a mocked example without providing the closing prices and volumes, you can use the `--use_mock` argument:

```bash
python obv.py --use_mock
```

## Code Overview

The OBV class is inherited from the BaseIndicator class. It calculates OBV values using closing prices and volume data of an asset. The calculated OBV values are then used to decide buy or sell signals.

* `calculate()` - This method calculates OBV values using closing prices and volumes which can be passed as arguments.
* `decide_signal()` - This method decides a buy or sell signal based on the calculated OBV values.


