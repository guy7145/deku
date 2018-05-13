import os
from bs4 import BeautifulSoup

from src import BrowseUtils, Site9AnimeStuff
from src.BrowseUtils import fetch_url, SOUP_PARSER_HTML
from src.Servers import RapidVideo, _find_all_servers_and_eps, G4, G3, F4, F2
from src.Site9AnimeStuff import find_series_url_by_name, sanitized
from src.log import error, log, bold


def download_episodes(anime_name, *args, **kwargs):
    log('fetching {}\'s series url...'.format(anime_name))
    series_url = find_series_url_by_name(anime_name)
    return download_episodes_by_url(anime_name, url=series_url, *args, **kwargs)


@sanitized
def download_episodes_by_url(anime_name, url, path=None, episodes_to_download=None, player_quality=None, server=RapidVideo):
    if path is None:
        path = os.getcwd()

    path = os.path.join(path, anime_name)
    server = server()
    log('downloading {} episodes {} from server {} to path \'{}\''.format(anime_name,
                                                                          episodes_to_download,
                                                                          server,
                                                                          path))
    try:
        server.download_episodes(series_page_url=url,
                                 requested_episodes=episodes_to_download,
                                 quality=player_quality,
                                 download_path=path)
    except Exception as e:
        error(e)
    finally:
        server.close()
    return


def get_video_links_by_url(series_page_url, eps=None, server=RapidVideo):
    return server().get_video_urls(series_page_url=series_page_url, eps=eps)


def get_video_links_by_name(anime_name, *args, **kwargs):
    return get_video_links_by_url(series_page_url=find_series_url_by_name(anime_name), *args, **kwargs)



def debug_src(name):
    return BeautifulSoup(fetch_url(find_series_url_by_name(name)), SOUP_PARSER_HTML)


def info(anime_name):
    print('fetching series url...')
    series_page_html = BrowseUtils.fetch_url(Site9AnimeStuff.find_series_url_by_name(anime_name))
    print('fetching series information...')
    hosts_to_eps = _find_all_servers_and_eps(series_page_html)
    for server_name in hosts_to_eps:
        bold(server_name)
        for ep in hosts_to_eps[server_name]:
            print(ep)
    return


def episodes(first=1, last=25):
    return list(range(first, last+1))
