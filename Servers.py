import os

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.command import Command

from BrowseUtils import driver_timeout_get_url, generate_chrome_driver, fetch_url, get_absolute_url, download_file
from Site9AnimeStuff import find_series_url_by_name
from log import warning, error, log, bold
from bs4 import BeautifulSoup

SOUP_PARSER_HTML = 'html.parser'


def find_all_servers_and_eps(series_page_html):
    hosts = dict()
    soup = BeautifulSoup(series_page_html, SOUP_PARSER_HTML)
    server_rows = soup.find_all(name='div', attrs={'class': 'server row'})
    for server_row in server_rows:
        name = list(server_row.find('label').strings)[-1].strip(' \n')
        ep_links = server_row.find_all('a')
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

    def __navigate(self, url):
        return driver_timeout_get_url(self.driver, url)

    def _find_episode_watch_links(self, series_page_html):
        hosts = find_all_servers_and_eps(series_page_html)
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
        for ep in episodes_to_download:
            self.__navigate(get_absolute_url(series_page_url, relative_url=ep.ep_id))
            self.set_quality(quality)
            download_url = self._find_download_url(self.driver.page_source)
            log('found download url for episode {}!'.format(ep.ep_number))
            if not os.path.exists(download_path):
                os.makedirs(download_path)
            download_file(download_url, "{}/ep{}.mp4".format(download_path, ep.ep_number))
        return

    def __repr__(self):
        return self.get_server_name()


class G3F4AndWhatever(ServerSpecificCrawler):
    QUALITIES = {1080: '1080p', 720: '720p', 480: '480p', 360: '360p'}
    HIGHEST_QUALITY = 1080

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        return

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
            error('no download link found')
            raise RuntimeError

        return download_link

    def set_quality(self, requested_quality):
        requested_quality = G3F4AndWhatever.QUALITIES[requested_quality]

        current_quality = self.driver.execute(Command.GET_LOCAL_STORAGE_ITEM, {'key': 'player_quality'})['value']
        if current_quality is not None:
            current_quality = current_quality.lower()

        if current_quality != requested_quality.lower():
            log('current quality: {}; changing to {}...'.format(current_quality, requested_quality))
            self.driver.execute(Command.SET_LOCAL_STORAGE_ITEM, {'key': 'player_quality', 'value': requested_quality})
            try:
                self.driver.refresh()
            except TimeoutException:
                pass
        return


class G3(G3F4AndWhatever):
    def get_server_name(self):
        return 'Server G3'


class F4(G3F4AndWhatever):
    def get_server_name(self):
        return 'Server F4'


class F2(G3F4AndWhatever):
    def get_server_name(self):
        return 'Server F2'
