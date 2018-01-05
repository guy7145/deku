import urllib
from math import inf
from urllib.request import urlopen, Request, urlretrieve

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.command import Command

from DownloadStatistics import DownloadStatistics
from log import log, warning, error

friendly_user_agent = \
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'

KILO = 2**10
MEGA = 2**20
SOUP_PARSER_HTML = 'html.parser'


def make_safe_url(url):
    return urllib.parse.quote(url, safe='$-_.+!*\'(),;/?:@=&%')


def create_request(url):
    user_agent = friendly_user_agent
    # log('using user agent {}'.format(user_agent))
    return Request(url, headers={'User-Agent': user_agent})


def fetch_url(url):
    # log('fetching {}'.format(url))
    req = create_request(url)
    with urlopen(req) as page:
        return str(page.read())


def get_absolute_url(domain, relative_url):
    return "{}/{}".format(domain, relative_url)


def generate_chrome_driver():
    options = webdriver.ChromeOptions()

    options.add_argument("--mute-audio")
    options.add_argument("--incognito")
    options.add_argument("--enable-devtools-experiments")
    # options.add_argument("--disable-extensions")
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


def download_file(url, file_path):
    log('downloading: {} -> {}'.format(url, file_path))
    url = make_safe_url(url)
    download_statistics = DownloadStatistics()

    def my_reporthook(count, block_size, total):
        download_statistics.report_block_downloaded(block_size)

        size_megabytes = total / MEGA
        done_megabytes = count * block_size / MEGA
        speed_megabytes = download_statistics.get_speed() / MEGA

        estimated = (size_megabytes - done_megabytes)/speed_megabytes if speed_megabytes != 0 else inf

        info_report_string = '\t{speed:.2f}MBps' \
                             '\t{done:.2f}/{total_size:.2f} (MB)' \
                             '\tEst: {estimated:.2f} minutes'
        info_report_string = info_report_string.format(speed=speed_megabytes,
                                                       done=done_megabytes,
                                                       total_size=size_megabytes,
                                                       estimated=estimated / 60)
        __draw_progressbar(count * block_size,
                           total,
                           '[{bar}]{percentage:.2%}' + info_report_string,
                           progress_bar_length=50)
        return

    headers = {'User-Agent': friendly_user_agent}
    response = requests.get(url, stream=True, headers=headers)
    chunk_size = 4096
    total_size = int(response.headers['content-length'])
    with open(file_path, 'wb') as outfile:
        for i, data in enumerate(response.iter_content(chunk_size=chunk_size)):
            outfile.write(data)
            my_reporthook(i, chunk_size, total_size)

    # urlretrieve(url=url, filename=file_path, reporthook=my_reporthook, data=headers)
    print()
    log('finished downloading {}'.format(file_path))
    return
