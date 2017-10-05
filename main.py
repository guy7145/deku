import urllib
from urllib.request import Request, urlopen, urlretrieve, FancyURLopener
from bs4 import BeautifulSoup
from selenium import webdriver
import re

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.command import Command

base_url = "http://9anime.to"
base_watch_url = "https://9anime.to/watch"
friendly_user_agent = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'

def log(txt):
    print(txt)
    return


def break_name(name):
    return name.split(' ')


def create_request(url):
    user_agent = 'Mozilla/5.0'
    log('using user agent {}'.format(user_agent))
    return Request(url, headers={'User-Agent': user_agent})


def fetch_url(url):
    log('fetching {}'.format(url))
    req = create_request(url)
    with urlopen(req) as page:
        return str(page.read())


def search_series_urls_by_name(bname):
    log('searching "{}"'.format(' '.join(bname)))
    page = fetch_url(base_url + "/search?keyword=" + '+'.join(bname))
    results = [line for line in page.split('\"') if base_watch_url in line]
    return set(results)


def find_series_url_by_name(bname):
    name = ' '.join(bname)
    search_pattern = '-'.join(bname) + '.'
    possible_results = search_series_urls_by_name(bname)
    results = [res for res in possible_results if search_pattern in res]
    if len(results) == 0:
        log("watching page of {} couldn't be found. please check for typos.".format(name))
        raise
    elif len(results) > 1:
        log("more than 1 result were found for {}, choosing the first one;".format(name))

    result = results[0]
    log('found watching page of {}: {}'.format(name, result))
    return result


def get_episodes_watch_urls(series_page):
    lines = [line.lstrip("<a ") for line in series_page.split('>') if 'data-base' in line]

    episodes = dict()
    servers = [episodes]
    last_ep = 0
    latest_ep = 0
    for line in lines:
        ep_number = int(re.search('data-base="(.{1,3})"', line).group(1))
        ep_id = re.search('data-id="(.{6})"', line).group(1)

        if ep_number < last_ep:
            episodes = dict()
            servers.append(episodes)
            latest_ep = last_ep

        episodes[ep_number] = ep_id
        last_ep = ep_number

    log('found {} episodes in {} servers'.format(latest_ep, len(servers)))
    return servers, latest_ep


def get_absolute_url(domain, relative_url):
    return "{}/{}".format(domain, relative_url)


def driver_timeout_get_url(driver, url, timeout):
    driver.execute(Command.SET_TIMEOUTS, {'ms': float(timeout * 1000), 'type': 'page load'})
    try:
        driver.get(url)
    except TimeoutException:
        log('timeout!')
    return


def generate_chrome_driver(load_timeout_seconds=5, player_quality='1080p'):
    options = webdriver.ChromeOptions()
    options.add_argument("--mute-audio")
    driver = webdriver.Chrome(chrome_options=options)
    driver_timeout_get_url(driver, base_url, load_timeout_seconds)
    driver.execute(Command.SET_LOCAL_STORAGE_ITEM, {'key': 'player_quality', 'value': player_quality})
    return driver


def get_download_url_from_ep_watch_url(episode_url, chrome, load_timeout_seconds=10):
    download_server_url = 'https://3.bp.blogspot.com/'
    driver_timeout_get_url(chrome, episode_url, load_timeout_seconds)
    source = chrome.page_source
    soup = BeautifulSoup(source, 'html.parser')

    download_link = None
    for link in soup.find_all('a'):
        ref = link.get('href')
        if download_server_url in str(ref):
            if download_link is not None:
                log('error: more than one download link found; {}, {}'.format(download_link, ref))
            download_link = ref

    if download_link is None:
        log('error: no download link found')
        raise

    log('found download link: {} (watch link: {})'.format(download_link, episode_url))
    return download_link


def download_file(url, file_path):
    log('downloading: {} -> {}'.format(url, file_path))
    url = url.replace(' ', '%20')
    u = urlopen(url)
    meta = u.info()
    log(meta)
    # file_size = int(meta.getheaders("Content-Length")[0])
    # log("Downloading: {} Bytes: {}".format(file_name, file_size))

    file_size_dl = 0
    block_sz = 8192
    with open(file_path, 'wb') as f:
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break

            file_size_dl += len(buffer)
            # log(len(buffer))
            f.write(buffer)
            # status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
            # status = status + chr(8) * (len(status) + 1)
            # log(status)
    log('finished downloading {}'.format(file_path))
    return


def download_file_simple(url, file_path):
    log('downloading: {} -> {}'.format(url, file_path))
    url = url.replace(' ', '%20')
    urllib.request.URLopener.version = friendly_user_agent
    urlretrieve(url=url, filename=file_path)
    log('finished downloading {}'.format(file_path))
    return


def download_episodes(bname, path, episodes_to_download, short_timeout=10, long_timeout=20, server_number=0):
    series_url = find_series_url_by_name(bname)
    servers, latest_ep = get_episodes_watch_urls(fetch_url(series_url))
    log('downloading {} (episodes {}) to path \'{}\''.format(' '.join(bname), episodes_to_download, path))
    discarded_episodes = [ep for ep in episodes_to_download if ep > latest_ep]
    episodes_to_download = [ep for ep in episodes_to_download if ep <= latest_ep]
    if len(discarded_episodes) > 0:
        log('warning: episodes {} not found; downloading only episodes {}'.format(discarded_episodes, episodes_to_download))

    episode_links = servers[server_number]
    episode_links = [get_absolute_url(series_url, episode_links[key]) for key in episode_links.keys()]

    chrome = generate_chrome_driver(load_timeout_seconds=short_timeout)
    for i in episodes_to_download:
        ep_index = i - 1
        try:
            download_url = get_download_url_from_ep_watch_url(episode_links[ep_index], chrome, load_timeout_seconds=short_timeout)
        except:
            download_url = get_download_url_from_ep_watch_url(episode_links[ep_index], chrome, load_timeout_seconds=long_timeout)
        finally:
            download_file_simple(download_url, "{}/ep{}.mp4".format(path, i))
    chrome.quit()
    return


def main():
    anime_name = "tokyo ghoul"
    download_path = 'tokyo_ghoul'
    eps = list(range(3, 13))

    download_episodes(bname=break_name(anime_name), path=download_path, episodes_to_download=eps,
                      short_timeout=10, long_timeout=20, server_number=0)
    return

if __name__ == '__main__':
    main()
