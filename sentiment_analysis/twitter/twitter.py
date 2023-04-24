#!/usr/bin/env python3.5

import os
import argparse
import time
import tweepy
from textblob import TextBlob
from utilities.constants import Constants
from utilities.utils import get_timestamp
from utilities.logger import setup_logger


class Twitter:
    def __init__(self, args, is_test=True, timestamp=get_timestamp()):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        consumer_key = args.consumer_key if args.consumer_key else os.environ.get('TWITTER_CONSUMER_KEY')
        consumer_secret = args.consumer_secret if args.consumer_secret else os.environ.get('TWITTER_CONSUMER_SECRET')
        access_token = args.access_token if args.access_token else os.environ.get('TWITTER_ACCESS_TOKEN')
        access_token_secret = args.access_token_secret if args.access_token_secret else os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
        credentials = {"consumer_key": consumer_key,
                       "consumer_secret": consumer_secret,
                       "access_token": access_token,
                       "access_token_secret": access_token_secret}
        missing_credentials = False
        for key, val in credentials.items():
            if not val:
                self.logger.error("Missing credentials {}".format(key))
                missing_credentials = True
        if missing_credentials:
            self.logger.critical("Cannot initialize Twitter API without all required credentials. Exiting API.")
            raise ValueError("Cannot initialize Twitter API without all required credentials")
        
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)

    def fetch_public_tweets(self, topic, count):
        start_time = time.perf_counter()
        public_tweets = self.api.search(topic, count=count)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Fetched {} {} tweets  in %.2f seconds".format(count, topic, elapsed_time))
        return public_tweets

    def get_sentiment_scores(self, public_tweets):
        start_time = time.perf_counter()
        self.logger.info("Calculating Twitter sentiment scores...")
        sentiment_scores = []
        for tweet in public_tweets:
            analysis = TextBlob(tweet.text)
            sentiment_scores.append(analysis.sentiment.polarity)

        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        self.logger.info("Average sentiment score: {}".fromat(avg_sentiment))
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Calulated sentiment scores in  {:0.4f} seconds".format(elapsed_time))
        
        return avg_sentiment
        # If the sentiment score is positive and the price is low, issue a buy signal
        # If the sentiment score is negative and the price is high, issue a sell signal
        # Otherwise, issue a hold signal

    def get_gpt_sentiment(self, tweets):
        ...
        # TODO: If the API works well, we can consider using GPT or other LLMs to analyse the tweets,
        # Instead of using sentiment scores
        # LLM's might have higher cost (for inference/api calls), but a better overal ability to analyze tweets


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch public Tweets and perform sentiment analysis on them")
    parser.add_argument('-t', '--topic', type=str, default="Bitcoin",
                        help='Topic to fetch tweets from',
                        required=True)
    parser.add_argument('-n', '--tweet_count', type=int, default=Constants.DEFAULT_TWEET_COUNT,
                        help='Number of public tweets to fetch',
                        required=True)
    parser.add_argument("--consumer_key",
                        help="Your Twitter API consumer key. If it is not present in the environment, you can pass it with this argument. Optional.",
                        required=False)
    parser.add_argument("--consumer_secret",
                        help="Your Twitter API consumer secret. If it is not present in the environment, you can pass it with this argument. Optional.",
                        required=False)
    parser.add_argument("--access_token",
                        help="Your Twitter API access token. If it is not present in the environment, you can pass it with this argument. Optional.",
                        required=False)
    parser.add_argument("--access_token_secret",
                        help="our Twitter API access token secret. If it is not present in the environment, you can pass it with this argument. Optional.",
                        required=False)
    args = parser.parse_args()

    twitter_api = Twitter(args)
    public_tweets = twitter_api.fetch_public_tweets(args.topic, args.tweet_count)
    avg_sentiment = twitter_api.get_sentiment_scores(public_tweets)