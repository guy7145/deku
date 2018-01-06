from bs4 import BeautifulSoup

from src import BrowseUtils, Site9AnimeStuff
from src.BrowseUtils import fetch_url, SOUP_PARSER_HTML
from src.Servers import RapidVideo, _find_all_servers_and_eps
from src.Site9AnimeStuff import find_series_url_by_name
from src.log import error, log, bold


def download_episodes(anime_name, episodes_to_download, path, player_quality=None, server=RapidVideo):
    log('fetching {}\'s series url...'.format(anime_name))
    series_url = find_series_url_by_name(anime_name)
    return download_episodes_by_url(series_url, anime_name, episodes_to_download, path, player_quality, server)


def download_episodes_by_url(series_url, anime_name, episodes_to_download, path, player_quality=None, server=RapidVideo):
    path = path + '\\' + anime_name
    server = server()
    log('downloading {} episodes {} from server {} to path \'{}\''.format(anime_name,
                                                                          episodes_to_download,
                                                                          server,
                                                                          path))
    try:
        server.download_episodes(series_page_url=series_url,
                                 requested_episodes=episodes_to_download,
                                 quality=player_quality,
                                 download_path=path)
    except Exception as e:
        error(e)
    finally:
        server.close()
    return


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
