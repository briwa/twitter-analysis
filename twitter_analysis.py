import re
from requests_html import HTMLSession, HTML
from datetime import datetime

session = HTMLSession()

def get_tweets(user, tweets=100, retweets=True, maxpages=25):
    """Gets tweets for a given user, via the Twitter frontend API."""

    url = f'https://twitter.com/i/profiles/show/{user}/timeline/tweets?include_available_features=1&include_entities=1&include_new_items_bar=true'
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': f'https://twitter.com/{user}',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8',
        'X-Twitter-Active-User': 'yes',
        'X-Requested-With': 'XMLHttpRequest'
    }

    def gen_tweets(tweets, retweets, maxpages):
        r = session.get(url, headers=headers)
        pages = maxpages
        found = tweets

        while pages > 0 and found > 0:
            try:
                html = HTML(html=r.json()['items_html'],
                            url='bunk', default_encoding='utf-8')
            except KeyError:
                raise ValueError(
                    f'Oops! Either "{user}" does not exist or is private.')

            comma = ","
            dot = "."
            tweets = []
            for tweet in html.find('.stream-item'):
                data = tweet.find('.tweet-text')
                if len(data) > 0:
                    text = tweet.find('.tweet-text')[0].full_text
                    raw = tweet.find('.tweet-text')[0].raw_html
                    tweetId = tweet.find(
                        '.js-permalink')[0].attrs['data-conversation-id']
                    orginalUserId = tweet.find(
                        '.js-original-tweet')[0].attrs['data-screen-name']
                    time = datetime.fromtimestamp(
                        int(tweet.find('._timestamp')[0].attrs['data-time-ms']) / 1000.0)
                    time = time.strftime("%Y-%m-%d %H:%M:%S")
                    interactions = [
                        x.text for x in tweet.find('.ProfileTweet-actionCount')]
                    replies = int(
                        interactions[0].split(" ")[0].replace(
                            comma, "").replace(dot, ""))
                    retweets = int(
                        interactions[1].split(" ")[0].replace(
                            comma, "").replace(dot, ""))
                    likes = int(
                        interactions[2].split(" ")[0].replace(
                            comma, "").replace(dot, ""))
                    hashtags = [
                        hashtag_node.full_text for hashtag_node in tweet.find('.twitter-hashtag')]
                    urls = [url_node.attrs['data-expanded-url']
                            for url_node in tweet.find('a.twitter-timeline-link:not(.u-hidden)')]
                    photos = [photo_node.attrs['data-image-url']
                              for photo_node in tweet.find('.AdaptiveMedia-photoContainer')]
                    if retweets or orginalUserId.lower() == user.lower():
                        found += -1
                        tweets.append({'tweetId': tweetId, 'time': time, 'user': user, 'orginaluser': orginalUserId,
                                        'text': text, 'raw' : raw, 'replies': replies, 'retweets': retweets, 'likes': likes,
                                       'entries': {
                                           'hashtags': hashtags,
                                           'urls': urls,
                                           'photos': photos
                                       }
                                       })

            last_tweet = html.find(
                '.stream-item')[-1].attrs['data-item-id']

            for tweet in tweets:
                if tweet:
                    tweet['text'] = re.sub('http', ' http', tweet['text'], 1)
                    remove = 'pic.twitter.com'
                    removelen = len(remove) + 11
                    index = tweet['text'].find(remove)
                    while index > 0:
                        tweet['text'] = tweet['text'][0:index] + \
                            tweet['text'][index + removelen:]
                        index = tweet['text'].find('pic.twitter.com')
                    yield tweet

            r = session.get(
                url, params={'max_position': last_tweet}, headers=headers)
            pages += -1

    yield from gen_tweets(tweets, retweets, maxpages)
