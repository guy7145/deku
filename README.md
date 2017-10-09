# deku

search(anime_name) - search for anime_name and print all results
find(anime_name) - search for anime_name and print it's watching-page if found, raise an error if no such page was found
check(anime_name) - finds anime_name's page and prints how many episodes and servers were found
download(anime_name, episodes, path='./', player_quality='1080p', server_number=0, short_timeout=10, long_timeout=20) -
downloads anime_name
episodes: list (or other form of iterable) of episode to download
path: the path to download to. a directory with the anime's name will be created if doesn't exist, the episodes will be downloaded there.
player_quality: either 360p, 480p, 720p or 1080p. works on server 0, not tested on other servers. if the requested quality doesn't exist, the episodes will probably be downloaded in 360p.
server number: the server to download the episodes from.
timeouts: the time chrome spends loading the page before requesting for the source. if using the short_timeout the requested links weren't found, long_timeout will be tried instead. if it still doesn't work, an error will be raised.
