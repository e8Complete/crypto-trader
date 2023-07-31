# Order Book Analysis
Order book analysis is a method of analyzing the open buy and sell orders for a particular cryptocurrency or asset. It can provide insight into the supply and demand for the asset, and help identify potential support and resistance levels.

Order books typically show the price and quantity of outstanding buy and sell orders at various price levels. By analyzing the order book, traders can get a sense of where buyers and sellers are clustered, and where there may be price support or resistance.

For example, if there are a large number of buy orders clustered around a certain price level, it may suggest that there is strong demand for the asset at that price. Conversely, if there are a large number of sell orders clustered around a certain price level, it may suggest that there is strong selling pressure at that price.

Traders can use this information to identify potential entry and exit points for trades, as well as to set stop-loss orders to limit potential losses.

The depth refers to the number of price levels that are included in the order book data. Each price level in the order book represents the amount of an asset that is available to buy or sell at a specific price.

For example, if the depth of the order book is set to 5, it means that the order book data includes the top 5 price levels for both buy and sell orders. These price levels are sorted by price, with the highest bid (buy) price at the top and the lowest ask (sell) price at the bottom.

Setting the depth to a higher number will include more price levels in the order book data, providing a more detailed view of the market. However, it can also increase the amount of data that needs to be processed, which may affect the performance of your script or application.


## Usage

The script can be run from the command line and requires several arguments:

- **-s, --symbol** (Optional, default is 'BTCUSDT'): Specifies the cryptocurrency symbol to fetch the order book for.
- **--depth** (Optional, default is Constants.DEFAULT_ORDERBOOK_DEPTH): Sets the depth to include more price levels in the order book data, providing a more detailed view of the market. A higher number can also increase the amount of data that needs to be processed, which may affect the performance of the script or application.
- **--use_mock** (Optional): If this argument is added, the script will run a mock example with an order book consisting of 10 bids and 10 asks generated randomly.

For instance, to run the script for the 'ETHBTC' symbol with a depth of 20, execute this command:

```shell
python oba.py --symbol ETHBTC --depth 20 --use_mock
```

Alternatively, use the `--use_mock` flag to generate a dataset of random prices for testing.

```sh
python oba.py --use_mock
```


## Future Developments

- Additional methods and data points could be added to improve signal decision accuracy.
- Collection and recording of historical order data for back-testing strategy would be beneficial.
- Additional command line parameters or a config file could be included for personalizing the strategy.