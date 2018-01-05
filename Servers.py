import os
from time import sleep
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.command import Command
from BrowseUtils import driver_timeout_get_url, generate_chrome_driver, fetch_url, get_absolute_url, download_file, \
    SOUP_PARSER_HTML
from Site9AnimeStuff import find_series_url_by_name
from log import warning, error, log, bold
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


def getRidOfCoverDiv(driver):
    js = "getEventListeners(document.getElementsByClassName('cover')[0])['click'][0].listener({type: 'click'})"
    driver.find_elements_by_class_name('cover')[0].click()
    driver.switch_to_window(driver.window_handles[1])
    driver.close()
    driver.switch_to_window(driver.window_handles[0])
    sleep(3)
    # driver.execute_script(js, [])
    # print(driver.execute("getEventListeners", "document.getElementsByClassName('cover')[0]"))
    return


class ServerSpecificCrawler:
    def __init__(self):
        self.driver = generate_chrome_driver()
        log('Crawler for {} is up.'.format(self.get_server_name()))
        return

    def get_server_name(self):
        raise NotImplementedError

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

    def download_episodes(self, series_page_url, requested_episodes, quality, download_path):
        if quality is None:
            quality = self.highest_quality()
            warning('no specific quality was requested; '
                    'using highest quality ({}) available in this server ({})'.format(quality, self.get_server_name()))

        series_page_html = fetch_url(series_page_url)
        available_episodes = self._find_episode_watch_links(series_page_html)

        # inform the user in case some episodes are missing...
        available_episodes_numbers = set([ep.ep_number for ep in available_episodes])
        requested_episodes = set(requested_episodes)
        requested_but_not_available = requested_episodes.difference(available_episodes_numbers)
        requested_and_available = requested_episodes.intersection(available_episodes_numbers)
        if len(requested_but_not_available) > 0:
            warning('episodes {} not available; downloading episodes {}'.format(requested_but_not_available,
                                                                                requested_and_available))
        # end of user stuff

        episodes_to_download = [ep for ep in available_episodes if ep.ep_number in requested_episodes]
        self.set_quality(quality)
        for ep in episodes_to_download:
            self._navigate(get_absolute_url(series_page_url, relative_url=ep.ep_id))

            getRidOfCoverDiv(self.driver)

            download_url = self._find_download_url(self.driver.page_source)
            log('found download url for episode {}!'.format(ep.ep_number))
            if not os.path.exists(download_path):
                os.makedirs(download_path)
            download_file(download_url, "{}/ep{}.mp4".format(download_path, ep.ep_number))
        return

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


if __name__ == '__main__':
    s = RapidVideo()
    try:
        s.download_episodes(find_series_url_by_name('shokugeki no souma'),
                            requested_episodes=[3, 4, 5, 6],
                            download_path='.\\downloaded\\shokugeki no souma',
                            quality=None)
    finally:
        s.close()
