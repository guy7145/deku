from Servers import find_all_servers_and_eps
from log import bold
import Site9AnimeStuff
import BrowseUtils
import deku
from Servers import F2, F4, G3, RapidVideo

search = Site9AnimeStuff.search_series_urls_by_name
find_by_substring = Site9AnimeStuff.find_series_urls_by_name_substring
find_by_keywords = Site9AnimeStuff.find_series_urls_by_keywords
find_exact = Site9AnimeStuff.find_series_url_by_name
find = find_exact


def info(anime_name):
    print('fetching series url...')
    series_page_html = BrowseUtils.fetch_url(Site9AnimeStuff.find_series_url_by_name(anime_name))
    print('fetching series information...')
    hosts_to_eps = find_all_servers_and_eps(series_page_html)
    for server_name in hosts_to_eps:
        bold(server_name)
        for ep in hosts_to_eps[server_name]:
            print(ep)
    return


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


def download(anime_name, episodes, path='.', *args, **kwargs):
    return deku.download_episodes(anime_name=anime_name, episodes_to_download=episodes, path=path, *args, **kwargs)


def download_by_url(series_url, anime_name, episodes, path='.', *args, **kwargs):
    return deku.download_episodes_by_url(series_url=series_url, anime_name=anime_name, episodes_to_download=episodes,
                                         path=path, *args, **kwargs)
