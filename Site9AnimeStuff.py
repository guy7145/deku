from BrowseUtils import fetch_url
from log import log

base_url = "http://9anime.to"
base_watch_url = "https://9anime.to/watch"


def search_series_urls_by_name(name):
    log('searching "{}"'.format(name))
    page = fetch_url(base_url + "/search?keyword=" + name.replace(' ', '+'))
    results = [line for line in page.split('\"') if base_watch_url in line]
    return set(results)


def find_series_urls_by_name_substring(name):
    return [url for url in search_series_urls_by_name(name) if url.find(name.replace(' ', '-')) >= 0]


def find_series_urls_by_keywords(name):
    def is_match(url):
        for keyword in name.split(' '):
            if url.find(keyword) == -1:
                return False
        return True

    return [url for url in search_series_urls_by_name(name) if is_match(url)]


def find_series_url_by_name(name):
    search_pattern = name.replace(' ', '-') + '.'
    possible_results = search_series_urls_by_name(name)
    results = [res for res in possible_results if search_pattern in res]
    if len(results) == 0:
        log("watching page of {} couldn't be found. please check for typos.".format(name))
        raise
    elif len(results) > 1:
        log("more than 1 result were found for {}, choosing the first one;".format(name))

    result = results[0]
    log('found watching page of {}: {}'.format(name, result))
    return result
