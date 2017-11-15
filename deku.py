from Servers import G3
from Site9AnimeStuff import find_series_url_by_name
from log import warning, error, log


def download_episodes(anime_name, episodes_to_download, path, player_quality=None, server=None):
    log('fetching {}\'s series url...'.format(anime_name))
    series_url = find_series_url_by_name(anime_name)
    return download_episodes_by_url(series_url, anime_name, episodes_to_download, path, player_quality, server)


def download_episodes_by_url(series_url, anime_name, episodes_to_download, path, player_quality=None, server=None):
    print(anime_name)
    print(path)
    path = path + '\\' + anime_name
    if server is None:
        server = G3()
    log('downloading {} episodes {} from server {} to path \'{}\''.format(anime_name,
                                                                          episodes_to_download,
                                                                          server,
                                                                          path))
    try:
        server.download_episodes(series_page_url=series_url,
                                 requested_episodes=episodes_to_download,
                                 quality=player_quality,
                                 download_path=path)
    finally:
        server.close()
    return
