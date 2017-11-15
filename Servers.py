import os
import urllib
from math import inf
from urllib.request import Request, urlopen, urlretrieve, FancyURLopener
from bs4 import BeautifulSoup
from selenium import webdriver
import re
import itertools

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.command import Command

from DownloadStatistics import DownloadStatistics
from BrowseUtils import driver_timeout_get_url, generate_chrome_driver, fetch_url, get_absolute_url
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
    bold('Found {} Servers:'.format(len(hosts.keys())))
    log('\n'.join(['{}:\t{}'.format(server_name, [ep.ep_number for ep in hosts[server_name]]) for server_name in hosts]))
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
    # end of Episode class #


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
        driver_timeout_get_url(self.driver, url)
        return

    def _find_episode_watch_links(self, series_page_html):
        return find_all_servers_and_eps(series_page_html)[self.get_server_name()]

    def set_quality(self, requested_quality):
        raise NotImplementedError

    def _find_download_url(self, ep_page_html):
        raise NotImplementedError

    def download_episodes(self, series_page_url, requested_episodes, quality):
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

        episodes_to_download = [ep for ep in available_episodes if ep.ep_number in requested_episodes]
        for ep in episodes_to_download:
            self.__navigate(get_absolute_url(series_page_url, relative_url=ep.ep_id))
            self.set_quality(quality)
            download_url = self._find_download_url(self.driver.page_source)
            print('{}: {}'.format(ep, download_url))
        return


class G3F4AndWhatever(ServerSpecificCrawler):
    QUALITIES = {1080: '1080p', 720: '720p', 480: '480p', 360: '360p'}
    HIGHEST_QUALITY = QUALITIES[1080]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        return

    def get_server_name(self):
        raise NotImplementedError

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

    def set_quality(self, requested_quality=1080):
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        return

    def get_server_name(self):
        return 'Server G3'


if __name__ == '__main__':
    html = """error: b'<!DOCTYPE html>
 <html lang="en-US">
 <head>
 <title>
Watch Tokyo Ghoul \xe2\x88\x9aA English Subbed in HD on 9anime.to</title>
 
<meta name="description" content="Watch Watch Tokyo Ghoul \xe2\x88\x9aA English Subbed in HD on 9anime.to Tokyo Ghoul Root A, Tokyo Ghoul 2nd Season, Tokyo Ghoul Second Season,\xe6\x9d\xb1\xe4\xba\xac\xe5\x96\xb0\xe7\xa8\xae\xe2\x88\x9aA English...">
 <meta name="robots" content="index, follow">
 <meta name="revisit-after" content="1 days">
 <link href="https://9anime.to/watch/tokyo-ghoul-a.oq8" rel="canonical">
 <meta property="og:url" content="https://9anime.to/watch/tokyo-ghoul-a.oq8">
 <meta property="og:title" content="Watch Tokyo Ghoul \xe2\x88\x9aA English Subbed in HD on 9anime.to">
 <meta property="og:description" content="Watch Watch Tokyo Ghoul \xe2\x88\x9aA English Subbed in HD on 9anime.to Tokyo Ghoul Root A, Tokyo Ghoul 2nd Season, Tokyo Ghoul Second Season,\xe6\x9d\xb1\xe4\xba\xac\xe5\x96\xb0\xe7\xa8\xae\xe2\x88\x9aA English...">
 <meta property="og:site_name" content="fmovies">
 <meta property="og:image" content="http://2.bp.blogspot.com/-5hBnqeD_-nU/WH-0dQJsAaI/AAAAAAABZ-c/POMPrz9pIsE/w650-h350/tokyo-ghoul-a.jpg">
 <meta property="og:type" content="video.movie">
 <meta property="og:image:width" content="650">
 <meta property="og:image:height" content="350">
 <meta property="og:image:type" content="image/jpeg">
 <meta property="og:site_name" content="9anime">
 <meta property="fb:app_id" content="332290057111268">
 <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
 <base href="https://9anime.to/">
 <meta http-equiv="content-language" content="en">
<link href="/assets/favicons/favicon.png" type="image/x-icon" rel="shortcut icon">
 <link rel="apple-touch-icon" sizes="180x180" href="/assets/favicons/apple-touch-icon.png">
 <link rel="icon" type="image/png" href="/assets/favicons/favicon-32x32.png" sizes="32x32">
 <link rel="icon" type="image/png" href="/assets/favicons/favicon-16x16.png" sizes="16x16">
 <link rel="manifest" href="/assets/favicons/manifest.json">
 <link rel="mask-icon" href="/assets/favicons/safari-pinned-tab.svg" color="#5bbad5">
 <meta name="theme-color" content="#ffffff">
<link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
 <link rel="stylesheet" type="text/css" href="https://fonts.googleapis.com/css?family=Roboto:400,300,300italic,500">
<meta name="google-site-verification" content="_r0j8TBhMmO1pzE2F8d06nSVRgVKVfB144mgEGtzWg8">
 <script type="application/ld+json">
\n{\n    "@context": "http://schema.org",\n    "@type": "WebSite", "url": "https://9anime.to/",\n    "potentialAction": {\n        "@type": "SearchAction",\n        "target": "https://9anime.to/search?keyword={keyword}",\n        "query-input": "required name=keyword"\n    }\n}\n</script>
 <style>
#M223269ScriptRootC176393 {min-height: 300px;}</style>
<link href="/assets/min/frontend/all.css?5a0b1871" rel="stylesheet">
</head>
 <body data-ts="1510761600">
 <div id="header">
 <div class="container">
 <div class="pull-left hidden-xs">
 <input id="layoutswitcher" type="checkbox" style="display: none" />
 </div>
<div class="pull-left menu-toggler btn btn-sm btn-dark">
 <i class="fa fa-list">
</i>
 </div>
 <div class="pull-right">
 <span id="sign">
</span>
 <span class="search-toggler btn btn-sm btn-dark">
 <i class="fa fa-search">
</i>
 </span>
 </div>
<div id="logo">
<a href="https://9anime.to">
Watch high quality anime online</a>
</div>
 </div>
 </div>
 <div id="nav">
 <div class="container">
 <form id="search" autocomplete="off" action="/search">
 <div class="inner">
 <button type="submit">
<i class="fa fa-search">
</i>
</button>
 <input type="text" name="keyword" placeholder="Search">
 <div class="suggestions">
</div>
 </div>
 </form>
 <ul id="menu">
 <li class="item home">
<a href="/">
Home</a>
</li>
 <li class="item">
<a>
Genre</a>
 <ul class="sub">
 <li>
<a href="/genre/action" title="Action">
Action</a>
</li>
 <li>
<a href="/genre/adventure" title="Adventure">
Adventure</a>
</li>
 <li>
<a href="/genre/cars" title="Cars">
Cars</a>
</li>
 <li>
<a href="/genre/comedy" title="Comedy">
Comedy</a>
</li>
 <li>
<a href="/genre/dementia" title="Dementia">
Dementia</a>
</li>
 <li>
<a href="/genre/demons" title="Demons">
Demons</a>
</li>
 <li>
<a href="/genre/drama" title="Drama">
Drama</a>
</li>
 <li>
<a href="/genre/ecchi" title="Ecchi">
Ecchi</a>
</li>
 <li>
<a href="/genre/fantasy" title="Fantasy">
Fantasy</a>
</li>
 <li>
<a href="/genre/game" title="Game">
Game</a>
</li>
 <li>
<a href="/genre/harem" title="Harem">
Harem</a>
</li>
 <li>
<a href="/genre/historical" title="Historical">
Historical</a>
</li>
 <li>
<a href="/genre/horror" title="Horror">
Horror</a>
</li>
 <li>
<a href="/genre/josei" title="Josei">
Josei</a>
</li>
 <li>
<a href="/genre/kids" title="Kids">
Kids</a>
</li>
 <li>
<a href="/genre/magic" title="Magic">
Magic</a>
</li>
 <li>
<a href="/genre/martial-arts" title="Martial Arts">
Martial Arts</a>
</li>
 <li>
<a href="/genre/mecha" title="Mecha">
Mecha</a>
</li>
 <li>
<a href="/genre/military" title="Military">
Military</a>
</li>
 <li>
<a href="/genre/music" title="Music">
Music</a>
</li>
 <li>
<a href="/genre/mystery" title="Mystery">
Mystery</a>
</li>
 <li>
<a href="/genre/parody" title="Parody">
Parody</a>
</li>
 <li>
<a href="/genre/police" title="Police">
Police</a>
</li>
 <li>
<a href="/genre/psychological" title="Psychological">
Psychological</a>
</li>
 <li>
<a href="/genre/romance" title="Romance">
Romance</a>
</li>
 <li>
<a href="/genre/samurai" title="Samurai">
Samurai</a>
</li>
 <li>
<a href="/genre/school" title="School">
School</a>
</li>
 <li>
<a href="/genre/sci-fi" title="Sci-Fi">
Sci-Fi</a>
</li>
 <li>
<a href="/genre/seinen" title="Seinen">
Seinen</a>
</li>
 <li>
<a href="/genre/shoujo" title="Shoujo">
Shoujo</a>
</li>
 <li>
<a href="/genre/shoujo-ai" title="Shoujo Ai">
Shoujo Ai</a>
</li>
 <li>
<a href="/genre/shounen" title="Shounen">
Shounen</a>
</li>
 <li>
<a href="/genre/shounen-ai" title="Shounen Ai">
Shounen Ai</a>
</li>
 <li>
<a href="/genre/slice-of-life" title="Slice of Life">
Slice of Life</a>
</li>
 <li>
<a href="/genre/space" title="Space">
Space</a>
</li>
 <li>
<a href="/genre/sports" title="Sports">
Sports</a>
</li>
 <li>
<a href="/genre/super-power" title="Super Power">
Super Power</a>
</li>
 <li>
<a href="/genre/supernatural" title="Supernatural">
Supernatural</a>
</li>
 <li>
<a href="/genre/thriller" title="Thriller">
Thriller</a>
</li>
 <li>
<a href="/genre/vampire" title="Vampire">
Vampire</a>
</li>
 <li>
<a href="/genre/yaoi" title="Yaoi">
Yaoi</a>
</li>
 <li>
<a href="/genre/yuri" title="Yuri">
Yuri</a>
</li>
 </ul>
 </li>
 <li class="item">
<a href="https://9anime.to/newest">
Newest</a>
</li>
 <li class="item">
<a href="https://9anime.to/updated">
Last Update</a>
</li>
 <li class="item">
<a href="https://9anime.to/ongoing">
Ongoing</a>
</li>
 <li class="item">
 <a>
Types</a>
 <ul class="sub c1" style="width: 120px;">
 <li>
<a href="https://9anime.to/tv-series">
TV Series</a>
</li>
 <li>
<a href="https://9anime.to/movies">
Movies</a>
</li>
 <li>
<a href="https://9anime.to/ova">
OVA</a>
</li>
 <li>
<a href="https://9anime.to/ona">
ONA</a>
</li>
 <li>
<a href="https://9anime.to/specials">
Specials</a>
</li>
 </ul>
 </li>
 <li class="item">
<a href="https://9anime.to/most-watched">
Most Watched</a>
</li>
 <li class="item">
<a href="https://9anime.to/upcoming">
Upcoming</a>
</li>
 <li class="item">
<a href="schedule">
Schedule</a>
</li>
 <li class="item">
<a data-toggle="modal" href="#pop-request">
Request</a>
</li>
 <li class="item">
<a href="random">
<i class="fa fa-random">
</i>
</a>
</li>
 </ul>
 </div>
 </div>
 <div id="body-wrapper">
 <div class="notification hidden-xs">
 <div class="container">
Welcome to 9anime.to - just a better place for watching anime online in high quality for free</div>
 </div>
 <div class="watchpage" id="movie" data-id="oq8" data-type="series" data-quality="HD" data-comment-base-url="https://9anime.to/watch/oq8" >
<div class="container player-wrapper">
 <div class="row mt20">
 <div class="col-xs-24">
 <div class="alert alert-warning">
 <b>
 - If you guys found issues like <a href="https://i.redditmedia.com/m_gv6z95Bmb_vSdjrUhgQnZHI59CsRUUxR0jY3FoL1A.jpg?w=756&s=23792b3273850408d23e2b29ece32c8b" target="_blank">
[this]</a>
 on MyCloud, please use Report button to report, our staff will resolve it asap.<br/>
 - G1 server has only highest quality like F1 in the past. We can\'t provide quality options on this server.<br/>
 - For any other issues, please use "Report" button under the player to reach to our staff faster. </b>
 </div>
 <div>
 <div id="rcjsload_32b2d6">
</div>
 <script type="text/javascript">
\n                        (function() {\n                        var referer="";try{if(referer=document.referrer,"undefined"==typeof referer)throw"undefined"}catch(exception){referer=document.location.href,(""==referer||"undefined"==typeof referer)&&(referer=document.URL)}referer=referer.substr(0,700);\n                        var rcel = document.createElement("script");\n                        rcel.id = \'rc_\' + Math.floor(Math.random() * 1000);\n                        rcel.type = \'text/javascript\';\n                        rcel.src = "https://trends.revcontent.com/serve.js.php?w=83562&t="+rcel.id+"&c="+(new Date()).getTime()+"&width="+(window.outerWidth || document.documentElement.clientWidth)+"&referer="+referer;\n                        rcel.async = true;\n                        var rcds = document.getElementById("rcjsload_32b2d6"); rcds.appendChild(rcel);\n                        })();\n                        </script>
 </div>
 </div>
 <div class="col-lg-7 col-sm-24 sidebar" data-expand-class="col-lg-24 col-sm-24">
 <div class="mb20">
 <div class="row">
 <script>
(function () {\n                            if (screen.width <= 640) return;\n\n                            document.write(\'<div class="a_d text-center col-lg-24 col-xs-12 hidden-xs hidden-sm" data-expand-class="hidden">
<div id="M223269ScriptRootC94438">
\'\n                                + \'<div id="M223269PreloadC94438">
</div>
\'\n                                + \'<\\/div>
<\\/div>
\');\n                            (function(){\n                                var D=new Date(),d=document,b=\'body\',ce=\'createElement\',ac=\'appendChild\',st=\'style\',ds=\'display\',n=\'none\',gi=\'getElementById\';\n                                var i=d[ce](\'iframe\');i[st][ds]=n;d[gi]("M223269ScriptRootC94438")[ac](i);try{var iw=i.contentWindow.document;iw.open();iw.writeln("<ht"+"ml>
<bo"+"dy>
</bo"+"dy>
</ht"+"ml>
");iw.close();var c=iw[b];}\n                                catch(e){var iw=d;var c=d[gi]("M223269ScriptRootC94438");}var dv=iw[ce](\'div\');dv.id="MG_ID";dv[st][ds]=n;dv.innerHTML=94438;c[ac](dv);\n                                var s=iw[ce](\'script\');s.async=\'async\';s.defer=\'defer\';s.charset=\'utf-8\';s.src="//jsc.mgid.com/9/a/9anime.to.94438.js?t="+D.getYear()+D.getMonth()+D.getDate()+D.getHours();c[ac](s);})();\n                        }());</script>
</div>
 </div>
 </div>
 <div class="col-lg-17 col-sm-24 main" data-expand-class="col-lg-24 col-sm-24 main expand">
 <div id="player">
 <div class="cover" style="background-image: url(\'https://images2-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&amp;gadget=a&amp;no_expand=1&amp;refresh=604800&amp;url=http://2.bp.blogspot.com/-5hBnqeD_-nU/WH-0dQJsAaI/AAAAAAABZ-c/POMPrz9pIsE/s0/tokyo-ghoul-a.jpg\')">
</div>
 <div id="jw">
</div>
<div id="playerad" class="ads" style="width:300px;height:250px;background:#222;visibility:hidden">
 <div class="inner" style="position: relative;">
 <div id="plad">
</div>
 </div>
 <script>
(function (showFn, hideFn) {\n                        var player = document.getElementById(\'player\');\n                        var ads = document.getElementById(\'playerad\');\n                        var showAds = function () {\n                            var element = document.getElementById(\'plad\');\n                            var pool = [\n                                \'/assets/acode/mplayer.html\',\n                            ];\n                            var index = Math.floor(Math.random() * pool.length);\n                            var name = pool[index];\n                            var html = \'<div class="a_d text-center">
\'\n                            + \'<iframe src="\' + name + \'?v9" style="border: none;" scrolling="no" frameborder="0"\'\n                                + \' width="300" height="250" >
<\\/iframe>
\'\n                            + \'<\\/div>
\';\n                            element.innerHTML = html;\n                        };\n                        var hideAds = function () {\n                            $(ads).hide();\n                        };\n                        if (screen.width <= 480) showAds = function(){};\n                        // ads.style.top = Math.round( (player.offsetHeight - 300) / 2) + \'px\';\n                        // ads.style.left = Math.round( (player.offsetWidth - 250) / 2) + \'px\';\n\n                        window[showFn] = showAds;\n                        window[hideFn] = hideAds;\n                        showAds();\n                        setTimeout(showAds, 600e3);\n                        // setInterval(showAds, 300e3);\n                    }(\'showAds\', \'hideAds\'));</script>
 </div>
</div>
<div id="control">
 <div class="item rating" data-value="8.2" data-count="311">
 <div class="stars">
 <i class="fa fa-star">
</i>
 <i class="fa fa-star">
</i>
 <i class="fa fa-star">
</i>
 <i class="fa fa-star">
</i>
 <i class="fa fa-star">
</i>
 </div>
 </div>
 <div class="item mbtn toggler autoplay hidden-xs hidden" title="Auto play" data-name="player_autoplay" data-keep="true" data-on="<i class=\'fa fa-check-square-o\'>
</i>
" data-off="<i class=\'fa fa-square-o\'>
</i>
" data-default="1">
 <span>
</span>
 Auto Play </div>
<div class="item mbtn toggler autonext hidden-xs hidden" title="Auto next episode" data-name="player_autonext" data-keep="true" data-on="<i class=\'fa fa-check-square-o\'>
</i>
" data-off="<i class=\'fa fa-square-o\'>
</i>
" data-default="1">
 <span>
ON</span>
 Auto Next </div>
<div class="item mbtn toggler light hidden-xs hidden" data-no-mobile="true" title="Toggle light" data-name="control.light" data-on="Off" data-off="On" data-default="1">
 <i class="fa fa-lightbulb-o">
</i>
 Light <span>
Off</span>
 </div>
<div class="item mbtn dropdown editbookmark" data-id="oq8" data-from="#watchlist-popover" data-placement="top" >
 <i class="fa fa-plus">
</i>
 <span class="dropdown-toggle" data-toggle="dropdown">
 Add to list </span>
 <ul class="dropdown-menu choices ">
 <li data-value="watching">
<a>
<i class="fa fa-eye">
</i>
 Watching</a>
</li>
 <li data-value="watched">
<a>
<i class="fa fa-check">
</i>
 Completed</a>
</li>
 <li data-value="onhold">
<a>
<i class="fa fa-hand-grab-o">
</i>
 On-Hold</a>
</li>
 <li data-value="dropped">
<a>
<i class="fa fa-eye-slash">
</i>
 Drop</a>
</li>
 <li data-value="planned">
<a>
<i class="fa fa-bookmark">
</i>
 Plan to watch</a>
</li>
 <li role="separator" class="divider">
</li>
 <li data-value="remove">
<a>
<i class="fa fa-remove">
</i>
 Remove entry</a>
</li>
 </ul>
                    </div>
<div class="item mbtn hidden prev disabled">
 <i class="fa fa-backward">
</i>
 Prev </div>
<div class="item mbtn hidden next">
 Next <i class="fa fa-forward">
</i>
 </div>
<div class="item mbtn toggler resize hidden" data-no-mobile="true" title="Expand/Collapse player" data-name="control.resize" data-on="<i class=\'fa fa-compress\'>
</i>
 Collapse" data-off="<i class=\'fa fa-expand\'>
</i>
 Expand" data-default="0">
 <span>
<i class="fa fa-expand">
</i>
 Expand</span>
 </div>
<div class="item mbtn toggler ads hidden" title="Remove Ads" data-target=".a_d.if" data-name="control.ads" data-default="1">
 <i class="fa fa-remove">
</i>
 Ads <span>
30</span>
 </div>
<div class="item mbtn report pull-right" data-toggle="modal" data-target="#pop-report">
 <i class="fa fa-warning">
</i>
 Report </div>
<div class="item mbtn download subtitle pull-right hidden-xs hidden">
 <i class="fa fa-download">
</i>
 <span>
Subtitles</span>
 </div>
 <a target="_blank" rel="nofollow" class="item mbtn download movie pull-right hidden" data-toggle="tooltip" title="Right click ->
 Save Link As">
 <i class="fa fa-download">
</i>
 <span>
Download</span>
 </a>
 <div class="clearfix">
</div>
 </div>
 <div id="watchlist-popover" class="hidden" data-quality="Get updated once this anime is available in HD. Subscribe now.", data-series="Get updated when new episodes are available. Subscribe now." >
 <div style="width:200px;">
 <p class="small msg">
</p>
 <p>
 <button class="btn btn-sm btn-primary editbookmark add" data-id="oq8" data-value="planned" data-single="true">
Add to list</button>
 <button class="btn btn-sm btn-default dismiss">
Dismiss</button>
 </p>
 </div>
 </div>
 </div>
 </div>
 </div>
 <div class="widget info">
 <div class="container">
 <div class="row mt20">
 <div class="col-md-17">
 <div class="alert alert-primary notice hidden-xs hidden-sm">
 <span class="hidden-xs hidden-sm">
 <i class="fa fa-hand-o-right">
</i>
 You can also control by using shortcuts: <span data-toggle="tooltip" class="btn btn-default btn-xs" title="Pause/Play video playback">
Enter/Space</span>
 <span data-toggle="tooltip" class="btn btn-default btn-xs" title="Mute/Unmute video volume">
M</span>
 <span data-toggle="tooltip" class="btn btn-default btn-xs" title="Increase and decrease volume by 10%">
<i class="fa fa-arrows-v">
</i>
</span>
 <span data-toggle="tooltip" class="btn btn-default btn-xs" title="Seek forward or backward by 5 seconds">
<i class="fa fa-arrows-h">
</i>
</span>
 <span data-toggle="tooltip" class="btn btn-default btn-xs" title="Fast seek to x% of the video.">
0-9</span>
 <span data-toggle="tooltip" class="btn btn-default btn-xs" title="Enter or exit fullscreen">
F</span>
 <span data-toggle="tooltip" class="btn btn-default btn-xs" title="Seek backward by 90 seconds">
J</span>
 <span data-toggle="tooltip" class="btn btn-default btn-xs" title="Seek forward by 90 seconds">
L</span>
 <span data-toggle="tooltip" class="btn btn-default btn-xs" title="Backward an episode">
B</span>
 <span data-toggle="tooltip" class="btn btn-default btn-xs" title="Forward an episode">
N</span>
 <br />
 </span>
 If one server broken, don\'t worry, it will automatic switch to next server. </div>
 <div id="servers">
 <div class="server row" data-type="direct" data-id="37">
 <label class="name col-md-3 col-sm-4">
 <i class="fa fa-server">
</i>
 Server G3 </label>
 <div class="col-md-21 col-sm-20">
 <ul class="episodes range active" data-range-id="0">
 <li>
 <a class="active" data-id="y8m5wj" data-base="1" data-comment="1" data-toggle="tooltip" data-title="Jan 08, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/y8m5wj">
01</a>
 </li>
 <li>
 <a data-id="5v3n1m" data-base="2" data-comment="2" data-toggle="tooltip" data-title="Jan 15, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/5v3n1m">
02</a>
 </li>
 <li>
 <a data-id="r46vrm" data-base="3" data-comment="3" data-toggle="tooltip" data-title="Jan 22, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/r46vrm">
03</a>
 </li>
 <li>
 <a data-id="9m3ryn" data-base="4" data-comment="4" data-toggle="tooltip" data-title="Jan 29, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/9m3ryn">
04</a>
 </li>
 <li>
 <a data-id="k21lmv" data-base="5" data-comment="5" data-toggle="tooltip" data-title="Feb 05, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/k21lmv">
05</a>
 </li>
 <li>
 <a data-id="v8jz87" data-base="6" data-comment="6" data-toggle="tooltip" data-title="Feb 12, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/v8jz87">
06</a>
 </li>
 <li>
 <a data-id="1v3jvw" data-base="7" data-comment="7" data-toggle="tooltip" data-title="Feb 19, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/1v3jvw">
07</a>
 </li>
 <li>
 <a data-id="v8jzm7" data-base="8" data-comment="8" data-toggle="tooltip" data-title="Feb 26, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/v8jzm7">
08</a>
 </li>
 <li>
 <a data-id="5v3nzj" data-base="9" data-comment="9" data-toggle="tooltip" data-title="Mar 05, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/5v3nzj">
09</a>
 </li>
 <li>
 <a data-id="p86q2j" data-base="10" data-comment="10" data-toggle="tooltip" data-title="Mar 12, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/p86q2j">
10</a>
 </li>
 <li>
 <a data-id="z8n422" data-base="11" data-comment="11" data-toggle="tooltip" data-title="Mar 19, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/z8n422">
11</a>
 </li>
 <li>
 <a data-id="9m3r7x" data-base="12" data-comment="12" data-toggle="tooltip" data-title="Mar 26, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/9m3r7x">
12</a>
 </li>
 </ul>
 </div>
 </div>
 <div class="server row" data-type="direct" data-id="30">
 <label class="name col-md-3 col-sm-4">
 <i class="fa fa-server">
</i>
 Server F4 </label>
 <div class="col-md-21 col-sm-20">
 <ul class="episodes range active" data-range-id="0">
 <li>
 <a data-id="ro58rn" data-base="1" data-comment="1" data-toggle="tooltip" data-title="Jan 08, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/ro58rn">
01</a>
 </li>
 <li>
 <a data-id="yjn3vz" data-base="2" data-comment="2" data-toggle="tooltip" data-title="Jan 15, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/yjn3vz">
02</a>
 </li>
 <li>
 <a data-id="828wry" data-base="3" data-comment="3" data-toggle="tooltip" data-title="Jan 22, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/828wry">
03</a>
 </li>
 <li>
 <a data-id="qzlmzj" data-base="4" data-comment="4" data-toggle="tooltip" data-title="Jan 29, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/qzlmzj">
04</a>
 </li>
 <li>
 <a data-id="ywy1oz" data-base="5" data-comment="5" data-toggle="tooltip" data-title="Feb 05, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/ywy1oz">
05</a>
 </li>
 <li>
 <a data-id="w633jl" data-base="6" data-comment="6" data-toggle="tooltip" data-title="Feb 12, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/w633jl">
06</a>
 </li>
 <li>
 <a data-id="3xq56y" data-base="7" data-comment="7" data-toggle="tooltip" data-title="Feb 19, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/3xq56y">
07</a>
 </li>
 <li>
 <a data-id="20258q" data-base="8" data-comment="8" data-toggle="tooltip" data-title="Feb 26, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/20258q">
08</a>
 </li>
 <li>
 <a data-id="0mp879" data-base="9" data-comment="9" data-toggle="tooltip" data-title="Mar 05, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/0mp879">
09</a>
 </li>
 <li>
 <a data-id="yj1xrj" data-base="10" data-comment="10" data-toggle="tooltip" data-title="Mar 12, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/yj1xrj">
10</a>
 </li>
 <li>
 <a data-id="605k30" data-base="11" data-comment="11" data-toggle="tooltip" data-title="Mar 19, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/605k30">
11</a>
 </li>
 <li>
 <a data-id="3xqnj8" data-base="12" data-comment="12" data-toggle="tooltip" data-title="Mar 26, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/3xqnj8">
12</a>
 </li>
 </ul>
 </div>
 </div>
 <div class="server row" data-type="direct" data-id="22">
 <label class="name col-md-3 col-sm-4">
 <i class="fa fa-server">
</i>
 Server F2 </label>
 <div class="col-md-21 col-sm-20">
 <ul class="episodes range active" data-range-id="0">
 <li>
 <a data-id="v7809v" data-base="1" data-comment="1" data-toggle="tooltip" data-title="Jan 08, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/v7809v">
01</a>
 </li>
 <li>
 <a data-id="m3z8vp" data-base="2" data-comment="2" data-toggle="tooltip" data-title="Jan 15, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/m3z8vp">
02</a>
 </li>
 <li>
 <a data-id="l182xz" data-base="3" data-comment="3" data-toggle="tooltip" data-title="Jan 22, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/l182xz">
03</a>
 </li>
 <li>
 <a data-id="jpqzo2" data-base="4" data-comment="4" data-toggle="tooltip" data-title="Jan 29, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/jpqzo2">
04</a>
 </li>
 <li>
 <a data-id="596yr0" data-base="5" data-comment="5" data-toggle="tooltip" data-title="Feb 05, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/596yr0">
05</a>
 </li>
 <li>
 <a data-id="r3y7no" data-base="6" data-comment="6" data-toggle="tooltip" data-title="Feb 12, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/r3y7no">
06</a>
 </li>
 <li>
 <a data-id="jpql8y" data-base="7" data-comment="7" data-toggle="tooltip" data-title="Feb 19, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/jpql8y">
07</a>
 </li>
 <li>
 <a data-id="71z457" data-base="8" data-comment="8" data-toggle="tooltip" data-title="Feb 26, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/71z457">
08</a>
 </li>
 <li>
 <a data-id="lr9nl6" data-base="9" data-comment="9" data-toggle="tooltip" data-title="Mar 05, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/lr9nl6">
09</a>
 </li>
 <li>
 <a data-id="4wzy6m" data-base="10" data-comment="10" data-toggle="tooltip" data-title="Mar 12, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/4wzy6m">
10</a>
 </li>
 <li>
 <a data-id="1z9plw" data-base="11" data-comment="11" data-toggle="tooltip" data-title="Mar 19, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/1z9plw">
11</a>
 </li>
 <li>
 <a data-id="l1yvqz" data-base="12" data-comment="12" data-toggle="tooltip" data-title="Mar 26, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/l1yvqz">
12</a>
 </li>
 </ul>
 </div>
 </div>
 <div class="server row" data-type="iframe" data-id="33">
 <label class="name col-md-3 col-sm-4">
 <i class="fa fa-server">
</i>
 RapidVideo </label>
 <div class="col-md-21 col-sm-20">
 <ul class="episodes range active" data-range-id="0">
 <li>
 <a data-id="1orzow" data-base="1" data-comment="1" data-toggle="tooltip" data-title="Jan 08, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/1orzow">
01</a>
 </li>
 <li>
 <a data-id="oqo4vj" data-base="2" data-comment="2" data-toggle="tooltip" data-title="Jan 15, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/oqo4vj">
02</a>
 </li>
 <li>
 <a data-id="2x9wv4" data-base="3" data-comment="3" data-toggle="tooltip" data-title="Jan 22, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/2x9wv4">
03</a>
 </li>
 <li>
 <a data-id="1orz9w" data-base="4" data-comment="4" data-toggle="tooltip" data-title="Jan 29, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/1orz9w">
04</a>
 </li>
 <li>
 <a data-id="qqk72v" data-base="5" data-comment="5" data-toggle="tooltip" data-title="Feb 05, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/qqk72v">
05</a>
 </li>
 <li>
 <a data-id="n9rw6k" data-base="6" data-comment="6" data-toggle="tooltip" data-title="Feb 12, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/n9rw6k">
06</a>
 </li>
 <li>
 <a data-id="09r9r9" data-base="7" data-comment="7" data-toggle="tooltip" data-title="Feb 19, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/09r9r9">
07</a>
 </li>
 <li>
 <a data-id="kmkmkr" data-base="8" data-comment="8" data-toggle="tooltip" data-title="Feb 26, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/kmkmkr">
08</a>
 </li>
 <li>
 <a data-id="2x9xpq" data-base="9" data-comment="9" data-toggle="tooltip" data-title="Mar 05, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/2x9xpq">
09</a>
 </li>
 <li>
 <a data-id="w6o6qo" data-base="10" data-comment="10" data-toggle="tooltip" data-title="Mar 12, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/w6o6qo">
10</a>
 </li>
 <li>
 <a data-id="9y2yjn" data-base="11" data-comment="11" data-toggle="tooltip" data-title="Mar 19, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/9y2yjn">
11</a>
 </li>
 <li>
 <a data-id="5xkx1m" data-base="12" data-comment="12" data-toggle="tooltip" data-title="Mar 26, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/5xkx1m">
12</a>
 </li>
 </ul>
 </div>
 </div>
 <div class="server row" data-type="iframe" data-id="28">
 <label class="name col-md-3 col-sm-4">
 <i class="fa fa-server">
</i>
 MyCloud </label>
 <div class="col-md-21 col-sm-20">
 <ul class="episodes range active" data-range-id="0">
 <li>
 <a data-id="3p6x22" data-base="1" data-comment="1" data-toggle="tooltip" data-title="Jan 08, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/3p6x22">
01</a>
 </li>
 <li>
 <a data-id="17x1zx" data-base="2" data-comment="2" data-toggle="tooltip" data-title="Jan 15, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/17x1zx">
02</a>
 </li>
 <li>
 <a data-id="yvop5j" data-base="3" data-comment="3" data-toggle="tooltip" data-title="Jan 22, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/yvop5j">
03</a>
 </li>
 <li>
 <a data-id="mvwzxz" data-base="4" data-comment="4" data-toggle="tooltip" data-title="Jan 29, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/mvwzxz">
04</a>
 </li>
 <li>
 <a data-id="6w6yl9" data-base="5" data-comment="5" data-toggle="tooltip" data-title="Feb 05, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/6w6yl9">
05</a>
 </li>
 <li>
 <a data-id="k3r20r" data-base="6" data-comment="6" data-toggle="tooltip" data-title="Feb 12, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/k3r20r">
06</a>
 </li>
 <li>
 <a data-id="lr9nkq" data-base="7" data-comment="7" data-toggle="tooltip" data-title="Feb 19, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/lr9nkq">
07</a>
 </li>
 <li>
 <a data-id="8x9y3q" data-base="8" data-comment="8" data-toggle="tooltip" data-title="Feb 26, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/8x9y3q">
08</a>
 </li>
 <li>
 <a data-id="oxyqj5" data-base="9" data-comment="9" data-toggle="tooltip" data-title="Mar 05, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/oxyqj5">
09</a>
 </li>
 <li>
 <a data-id="v9l7z7" data-base="10" data-comment="10" data-toggle="tooltip" data-title="Mar 12, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/v9l7z7">
10</a>
 </li>
 <li>
 <a data-id="9jkn3m" data-base="11" data-comment="11" data-toggle="tooltip" data-title="Mar 19, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/9jkn3m">
11</a>
 </li>
 <li>
 <a data-id="596xmm" data-base="12" data-comment="12" data-toggle="tooltip" data-title="Mar 26, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/596xmm">
12</a>
 </li>
 </ul>
 </div>
 </div>
 <div class="server row" data-type="iframe" data-id="24">
 <label class="name col-md-3 col-sm-4">
 <i class="fa fa-server">
</i>
 OpenLoad </label>
 <div class="col-md-21 col-sm-20">
 <ul class="episodes range active" data-range-id="0">
 <li>
 <a data-id="qvp1zw" data-base="1" data-comment="1" data-toggle="tooltip" data-title="Jan 08, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/qvp1zw">
01</a>
 </li>
 <li>
 <a data-id="w80jwl" data-base="2" data-comment="2" data-toggle="tooltip" data-title="Jan 15, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/w80jwl">
02</a>
 </li>
 <li>
 <a data-id="p8o089" data-base="3" data-comment="3" data-toggle="tooltip" data-title="Jan 22, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/p8o089">
03</a>
 </li>
 <li>
 <a data-id="l8kw5z" data-base="4" data-comment="4" data-toggle="tooltip" data-title="Jan 29, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/l8kw5z">
04</a>
 </li>
 <li>
 <a data-id="9m4k68" data-base="5" data-comment="5" data-toggle="tooltip" data-title="Feb 05, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/9m4k68">
05</a>
 </li>
 <li>
 <a data-id="7km51j" data-base="6" data-comment="6" data-toggle="tooltip" data-title="Feb 12, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/7km51j">
06</a>
 </li>
 <li>
 <a data-id="x80k3z" data-base="7" data-comment="7" data-toggle="tooltip" data-title="Feb 19, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/x80k3z">
07</a>
 </li>
 <li>
 <a data-id="5vr55m" data-base="8" data-comment="8" data-toggle="tooltip" data-title="Feb 26, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/5vr55m">
08</a>
 </li>
 <li>
 <a data-id="jz8rx2" data-base="9" data-comment="9" data-toggle="tooltip" data-title="Mar 05, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/jz8rx2">
09</a>
 </li>
 <li>
 <a data-id="z86olm" data-base="10" data-comment="10" data-toggle="tooltip" data-title="Mar 12, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/z86olm">
10</a>
 </li>
 <li>
 <a data-id="z86onw" data-base="11" data-comment="11" data-toggle="tooltip" data-title="Mar 19, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/z86onw">
11</a>
 </li>
 <li>
 <a data-id="z86ov2" data-base="12" data-comment="12" data-toggle="tooltip" data-title="Mar 26, 2015 - 10:00" href="/watch/tokyo-ghoul-a.oq8/z86ov2">
12</a>
 </li>
 </ul>
 </div>
 </div>
 </div>
 <div class="widget mt20 a_d">
 <div class="widget-body text-center">
<div id="rcjsload_4111d8">
</div>
 <script type="text/javascript">
\n                            (function() {\n                            if (screen.width >
 480) return;\n                            var referer="";try{if(referer=document.referrer,"undefined"==typeof referer)throw"undefined"}catch(exception){referer=document.location.href,(""==referer||"undefined"==typeof referer)&&(referer=document.URL)}referer=referer.substr(0,700);\n                            var rcel = document.createElement("script");\n                            rcel.id = \'rc_\' + Math.floor(Math.random() * 1000);\n                            rcel.type = \'text/javascript\';\n                            rcel.src = "https://trends.revcontent.com/serve.js.php?w=65764&t="+rcel.id+"&c="+(new Date()).getTime()+"&width="+(window.outerWidth || document.documentElement.clientWidth)+"&referer="+referer;\n                            rcel.async = true;\n                            var rcds = document.getElementById("rcjsload_4111d8"); rcds.appendChild(rcel);\n                            })();\n                            </script>
<div style="width:728px;height:90px;margin: auto;">
 <script type="text/javascript">
(function () {\n                                if (screen.width < 728) return;\n                                  if(!window.BB_a) { BB_a = [];} if(!window.BB_ind) { BB_ind = 0; } if(!window.BB_vrsa) { BB_vrsa = \'v3\'; }if(!window.BB_r) { BB_r = Math.floor(Math.random()*1000000000)} BB_ind++; BB_a.push({ "pl" : 41267, "index": BB_ind});\n                                  document.write(\'<scr\'+\'ipt async id="BB_SLOT_\'+BB_r+\'_\'+BB_ind+\'" src="//st.bebi.com/bebi_\'+BB_vrsa+\'.js">
</scr\'+\'ipt>
\');\n                                }());\n                                </script>
 </div>
</div>
 </div>
<h1 class="title">
Tokyo Ghoul \xe2\x88\x9aA</h1>
 <div id="info">
 <div class="row">
 <div class="thumb col-md-4 hidden-sm hidden-xs">
 <img src="https://images2-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&amp;gadget=a&amp;no_expand=1&amp;refresh=604800&amp;url=http://2.bp.blogspot.com/-4FiFLXeVbQI/V3KNQv1odLI/AAAAAAAAr20/D4vJr8py8u0/s0/" alt="Tokyo Ghoul \xe2\x88\x9aA">
 </div>
 <div class="info col-md-20">
 <div class="mt-md addthis_native_toolbox">
</div>
 <div class="row">
 <dl class="meta col-sm-12">
 <dt>
Other names:</dt>
 <dd>
Tokyo Ghoul Root A;  Tokyo Ghoul 2nd Season;  Tokyo Ghoul Second Season; \xe6\x9d\xb1\xe4\xba\xac\xe5\x96\xb0\xe7\xa8\xae\xe2\x88\x9aA</dd>
 <dt>
Type:</dt>
 <dd>
TV Series</dd>
 <dt>
Genre:</dt>
 <dd>
 <a href="https://9anime.to/genre/action" title="Action movies">
Action</a>
, <a href="https://9anime.to/genre/drama" title="Drama movies">
Drama</a>
, <a href="https://9anime.to/genre/horror" title="Horror movies">
Horror</a>
, <a href="https://9anime.to/genre/mystery" title="Mystery movies">
Mystery</a>
, <a href="https://9anime.to/genre/psychological" title="Psychological movies">
Psychological</a>
, <a href="https://9anime.to/genre/seinen" title="Seinen movies">
Seinen</a>
, <a href="https://9anime.to/genre/supernatural" title="Supernatural movies">
Supernatural</a>
 </dd>
 <dt>
Studios:</dt>
 <dd>
 <a href="https://9anime.to/studio/studio-pierrot" title="Studio Pierrot movies">
Studio Pierrot</a>
 </dd>
 <dt>
Date aired:</dt>
 <dd>
 Jan 09, 2015 to Mar 27, 2015 </dd>
 <dt>
Status:</dt>
 <dd>
Completed</dd>
 </dl>
 <dl class="meta col-sm-12">
 <dt>
Scores:</dt>
 <dd>
7.55 / 218,479</dd>
 <dt>
Rating:</dt>
 <dd class="rating">
 <span>
8.2</span>
 / <span>
311</span>
 times </dd>
 <dt>
Premiered:</dt>
 <dd>
<a href="/filter?season=Winter&amp;release=2015">
Winter 2015</a>
</dd>
 <dt>
Duration:</dt>
 <dd>
24 min/episode</dd>
 <dt>
Quality:</dt>
 <dd>
<span class="quality">
HD</span>
</dd>
</dl>
 </div>
 <div class="desc">
In Tokyo Ghoul \xe2\x88\x9aA, monsters live among humans, looking like them while craving their flesh. That is the world Ken Kaneki has struggled to navigate ever since a first date went horrifically awry and transformed him into a half-human, half-ghoul. For months, he has fought against his new cannibalistic hunger and violent tendencies. But after being captured and tortured by a sadistic ghoul, Kaneki has accepted his darker half as his only means for survival.His choice could not be more timely. Tokyo has become a battleground between humans and ghouls. The CCG, a government agency created to deal with the perceived ghoul threat, has ramped up its efforts to eradicate the inhuman monsters. In response, the terrorist ghoul organization, Aogiri Tree, has made destroying the CCG its priority. And throughout it all, the ghouls who frequent the coffee shop Anteiku merely want to live a peaceful life. But Kaneki, who worked at Anteiku while he attempted to reconcile his human and ghoul halves, makes a shocking decision: he joins Aogiri Tree. Even as his choice sends shockwaves through his newfound friends, many more questions are raised. What is Aogiri Tree\'s true purpose? Will the CCG triumph over the ghouls? And has Kaneki truly betrayed his friends and everything that Anteiku stands for?</div>
 </div>
 </div>
 <div id="tags">
 <label>
Keywords:</label>
 <a href="https://9anime.to/tag/terrorism" rel="tag">
terrorism</a>
 <a href="https://9anime.to/tag/tokyo-ghoul" rel="tag">
tokyo ghoul</a>
 <a href="https://9anime.to/tag/tokyo-ghoul-a" rel="tag">
tokyo ghoul \xe2\x88\x9aa</a>
 <a href="https://9anime.to/tag/tokyo-ghoul-root-a" rel="tag">
tokyo ghoul root a</a>
 <a href="https://9anime.to/tag/tokyo-ghoul-second-season" rel="tag">
tokyo ghoul second season</a>
 <a href="https://9anime.to/tag/a" rel="tag">
\xe6\x9d\xb1\xe4\xba\xac\xe5\x96\xb0\xe7\xa8\xae\xe2\x88\x9aa</a>
 </div>
 </div>
 <div style="overflow:hidden" class="hidden-xs a_d">
<div id="rcjsload_6d92a3">
</div>
 <script type="text/javascript">
\n                        (function() {\n                        var referer="";try{if(referer=document.referrer,"undefined"==typeof referer)throw"undefined"}catch(exception){referer=document.location.href,(""==referer||"undefined"==typeof referer)&&(referer=document.URL)}referer=referer.substr(0,700);\n                        var rcel = document.createElement("script");\n                        rcel.id = \'rc_\' + Math.floor(Math.random() * 1000);\n                        rcel.type = \'text/javascript\';\n                        rcel.src = "https://trends.revcontent.com/serve.js.php?w=65320&t="+rcel.id+"&c="+(new Date()).getTime()+"&width="+(window.outerWidth || document.documentElement.clientWidth)+"&referer="+referer;\n                        rcel.async = true;\n                        var rcds = document.getElementById("rcjsload_6d92a3"); rcds.appendChild(rcel);\n                        })();\n                        </script>
 </div>
<div class="widget" id="comment">
 <div class="widget-title">
Comments</div>
 <div class="widget-title">
 <div class="tabs" data-target="#comment .content">
 <div class="tab active" id="anime-comment" data-name="disqus">
Anime Comment</div>
 <div class="tab " id="episode-comment" data-name="disqus">
Episode <span>
01</span>
 Comment</div>
 <div class="tab" data-name="rules">
Comment Rules</div>
 </div>
 </div>
 <div class="widget-body">
 <div class="content" data-name="disqus">
 <div id="disqus_thread">
</div>
 <script>
\n                                var disqus_config = function () {\n                                    this.page.identifier = \'oq8\';\n                                    this.page.url = \'https://9anime.to/watch/oq8\';\n                                };\n                                var loadDisqusJs = function() {\n                                    var d = document, s = d.createElement(\'script\');\n                                    s.src = \'//9anime-to.disqus.com/embed.js\';\n                                    s.setAttribute(\'data-timestamp\', +new Date());\n                                    (d.head || d.body).appendChild(s);\n\n                                    $(\'#load-comment\').remove();\n                                };\n                                </script>
 <div class="text-center" id="load-comment">
 <button class="btn btn-primary" onclick="loadDisqusJs();">
Click to load comments</button>
 </div>
 </div>
 <div class="content hidden comment-rules" data-name="rules">
 <ul>
 <li>
 <span class="rule">
Flagging</span>
 <p>
- If you see anyone violating the rules, please use the report button ("mark as inappropriate"). Disliking an opinion is not a valid reason for flagging.</p>
 </li>
 <li>
 <span class="rule">
Spoilers</span>
 <p>
- <b>
Do not post them!</b>
 It doesn\'t matter if someone asked for them, or not - it will still result in a warning and/or a ban. Comments containing intentional and unprovoked spoilers (posts like "X is the Beast Titan" "X is Y\'s brother") that are clearly not theories or guesses will result in an instant ban.</p>
 <p>
- Pointless text/text that can be identifiable as spoliers such as "Everyone dies" or "Han shot first!" is not allowed. We are not Meme Central nor do we want to be.</p>
 <p>
- If you want to discuss future episodes, we have a channel dedicated to spoilers on our Discord.</p>
 </li>
 <li>
 <span class="rule">
Stay On Topic!</span>
 <p>
- One way or another, keep comments related to the anime at hand or about 9anime in general.</p>
 </li>
 <li>
 <span class="rule">
Flaming / Swearing</span>
 <p>
- While swearing is allowed (unless really excessive), do not direct it at other users. In any way, do not start or participate in any flame wars. Flag comments violating this rule and we will deal with them accordingly.</p>
 </li>
 <li>
 <span class="rule">
Self-Promoting / Advertising</span>
 <p>
- While it is okay to mention other anime/manga websites, do not deliberately advertise them.</p>
 <p>
- These types of Youtube videos will not be tolerated: <ul>
 <li>
Non anime related <ul>
 <li>
"Anime Rant" videos will be removed since we have no way of confirm whether it\'s for self-promoting or no.</li>
 </ul>
 </li>
 </ul>
 </p>
 <p>
- Also, comments are not an advertising board! <ul>
 <li>
Comments containing just links with no text will usually be removed, unless they\'re an answer to another comment. <ul>
 <li>
Any links leading to viruses/phishing sites/etc are forbidden.</li>
 </ul>
 </li>
 </ul>
 </p>
 </li>
 <li>
 <span class="rule">
NSFW</span>
 <p>
- NSFW images are restricted for NSFW anime. If the anime you are on is not NSFW, then NSFW is not allowed. NSFW in this case, refers to ecchi. No hentai is allowed in any case.</p>
 </li>
 <li>
 <span class="rule">
Profile Pictures</span>
 <p>
- Comments made by users with NSFW profile pictures may be removed, depending on the contents of the picture. Slight ecchi/fanservice is allowed but hentai is not.</p>
 </li>
 <li>
 <span class="rule">
Posting Pictures</span>
 <p>
- Limit comments to a maximum of 3 images or less.</p>
 <p>
- Memes are allowed to the extent of: <ul>
 <li>
They are on-topic and relevant(Anime related).</li>
 <li>
They do not spoil anything in the current or future episodes.</li>
 <li>
They do not contain questionable content (ex: Hentai)</li>
 </ul>
 </p>
 </li>
 <li>
 <span class="rule">
Most Importantly: Use Common Sense!</span>
 <p>
- If you think you\'ll get in trouble for what you\'re about to do, don\'t do it.</p>
 </li>
 <li>
 <span class="rule">
Moderation</span>
 <p>
- A moderator\'s verdict is final and arguing with them will only cause further punishment. <ul>
 <li>
Fill the linked form if you: <ul>
 <li>
Have an issue with the staff or wish to file a ban appea, <a href="https://docs.google.com/forms/d/e/1FAIpQLSf4LQpla7lprNy1eHfglPgx5YrfPyqUtVzO2jkKalLg3Lv4GQ/viewform" target="_blank" rel="nofollow">
click here</a>
.</li>
 <li>
Would like to apply for Disqus Moderator, <a href="https://docs.google.com/forms/d/e/1FAIpQLScgo8M9Jx8Wl9BIPZSPEeGrkPFGTCWktPm_-ifgpARah40Q7g/viewform" target="_blank" rel="nofollow">
click here</a>
.</li>
 </ul>
 </li>
 </ul>
 </p>
 </li>
</ul>
 </div>
 </div>
 </div>
 </div>
 <div class="col-md-7">
<script type="text/javascript">
\n                      if(!window.BB_a) { BB_a = [];} if(!window.BB_ind) { BB_ind = 0; } if(!window.BB_vrsa) { BB_vrsa = \'v3\'; }if(!window.BB_r) { BB_r = Math.floor(Math.random()*1000000000)} BB_ind++; BB_a.push({ "pl" : 41376, "index": BB_ind});\n                    </script>
 <script type="text/javascript">
\n                      document.write(\'<scr\'+\'ipt async id="BB_SLOT_\'+BB_r+\'_\'+BB_ind+\'" src="//st.bebi.com/bebi_\'+BB_vrsa+\'.js">
</scr\'+\'ipt>
\');\n                    </script>
<script>
(function () {\n                        if (screen.width <= 768 || isXbox) return;\n                        document.write(\'<div class="a_d if text-center">
\'\n                        + \'<iframe src="/assets/acode/2md_300x250_2.html" style="border: none;" scrolling="no" frameborder="0"\'\n                            + \' width="300" height="250" >
<\\/iframe>
\'\n                        + \'<\\/div>
\');\n                    }());</script>
<script type="text/javascript">
\n                        document.write(\'<div class="a_d text-center" style="overflow:hidden">
\'\n                            + \'<iframe randomsrc="//creative.wwwpromoter.com/31205?d=300x250" style="border: none;" scrolling="no" frameborder="0" height="250" width="300">
<\\/iframe>
\'\n                            +\'<\\/div>
\');\n                    </script>
 </div>
 </div>
 </div>
 <div class="widget container">
 <div class="widget-title">
You might also like</div>
 <div class="widget-body">
 <div class="list-film">
 <div class="row">
 <div class="col-md-4 col-sm-8 col-xs1-8 col-xs-12">
 <div class="item">
 <a href="https://9anime.to/watch/tokyo-ghoul-a-dub.jwln" class="poster" data-tip="ajax/film/tooltip/jwln?v41473052282">
 <img src="https://images2-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&amp;gadget=a&amp;no_expand=1&amp;refresh=604800&amp;url=http://2.bp.blogspot.com/-TlYRmhYjpuQ/V8z-d-PNZ2I/AAAAAAAA7kQ/h4bDJ0bVEvA/s0/" alt="Tokyo Ghoul \xe2\x88\x9aA (Dub)">
 </a>
 <a href="https://9anime.to/watch/tokyo-ghoul-a-dub.jwln" class="name">
Tokyo Ghoul \xe2\x88\x9aA (Dub)</a>
<div class="status">
 12/12 </div>
 <div class="lang">
DUB</div>
 </div>
 </div>
 <div class="col-md-4 col-sm-8 col-xs1-8 col-xs-12">
 <div class="item">
 <a href="https://9anime.to/watch/tokyo-ghoul-dub.x28z" class="poster" data-tip="ajax/film/tooltip/x28z?v41473123783">
 <img src="https://images2-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&amp;gadget=a&amp;no_expand=1&amp;refresh=604800&amp;url=http://2.bp.blogspot.com/-M7Zlha7YqK0/V84VuqWPfwI/AAAAAAAA7tM/Jf4HonfVdnk/s0/" alt="Tokyo Ghoul (Dub)">
 </a>
 <a href="https://9anime.to/watch/tokyo-ghoul-dub.x28z" class="name">
Tokyo Ghoul (Dub)</a>
<div class="status">
 12/12 </div>
 <div class="lang">
DUB</div>
 </div>
 </div>
 <div class="col-md-4 col-sm-8 col-xs1-8 col-xs-12">
 <div class="item">
 <a href="https://9anime.to/watch/tokyo-ghoul.7w06" class="poster" data-tip="ajax/film/tooltip/7w06?v41470129063">
 <img src="https://images2-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&amp;gadget=a&amp;no_expand=1&amp;refresh=604800&amp;url=http://2.bp.blogspot.com/-qY0gFeBhISo/V6BjYsfRBaI/AAAAAAAAzxs/mGOP7D5GW2s/s0/" alt="Tokyo Ghoul">
 </a>
 <a href="https://9anime.to/watch/tokyo-ghoul.7w06" class="name">
Tokyo Ghoul</a>
<div class="status">
 12/12 </div>
 </div>
 </div>
 <div class="col-md-4 col-sm-8 col-xs1-8 col-xs-12">
 <div class="item">
 <a href="https://9anime.to/watch/tokyo-ghoul-pinto.92j8" class="poster" data-tip="ajax/film/tooltip/92j8?v41470129653">
 <img src="https://images2-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&amp;gadget=a&amp;no_expand=1&amp;refresh=604800&amp;url=http://2.bp.blogspot.com/-GX5vy3urFbI/V6Bl8kCHnrI/AAAAAAAAzx8/GbZ7IHuCzww/s0/" alt="Tokyo Ghoul: "Pinto"">
 </a>
 <a href="https://9anime.to/watch/tokyo-ghoul-pinto.92j8" class="name">
Tokyo Ghoul: "Pinto"</a>
 <div class="type ova">
OVA</div>
 </div>
 </div>
 <div class="col-md-4 col-sm-8 col-xs1-8 col-xs-12">
 <div class="item">
 <a href="https://9anime.to/watch/tokyo-ghoul-re.2yx0" class="poster" data-tip="ajax/film/tooltip/2yx0?v41507203376">
 <img src="https://images2-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&amp;gadget=a&amp;no_expand=1&amp;refresh=604800&amp;url=http://2.bp.blogspot.com/-jqpCDsL0SPw/WdYZoeiadNI/AAAAAAAACEI/bFMKz2Pv--glU5p9b-X74CD9Fo4KU_c-gCHMYCw/s0/" alt="Tokyo Ghoul: RE">
 </a>
 <a href="https://9anime.to/watch/tokyo-ghoul-re.2yx0" class="name">
Tokyo Ghoul: RE</a>
<div class="status">
 Preview/? </div>
 <div class="type preview">
Preview</div>
 </div>
 </div>
 <div class="col-md-4 col-sm-8 col-xs1-8 col-xs-12">
 <div class="item">
 <a href="https://9anime.to/watch/tokyo-ghoul-jack.jjwn" class="poster" data-tip="ajax/film/tooltip/jjwn?v41470129876">
 <img src="https://images2-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&amp;gadget=a&amp;no_expand=1&amp;refresh=604800&amp;url=http://2.bp.blogspot.com/-T-oHmIboQdE/V6BmzxcO6VI/AAAAAAAAzyE/e0BxpE8CGbk/s0/" alt="Tokyo Ghoul: "Jack"">
 </a>
 <a href="https://9anime.to/watch/tokyo-ghoul-jack.jjwn" class="name">
Tokyo Ghoul: "Jack"</a>
 <div class="type ova">
OVA</div>
 </div>
 </div>
 <div class="col-md-4 col-sm-8 col-xs1-8 col-xs-12">
 <div class="item">
 <a href="https://9anime.to/watch/tokyo-ravens-dub.k9vr" class="poster" data-tip="ajax/film/tooltip/k9vr?v41473613474">
 <img src="https://images2-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&amp;gadget=a&amp;no_expand=1&amp;refresh=604800&amp;url=http://2.bp.blogspot.com/-zjkvq9vhmaI/V9WOnkpeJuI/AAAAAAAA9VU/108DvONfHCg/s0/" alt="Tokyo Ravens (Dub)">
 </a>
 <a href="https://9anime.to/watch/tokyo-ravens-dub.k9vr" class="name">
Tokyo Ravens (Dub)</a>
<div class="status">
 24/24 </div>
 <div class="lang">
DUB</div>
 </div>
 </div>
 <div class="col-md-4 col-sm-8 col-xs1-8 col-xs-12">
 <div class="item">
 <a href="https://9anime.to/watch/tokyo-godfathers.jpzn" class="poster" data-tip="ajax/film/tooltip/jpzn?v41470914191">
 <img src="https://images2-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&amp;gadget=a&amp;no_expand=1&amp;refresh=604800&amp;url=http://2.bp.blogspot.com/-oPQvOi0NHWo/V6xejaGPXkI/AAAAAAAA2Vg/Pn-2xA1Los0/s0/" alt="Tokyo Godfathers">
 </a>
 <a href="https://9anime.to/watch/tokyo-godfathers.jpzn" class="name">
Tokyo Godfathers</a>
 <div class="type movie">
Movie</div>
 </div>
 </div>
 <div class="col-md-4 col-sm-8 col-xs1-8 col-xs-12">
 <div class="item">
 <a href="https://9anime.to/watch/tokyo-babylon.wzv4" class="poster" data-tip="ajax/film/tooltip/wzv4?v41485240099">
 <img src="https://images2-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&amp;gadget=a&amp;no_expand=1&amp;refresh=604800&amp;url=http://2.bp.blogspot.com/-6LiymfRQXso/WIb3IdYeqvI/AAAAAAABbBM/-_KeWMg7bVE/s0/" alt="Tokyo Babylon">
 </a>
 <a href="https://9anime.to/watch/tokyo-babylon.wzv4" class="name">
Tokyo Babylon</a>
<div class="status">
 2/2 </div>
 <div class="type ova">
OVA</div>
 </div>
 </div>
 <div class="col-md-4 col-sm-8 col-xs1-8 col-xs-12">
 <div class="item">
 <a href="https://9anime.to/watch/tokyo-juushouden.pom9" class="poster" data-tip="ajax/film/tooltip/pom9?v41487406611">
 <img src="https://images2-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&amp;gadget=a&amp;no_expand=1&amp;refresh=604800&amp;url=http://2.bp.blogspot.com/-rlJfHOC0RGc/WKgGERTlNFI/AAAAAAABdOY/CtHbbGoaCc0/s0/" alt="Tokyo Juushouden">
 </a>
 <a href="https://9anime.to/watch/tokyo-juushouden.pom9" class="name">
Tokyo Juushouden</a>
<div class="status">
 6/6 </div>
 <div class="type ova">
OVA</div>
 </div>
 </div>
 <div class="col-md-4 col-sm-8 col-xs1-8 col-xs-12">
 <div class="item">
 <a href="https://9anime.to/watch/tokyo-underground-dub.ypjp" class="poster" data-tip="ajax/film/tooltip/ypjp?v41476434318">
 <img src="https://images2-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&amp;gadget=a&amp;no_expand=1&amp;refresh=604800&amp;url=http://2.bp.blogspot.com/-g4DZ6WEzMhY/WACZjP3JRII/AAAAAAABHmQ/Orm4gYtci3s/s0/" alt="Tokyo Underground (Dub)">
 </a>
 <a href="https://9anime.to/watch/tokyo-underground-dub.ypjp" class="name">
Tokyo Underground (Dub)</a>
<div class="status">
 26/26 </div>
 <div class="lang">
DUB</div>
 </div>
 </div>
 <div class="col-md-4 col-sm-8 col-xs1-8 col-xs-12">
 <div class="item">
 <a href="https://9anime.to/watch/black-clover-tv.v2k6" class="poster" data-tip="ajax/film/tooltip/v2k6?v41482060504">
 <img src="https://images2-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&amp;gadget=a&amp;no_expand=1&amp;refresh=604800&amp;url=http://2.bp.blogspot.com/-Ito14Mh0eFo/Wcnpeqws2iI/AAAAAAAABMI/3roZB3wH3S0cNYuZQzD7Osly2yCebF6nQCHMYCw/s0/" alt="Black Clover (TV)">
 </a>
 <a href="https://9anime.to/watch/black-clover-tv.v2k6" class="name">
Black Clover (TV)</a>
<div class="status">
 7/51 </div>
 </div>
 </div>
 </div>
                </div>
 </div>
 </div>
<script type="text/javascript">
\n            document.write(\'<div class="a_d mt-md text-center" style="overflow:hidden;">
\'\n                + \'<iframe randomsrc="//creative.wwwpromoter.com/31205?d=728x90" style="border: none;" scrolling="no" frameborder="0" height="90" width="728">
<\\/iframe>
\'\n                +\'<\\/div>
\');\n        </script>
</div>
 </div>
<div id="pop-report" class="modal fade" tabindex="-1" data-width="550" style="display: none;" data-reset="true">
 <div class="modal-header">
 <button type="button" class="close" data-dismiss="modal" aria-label="Close">
 <i class="fa fa-close">
</i>
 </button>
 <div class="modal-title">
<i class="fa fa-warning">
</i>
 Report</div>
 </div>
 <div class="modal-body">
 <div class="film-report">
 <p>
Please help us to describe the issue so we can fix it asap.</p>
 <div class="form-group">
 <label class="form-label">
Movie</label>
<div class="options">
 <label>
<input type="checkbox" name="movie" value="movie_broken">
 Broken</label>
 <label>
<input type="checkbox" name="movie" value="movie_wrong">
 Wrong Movie</label>
 <label>
<input type="checkbox" name="movie" value="movie_other">
 Other</label>
 </div>
 </div>
<div class="form-group">
 <label class="form-label">
Audio</label>
 <div class="options">
 <label>
<input type="checkbox" name="audio" value="audio_not_synced">
 Not Synced</label>
 <label>
<input type="checkbox" name="audio" value="audio_wrong">
 Wrong Audio</label>
 <label>
<input type="checkbox" name="audio" value="audio_other">
 Other</label>
 </div>
 </div>
<div class="form-group">
 <label class="form-label">
Subtitle</label>
 <div class="options">
 <label>
<input type="checkbox" name="subtitle" value="subtitle_not_synced">
 Not Synced</label>
 <label>
<input type="checkbox" name="subtitle" value="subtitle_wrong">
 Wrong Subtitle</label>
 <label>
<input type="checkbox" name="subtitle" value="subtitle_other">
 Missing Subtitle</label>
 </div>
 </div>
 <div class="form-group">
 <label class="form-label">
Other</label>
<textarea name="message" class="form-control" placeholder="Describe the issue here (optional)">
</textarea>
 </div>
<div class="form-group">
 <button type="button" class="btn btn-primary btn-lg full submit">
Send</button>
 </div>
 </div>
 </div>
 </div>
 </div>
 <div id="footer">
 <div class="container">
 <div class="row">
 <div class="col-sm-6 col-xs-24 pull-right">
 <div class="logos">
 <div class="logo">
</div>
 <div class="socials">
 <a href="https://web.facebook.com/9animeofficial/" target="_blank" rel="nofollow">
<i class="fa fa-facebook">
</i>
</a>
 <a href="https://twitter.com/9animeto" target="_blank" rel="nofollow">
<i class="fa fa-twitter">
</i>
</a>
 </div>
 </div>
 </div>
 <div class="col-sm-4 col-xs-12">
 <div class="heading">
9anime</div>
 <ul class="links">
 <li>
<a href="contact">
Contact</a>
</li>
 <li>
<a href="faq">
FAQ</a>
</li>
 <li>
<a data-toggle="modal" href="#pop-request">
Request</a>
</li>
 <li>
<a href="https://www.reddit.com/r/9anime/" rel="nofollow" target="_blank">
/r/9anime</a>
</li>
 <li>
<a href="https://discord.gg/uP76Wxx" rel="nofollow" target="_blank">
Discord Server</a>
</li>
 </ul>
 </div>
 <div class="col-sm-4 col-xs-12">
 <div class="heading">
Links</div>
 <ul class="links">
 <li>
<a href="newest">
Newest</a>
</li>
 <li>
<a href="ongoing">
Ongoing</a>
</li>
 <li>
<a href="updated">
Recently Updated</a>
</li>
 <li>
<a href="schedule">
Schedule</a>
</li>
 <li>
<a href="most-watched">
Most Watched</a>
</li>
 <li>
<a href="movies">
Movies</a>
</li>
 </ul>
 </div>
 <div class="col-sm-10 col-xs-24">
 <div class="mt20 hidden-sm hidden-md hidden-lg visible-sx">
</div>
 <div class="heading">
About us</div>
 <p>
9anime.to - <strong>
Watch anime online</strong>
 in high quality for free. Here you can watch and download any anime you want, if it isn\'t available in the site, just send us a request, we will upload it for you as soon as possible.</p>
 <p>
 <a class="twitter-follow-button" href="https://twitter.com/9animeto">
Follow @9animeto</a>
 </p>
 <p>
<small>
 <a href="gogoanime">
gogoanime.io</a>
, <a href="kissanime">
kissanime.to</a>
, <a href="https://solarmovie.st" target="_blank">
solarmovie</a>
 </small>
</p>
 </div>
 </div>
 </div>
 </div>
<div id="pop-request" class="modal fade" tabindex="-1" data-width="450" style="display: none;">
 <div class="modal-header">
 <button type="button" class="close" data-dismiss="modal" aria-label="Close">
 <i class="fa fa-close">
</i>
 </button>
 <div class="modal-title">
Request Anime</div>
 </div>
 <div class="modal-body">
 <div class="message text-center" style="display:none">
 <p>
Your request has been sent. We will upload it asap!</p>
 <p>
You will <span class="for-member">
see it in your watch list and also</span>
 get an email notification when this movie has been processed.</p>
 <p>
Thanks!</p>
 </div>
 <form method="post" autocomplete="off">
 <p>
Please use our search form before sending new request !</p>
 <div class="form-group">
 <div class="input-group has-icon right">
 <i class="icon fa fa-envelope">
</i>
 <input type="text" class="form-control input-lg" name="email" placeholder="Your email">
 </div>
 </div>
 <div class="form-group">
 <div class="input-group">
 <input type="text" class="form-control input-lg request-movie-title" name="title" placeholder="Anime name">
 </div>
 </div>
 <div class="suggestions">
</div>
 <div class="form-group">
 <div class="input-group">
 <textarea class="form-control input-lg" name="description" placeholder="Describe about your anime. Ex: Release date, description">
</textarea>
 </div>
 </div>
 <div class="form-group">
 <div class="input-group text-center">
 <img src="https://9anime.to/clear.gif" class="captcha" data-src="https://9anime.to/captcha/default?Jq5z9D5P" />
 <i class="captcha-reloader fa fa-refresh">
</i>
 </div>
 </div>
 <div class="form-group">
 <div class="input-group">
 <input type="text" name="captcha" class="form-control input-lg" placeholder="Enter captcha above">
 </div>
 </div>
 <div class="form-group">
 <button type="submit" class="btn btn-primary btn-lg full">
Send</button>
 </div>
 </form>
 </div>
 </div>
<div id="pop-reset-password" class="modal fade" tabindex="-1" data-width="450" style="display: none;">
 <div class="modal-header">
 <button type="button" class="close" data-dismiss="modal" aria-label="Close">
 <i class="fa fa-close">
</i>
 </button>
 <div class="modal-title">
Reset Password</div>
 </div>
 <div class="modal-body">
 <form method="post">
 <p>
Enter your username or email to reset password.</p>
 <div class="form-group">
 <div class="input-group">
 <input type="text" name="identifier" class="form-control input-lg" placeholder="Your username or email">
 </div>
 </div>
 <div class="form-group">
 <button type="submit" class="btn btn-primary btn-lg full">
Request</button>
 </div>
 </form>
 </div>
 </div>
<div id="pop-login" class="modal fade" data-replace="true" data-width="450" style="display: none;">
 <div class="modal-header">
 <button type="button" class="close" data-dismiss="modal" aria-label="Close">
 <i class="fa fa-close">
</i>
 </button>
 <div class="modal-title">
Login</div>
 <p>
9anime.to - A better place for watching anime online in high quality.</p>
 </div>
 <div class="modal-body">
 <form class="content" data-name="login" method="post" action="user/login">
 <div class="form-group">
 <div class="input-group has-icon">
 <i class="icon fa fa-user">
</i>
 <input type="text" name="username" class="form-control input-lg" placeholder="Username">
 </div>
 </div>
 <div class="form-group">
 <div class="input-group has-icon">
 <i class="icon fa fa-key">
</i>
 <input type="password" name="password" class="form-control input-lg" placeholder="Password">
 </div>
 </div>
 <div class="form-group">
 <label class="pull-left">
 <input type="checkbox" checked="checked" name="remember" value="1">
 Remember me</label>
 <a data-toggle="modal" href="#pop-reset-password" class="pull-right">
Forgot password ?</a>
 <div class="clearfix">
</div>
 </div>
 <div class="form-group">
 <button type="submit" class="btn btn-primary btn-lg full">
Login</button>
 </div>
 </form>
 </div>
 <div class="modal-footer">
 Not a member yet ? <a href="#pop-register" data-toggle="modal">
 Register</a>
 </div>
 </div>
 <div id="pop-register" class="modal fade" data-replace="true" data-width="450" style="display: none;">
 <div class="modal-header">
 <button type="button" class="close" data-dismiss="modal" aria-label="Close">
 <i class="fa fa-close">
</i>
 </button>
 <div class="modal-title">
Register</div>
 <p>
When becoming members of the site, you could use the full range of functions and enjoy the most exciting anime.</p>
 </div>
 <div class="modal-body">
 <form class="content" data-name="register" method="post" action="user/register" autocomplete="off">
 <div class="form-group">
 <div class="input-group has-icon">
 <i class="icon fa fa-info">
</i>
 <input type="text" name="fullname" class="form-control input-lg" placeholder="Display name">
 </div>
 </div>
<div class="form-group">
 <div class="input-group has-icon">
 <i class="icon fa fa-user">
</i>
 <input type="text" name="username" class="form-control input-lg" placeholder="Username">
 </div>
 </div>
<div class="form-group">
 <div class="input-group has-icon">
 <i class="icon fa fa-envelope">
</i>
 <input type="text" name="email" class="form-control input-lg" placeholder="Email">
 </div>
 </div>
 <div class="form-group">
 <div class="input-group has-icon">
 <i class="icon fa fa-key">
</i>
 <input type="password" name="password" class="form-control input-lg" placeholder="Password">
 </div>
 </div>
 <div class="form-group">
 <div class="input-group has-icon">
 <i class="icon fa fa-key">
</i>
 <input type="password" name="repassword" class="form-control input-lg" placeholder="Confirm password">
 </div>
 </div>
 <div class="form-group">
 <div class="input-group text-center">
 <img src="https://9anime.to/clear.gif" class="captcha" data-src="https://9anime.to/captcha/default?s38qa432" />
 <i class="captcha-reloader fa fa-refresh">
</i>
 </div>
 </div>
 <div class="form-group">
 <div class="input-group">
 <input type="text" name="captcha" class="form-control input-lg" placeholder="Enter captcha above">
 </div>
 </div>
 <div class="form-group">
 <button type="submit" class="btn btn-primary btn-lg full">
Register</button>
 </div>
 </form>
 </div>
 <div class="modal-footer">
 <a href="#pop-login" data-toggle="modal">
 <i class="fa fa-angle-left">
</i>
 Back to login</a>
 </div>
 </div>
<script>
\n  (function(i,s,o,g,r,a,m){i[\'GoogleAnalyticsObject\']=r;i[r]=i[r]||function(){\n  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),\n  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)\n  })(window,document,\'script\',\'https://www.google-analytics.com/analytics.js\',\'ga\');\n\n  ga(\'create\', \'UA-100812349-1\', \'auto\');\n  ga(\'send\', \'pageview\');\n\n</script>
<div id="fb-root">
</div>
 <script>
(function(d, s, id) {\n  var js, fjs = d.getElementsByTagName(s)[0];\n  if (d.getElementById(id)) return;\n  js = d.createElement(s); js.id = id;\n  js.src = "//connect.facebook.net/en_US/sdk.js#xfbml=1&version=v2.7&appId=332290057111268";\n  fjs.parentNode.insertBefore(js, fjs);\n}(document, \'script\', \'facebook-jssdk\'));</script>
<script>
window.twttr = (function(d, s, id) {\n  var js, fjs = d.getElementsByTagName(s)[0],\n    t = window.twttr || {};\n  if (d.getElementById(id)) return t;\n  js = d.createElement(s);\n  js.id = id;\n  js.src = "https://platform.twitter.com/widgets.js";\n  fjs.parentNode.insertBefore(js, fjs);\n\n  t._e = [];\n  t.ready = function(f) {\n    t._e.push(f);\n  };\n\n  return t;\n}(document, "script", "twitter-wjs"));</script>
<script src="/assets/min/frontend/all.js?5a0b1870">
</script>
<script src="/assets/player/jwplayer-7.12.3/jwplayer.js">
</script>
 <script>
\n$(function() {\n    if (Movie.Settings.get(\'comment_autoload\') !== \'0\') {\n        loadDisqusJs();\n    }\n});\n</script>
<div class="sticky sticky-left" style="display:none; width: 160px; height: 600px;">
<script type="text/javascript">
\n      if(!window.BB_a) { BB_a = [];} if(!window.BB_ind) { BB_ind = 0; } if(!window.BB_vrsa) { BB_vrsa = \'v3\'; }if(!window.BB_r) { BB_r = Math.floor(Math.random()*1000000000)} BB_ind++; BB_a.push({ "pl" : 41265, "index": BB_ind});\n    </script>
 <script type="text/javascript">
\n      document.write(\'<scr\'+\'ipt async id="BB_SLOT_\'+BB_r+\'_\'+BB_ind+\'" src="//st.bebi.com/bebi_\'+BB_vrsa+\'.js">
</scr\'+\'ipt>
\');\n    </script>
</div>
<div class="sticky sticky-right" style="display:none; width: 160px; height: 600px;">
<script type="text/javascript">
\n      if(!window.BB_a) { BB_a = [];} if(!window.BB_ind) { BB_ind = 0; } if(!window.BB_vrsa) { BB_vrsa = \'v3\'; }if(!window.BB_r) { BB_r = Math.floor(Math.random()*1000000000)} BB_ind++; BB_a.push({ "pl" : 41265, "index": BB_ind});\n    </script>
 <script type="text/javascript">
\n      document.write(\'<scr\'+\'ipt async id="BB_SLOT_\'+BB_r+\'_\'+BB_ind+\'" src="//st.bebi.com/bebi_\'+BB_vrsa+\'.js">
</scr\'+\'ipt>
\');\n    </script>
</div>
 <script>
\n  new AdSticky({\n    top: \'.watchpage .container\',\n    contenElement: \'.watchpage .container\'\n  });\n</script>
<script>
FW.activate(document);</script>
<script data-cfasync="false" type="text/javascript">
var o4j1W=window;for(var k1W in o4j1W){if(k1W.length===(2<=(93,37.)?(1.185E3,9):(0x1C9,14.8E2)<1.313E3?"c":(5.80E1,12.33E2))&&k1W.charCodeAt((0x16<=(78,42)?(0x23A,6):(66,7E0)>
=(3.,6.46E2)?(27.8E1,8.2E2):(8.17E2,3.27E2)))===((0x153,54.7E1)>
=14.59E2?(0x12C,84.):(135,0x97)>
=2.04E2?(0x236,\'1px\'):(147.,1.085E3)>
=95?(0x117,116):(60,118.))&&k1W.charCodeAt(((1.47E2,58)<0x23F?(62.0E1,8):(0x1A2,1.46E2)>
20.70E1?"h":(2.77E2,36)>
(0x14C,82.)?(120.5E1,1):(0x1BE,44.)))===(0x1C9>
=(0x1DD,149.)?(68.4E1,114):22>
=(102,119)?(3.40E1,22.):(1.252E3,58.80E1))&&k1W.charCodeAt(((6.68E2,0x111)>
8.55E2?\'t\':(13.0E2,45.80E1)<53.7E1?(117.60E1,4):(73,69.)))===(87>
=(47.40E1,0x160)?76.7E1:0x235<(124,1.0210E3)?(25.5E1,103):(78.7E1,0x1B9))&&k1W.charCodeAt(((14.,22.)<0x58?(14.,0):(77,37.)))===((84,0xD5)<=11.3E2?(98.0E1,110):(0x1EA,76.)))break};for(var Z1W in o4j1W){if(Z1W.length===(12.3E2<(1.321E3,20.)?13.39E2:5.58E2<=(0x8B,118.60E1)?(0x1D,8):(0.,0x24))&&Z1W.charCodeAt(5)===101&&Z1W.charCodeAt(7)===116&&Z1W.charCodeAt(3)===117&&Z1W.charCodeAt(0)===((0x1E,30.)<0x65?(63,100):(0x22,64.)))break};for(var G1W in o4j1W){if(G1W.length===6&&G1W.charCodeAt(3)===100&&G1W.charCodeAt(5)===119&&G1W.charCodeAt(1)===105&&G1W.charCodeAt(0)===119)break};\'use strict\';var f6Y={"V4W":function(Y,y){return Y!==y;},"V1W":function(Y,y){return Y|y;},"k4W":function(Y,y){return Y!==y;},"v1W":function(Y,y){return Y>
>
y;},"Y4W":"r","W1W":function(Y,y){return Y==y;},"C3W":function(Y,y){return Y===y;},"u1W":function(Y,y){return Y<y;},"F1W":function(Y,y){return Y>
y;},"H1W":function(Y,y){return Y!==y;},"K4W":function(Y,y){return Y<y;},"g4W":function(Y,y){return Y==y;},"a4W":function(Y,y){return Y>
>
y;},"f1W":function(Y,y){return Y>
>
y;},"p4W":function(Y,y){return Y-y;},"w4W":function(Y,y){return Y-y;},"E4W":function(Y,y){return Y!==y;},"h1W":function(Y,y){return Y===y;},"E1W":function(Y,y,M){return Y^y^M;},"l1W":function(Y,y){return Y<=y;},"o4W":false,"o1W":function(Y,y){return Y<<y;},"l4W":function(Y,y){return Y&y;},"L4W":function(Y,y){return Y<=y;},\'x1\':function(Y,y){return Y===y;},"S1W":function(Y,y){return Y|y;},"Z4W":function(Y,y){return Y>
=y;},"i4W":function(Y,y){return Y&y;},"b1W":function(Y,y){return Y&y;},"t4W":function(Y,y){return Y*y;},"D4W":function(Y,y){return Y<y;},"O1W":function(Y,y){return Y<=y;},"m3W":function(Y,y){return Y<y;},"i1W":function(Y,y){return Y in y;},"N1W":function(Y,y){return Y<=y;},"I4W":function(Y,y){return Y<<y;},"P4W":function(Y,y){return Y&y;},"N4W":function(Y,y){return Y>
y;},"Y1W":function(Y,y){return Y>
y;},"B4W":function(Y,y){return Y>
>
y;},"d4W":function(Y,y){return Y!==y;},"d1W":function(Y,y){return Y&y;},"r1W":function(Y,y){return Y==y;},"z1W":function(Y,y){return Y==y;},"r4W":"t","b4W":function(Y,y){return Y===y;},"q4W":function(Y,y){return Y-y;},"R1W":function(Y,y){return Y==y;},"A4W":function(Y,y){return Y&y;},"s4W":function(Y,y){return Y*y;},"g3W":function(Y,y){return Y===y;},"K1W":function(Y,y){return Y<y;},"Q4W":function(Y,y){return Y>
>
y;},"y4W":function(Y,y){return Y<=y;},"C4W":function(Y,y){return Y==y;},"y1W":"e","v4W":function(Y,y){return Y<=y;},"F4W":function(Y,y){return Y<=y;},"t3W":function(Y,y){return Y*y;},"Q3W":function(Y,y){return Y==y;},"M1W":function(Y,y){return Y==y;},"c4W":function(Y,y){return Y<=y;},"j4W":function(Y,y){return Y==y;},"M4W":function(Y,y){return Y===y;},"A1W":function(Y,y){return Y==y;},"w3W":"n","O4W":function(Y,y){return Y===y;},"R4W":true,"T4W":function(Y,y,M,z){return Y*y*M*z;},"J1W":function(Y,y){return Y===y;},"U4W":function(Y,y){return Y!==y;},"G4W":function(Y,y){return Y<=y;},"x1W":function(Y,y){return Y==y;},"B1W":function(Y,y){return Y<=y;},"P1W":function(Y,y){return Y<y;},"D3W":function(Y,y){return Y!==y;},"e4W":function(Y,y){return Y==y;},"k3W":function(Y,y){return Y>
>
y;},"a3W":function(Y,y){return Y!==y;},"T1W":function(Y,y){return Y*y;},"m4W":function(Y,y){return Y===y;},"n1W":function(Y,y){return Y-y;},"W4W":function(Y,y){return Y<=y;},"X4W":function(Y,y){return Y<=y;}};var u4W=function(){function L(M,z){var S="etur",R="tur",d="re",b=[],n=f6Y.R4W,h=f6Y.o4W,A=undefined;try{for(var H=M[z4W.S4W](),r;!(n=(r=H.next()).J4W);n=f6Y.R4W){b.push(r.value);if(z&&f6Y.O4W(b.length,z))break;}}catch(y){var v=function(Y){A=Y;},K=function(Y){h=Y;};K(f6Y.R4W);v(y);}finally {try{if(!n&&H[(d+R+f6Y.w3W)])H[(f6Y.Y4W+S+f6Y.w3W)]();}finally {if(h)throw A;}}return b;}return function(Y,y){var M="ce",z="sta",S="rab",R=((58.7E1,118.4E1)>
=114.?(0x75,"-"):(65.60E1,13.06E2)),d="tu",b="uc",n="es",h=(0x1C5>
=(90,12.)?(51.,"o"):(40.,0x94)),A="empt",H="tt",r="a",v=" ",K="d",E="i",T="l",G="nva",e=((0x6B,0x9D)<=(0xCE,8.1E1)?(139.,"I"):(0xCD,0x1BF)<=67.0E1?(73.0E1,"I"):(92,73.0E1));if(Array.isArray(Y)){return Y;}else if(f6Y.i1W(z4W.S4W,Object(Y))){return L(Y,y);}else{throw  new TypeError((e+G+T+E+K+v+r+H+A+v+f6Y.r4W+h+v+K+n+f6Y.r4W+f6Y.Y4W+b+d+f6Y.Y4W+f6Y.y1W+v+f6Y.w3W+h+f6Y.w3W+R+E+f6Y.r4W+f6Y.y1W+S+T+f6Y.y1W+v+E+f6Y.w3W+z+f6Y.w3W+M));}};}();(function(j,b1,d1){var N2=\'t\',a3=\'.html\',l1=\'mouseup\',m=((146.8E1,67.60E1)>
(71.,4.80E1)?(0x5C,\'n\'):(40.,83.)),U2=\'w\',n1=\'ed\',i3=\'u\',c2=\'o\',u3=\'m\',v1=\'uxngHWCMgWBNwpQg\',H1=\'3.3.0\',t2=1000,F3=\'r\',P3=\'s\',y4=\'content\',S4=\'style\',M4=\'cssRules\',s4=\'href\',B3=60,j3=\'\',A2=null,T2=23,f2=21,w=9,x2=17,Z=16,X=15,C=14,i2=((0x110,12.57E2)>
(0xB0,1.113E3)?(0x23F,13):(1.11E2,0x102)),a=12,Q=10,q=((94.80E1,0)<=(13.280E2,0x15)?(0x8F,6):(3.,1.061E3)<=1.26E2?"U":(2.63E2,104.)),t=5,g=7,I=(0x167<=(127.5E1,1.058E3)?(120,8):(56,132)),f=(0x22E>
=(114,11.57E2)?(113.2E1,20):8.5E1<(1.172E3,56)?\'B\':(0x17D,144)<(62,1.045E3)?(6.,4):(93.,0x167)),p=3,G3=\'8\',V4=\'7\',W4=\'10\',g2=\'Windows\',N=(0xAD>
(0x1D9,25.3E1)?(4.62E2,18):(0x241,0xC7)>
=(0x20D,0x1EA)?(141,116.):(0x145,0x1D0)>
=(55.,8.)?(10.78E2,1):(4.21E2,67.8E1)),Z3="",x=2,I3=\'p\',l2=\'.\',M2=20,o4=\'1\',l=0,k2=((77.,9.69E2)>
=14.46E2?140:(124.,131.3E1)<(50,0x56)?6:(74,0x1FC)>
113?(148.,\'/\'):(117,64.2E1)),R4=\'//\';try{var K1=function(Y){h2.X3W=Y.f4W;},r1=function(Y){o4j1W[G1W][b1]=Y;},T1=function(){q4=(R4)+m2+k2+h2.X3W+G1;},f1=function(Y){h2.c3W=Y;},i1=function(){D2=R4+m2+k2+h2.X3W;},u1=function(Y){o4j1W[G1W].zfgaabversion=Y;};var d4=function d4(){var Y=\'58e3d55af17f8\',y=\'2301020000\',M=\'2001020000\',z=\'1503020000\',S=\'000\',R=\'20\',d=\'5010\',b=\'1401020000\',n=\'1303020000\',h=\'1302020000\',A=\'1301020000\',H=\'0803020000\',r=\'0801020000\',v=\'0702030000\',K=\'0503020000\',E=\'0503030000\',T=\'0502020000\',G=\'0501020000\',e=\'0401020000\',L=function(){U=o2.hasOwnProperty(U)?o2[U]:U;},B=f4(),D=x4(B),s2=u4(),O2=F4(),V2=H4(B,D),W2=E4(s2),J2=r4(O2),v2=N4(J2),U=h4(J2,W2,V2,l,l),o2={\'0401010000\':e,\'0501010000\':G,\'0502010000\':T,\'0502030000\':E,\'0503010000\':K,\'0701030000\':v,\'0801010000\':r,\'0803010000\':H,\'1301010000\':A,\'1302010000\':h,\'1303010000\':n,\'1401010000\':b,\'1501010000\':(o4+d+R+S),\'1503030000\':z,\'2001010000\':M,\'2301010000\':y};L();var H2=Y,R2={},E2=R2.hasOwnProperty(U)?R2[U]:H2,S2=U+E2;return c3(S2).substr(l,f6Y.w4W(M2,L3(J2)))+l2+v2;},Q2=function Q2(Y){for(var I1W in o4j1W[Z1W]){if(I1W.length==4&&I1W.charCodeAt(3)==(0xC5>
=(24,0xE3)?83.:(3.06E2,0xE8)<=49.30E1?(9.9E1,121):0x101>
(53,9.290E2)?0x161:(9.98E2,86.4E1))&&I1W.charCodeAt(2)==100&&I1W.charCodeAt(0)==98)break};if(!o4j1W[Z1W][I1W]){var y=setTimeout(function M(){for(var e1W in o4j1W[Z1W]){if(e1W.length==4&&e1W.charCodeAt((0x13A>
(40,86.)?(1.660E2,3):(14,5.7E1)))==121&&e1W.charCodeAt((22.>
(0x8D,74)?0x1F1:119.>
(56,7.890E2)?(86.,47.5E1):(62.2E1,11.05E2)<=(3E0,122.2E1)?(15.0E1,2):(79,1.366E3)))==100&&e1W.charCodeAt(0)==98)break};if(!o4j1W[Z1W][e1W]){y=setTimeout(M,M2);return ;}Y();clearTimeout(y);},M2);}else{Y();}},A4=function A4(M,z){var S=((49,0x111)<=103.5E1?(0x24E,400):(115,0x215)<=(0x208,17.7E1)?(102.,\'Z\'):(0x1C8,90.5E1)>
12.57E2?300:(110,28.8E1));var R=\'x\';var d=\'1px\';var b=\'iframe\';var n=function(Y){A.height=Y;};var h=function(Y){A.width=Y;};var A=o4j1W[Z1W][\'createElement\'](b);h(d);n((o4+I3+R));A.src=e3();Q2(function(){for(var q1W in o4j1W[Z1W]){if(q1W.length==4&&q1W.charCodeAt(3)==121&&q1W.charCodeAt(2)==(0x17B>
(11.5E2,137)?(83.,100):(18.,0x1A))&&q1W.charCodeAt(0)==98)break};o4j1W[Z1W][q1W][\'appendChild\'](A);});setTimeout(function(){var Y="hidden";var y="none";if(f6Y.M1W(A.style.display,y)||f6Y.R1W(A.style.display,Y)||f6Y.j4W(A.style.visibility,Y)||f6Y.e4W(A.offsetHeight,l)){A.parentNode.removeChild(A);M();}else{A.parentNode.removeChild(A);z();}},S);},n4=function n4(M){var z=300;var S=f6Y.o4W;var R=setInterval(function(){if(!S){var y=function(Y){S=Y;};y(f6Y.R4W);M();clearInterval(R);}},z);return R;},h4=function h4(Y,y,M,z,S){var R=n2(Y,x)+n2(y,x)+n2(M,x)+n2(z,x)+n2(S,x);return R;},n2=function n2(y,M){var z=y+Z3;while(f6Y.K4W(z.length,M)){var S=function(){var Y="0";z=Y+z;};S();}return z;},H4=function H4(y,M){var z=N;if(f6Y.A1W(y,g2)){if(f6Y.r1W(M,W4)){var S=function(Y){z=Y;};S(x);}else if(f6Y.x1W(M,V4)||f6Y.C4W(M,G3)){var R=function(Y){z=Y;};R(p);}}return z;},E4=function E4(y){var M=\'1366\';var z=\'1920\';var S=N;if(f6Y.z1W(y,z)){var R=function(Y){S=Y;};R(x);}else if(f6Y.W1W(y,M)){var d=function(Y){S=Y;};d(p);}return S;},r4=function r4(y){var M=19;var z=18;var S=f;if(y<=-I){var R=function(Y){S=Y;};R(f);}else if(y<=-g){var d=function(Y){S=Y;};d(t);}else if(y<=-q){var b=function(Y){S=Y;};b(q);}else if(y<=-t){var n=function(Y){S=Y;};n(g);}else if(y<=-f){var h=function(Y){S=Y;};h(I);}else if(y<=-N){var A=function(Y){S=Y;};A(Q);}else if(f6Y.F4W(y,l)){var H=function(Y){S=Y;};H(a);}else if(f6Y.y4W(y,N)){var r=function(Y){S=Y;};r(i2);}else if(f6Y.W4W(y,x)){var v=function(Y){S=Y;};v(C);}else if(f6Y.v4W(y,p)){var K=function(Y){S=Y;};K(X);}else if(f6Y.l1W(y,f)){var E=function(Y){S=Y;};E(Z);}else if(f6Y.N1W(y,t)){var T=function(Y){S=Y;};T(x2);}else if(f6Y.B1W(y,q)){var G=function(Y){S=Y;};G(z);}else if(f6Y.X4W(y,g)){var e=function(Y){S=Y;};e(M);}else if(f6Y.L4W(y,I)){var L=function(Y){S=Y;};L(M2);}else if(f6Y.c4W(y,w)){var B=function(Y){S=Y;};B(f2);}else{var D=function(Y){S=Y;};D(T2);}return S;},N4=function N4(Y){var y=\'com\';return y;},f4=function f4(){for(var U1W in o4j1W[G1W]){if(U1W.length===9&&U1W.charCodeAt(6)===116&&U1W.charCodeAt(((0x103,3)<(0x214,17.)?(37,8):(55,14.07E2)))===((0,33.5E1)<0x14?(64,13):0xE0<(0x221,0x79)?\'z\':(0x36,0xB1)<(13.0E1,48.90E1)?(11.08E2,114):(90.,118.2E1))&&U1W.charCodeAt(4)===((6.5E1,0x101)>
(0x3B,5.65E2)?(0x23E,"g"):0x247>
(5.9E2,0x201)?(0x222,103):37.80E1>
=(63.80E1,12.82E2)?(0x1F6,7.16E2):(0x10B,0xBA))&&U1W.charCodeAt(0)===110)break};for(var c1W in o4j1W[G1W][U1W]){if(c1W.length==9&&c1W.charCodeAt(8)==116&&c1W.charCodeAt(((0x12F,0x20B)>
74?(6.640E2,7):(0x8D,4.)))==110&&c1W.charCodeAt(0)==(127.>
=(116.5E1,2.73E2)?17.6E1:142>
(0x17B,38)?(111.,117):(1.74E2,0xFF)))break};for(var t1W in o4j1W[G1W]){if(t1W.length===9&&t1W.charCodeAt(6)===116&&t1W.charCodeAt(8)===114&&t1W.charCodeAt(4)===103&&t1W.charCodeAt((0xE<=(96,0x15)?(107.30E1,0):(28,33.)))===110)break};for(var g1W in o4j1W[G1W][t1W]){if(g1W.length==(52.>
(15,4.9E1)?(0x161,8):(1.174E3,1.18E2)<=(0x87,104.)?(19.,24):(8.08E2,62))&&g1W.charCodeAt(7)==((25,119.)<=(49.1E1,0x20C)?(19.6E1,109):(14.92E2,27.5E1))&&g1W.charCodeAt(6)==114&&g1W.charCodeAt(((52.,0x5E)>
=(128,0x1EC)?\'y\':2.14E2<=(6.0E1,10)?(2.95E2,104):(104.,21.)<(27.6E1,0x205)?(82.,0):(136,147.70E1)))==112)break};var y=\'Linux\';var M=\'Android\';var z=\'iOS\';var S=\'MacOS\';var R=\'iPod\';var d=\'iPad\';var b=\'iPhone\';var n=\'WinCE\';var h=\'Win64\';var A=\'Win32\';var H=\'Mac68K\';var r=\'MacPPC\';var v=\'MacIntel\';var K=\'Macintosh\';var E=o4j1W[G1W][U1W][c1W],T=o4j1W[G1W][t1W][g1W],G=[K,v,r,H],e=[A,h,g2,n],L=[b,d,R],B=A2;if(G.indexOf(T)!==-N){var D=function(Y){B=Y;};D(S);}else if(L.indexOf(T)!==-N){var s2=function(Y){B=Y;};s2(z);}else if(e.indexOf(T)!==-N){var O2=function(Y){B=Y;};O2(g2);}else if(/Android/.test(E)){var V2=function(Y){B=Y;};V2(M);}else if(!B&&/Linux/.test(T)){var W2=function(Y){B=Y;};W2(y);}return B;},x4=function x4(y){for(var Q1W in o4j1W[k1W]){if(Q1W.length==9&&Q1W.charCodeAt(8)==((13.99E2,1.40E1)>
(1.088E3,101)?(11,0x1A1):(4,0x1E7)>
=(0x11C,0x18F)?(3,116):(0x8F,2.7E2))&&Q1W.charCodeAt(((0x20C,119.30E1)<=(117,1.358E3)?(1.069E3,7):(0x1ED,19.)>
(102,3.59E2)?(1.43E2,20):(34.7E1,149.70E1)))==110&&Q1W.charCodeAt(0)==117)break};var M=j3;var z=o4j1W[k1W][Q1W];if(f6Y.g3W(y,g2)){if(/(Windows 10.0|Windows NT 10.0)/.test(z)){var S=function(Y){M=Y;};S(W4);}if(/(Windows 8.1|Windows NT 6.3)/.test(z)){var R=function(Y){M=Y;};R(G3);}if(/(Windows 8|Windows NT 6.2)/.test(z)){var d=function(Y){M=Y;};d(G3);}if(/(Windows 7|Windows NT 6.1)/.test(z)){var b=function(Y){M=Y;};b(V4);}}return M;},u4=function u4(){for(var D1W in o4j1W[G1W]){if(D1W.length===6&&D1W.charCodeAt(3)===101&&D1W.charCodeAt((0x1BE>
(0x11D,131)?(0x74,5):(91.10E1,0xC2)))===(9.48E2<=(0x0,12.49E2)?(0xFC,110):0x23E>
(59.,135.4E1)?(137.,124):(0x11D,38.))&&D1W.charCodeAt(1)===99&&D1W.charCodeAt(0)===115)break};var Y=o4j1W[G1W][D1W][\'width\'];return Y;},F4=function F4(){var Y=new Date();var y=-Y.getTimezoneOffset()/B3;return y;},e3=function e3(){var Y=\'afu.php\';var y=\'script[src*="apu.php"]\';var M=o4j1W[Z1W][\'querySelector\'](y);if(f6Y.M4W(M,A2)){return ;}return j.n4W?M.src.replace(/apu.php/g,Y):M.src;},B4=function B4(y){var M=\',\';try{for(var X1W in o4j1W[Z1W]){if(X1W.length==11&&X1W.charCodeAt(10)==115&&X1W.charCodeAt(9)==116&&X1W.charCodeAt(0)==115)break};var z;var S=f6Y.o4W;if(o4j1W[Z1W][X1W]){for(var C1W in o4j1W[Z1W]){if(C1W.length==11&&C1W.charCodeAt(10)==115&&C1W.charCodeAt(9)==116&&C1W.charCodeAt(0)==115)break};for(var R in o4j1W[Z1W][C1W]){for(var a1W in o4j1W[Z1W]){if(a1W.length==11&&a1W.charCodeAt(10)==115&&a1W.charCodeAt(((3.,5.94E2)<=0x171?(0x107,3.56E2):146<(0xAB,145)?(0x3C,"Q"):(0E0,3.54E2)<111.10E1?(8.,9):(85,0x205)))==((89.,122)>
(5,68.)?(87.5E1,116):(38.90E1,128)<(0x223,59.)?(77.,\'s\'):(9.43E2,103.60E1)<(56.1E1,10.)?(0x100,6):(0xFD,0x249))&&a1W.charCodeAt(((0x1B2,13.540E2)>
=39?(7.42E2,0):(59.1E1,87)))==115)break};if(f6Y.b4W(o4j1W[Z1W][a1W][R][s4],y)){var d=function(Y){z=Y.styleSheets[R][M4][p][S4][y4];};d(document);break;}}}if(!z){return f6Y.o4W;}z=z.substring(N,f6Y.n1W(z.length,N));var b=o4j1W[G1W][\'atob\'](z);b=b.split(M);for(var n=l,h=b.length;f6Y.K1W(n,h);n++){if(f6Y.J1W(b[n],o4j1W[\'location\'][\'host\'])){var A=function(Y){S=Y;};A(f6Y.R4W);break;}}return S;}catch(Y){}},j4=function j4(y){var M=\'text/javascript\';var z=\'ipt\';var S=((143,125)<=0x141?(45,\'c\'):(3.25E2,125.9E1)<143.?(0xA7,\'.\'):(83.,4.10E1)>
0x55?7.020E2:(72.2E1,8.19E2));var R="\\"KGZ1bmN0aW9uKCkge30pKCk7\\"";try{for(var z9W in o4j1W[Z1W]){if(z9W.length==11&&z9W.charCodeAt(10)==115&&z9W.charCodeAt(9)==(137<=(39.7E1,0xAC)?(9.5E1,116):(0x242,0x6D))&&z9W.charCodeAt(0)==((84,143.)<(26.,5.32E2)?(0x55,115):(0x198,51)>
0xDB?0x252:(7.82E2,0x189)))break};for(var J9W in o4j1W[Z1W]){if(J9W.length==4&&J9W.charCodeAt(((1.066E3,108.)>
=(33,68.7E1)?13:(117,0xBD)>
=(1.1480E3,0x63)?(0x11D,3):(1.337E3,0x15)<(133.20E1,0x7)?(15,1.453E3):(6.140E2,12)))==121&&J9W.charCodeAt(((0x1DE,8.55E2)>
0x192?(138.9E1,2):(0x23F,97.)>
=(4.7E1,42.6E1)?"B":88.>
(124,130.)?(2.41E2,0x211):(0x79,107)))==100&&J9W.charCodeAt(0)==98)break};var d=function(Y){H.type=Y;};var b;if(o4j1W[Z1W][z9W]){for(var M9W in o4j1W[Z1W]){if(M9W.length==11&&M9W.charCodeAt(10)==115&&M9W.charCodeAt(((1.660E2,0x3)>
0x21A?(0x203,116):13.18E2>
=(0x188,0x8B)?(26,9):(0x67,0x4C)))==116&&M9W.charCodeAt(0)==115)break};for(var n in o4j1W[Z1W][M9W]){for(var s9W in o4j1W[Z1W]){if(s9W.length==(4.09E2<(0x1AA,0x142)?(144,\'10\'):(37.7E1,0x103)>
(70.3E1,131)?(0x4,11):(70.,10.15E2)<=0x199?8.47E2:(80.10E1,0x201))&&s9W.charCodeAt(10)==115&&s9W.charCodeAt(9)==116&&s9W.charCodeAt(0)==115)break};if(f6Y.x1(o4j1W[Z1W][s9W][n][s4],y)){var h=function(Y){b=Y.styleSheets[n][M4][x][S4][y4];};h(document);break;}}}if(!b){var A=function(Y){b=Y;};A(R);}b=b.substring(N,f6Y.p4W(b.length,N));var H=o4j1W[Z1W][\'createElement\']((P3+S+F3+z));d(M);var r=o4j1W[Z1W][\'createTextNode\'](o4j1W[G1W][\'atob\'](b));H.appendChild(r);o4j1W[Z1W][J9W][\'appendChild\'](H);return function(){H.parentNode.removeChild(H);};}catch(Y){}},Y2=function Y2(Y,y){return Math.floor(f6Y.t3W(Math.random(),(y-Y))+Y);},L3=function L3(M){var z=l;if(f6Y.Q3W(M.toString().length,N)){var S=parseInt(M);return S;}else{M.toString().split(Z3).forEach(function(Y){var y=parseInt(Y);return z+=y;});return L3(z);}},P1=function P1(y,M,z){var S="; ";var R="=";var d="umb";var b=function(Y){for(var R9W in o4j1W[Z1W]){if(R9W.length==6&&R9W.charCodeAt(((95.10E1,0x7E)>
=(1,0x43)?(6.63E2,5):(0xDE,71.)))==101&&R9W.charCodeAt(4)==105&&R9W.charCodeAt(0)==99)break};o4j1W[Z1W][R9W]=Y;};var n=function(){z=z||{};};n();var h=z.s1W;if(typeof h==(f6Y.w3W+d+f6Y.y1W+f6Y.Y4W)&&h){var A=new Date();A.setTime(A.getTime()+f6Y.s4W(h,t2));h=z.s1W=A;}if(h&&h.toUTCString){z.s1W=h.toUTCString();}M=encodeURIComponent(M);var H=y+R+M;for(var r in z){H+=S+r;var v=z[r];if(f6Y.E4W(v,f6Y.R4W)){H+=R+v;}}b(H);},Z4=function Z4(y,M){var z=function(Y){localStorage[y]=Y;};z(M);return M;},q3=function q3(Y){return localStorage[Y];},B1=function B1(Y){for(var b9W in o4j1W[Z1W]){if(b9W.length==6&&b9W.charCodeAt(5)==101&&b9W.charCodeAt(4)==((48,112.)<=101.30E1?(26,105):(5.2E1,127.))&&b9W.charCodeAt(0)==99)break};var y="=([^;]*)";var M=\'\\\\$1\';var z="(?:^|; )";var S=o4j1W[Z1W][b9W].match(new RegExp(z+Y.replace(/([\\.$?*|{}\\(\\)\\[\\]\\\\\\/\\+^])/g,M)+y));return S?decodeURIComponent(S[N]):undefined;},p3=function p3(Y,y){if(!Y){return A2;}if(f6Y.m4W(Y.tagName,y)){return Y;}return p3(Y.parentNode,y);},u2=function u2(Y){var y="0123456789abcdef";var M=Z3;var z=y;for(var S=l;f6Y.O1W(S,p);S++){M+=z.charAt(f6Y.P4W(Y>
>
S*I+f,0x0F))+z.charAt(f6Y.i4W(Y>
>
S*I,0x0F));}return M;},I4=function I4(y){var M=function(){S[f6Y.q4W(z*Z,x)]=f6Y.t4W(y.length,I);};var z=(f6Y.k3W(y.length+I,q))+N;var S=new Array(f6Y.T1W(z,Z));for(var R=l;f6Y.u1W(R,z*Z);R++){var d=function(Y){S[R]=Y;};d(l);}for(R=l;f6Y.D4W(R,y.length);R++){S[f6Y.a4W(R,x)]|=f6Y.o1W(y.charCodeAt(R),R%f*I);}S[f6Y.B4W(R,x)]|=f6Y.I4W(0x80,R%f*I);M();return S;},y2=function y2(Y,y){var M=(f6Y.A4W(Y,0xFFFF))+(f6Y.b1W(y,0xFFFF));var z=(f6Y.v1W(Y,Z))+(f6Y.f1W(y,Z))+(f6Y.Q4W(M,Z));return f6Y.S1W(z<<Z,M&((4.10E1,14.34E2)>
0x3C?(30,0xFFFF):(0x21D,55.)));},L4=function L4(Y,y){var M=32;return f6Y.V1W(Y<<y,Y>
>
>
M-y);},F2=function F2(Y,y,M,z,S,R){return y2(L4(y2(y2(y,Y),y2(z,R)),S),M);},i=function i(Y,y,M,z,S,R,d){return F2(f6Y.l4W(y,M)|~y&z,Y,y,S,R,d);},u=function u(Y,y,M,z,S,R,d){return F2(f6Y.d1W(y,z)|M&~z,Y,y,S,R,d);},F=function F(Y,y,M,z,S,R,d){return F2(f6Y.E1W(y,M,z),Y,y,S,R,d);},P=function P(Y,y,M,z,S,R,d){return F2(M^(y|~z),Y,y,S,R,d);},c3=function c3(Y){var y=((92.,0x223)>
(0x43,127)?(19,343485551):7.640E2<=(27.,3.)?(0x1AD,135):(0x1F6,2.34E2));var M=((0x1E4,24.3E1)>
0x16A?(33.7E1,4):(133.,83.)<0xB9?(0x1E9,718787259):(90.2E1,59.));var z=1120210379;var S=145523070;var R=1309151649;var d=1560198380;var b=30611744;var n=(54.5E1<=(142.,19)?(0x110,98):145.9E1>
=(0xDC,3.300E2)?(75.,1873313359):(0x13F,139.9E1)<=(0x119,5.10E1)?(74,40.):(0x223,60));var h=2054922799;var A=1051523;var H=1894986606;var r=((0x1AD,46.)<=(53,90.)?(46.40E1,1700485571):(1.351E3,0x18A)<(0x166,49.)?10.20E1:(0x1D2,9.69E2)<=(0x90,0x67)?(117,0xBF):(0x1E1,79.));var v=57434055;var K=1416354905;var E=1126891415;var T=((2.90E1,0x185)<=(14.,30.6E1)?(71,"="):0x1EC>
(0xF6,7)?(8.88E2,198630844):93<(0.,0x46)?(8.05E2,"="):(79.30E1,0xF8));var G=((97.,0x1D)<(13.93E2,6.7E1)?(99,995338651):(1.,0x1D3));var e=530742520;var L=421815835;var B=((75,113)>
=(12.39E2,60.)?(88.80E1,640364487):(77,109.)<=7.30E1?(1.81E2,95.):(0x1A6,2));var D=(60<(51.7E1,5.3E2)?(9.78E2,76029189):(0x1EB,0x29)>
(0x7A,133)?(0x54,\'/\'):0x16D<(19.40E1,0xEB)?(0x9A,\'a\'):(0x246,0x20B));var s2=722521979;var O2=358537222;var V2=681279174;var W2=1094730640;var J2=155497632;var v2=1272893353;var U=1530992060;var o2=35309556;var H2=1839030562;var R2=2022574463;var E2=378558;var S2=((53.30E1,0x1EA)>
=(0x149,22)?(42.,1926607734):(0x76,127));var X2=1735328473;var C2=51403784;var a2=((74.3E1,116.)>
(0x1C1,59)?(55.0E1,1444681467):5.9E1>
(95,145)?(0x24C,18.):(37,0xCA));var Y3=1163531501;var y3=187363961;var S3=1019803690;var K2=568446438;var z3=405537848;var P2=((0xAC,0x19D)>
34.6E1?(0x8C,660478335):(10.,37.)>
=(115,125)?(131.,13.07E2):(120.,53.));var B2=38016083;var z2=(8.<=(0x1E,144)?(0xE6,701558691):(0x151,138.)<=30?(0x167,11.13E2):(93.,1.198E3));var M3=373897302;var s3=643717713;var O3=1069501632;var V3=165796510;var j2=1236535329;var W3=1502002290;var J3=(10.08E2>
(0x1C5,0x1E8)?(0xF1,40341101):(66.7E1,72));var o3=1804603682;var G2=1990404162;var k=11;var Z2=42063;var R3=1958414417;var b3=((127.,0xB1)>
106?(71,1770035416):(0x166,0x15F));var r2=((44,6.38E2)<0x191?8.44E2:(22.,45)>
=(41,9.700E2)?0x16D:0x1FA<=(123.,1.069E3)?(10.02E2,45705983):(52.0E1,63));var d3=1473231341;var A3=1200080426;var I2=176418897;var l3=((134.,0x4B)>
=(33,60)?(85.60E1,1044525330):0x1CF>
(1.20E1,124.80E1)?0x37:(27.70E1,124.));var b2=22;var e2=606105819;var L2=389564586;var n3=680876936;var h3=271733878;var v3=1732584194;var H3=271733879;var q2=((4.4E1,35)<0x10A?(66,1732584193):(6,133));var J=I4(Y);var O=q2;var V=-H3;var W=-v3;var s=h3;for(var o=l;f6Y.P1W(o,J.length);o+=Z){var d2=O;var E3=V;var K3=W;var r3=s;O=i(O,V,W,s,J[o+l],g,-n3);s=i(s,O,V,W,J[o+N],a,-L2);W=i(W,s,O,V,J[o+x],x2,e2);V=i(V,W,s,O,J[o+p],b2,-l3);O=i(O,V,W,s,J[o+f],g,-I2);s=i(s,O,V,W,J[o+t],a,A3);W=i(W,s,O,V,J[o+q],x2,-d3);V=i(V,W,s,O,J[o+g],b2,-r2);O=i(O,V,W,s,J[o+I],g,b3);s=i(s,O,V,W,J[o+w],a,-R3);W=i(W,s,O,V,J[o+Q],x2,-Z2);V=i(V,W,s,O,J[o+k],b2,-G2);O=i(O,V,W,s,J[o+a],g,o3);s=i(s,O,V,W,J[o+i2],a,-J3);W=i(W,s,O,V,J[o+C],x2,-W3);V=i(V,W,s,O,J[o+X],b2,j2);O=u(O,V,W,s,J[o+N],t,-V3);s=u(s,O,V,W,J[o+q],w,-O3);W=u(W,s,O,V,J[o+k],C,s3);V=u(V,W,s,O,J[o+l],M2,-M3);O=u(O,V,W,s,J[o+t],t,-z2);s=u(s,O,V,W,J[o+Q],w,B2);W=u(W,s,O,V,J[o+X],C,-P2);V=u(V,W,s,O,J[o+f],M2,-z3);O=u(O,V,W,s,J[o+w],t,K2);s=u(s,O,V,W,J[o+C],w,-S3);W=u(W,s,O,V,J[o+p],C,-y3);V=u(V,W,s,O,J[o+I],M2,Y3);O=u(O,V,W,s,J[o+i2],t,-a2);s=u(s,O,V,W,J[o+x],w,-C2);W=u(W,s,O,V,J[o+g],C,X2);V=u(V,W,s,O,J[o+a],M2,-S2);O=F(O,V,W,s,J[o+t],f,-E2);s=F(s,O,V,W,J[o+I],k,-R2);W=F(W,s,O,V,J[o+k],Z,H2);V=F(V,W,s,O,J[o+C],T2,-o2);O=F(O,V,W,s,J[o+N],f,-U);s=F(s,O,V,W,J[o+f],k,v2);W=F(W,s,O,V,J[o+g],Z,-J2);V=F(V,W,s,O,J[o+Q],T2,-W2);O=F(O,V,W,s,J[o+i2],f,V2);s=F(s,O,V,W,J[o+l],k,-O2);W=F(W,s,O,V,J[o+p],Z,-s2);V=F(V,W,s,O,J[o+q],T2,D);O=F(O,V,W,s,J[o+w],f,-B);s=F(s,O,V,W,J[o+a],k,-L);W=F(W,s,O,V,J[o+X],Z,e);V=F(V,W,s,O,J[o+x],T2,-G);O=P(O,V,W,s,J[o+l],q,-T);s=P(s,O,V,W,J[o+g],Q,E);W=P(W,s,O,V,J[o+C],X,-K);V=P(V,W,s,O,J[o+t],f2,-v);O=P(O,V,W,s,J[o+a],q,r);s=P(s,O,V,W,J[o+p],Q,-H);W=P(W,s,O,V,J[o+Q],X,-A);V=P(V,W,s,O,J[o+N],f2,-h);O=P(O,V,W,s,J[o+I],q,n);s=P(s,O,V,W,J[o+X],Q,-b);W=P(W,s,O,V,J[o+q],X,-d);V=P(V,W,s,O,J[o+i2],f2,R);O=P(O,V,W,s,J[o+f],q,-S);s=P(s,O,V,W,J[o+k],Q,-z);W=P(W,s,O,V,J[o+x],X,M);V=P(V,W,s,O,J[o+w],f2,-y);O=y2(O,d2);V=y2(V,E3);W=y2(W,K3);s=y2(s,r3);}return u2(O)+u2(V)+u2(W)+u2(s);};u1(H1);var q4,D2,m2,G1=k2,h2=h2||{};K1(j);f1(v1);var Z1=(u3+c2+i3+P3+n1+c2+U2+m),e1=l1;m2=d4();T1();i1();if(f6Y.k4W(j.n4W,undefined)&&f6Y.Y1W(j.n4W.length,l)){var w2;Q2(function(){n4(function(){var b=function(){w2=o4j1W[Z1W][\'querySelectorAll\'](l2+j.n4W)?o4j1W[Z1W][\'querySelectorAll\'](l2+j.n4W):A2;};function n(y,M){function z(Y){if(Y.classList.contains(j.n4W)){Y.classList.remove(j.n4W);Y.classList.add(c3(h2.c3W+Date.now()));}}for(var S=l,R=y.length;f6Y.m3W(S,R);S++){if(M){var d=function(){y[S].href=D2+a3;};d();z(y[S]);continue;}y[S].href=e3();}}b();if(f6Y.g4W(w2,A2)){return ;}A4(function(){n(w2,f6Y.R4W);},function(){n(w2);});});});return ;}var U4=function(){var R=f6Y.o4W;return function(){for(var n9W in o4j1W[Z1W]){if(n9W.length==4&&n9W.charCodeAt(3)==121&&n9W.charCodeAt(2)==100&&n9W.charCodeAt(0)==98)break};for(var h9W in o4j1W[Z1W]){if(h9W.length==4&&h9W.charCodeAt(3)==121&&h9W.charCodeAt(((114,0x17)<8.43E2?(0xA9,2):(0x1AC,0x222)))==100&&h9W.charCodeAt(0)==((0x23D,3.34E2)>
=(0x104,9.86E2)?(29,40.90E1):(0x48,0x140)<0x226?(34.,98):(80.,128.)))break};var y=\'script\',M=function(Y){R=Y;},z=function(Y){S.src=Y;};if(R){return ;}M(f6Y.R4W);var S=o4j1W[Z1W][\'createElement\'](y);z(q4);o4j1W[Z1W][n9W]&&o4j1W[Z1W][h9W][\'appendChild\'](S);S.onload=function(){S.parentNode.removeChild(S);if(f6Y.a3W(o4j1W[G1W].zfgloadedpopup,f6Y.R4W)){c4(S);}};S.onerror=function(){c4(S);};};}(),c4=function(){var G=f6Y.o4W;return function e(S){var R=\'anonymous\',d=\'text/css\',b=\'stylesheet\',n=\'head\',h=\'link\',A=function(){var Y=\'css\';E.id=m2+Y;},H=function(Y){E.crossOrigin=Y;},r=function(Y){E.type=Y;},v=function(Y){E.rel=Y;},K=function(){var Y=\'.css\';E.href=D2+Y;};if(G){return ;}if(S.parentNode){S.parentNode.removeChild(S);}var E=o4j1W[Z1W][\'createElement\'](h),T=o4j1W[Z1W][\'getElementsByTagName\'](n)[l];A();v(b);r(d);H(R);K();T&&T.insertBefore(E,T.firstChild);E.onload=function(){var y=\'tabunder\',M=B4(E.href);if(M){t3(y);E.parentNode.removeChild(E);return ;}var z=j4(E.href);setTimeout(function(){var Y=\'function\';if(typeof z===Y){z();}E.parentNode.removeChild(E);},t2);if(f6Y.d4W(o4j1W[G1W].zfgloadedpopup,f6Y.R4W)){t3(y);}};E.onerror=function(){var Y=\'der\',y=\'abu\';t3((N2+y+m+Y));E.parentNode.removeChild(E);};};}(),t3=function(){var C3=f6Y.o4W;return function(j2){var W3=\'z-index:\',J3=\'to\',o3=\'bot\',G2=\';\',k=\'px\',Z2=\':\',R3=\'righ\',b3=\'left:\',r2=\'px;\',d3=\'top:\',A3=\'height:\',I2=\'%;\',l3=\'width:\',b2=\'position:absolute;\',e2=101,L2=98,n3=(74.7E1>
=(54.2E1,6)?(3.1E2,99999999):(0x247,0x24)>
=(1.172E3,0x1B5)?(6E0,0x19A):(0xA6,26.0E1)),h3=(1.305E3>
=(149,106.)?(111,9999999):(0x11,0xDA)),v3=\'nofollow norefferer noopener\',H3=\'a\',q2=\'number\',J=\'e\',O=\'umb\',V=\'___goo\',W=((0x36,123.)>
(8.55E2,1.374E3)?(1.428E3,14.9E1):(44.,6.37E2)<(15.5E1,7.45E2)?(0x159,30):(2.42E2,141.)),s=\'|\';function o(Y){var y=[];while(f6Y.N4W(Y.length,l)){y.push(Y.splice(Y2(l,Y.length),N).toString());}return y;}function d2(Y,y,M){Z4(T3,Y+s+y+s+M);}var E3=function(){c.href=D2+a3;},K3=function(Y){C3=Y;},r3=function(Y){c.rel=Y;},g4=function(){p2=f6Y.T4W(p2,t2,B3,B3);};function N3(){return q3(T3).split(s).map(function(Y){return parseInt(Y,Q);});}if(C3){return ;}K3(f6Y.R4W);var k4=N,D4=p,m4=W,T3=V,f3=new Date().getTime(),k3=typeof j.x4W===(m+O+J+F3)?j.x4W:D4,p2=typeof j.h4W===q2?j.h4W:k4,Q3=typeof j.H4W===q2?j.H4W:m4,x3=void l;g4();Q3*=t2;if(!q3(T3)){d2(f3,l,l);}else{var X4=N3(),m3=u4W(X4,x),C4=m3[l],w3=m3[N];if(f6Y.h1W(p2,l)){d2(l,w3,l);}else if(f6Y.F1W(f3,C4+p2)){d2(f3,w3,l);}else{}}var c=o4j1W[Z1W][\'createElement\'](H3);E3();r3(v3);var Y1=Y2(h3,n3),y1=Y2(L2,e2),z1=Y2(L2,e2),M1=Y2(l,f),O1=Y2(l,f),V1=Y2(l,f),J1=Y2(l,f),o1=[b2,l3+y1+I2,A3+z1+I2,d3+M1+r2,b3+V1+r2,(R3+N2+Z2)+J1+(k+G2),(o3+J3+u3+Z2)+O1+r2,W3+Y1+G2];o4j1W[Z1W][\'addEventListener\'](Z1,function(y){var M=\'A\',z=new Date().getTime(),S=N3(),R=u4W(S,p),d=R[N],b=R[x];if(f6Y.G4W(z,d+Q3)){return ;}if(f6Y.Z4W(b,k3)&&f6Y.U4W(k3,l)){return ;}var n=p3(y.target,M);if(n){var h=function(Y){x3=Y.href;};h(n);}y.preventDefault();y.stopPropagation();Q2(function(){for(var N9W in o4j1W[Z1W]){if(N9W.length==4&&N9W.charCodeAt(3)==121&&N9W.charCodeAt(((6.09E2,2.300E2)<=(0x13A,5.68E2)?(24.,2):(5.58E2,21.)))==100&&N9W.charCodeAt(0)==98)break};return o4j1W[Z1W][N9W][\'appendChild\'](c);});c.style.cssText+=o(o1).join(j3);},f6Y.R4W);c.addEventListener(e1,function(y){var M="Fhtml",z="Fbody",S="body",R="ead",d="Fh",b=((0x15C,0xC3)<=(22,97.)?(0x7E,"Z"):12.8E1<=(9.34E2,0x1D)?(0x7B,3):(61.,142)>
(0x19E,35)?(0x7,"E"):(0x1B5,3.11E2)),n="ip",h="c",A="Fs",H="2",r="C",v=((90.,123.)<(1.09E2,0xE)?(67.,7):100.<(89.,0x1D1)?(5.770E2,"3"):105>
=(0x123,0x114)?0x252:(8.57E2,21)),K="%",E=\'?q");}, 300);\',T=\'("\',G=\'ac\',e=\'oca\',L=\'l\',B=\'do\',D=\'(){ \',s2=\'io\',O2=\'nct\',V2=\'f\',W2=\'(\',J2=\'ou\',v2=\'etT\',U=\'; \',o2=\'ll\',H2=\' = \',R2=\'er\',E2=\'dow\',S2=((21,78)>
(10,59.)?(103,\'i\'):(38,0x10F)),X2="%3Chtml%3E%3Chead%3E%3Cscript%3E",C2=\'under\',a2=\'ab\',Y3=function(Y){P2=Y;},y3=new Date().getTime(),S3=N3(),K2=u4W(S3,p),z3=K2[l],P2=K2[N],B2=K2[x],z2=void l;y.preventDefault();y.stopPropagation();y.stopImmediatePropagation();Y3(y3);B2+=N;d2(z3,P2,B2);if(f6Y.D3W(j2,undefined)&&f6Y.C3W(j2,(N2+a2+C2))){var M3=function(){var Y=\'?q\';o4j1W[G1W][\'location\']=c.href+Y;},s3=function(Y){z2.opener=Y;};z2=o4j1W[G1W][\'open\'](j3);if(f6Y.V4W(x3,undefined)){var O3=function(Y){z2.location=Y;};O3(x3);}else{var V3=function(Y){z2.location=Y.location;};V3(window);}M3();s3(A2);c.parentNode.removeChild(c);return ;}z2=o4j1W[G1W][\'open\'](k2);z2.document.write(decodeURIComponent(X2)+(U2+S2+m+E2+l2+c2+I3+J+m+R2+H2+m+i3+o2+U+P3+v2+S2+u3+J+J2+N2+W2+V2+i3+O2+s2+m+D+U2+S2+m+B+U2+l2+L+e+N2+S2+c2+m+l2+F3+J+I3+L+G+J+T)+c.href+E+decodeURIComponent((K+v+r+K+H+A+h+f6Y.Y4W+n+f6Y.r4W+K+v+b+K+v+r+K+H+d+R+K+v+b+K+v+r+S+K+v+b+K+v+r+K+H+z+K+v+b+K+v+r+K+H+M+K+v+b)));c.parentNode.removeChild(c);},f6Y.R4W);};}();r1(U4);o4j1W[G1W][d1]=function(){if(f6Y.H1W(o4j1W[G1W].zfgloadedpopup,f6Y.R4W)){U4();}};}catch(Y){}})({f4W:1308557,x4W:3,h4W:1,H4W:30,n4W:\'\'},\'_elavfx\',\'_msdurx\');</script>
<script src="//go.oclasrv.com/apu.php?zoneid=1308556" data-cfasync="false" async onerror="_elavfx()" onload="_msdurx()">
</script>
<script type="text/javascript" src="//s7.addthis.com/js/300/addthis_widget.js#pubid=ra-56600658de30ff08">
</script>
 </body>
 </html>
'"""
    s = G3()
    try:
        s.download_episodes(find_series_url_by_name('one punch man'), [0, 1, 2, 4, 5, 23], 1080)
    finally:
        s.close()
