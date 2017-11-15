# deku

### Search and Find Operations
##### <i>search(anime_name)</i>
searches for <i>anime_name</i> and prints all of the results
<br><br>

##### <i>find(anime_name) / find_exact(anime_name)</i>
searches for <i>anime_name</i> and prints it's watching-page if found;
<br>
raises an error if no page was found
<br>

##### <i>find_by_substring(anime_name)</i>
looks for all the animes that contain <i>anime_name</i> in their name
<br>
example: find_by_substring('one punch man') will find 'one punch man', 'one punch man dub', 'one punch man specials', etc.
<br>

##### <i>find_by_keywords(anime_name)</i>
looks for all the animes that contain all the words from <i>anime_name</i> in their name
<br>
example: find_by_keywords('one road punch') will find 'one punch man road to hero' (and possibly some more results...)
<br><br>

### Gathering info and updates
##### <i>check(anime_name) </i>
finds (using <i>find</i>) <i>anime_name</i>'s page and prints how many episodes were found
<br><br>

##### <i>estimate(anime_name)</i>
prints how many episodes were found for <i>anime_name</i> + an estimate of the 
airing time and date of the next episode (if exists)
<br><br>


### Downloading
#### <i>download(anime_name, episodes, path='./', player_quality='1080p', server_number=0, timeouts=(5, 10, 20))</i>
downloads <i>anime_name</i> to "<i>./path/anime_name</i>"
(a directory named "<i>anime_name</i>" will be created if doesnt exist, and the episodes will be downloaded there).
<br><br>
<i>episodes</i>: list (or other form of iterable) of episode to download.
<br><br>
<i>player_quality</i>: either '360', '480', '720' or '1080' (notice: no 'p'). works on server 0, not tested on other servers. if the requested quality isn't available, there's no guarantee on the quality the episodes will be downloaded in.
<br><br>
<i>server_number</i>: the server to download the episodes from.
<br><br>
timeouts: the time chrome spends loading the page before requesting for the source. if while using timeouts[i] the requested links weren't found, timeouts[i+1] will be tried and so on. if the links still can't be found at the end, an error will be raised.
<br><br>

#### <i>download_by_url(series_url, anime_name, episodes, path='./', player_quality='1080p', server_number=0, timeouts=(5, 10, 20))</i>
downloads <i>anime_name</i> to "<i>./path/anime_name</i>", from the specified url: <i>series_url</i>; (a directory named "<i>anime_name</i>" will be created if doesnt exist, and the episodes will be downloaded there).
<br>
<strong>** use this function in case the normal download function fails to find the <i>watch url</i> (an indicator is when the '<i>find</i>' function fails)</strong>
<br><br>
<i>series_url</i>: the base url for the specified anime
<br>
example: https://9anime.to/watch/one-punch-man.928
<br><br>
