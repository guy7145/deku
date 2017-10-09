import deku


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


def download(anime_name, episodes, path='./', *args, **kwargs):
    return deku.download_episodes(anime_name=anime_name, episodes_to_download=episodes, path=path, *args, **kwargs)
