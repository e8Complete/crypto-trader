# Crypto Trading Bot

## Indicators
Uses the following indicators to get a buy/sell/hold signal:
- Average Directional Index (ADX)
- Bollinger Bands
- Double Top/Bottom
- Elliott Wave Theory
- Fibonacci Retracements
- Head And Shoulders
- Ichimoku Cloud
- Moving Average Convergence Divergence (MACD)
- Order Book Analysis
- On-Balance Volume (OBV)
- Relative Strength Index (RSI)
- Stochastic Oscillator
- Supertrend Indicator
- Triangle pattern
- Volume Weighted Average Price (VWAP)

## Sentiment Analysis
Uses the following tools for sentiment analysis
- Twitter Sentiment Analysis
- Google Trends
- Reddit Sentiment Analysis
- Bing latest news sentiment analysis


Finally it uses GPT to evaluate the signals and perform a trading decision


## Requirements
### OpenAI
- OpenAI API_KEY
- OpenAI ORG_ID
### Twitter API credentials
- consumer_key = 'YOUR_CONSUMER_KEY'
- consumer_secret = 'YOUR_CONSUMER_SECRET'
- access_token = 'YOUR_ACCESS_TOKEN'
- access_token_secret = 'YOUR_ACCESS_TOKEN_SECRET'
### Reddit API credentials
- reddit_client_id
- reddit_client_secret
- reddit_username
- reddit_password
- reddit_user_agent



```
pip install -r requirements.txt
```



https://python-binance.readthedocs.io/en/latest/




How can i implement a python script that uses Google Trends to indicate as buy/sell/hold signal, using binance api


# TODO:
# fix arguments for each indicator
# Add defaults to constants?
# fix detail logging in all indicators
# Make it possible to set all arguments for all APIs from main.py
# Save data to csv file
# Add posibility to plot all indicators (save plots to logs for each run)
