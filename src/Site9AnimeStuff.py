from bs4 import BeautifulSoup
from src.BrowseUtils import fetch_url, SOUP_PARSER_HTML
from src.log import log

base_url = "http://9anime.to"
base_watch_url = "https://9anime.to/watch"


def sanitize_name(name):
    new_name = ''
    for c in name.lower():
        if c.isalnum() or c.isspace():
            new_name += c
        else:
            new_name += ' '

    new_name = ' '.join(new_name.split())  # remove double-spaces and strip
    return new_name


def sanitized(func):
    def sanitized_func(name, *args, **kwargs):
        return func(sanitize_name(name), *args, **kwargs)
    return sanitized_func


@sanitized
def search_series_urls_by_name(name):
    log('searching "{}"'.format(name))
    page = fetch_url(base_url + "/search?keyword=" + name.replace(' ', '+'))
    soup = BeautifulSoup(page, SOUP_PARSER_HTML)
    posters = soup.find_all('a', {'class': 'poster'})
    names = [poster.find('img')['alt'] for poster in posters]
    urls = [poster['href'] for poster in posters]
    return names, urls


@sanitized
def find_series_urls_by_name_substring(name):
    return [url for _name, url in zip(*search_series_urls_by_name(name)) if sanitize_name(_name).find(name) >= 0]


@sanitized
def find_series_urls_by_keywords(name):
    @sanitized
    def is_match(txt):
        for keyword in name.split(' '):
            if txt.find(keyword) == -1:
                return False
        return True

    return [url for _name, url in zip(*search_series_urls_by_name(name)) if is_match(_name)]


@sanitized
def find_series_url_by_name(name):
    results = [url for _name, url in zip(*search_series_urls_by_name(name)) if name == sanitize_name(_name)]

    if len(results) == 0:
        log("watching page of {} couldn't be found. please check for typos or switch to names in opposite language (english/japanese)".format(name))
        raise Exception()
    elif len(results) > 1:
        log("more than 1 result were found for {}, choosing the first one;".format(name))

    result = results[0]
    log('found watching page of {}: {}'.format(name, result))
    return result
