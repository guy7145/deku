# deku

### Search and Find Operations
##### <i>search(anime_name)</i>
searches for <i>anime_name</i> and prints all of the results
<br><br>
example: 
<br>
search('one punch man'):
<br><br>
results:
<br>
['One Punch Man (Dub)',
 'One Punch Man Specials (Dub)',
 'One Punch Man',
 'One Punch Man Specials',
 'One Punch Man: Road to Hero',
 'Punch Line',
 'Sweat Punch', ...],<br>
['https://9anime.ch/watch/one-punch-man-dub.zwx2',
 'https://9anime.ch/watch/one-punch-man-specials-dub.py9x',
 'https://9anime.ch/watch/one-punch-man.928',
 'https://9anime.ch/watch/one-punch-man-specials.pwjj',
 'https://9anime.ch/watch/one-punch-man-road-to-hero.q7kn',
 'https://9anime.ch/watch/punch-line.n398',
 'https://9anime.ch/watch/sweat-punch.pokx', ...]
<br>

##### <i>find(anime_name) / find_exact(anime_name)</i>
searches for <i>anime_name</i> and prints it's watching-page if found;
<br>
raises an error if no page was found
<br><br>
example:
<br>
find('one punch man'):
<br><br>
results:
<br>
'https://9anime.ch/watch/one-punch-man.928'
<br>


##### <i>find_by_substring(anime_name)</i>
looks for all the animes that contain <i>anime_name</i> in their name
<br><br>
example:
<br>
find_by_substring('one punch man'):
<br><br>
results:
<br>
['https://9anime.ch/watch/one-punch-man-dub.zwx2',
 'https://9anime.ch/watch/one-punch-man-specials-dub.py9x',
 'https://9anime.ch/watch/one-punch-man.928',
 'https://9anime.ch/watch/one-punch-man-specials.pwjj',
 'https://9anime.ch/watch/one-punch-man-road-to-hero.q7kn']
 <br>

##### <i>find_by_keywords(anime_name)</i>
looks for all the animes that contain all the words from <i>anime_name</i> in their name
<br><br>
example: 
<br>
find_by_keywords('one punch man')
<br><br>
results:
<br>
['https://9anime.ch/watch/one-punch-man-dub.zwx2',
 'https://9anime.ch/watch/one-punch-man-specials-dub.py9x',
 'https://9anime.ch/watch/one-punch-man.928',
 'https://9anime.ch/watch/one-punch-man-specials.pwjj',
 'https://9anime.ch/watch/one-punch-man-road-to-hero.q7kn']
<br>

### Gathering info and updates
##### <i>info(anime_name)</i>
finds (using <i>find</i>) <i>anime_name</i>'s page and prints how many episodes were found
<br><br>
example: 
<br>
info('one punch man')
<br><br>
results:
<br>
RapidVideo<br>
ep 1    (added at Oct 04, 2015 - 11:05) q2w2rw<br>
ep 2    (added at Oct 11, 2015 - 11:05) m4p4n7<br>
ep 3    (added at Oct 18, 2015 - 11:05) y94931<br>
ep 4    (added at Oct 25, 2015 - 11:05) x6364w<br>
ep 5    (added at Nov 01, 2015 - 11:05) j6m688<br>
ep 6    (added at Nov 08, 2015 - 11:05) n2q20j<br>
ep 7    (added at Nov 15, 2015 - 11:05) r9x90p<br>
ep 8    (added at Nov 22, 2015 - 11:05) n2q2mj<br>
ep 9    (added at Nov 29, 2015 - 11:05) 97x7rq<br>
ep 10   (added at Dec 06, 2015 - 11:05) y94951<br>
ep 11   (added at Dec 13, 2015 - 11:05) r9x9qp<br>
ep 12   (added at Dec 20, 2015 - 11:05) 6yry4z<br>
MyCloud<br>
ep 1    (added at Oct 04, 2015 - 11:05) n2q2oj<br>
ep 2    (added at Oct 11, 2015 - 11:05) j6m6k8<br>
ep 3    (added at Oct 18, 2015 - 11:05) v212x6<br>
ep 4    (added at Oct 25, 2015 - 11:05) r9x9vp<br>
ep 5    (added at Nov 01, 2015 - 11:05) 7yvy9y<br>
ep 6    (added at Nov 08, 2015 - 11:05) k4n406<br>
ep 7    (added at Nov 15, 2015 - 11:05) o8r80y<br>
ep 8    (added at Nov 22, 2015 - 11:05) k4n4j6<br>
ep 9    (added at Nov 29, 2015 - 11:05) 6yryoz<br>
ep 10   (added at Dec 06, 2015 - 11:05) v21246<br>
ep 11   (added at Dec 13, 2015 - 11:05) o8r8ny<br>
ep 12   (added at Dec 20, 2015 - 11:05) 3yoy49<br>
OpenLoad<br>
ep 1    (added at Oct 04, 2015 - 11:05) p2v2qx<br>
ep 2    (added at Oct 11, 2015 - 11:05) l4o4mm<br>
ep 3    (added at Oct 18, 2015 - 11:05) x6360w<br>
ep 4    (added at Oct 25, 2015 - 11:05) wy2y4l<br>
ep 5    (added at Nov 01, 2015 - 11:05) 97x74q<br>
ep 6    (added at Nov 08, 2015 - 11:05) m4p487<br>
ep 7    (added at Nov 15, 2015 - 11:05) q2w23w<br>
ep 8    (added at Nov 22, 2015 - 11:05) m4p4l7<br>
ep 9    (added at Nov 29, 2015 - 11:05) 87w7q3<br>
ep 10   (added at Dec 06, 2015 - 11:05) x6365w<br>
ep 11   (added at Dec 13, 2015 - 11:05) q2w2pw<br>
ep 12   (added at Dec 20, 2015 - 11:05) 5yqy7v<br>
<br>

##### <strike><i>estimate(anime_name)</i>
prints how many episodes were found for <i>anime_name</i> + an estimate of the 
airing time and date of the next episode (if exists)</strike>
<br><br>


### Downloading
#### <i>download(anime_name, episodes, path='.', server=RapidVideo)</i>
downloads <i>anime_name</i> to "<i>./path/anime_name</i>"
(a directory named "<i>anime_name</i>" will be created if doesn't exist, and the episodes will be downloaded there).
<br><br>
<i>episodes</i>: list (or other form of iterable) of episode to download.
<br><br>
<i>player_quality</i>: either '360', '480', '720' or '1080' (notice: no 'p'). works on server 0, not tested on other servers. if the requested quality isn't available, there's no guarantee on the quality the episodes will be downloaded in.
<br><br>
<i>server</i>: the server to use (right now only G3 is supported so you actually have no choice here, leave it empty)
<br><br>

#### <i>download_by_url(anime_name, url, episodes, path='.', server=RapidVideo)</i>
downloads <i>anime_name</i> to "<i>./path/anime_name</i>", from the specified url: <i>series_url</i>; (a directory named "<i>anime_name</i>" will be created if doesnt exist, and the episodes will be downloaded there).
<br>
<strong>** use this function in case the normal download function fails to find the <i>watch url</i> (an indicator is when the '<i>find</i>' function fails)</strong>
<br><br>
<i>series_url</i>: the base url for the specified anime
<br>
example: https://9anime.to/watch/one-punch-man.928
<br><br>

#### shortcuts
#### <i>download(anime_name)</i>
download all episodes of <i>anime_name</i>

#### <i>download(anime_name, episodes(first, last))</i>
download all episodes of <i>anime_name</i> start from <i>first</i> to <i>last</i>
