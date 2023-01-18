import os
import praw
import logging
import pandas as pd
from typing import Generator
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class RedditBot:
    def __init__(
        self, 
        client_id: str | None = None, 
        client_secret: str | None = None, 
        username: str | None = None, 
        password: str | None = None
    ) -> None:

        self.reddit = praw.Reddit(
            client_id = client_id if client_id else os.getenv('REDDIT_CLIENT_ID'), 
            client_secret = client_secret if client_secret else os.getenv('REDDIT_CLIENT_SECRET'), 
            username = username if username else os.getenv('REDDIT_USERNAME'), 
            password = password if password else os.getenv('REDDIT_PASSWORD'), 
            user_agent='bot'
    )

    def get_subreddits_posts(self, name: str, type: str, amount=100) -> Generator:
        """Gets the posts from a given subreddit"""
        subreddit = self.reddit.subreddit(name)
        if type == 'new':
            posts = subreddit.new(limit=amount)
        elif type == 'hot':
            posts = subreddit.hot(limit=amount)
        elif type == 'top':
            posts = subreddit.top(limit=amount)
        elif type == 'rising':
            posts = subreddit.rising(limit=amount)

        return posts 

    @staticmethod
    def convert_posts_to_df(posts: Generator) -> pd.DataFrame:
        """Extracts the title and text from a post"""
        df = pd.DataFrame(columns=['Title', 'Content'])
        for n, p in enumerate(posts):
            df.loc[n, 'Title'] = p.title
            df.loc[n, 'Content'] = p.selftext
        
        return df

    def subreddit_exists(self, name: str) -> bool:
        try:
            self.reddit.subreddits.search_by_name(name, exact=True)
            return True
        except Exception as e:
            logger.error(e)
            return False