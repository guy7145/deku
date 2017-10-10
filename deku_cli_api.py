import re

import deku
from bs4 import BeautifulSoup

def search(anime_name):
    res = deku.search_series_urls_by_name(anime_name)
    print('\n'.join(res))
    return


find = deku.find_series_url_by_name


def check(anime_name):
    print('fetching series url...')
    series_url = deku.find_series_url_by_name(anime_name)
    print('fetching episodes urls...')
    deku.get_episodes_watch_urls(deku.fetch_url(series_url))
    return


def estimate(anime_name, load_timeout_seconds=5):
    print('fetching series url...')
    series_url = deku.find_series_url_by_name(anime_name)

    print('fetching episodes urls...')
    servers, latest_ep = deku.get_episodes_watch_urls(deku.fetch_url(series_url))
    some_episode_url = deku.get_absolute_url(series_url, servers[0][1])

    chrome = deku.generate_chrome_driver(player_quality=None)
    deku.driver_timeout_get_url(driver=chrome, url=some_episode_url, timeout=load_timeout_seconds)
    source = chrome.page_source
    chrome.close()
    estimation = re.search('Estimated the next episode will come at (.*?)</div>', source)
    if estimation is None:
        estimation = 'No estimation of upcoming episodes was found.'
    else:
        counter = re.search('\(<i>(.*?)</i>\)', estimation.group(1)).group(1)[:-1]
        date = estimation.group(1)[:estimation.group(1).find(' (<i>')]
        estimation = 'Found an estimation for the next episode\'s airing: {} ({})'.format(date, counter)
    print(estimation)
    return


def download(anime_name, episodes, path='./', *args, **kwargs):
    return deku.download_episodes(anime_name=anime_name, episodes_to_download=episodes, path=path, *args, **kwargs)
