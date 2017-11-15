import os
import re

from bs4 import BeautifulSoup
from selenium.webdriver.remote.command import Command

from BrowseUtils import fetch_url, get_absolute_url, driver_timeout_get_url, generate_chrome_driver, download_file
from Site9AnimeStuff import base_url, find_series_url_by_name
from log import warning, error, log


# def get_episodes_watch_urls(series_page):
#     lines = [line.lstrip("<a ") for line in series_page.split('>') if 'data-base' in line]
#
#     episodes = dict()
#     servers = [episodes]
#     last_ep = 0
#     latest_ep = 0
#     for line in lines:
#         ep_number = int(re.search('data-base="(.{1,4})"', line).group(1))
#         ep_id = re.search('data-id="(.{6})"', line).group(1)
#
#         if ep_number <= last_ep:
#             episodes = dict()
#             servers.append(episodes)
#             latest_ep = last_ep
#
#         episodes[ep_number] = ep_id
#         last_ep = ep_number
#
#     log('found {} episodes in {} servers'.format(latest_ep, len(servers)))
#     return servers, latest_ep


# def set_driver_quality(driver, requested_quality):
#     current_quality = driver.execute(Command.GET_LOCAL_STORAGE_ITEM, {'key': 'player_quality'})['value']
#
#     if current_quality is not None:
#         current_quality = current_quality.lower()
#
#     if current_quality != requested_quality.lower():
#         driver.execute(Command.SET_LOCAL_STORAGE_ITEM, {'key': 'player_quality', 'value': requested_quality})
#         driver.refresh()
#     return


def get_download_url_from_ep_watch_url(episode_url, chrome, load_timeout_seconds=10):
    download_url_pattern = 'googleusercontent'
    driver_timeout_get_url(chrome, episode_url, load_timeout_seconds)
    source = chrome.page_source
    soup = BeautifulSoup(source, 'html.parser')

    download_link = None
    for link in soup.find_all('a'):
        ref = link.get('href')
        if download_url_pattern in str(ref):
            if download_link is not None:
                error('more than one download link found; {}, {}'.format(download_link, ref))
            download_link = ref

    if download_link is None:
        error('no download link found')
        raise RuntimeError

    log('found download link: {} (watch link: {})'.format(download_link, episode_url))
    return download_link


def download_episodes(anime_name, episodes_to_download, path, player_quality='1080p',
                      server_number=0, timeouts=(5, 10, 20)):
    log('downloading {} (episodes {}) from server {} to path \'{}\''.format(anime_name,
                                                                            episodes_to_download,
                                                                            server_number,
                                                                            path))
    log('fetching series url...')
    series_url = find_series_url_by_name(anime_name)
    download_episodes_by_url(series_url,
                             anime_name,
                             episodes_to_download,
                             path,
                             player_quality,
                             server_number,
                             timeouts)
    return


def download_episodes_by_url(series_url,
                             anime_name,
                             episodes_to_download,
                             path,
                             player_quality='1080p',
                             server_number=0,
                             timeouts=(5, 10, 20)):
    path = path + '\\' + anime_name
    log('fetching episodes urls...')
    servers, latest_ep = get_episodes_watch_urls(fetch_url(series_url))
    episode_links = servers[server_number]
    for key in episode_links.keys():
        episode_links[key] = get_absolute_url(series_url, episode_links[key])
    discarded_episodes = [ep for ep in episodes_to_download if ep not in episode_links.keys()]
    episodes_to_download = [ep for ep in episodes_to_download if ep in episode_links.keys()]
    if len(discarded_episodes) > 0:
        warning('episodes {} not found; downloading only episodes {}'.format(discarded_episodes, episodes_to_download))
    log('opening browser...')
    chrome = generate_chrome_driver()
    driver_timeout_get_url(chrome, url=base_url, timeout=timeouts[0])
    set_driver_quality(chrome, player_quality)
    log('downloading {} episodes {}'.format(anime_name, episodes_to_download))
    for ep_index in episodes_to_download:
        log('finding episode {} download link...'.format(ep_index))
        download_url = None
        for timeout in timeouts:
            try:
                download_url = get_download_url_from_ep_watch_url(episode_links[ep_index],
                                                              chrome,
                                                              load_timeout_seconds=timeout)
                break

            except:
                continue

        if download_url is None:
            print(chrome.page_source)
            error("couldn't find download url for {} ep {}".format(anime_name, ep_index))

        else:
            if not os.path.exists(path):
                os.makedirs(path)
            download_file(download_url, "{}/ep{}.mp4".format(path, ep_index))
    chrome.quit()
