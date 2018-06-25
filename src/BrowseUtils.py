import copy
import urllib
from math import inf
from urllib.request import urlopen, Request

import os
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException

from src.DownloadStatistics import DownloadStatistics
from src.log import log


friendly_user_agent = \
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'
    # 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'

KILO = 2**10
MEGA = 2**20
SOUP_PARSER_HTML = 'html.parser'
CONTENT_LENGTH = 'content-length'


def make_safe_url(url):
    return urllib.parse.quote(url, safe='$-_.+!*\'(),;/?:@=&%')


def fetch_url(url, headers=None, return_bytes=False):
    # log('fetching {}'.format(url))
    headers = make_headers_with_user_agent(headers)
    req = Request(url, headers=headers)
    with urlopen(req) as page:
        response = page.read()
    if return_bytes:
        return response
    else:
        return str(response)


def make_headers_with_user_agent(headers):
    if headers is None:
        headers = dict()
    headers['User-Agent'] = friendly_user_agent
    return headers


def get_absolute_url(domain, relative_url):
    return "{}/{}".format(domain, relative_url)


def generate_chrome_driver():
    options = webdriver.ChromeOptions()
    # no junk output in console
    options.add_argument('log-level=3')

    options.add_argument("--mute-audio")
    options.add_argument("--incognito")
    # options.add_argument("--enable-devtools-experiments")
    options.add_argument("--disable-extensions")
    options.add_argument("--headless")

    capabilities = webdriver.DesiredCapabilities.CHROME
    # capabilities['javascriptEnabled'] = True
    driver = webdriver.Chrome(chrome_options=options, desired_capabilities=capabilities)
    return driver


def driver_timeout_get_url(driver, url):
    try:
        driver.get(url)
    except TimeoutException:
        pass
    return


def __draw_progressbar(done, total, report_string_format, progress_bar_length=30):
    bar_done = '#' * int(progress_bar_length * done/total)
    bar_left = '-' * int(progress_bar_length * (total - done)/total)
    percentage = done/total
    print('\r' + report_string_format.format(bar=bar_done + bar_left, percentage=percentage), end='')
    return


def my_reporthook(count, block_size, total, download_statistics):
    download_statistics.report_block_downloaded(block_size)

    done_megabytes = count * block_size / MEGA
    speed_megabytes = download_statistics.get_speed() / MEGA
    info_report_string = '\t{speed:.2f}MBps'

    if total is not None:
        size_megabytes = total / MEGA
        estimated = ((size_megabytes - done_megabytes)/speed_megabytes if speed_megabytes != 0 else inf) / 60
        info_report_string += '\t{done:.2f}/{total_size:.2f} (MB)\tEst: {estimated:.2f} minutes'
    else:
        size_megabytes = '?'
        estimated = '?'
        info_report_string += '\t{done:.2f}/{total_size} (MB)\tEst: {estimated} minutes'

    info_report_string = info_report_string.format(speed=speed_megabytes,
                                                   done=done_megabytes,
                                                   total_size=size_megabytes,
                                                   estimated=estimated)

    if total is not None:
        __draw_progressbar(count * block_size,
                           total,
                           '[{bar}]{percentage:.2%}' + info_report_string,
                           progress_bar_length=50)
    else:
        print('\r' + info_report_string, end='')
    return


def download_file(url, file_path, headers=None):
    log('downloading: {} -> {}'.format(url, file_path))
    url = make_safe_url(url)
    headers = make_headers_with_user_agent(headers)

    download_statistics = DownloadStatistics()
    response = requests.get(url, stream=True, headers=headers)
    chunk_size = 4096
    if CONTENT_LENGTH in response.headers.keys():
        total_size = int(response.headers[CONTENT_LENGTH])
    else:
        total_size = None
    with open(file_path, 'wb') as outfile:
        for i, data in enumerate(response.iter_content(chunk_size=chunk_size)):
            outfile.write(data)
            my_reporthook(i, chunk_size, total_size, download_statistics)

    # urlretrieve(url=url, filename=file_path, reporthook=my_reporthook, data=headers)
    print()
    log('finished downloading {}'.format(file_path))
    return


def download_file_from_multiple_sources(urls, path, headers=None):
    log('downloading {} from multiple urls'.format(path))
    # if not os.path.exists(path):
    #     os.makedirs(path)

    headers = make_headers_with_user_agent(headers)
    with open(path, 'wb') as f:
        for i, url in enumerate(urls):
            # file_name = url[url.rfind('/') + 1:]
            # file_path = os.path.join(path, file_name)
            f.write(fetch_url(url, headers=headers, return_bytes=True))
            print('\r{}/{}...'.format(i, len(urls)), end='')
    print()
    log('finished downloading {}'.format(path))
    return
