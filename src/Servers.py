import json
import os
from time import sleep

import re
from selenium.webdriver.remote.command import Command
from src.BrowseUtils import driver_timeout_get_url, generate_chrome_driver, fetch_url, get_absolute_url, download_file, \
    SOUP_PARSER_HTML, download_file_from_multiple_sources
from src.Site9AnimeStuff import find_series_url_by_name
from src.log import warning, error, log, bold
from bs4 import BeautifulSoup


def _find_all_servers_and_eps(series_page_html):
    hosts = dict()
    soup = BeautifulSoup(series_page_html, SOUP_PARSER_HTML)

    widget = soup.find(attrs={'class': 'widget servers'})
    titles = widget.find(attrs={'class': 'widget-title'}).find(attrs={'class': 'tabs'}).find_all(attrs={'class': 'tab'})
    servers = widget.find(attrs={'class': 'widget-body'}).find_all(attrs={'class': 'server'})

    for title, server in zip(titles, servers):
        name = title.text
        ep_links = server.find_all('a')
        eps = list()
        for ep_link in ep_links:
            ep = Episode(ep_number=int(ep_link['data-base']),
                         date_added=ep_link['data-title'],
                         ep_id=ep_link['data-id'],
                         rel_url=ep_link['href'])
            eps.append(ep)
        hosts[name] = eps

    return hosts


class Episode:
    def __init__(self, ep_number, date_added, ep_id, rel_url):
        self.ep_number = ep_number
        self.date_added = date_added
        self.ep_id = ep_id
        self.rel_url = rel_url
        return

    def __hash__(self):
        return self.ep_id

    def __repr__(self):
        return 'ep {ep_num}\t(added at {date})\t{ep_id}'.format(ep_num=self.ep_number,
                                                                ep_id=self.ep_id,
                                                                date=self.date_added)


def close_ads(driver):
    for tab in driver.window_handles:
        driver.switch_to_window(tab)
        sleep(1)
        if '9anime' not in driver.current_url:
            driver.close()
    driver.switch_to_window(driver.window_handles[0])
    return


def getRidOfCoverDiv(driver):
    js = "getEventListeners(document.getElementsByClassName('cover')[0])['click'][0].listener({type: 'click'})"
    driver.find_elements_by_class_name('cover')[0].click()
    close_ads(driver)
    sleep(2)
    return


class ServerSpecificCrawler:
    def __init__(self):
        self.driver = generate_chrome_driver()
        log('Crawler for {} is up.'.format(self.get_server_name()))
        return

    def get_server_name(self):
        raise NotImplementedError

    def get_headers(self):
        return None

    def close(self):
        self.driver.close()
        log('Crawler for {} is down.'.format(self.get_server_name()))
        return

    def _navigate(self, url):
        return driver_timeout_get_url(self.driver, url)

    def _find_episode_watch_links(self, series_page_html):
        hosts = _find_all_servers_and_eps(series_page_html)
        bold('Found {} Servers:'.format(len(hosts.keys())))
        log('\n'.join(
            ['{}:\t{}'.format(server_name, [ep.ep_number for ep in hosts[server_name]]) for server_name in hosts]
        ))
        return hosts[self.get_server_name()]

    def highest_quality(self):
        raise NotImplementedError

    def set_quality(self, requested_quality):
        raise NotImplementedError

    def _find_download_url(self, ep_page_html):
        raise NotImplementedError

    def _travel_episodes(self, series_url, eps):
        for ep in eps:
            self._navigate(get_absolute_url(series_url, relative_url=ep.ep_id))
            getRidOfCoverDiv(self.driver)
            yield self._find_download_url(self.driver.page_source)

    def download_episodes(self, series_page_url, requested_episodes, quality, download_path):
        series_page_html = fetch_url(series_page_url)
        available_episodes = self._find_episode_watch_links(series_page_html)

        # region quality
        if quality is None:
            quality = self.highest_quality()
            warning('no specific quality was requested; '
                    'using highest quality ({}) available in this server ({})'.format(quality, self.get_server_name()))

        self.set_quality(quality)
        # endregion

        episodes_to_download = self.intersect_availible_and_requested_episodes(available_episodes, requested_episodes)

        ep_fmt = 'ep{ep:03d}.{extension}'
        for download_url, ep in zip(self._travel_episodes(series_page_url, episodes_to_download), episodes_to_download):
            log('found download url for episode {}!'.format(ep.ep_number))
            if not os.path.exists(download_path):
                os.makedirs(download_path)
            if type(download_url) is str:
                download_file(download_url, os.path.join(download_path, ep_fmt.format(ep=ep.ep_number, extension='mp4')), self.get_headers())
            else:
                download_file_from_multiple_sources(download_url, os.path.join(download_path, ep_fmt.format(ep=ep.ep_number, extension='ts')), self.get_headers())

        return

    def intersect_availible_and_requested_episodes(self, available_episodes, requested_episodes):
        available_episodes_numbers = set([ep.ep_number for ep in available_episodes])
        if requested_episodes is None:
            requested_episodes = available_episodes_numbers
        else:
            requested_episodes = set(requested_episodes)
            requested_but_not_available = requested_episodes.difference(available_episodes_numbers)
            requested_and_available = requested_episodes.intersection(available_episodes_numbers)
            if len(requested_but_not_available) > 0:
                warning('episodes {} not available; downloading episodes {}'.format(requested_but_not_available,
                                                                                    requested_and_available))
        episodes_to_download = [ep for ep in available_episodes if ep.ep_number in requested_episodes]
        return episodes_to_download

    def get_video_urls(self, series_page_url, eps=None):
        series_page_html = fetch_url(series_page_url)
        available_episodes = self._find_episode_watch_links(series_page_html)

        eps = self.intersect_availible_and_requested_episodes(available_episodes, eps)
        links = []
        for link in self._travel_episodes(series_page_url, eps):
            print(link)
            links.append(link)

        for ep, link in zip(eps, links):
            print("ep{}:\t{}".format(ep.ep_number, link))

        return links

    def __repr__(self):
        return self.get_server_name()


class RapidVideo(ServerSpecificCrawler):
    QUALITY_ORDER = (1080, 720, 480, 360)

    def _find_download_url(self, ep_page_html):
        soup = BeautifulSoup(ep_page_html, SOUP_PARSER_HTML)
        link = soup.find(attrs={'id': 'player'}).find('iframe')['src']
        # link = link[:link.index('?')]   # no 'autostart=True' parameter
        self._navigate(link)
        sleep(3)
        actual_page = self.driver.page_source
        soup = BeautifulSoup(actual_page, SOUP_PARSER_HTML)
        home_video_div = soup.find('div', id='home_video')
        links = [a['href'] for a in home_video_div.find_all('a')]
        log('links found in RapidVideo: {}'.format(links))
        for q in RapidVideo.QUALITY_ORDER:
            for link in links:
                if '&q={}p'.format(q) in link:
                    log('highest resolution found: {}p'.format(q))
                    soup = BeautifulSoup(fetch_url(link), SOUP_PARSER_HTML)
                    return soup.find('source')['src']
        raise RuntimeError('can\'t find download link')

    def get_server_name(self):
        return 'RapidVideo'

    def set_quality(self, requested_quality):
        # self._navigate('https://www.rapidvideo.com/')
        # self.driver.add_cookie({'name': 'q', 'value': str(requested_quality), 'domain': '.rapidvideo.com'})
        return

    def highest_quality(self):
        return 1080


class G3F4AndWhatever(ServerSpecificCrawler):
    QUALITIES = {1080: '1080p', 720: '720p', 480: '480p', 360: '360p'}
    HIGHEST_QUALITY = 1080

    def get_server_name(self):
        raise NotImplementedError

    def highest_quality(self):
        return G3F4AndWhatever.HIGHEST_QUALITY

    def _find_download_url(self, ep_page_html):
        download_url_pattern = 'googleusercontent'
        soup = BeautifulSoup(ep_page_html, SOUP_PARSER_HTML)

        download_link = None
        for link in soup.find_all('a'):
            ref = link.get('href')
            if download_url_pattern in str(ref):
                if download_link is not None:
                    error('more than one download link found; {}, {}'.format(download_link, ref))
                download_link = ref

        if download_link is None:
            raise RuntimeError('no download link found')

        return download_link

    def set_quality(self, requested_quality):
        requested_quality = G3F4AndWhatever.QUALITIES[requested_quality]
        self._navigate('https://9anime.to/')
        current_quality = self.driver.execute(Command.GET_LOCAL_STORAGE_ITEM, {'key': 'player_quality'})['value']
        if current_quality is not None:
            current_quality = current_quality.lower()

        if current_quality != requested_quality.lower():
            log('current quality: {}; changing to {}...'.format(current_quality, requested_quality))
            self.driver.execute(Command.SET_LOCAL_STORAGE_ITEM, {'key': 'player_quality', 'value': requested_quality})
        return


class G3(G3F4AndWhatever):
    def get_server_name(self):
        return 'Server G3'


class G4(G3F4AndWhatever):
    def get_server_name(self):
        return 'Server G4'


class F4(G3F4AndWhatever):
    def get_server_name(self):
        return 'Server F4'


class F2(G3F4AndWhatever):
    def get_server_name(self):
        return 'Server F2'


class MyCloud(ServerSpecificCrawler):
    DOMAIN = 'https://mcloud.to'
    spoofed_headers = {
        # 'Host': 'mcloud.to',
        # 'Origin': DOMAIN,
        'Referer': DOMAIN,
        # 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        # 'accept-encoding': 'gzip, deflate, br',
        # 'accept-language': 'en-US,en;q=0.9',
        # 'cache-control': 'max-age=0',
        # 'upgrade-insecure-requests': '1',
        # 'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'
    }

    def get_headers(self):
        return MyCloud.spoofed_headers

    def get_server_name(self):
        return 'MyCloud'

    def highest_quality(self):
        pass

    def set_quality(self, requested_quality):
        pass

    def __get_playlists_list(self):
        iframe = self.driver.find_elements_by_tag_name('iframe')[0]
        self.driver.switch_to_frame(iframe)
        lst = re.search('\[{"file":"(.+)"}\]', self.driver.page_source).group(1)
        return lst

    httpGetJavaScript = """return (function(theUrl)
  {
    var xmlHttp = null;
    xmlHttp = new XMLHttpRequest();
    xmlHttp.open( "GET", theUrl, false );
    xmlHttp.send( null );
    return xmlHttp.responseText;
    
  })(arguments[0])"""

    def _find_download_url(self, ep_page_html):
        list_of_qualities = self.__get_playlists_list()
        ep_dir = list_of_qualities[:list_of_qualities.rfind('/')]
        print(ep_dir)
        print(list_of_qualities)
        self._navigate(self.DOMAIN)

        m3us_text = self.driver.execute_script(self.httpGetJavaScript, [list_of_qualities])
        playlists = re.findall('#EXT-X-STREAM-INF:PROGRAM-ID=., BANDWIDTH=.+, RESOLUTION=(.+)\n(.+)', m3us_text)
        quality, playlist_url = max(playlists, key=lambda opt: int(opt[0].split('x')[1]))  # 1280x720 -> 720; 640x360 -> 360; etc.
        playlist_url = ep_dir + '/' + playlist_url

        print('found playlist with quality {} in {}'.format(quality, playlist_url))

        # ts_urls = self.driver.execute_script(self.httpGetJavaScript, [ep_dir + '/' + playlist_url]).split('\n')
        ts_urls = fetch_url(playlist_url,
                            headers=MyCloud.spoofed_headers,
                            return_bytes=True).decode('ascii').split('\n')
        ts_urls = [line for line in ts_urls if '.ts' in line]

        ep_dir_url = ep_dir + '/hls/{}/'.format(quality.split('x')[1])
        ts_urls = [ep_dir_url + url for url in ts_urls]
        print(ts_urls[1])
        # return [playlist_url] + ts_urls
        return ts_urls


if __name__ == '__main__':
    # test header spoofing
    print(fetch_url('https://stream.mcloud.to/q13/i0/h0/p26/NdhlMSLfjNnSOYSuRpMROQ/1520571600/e/3/a/ll99nn/hls/720/720-0001.ts',
                    MyCloud.spoofed_headers,
                    return_bytes=True).decode(errors='ignore'))
