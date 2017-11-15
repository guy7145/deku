from deku import *
from deku_cli_api import estimate


def main():
    # anime_name = "tokyo ghoul a"
    # print(find_series_urls_by_keywords(anime_name))
    # estimate(anime_name)
    download_path = 'D:\_Guy\d9anime\downloaded'
    eps = range(9, 13)
    download_episodes(anime_name='tokyo ghoul a',
                      path=download_path,
                      episodes_to_download=eps,
                      timeouts=(10, 20), server_number=1)
    # download_episodes_by_url(series_url='https://9anime.to/watch/fatezero.2vl',
    #                          anime_name='fate zero',
    #                          path=download_path,
    #                          episodes_to_download=eps)
    return

if __name__ == '__main__':
    main()
