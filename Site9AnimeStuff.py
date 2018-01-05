from bs4 import BeautifulSoup

from BrowseUtils import fetch_url, SOUP_PARSER_HTML
from log import log

base_url = "http://9anime.to"
base_watch_url = "https://9anime.to/watch"


def search_series_urls_by_name(name):
    name = name.lower()
    log('searching "{}"'.format(name))
    page = fetch_url(base_url + "/search?keyword=" + name.replace(' ', '+'))
    soup = BeautifulSoup(page, SOUP_PARSER_HTML)
    posters = soup.find_all('a', {'class': 'poster'})
    results = [(poster.find('img')['alt'], poster['href']) for poster in posters]
    return results


def find_series_urls_by_name_substring(name):
    name = name.lower()
    return [name_url[1] for name_url in search_series_urls_by_name(name)
            if name_url[0].lower().find(name.lower()) >= 0]


def find_series_urls_by_keywords(name):
    name = name.lower()

    def is_match(txt):
        for keyword in name.split(' '):
            if txt.find(keyword) == -1:
                return False
        return True

    return [name_url[1] for name_url in search_series_urls_by_name(name) if is_match(name_url[0])]


def find_series_url_by_name(name):
    # search_pattern = name.replace(' ', '-') + '.'
    def compare_approx(txt1, txt2):
        replaceables = '!?-=_+[]{}()@#$%^&*;:\'\"\\|,.<>'
        for c in replaceables:
            txt1 = txt1.replace(c, '')
            txt2 = txt2.replace(c, '')
        txt1 = txt1.lower()
        txt2 = txt2.lower()
        return txt1 == txt2

    name = name.lower()
    possible_results = search_series_urls_by_name(name)
    results = [res[1] for res in possible_results if compare_approx(name, res[0])]
    if len(results) == 0:
        log("watching page of {} couldn't be found. please check for typos or switch to names in opposite language (english/japanese).".format(name))
        raise Exception
    elif len(results) > 1:
        log("more than 1 result were found for {}, choosing the first one;".format(name))

    result = results[0]
    log('found watching page of {}: {}'.format(name, result))
    return result
