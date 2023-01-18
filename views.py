import os
import pandas as pd
from bertopic import BERTopic
from src.reddit import RedditBot
from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory

DOWNLOADS_PATH = os.path.join(os.getcwd(), 'downloads')

views = Blueprint(__name__, 'views')
reddit = RedditBot()
topic_model = BERTopic()


def retrieve_subreddits(data: dict) -> pd.DataFrame:
    # Retrieve subreddits through its API
    posts = reddit.get_subreddits_posts(
        name=data.get('subreddit'), 
        type=data.get('type'), 
        amount=int(data.get('amount'))
    )
    df = reddit.convert_posts_to_df(posts=posts)
    df['Text'] = df.apply(lambda row: row.Title + ': ' + row.Content, axis=1)
    return df

@views.route('/', methods=['POST', 'GET'])
def home():
    data = request.form
    if request.method == 'POST':
        if (int(data.get('amount')) < 0 or int(data.get('amount')) > 1000):
            return redirect(url_for('views.error', type_of_error='amount'))
        elif data.get('type') not in ['hot', 'new', 'rising', 'top']:
            print(data.get('type'))
            return redirect(url_for('views.error', type_of_error='type'))
        elif not reddit.subreddit_exists(data.get('subreddit')):
            return redirect(url_for('views.error', type_of_error='subreddit'))
        else:
            # Retrieve subreddits
            subreddits_df = retrieve_subreddits(data=data)
            # Topic modelling using BERTtopic
            _, _ = topic_model.fit_transform(subreddits_df.Text)
            topics_df = topic_model.get_topic_info()
            for t in topics_df.Topic:
                topics_df.loc[topics_df.Topic == t, 'Top words'] = str([w for w, p in topic_model.get_topic(t)])
            # Donwload topics
            docs_df = topic_model.get_document_info(subreddits_df.Text)

            writer = pd.ExcelWriter(os.path.join(DOWNLOADS_PATH, 'topics.xlsx'), engine='xlsxwriter')
            topics_df.to_excel(writer, 'topics', index=False)
            docs_df.to_excel(writer, 'docs', index=False)
            writer.close()

            return send_from_directory(
                directory=DOWNLOADS_PATH,
                path='topics.xlsx', 
                as_attachment=True
            )

    return render_template('index.html')

@views.route('/succes', methods=['GET'])
def success():
    return render_template('success.html')

@views.route('/error/<type_of_error>', methods=['GET'])
def error(type_of_error: str):
    if type_of_error == 'amount':
        return render_template('error.html', type_of_error='The amount is higher than 1000 or lower than 0')
    elif type_of_error == 'type':
        return render_template('error.html', type_of_error='The ordering is not within hot, rising, new, top')
    elif type_of_error == 'subreddit':
        return render_template('error.html', type_of_error='The subreddit does not exist')
