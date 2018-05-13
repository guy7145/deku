import ctypes
import os
from Servers import RapidVideo, MyCloud, G3, G4, F4, F2
from src import Site9AnimeStuff, deku


def no_exception(f):
    def no_ex(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print('--> An exception has occurred during the last operation: {}'.format(e))
    return no_ex


search = no_exception(Site9AnimeStuff.search_series_urls_by_name)
find_by_substring = no_exception(Site9AnimeStuff.find_series_urls_by_name_substring)
find_by_keywords = no_exception(Site9AnimeStuff.find_series_urls_by_keywords)
find_exact = no_exception(Site9AnimeStuff.find_series_url_by_name)
find = find_exact

info = no_exception(deku.info)
episodes = no_exception(deku.episodes)
eps = episodes


# def estimate(anime_name, load_timeout_seconds=5):
#     print('fetching series url...')
#     series_url = Site9AnimeStuff.find_series_url_by_name(anime_name)
#
#     print('fetching episodes urls...')
#     servers, latest_ep = deku.get_episodes_watch_urls(BrowseUtils.fetch_url(series_url))
#     some_episode_url = BrowseUtils.get_absolute_url(series_url, servers[0][1])
#
#     chrome = BrowseUtils.generate_chrome_driver()
#     BrowseUtils.driver_timeout_get_url(driver=chrome, url=some_episode_url, timeout=load_timeout_seconds)
#     source = chrome.page_source
#     chrome.close()
#     estimation = re.search('Estimated the next episode will come at (.*?)</div>', source)
#     if estimation is None:
#         estimation = 'No estimation of upcoming episodes was found.'
#     else:
#         counter = re.search('\(<i>(.*?)</i>\)', estimation.group(1)).group(1)[:-1]
#         date = estimation.group(1)[:estimation.group(1).find(' (<i>')]
#         estimation = 'Found an estimation for the next episode\'s airing: {} ({})'.format(date, counter)
#     print(estimation)
#     return


@no_exception
def download(anime_name, episodes=None, path=None, *args, **kwargs):
    return deku.download_episodes(anime_name=anime_name, episodes_to_download=episodes, path=path, *args, **kwargs)


@no_exception
def download_by_url(anime_name, url, episodes=None, path=None, *args, **kwargs):
    return deku.download_episodes_by_url(anime_name=anime_name, url=url, path=path, episodes_to_download=episodes,
                                         *args, **kwargs)


ctypes.windll.kernel32.SetConsoleTitleW("deku")
