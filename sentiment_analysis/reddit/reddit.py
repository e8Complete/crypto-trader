#!/usr/bin/env python3.5

import os
import argparse
import time
import praw
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from scripts.constants import Constants
from scripts.utils import get_timestamp
from scripts.logger import setup_logger


class Reddit:
    def __init__(self, args, is_test=True, timestamp=get_timestamp()):
        log_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        self.logger = setup_logger(name=log_name,
                                   is_test=is_test,
                                   timestamp=timestamp,
                                   )
        self.logger.debug("Timestamp: {}".format(timestamp))
        self.logger.debug("Is test: {}".format(is_test))
        reddit_client_id = args.reddit_client_id if args.reddit_client_id else os.environ.get('REDDIT_CLIENT_ID')
        reddit_client_secret = args.reddit_client_secret if args.reddit_client_secret else os.environ.get('REDDIT_CLIENT_SECRET')
        reddit_username = args.reddit_username if args.reddit_username else os.environ.get('REDDIT_USERNAME')
        reddit_password = args.reddit_password if args.reddit_password else os.environ.get('REDDIT_PASSWORD')
        reddit_user_agent = args.reddit_user_agent if args.reddit_user_agent else os.environ.get('REDDIT_USER_AGENT')
        credentials = {"reddit_client_id": reddit_client_id,
                       "reddit_client_secret": reddit_client_secret,
                       "reddit_username": reddit_username,
                       "reddit_password": reddit_password,
                       "reddit_user_agent": reddit_user_agent}
        missing_credentials = False
        for key, val in credentials.items():
            if not val:
                self.logger.error("Missing credentials {}".format(key))
                missing_credentials = True
        if missing_credentials:
            self.logger.critical("Cannot initialize Reddit API without all required credentials. Exiting API.")
            raise ValueError("Cannot initialize Reddit API without all required credentials")

        self.analyzer = SentimentIntensityAnalyzer()
        self.api = praw.Reddit(client_id=reddit_client_id,
                                client_secret=reddit_client_secret,
                                username=reddit_username,
                                password=reddit_password,
                                user_agent=reddit_user_agent)

    def fetch_subreddits(self, topic, count):
        start_time = time.perf_counter()
        
        # TODO: set fetch count
        subreddit = self.api.subreddit(topic)
        search_results = subreddit.search(topic, sort="top", time_filter="top")  # TODO: Set time_filter dynamically

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Fetched {} {} subreddits  in {:0.4f} seconds".format(count, topic, elapsed_time))

        return search_results

    def get_sentiment_scores(self, subreddits):
        start_time = time.perf_counter()
        self.logger.info("Calculating Reddit sentiment scores...")

        sentiment_score = 0
        for post in subreddits:
            title_score = self.analyzer.polarity_scores(post.title)['compound']
            print(f"Title score: {title_score}")
            sentiment_score += title_score

        sentiment_score /= len(subreddits)

        self.logger.info("Average sentiment score: {}".fromat(sentiment_score))
        
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        self.logger.info("Calulated sentiment scores in  {:0.4f} seconds".format(elapsed_time))
        
        return sentiment_score
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
                        required=True)  # TODO: Set this
    parser.add_argument("--reddit_client_id",
                        help="Your Reddit API client ID. If it is not present in the environment, you can pass it with this argument. Optional.",
                        required=False)
    parser.add_argument("--reddit_client_secret",
                        help="Your Reddit API client secret. If it is not present in the environment, you can pass it with this argument. Optional.",
                        required=False)
    parser.add_argument("--reddit_username",
                        help="Your Reddit username. If it is not present in the environment, you can pass it with this argument. Optional.",
                        required=False)
    parser.add_argument("--reddit_password",
                        help="our Reddit password. If it is not present in the environment, you can pass it with this argument. Optional.",
                        required=False)
    parser.add_argument("--reddit_user_agent",
                        help="our Reddit user agent. If it is not present in the environment, you can pass it with this argument. Optional.",
                        required=False)
    args = parser.parse_args()

    reddit_api = Reddit(args)
    subreddits = reddit_api.fetch_subreddits(args.topic, args.tweet_count)
    avg_sentiment = reddit_api.get_sentiment_scores(subreddits)