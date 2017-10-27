from deku import *
from deku_cli_api import estimate


def main():
    # anime_name = "tokyo ghoul a"
    # print(find_series_urls_by_keywords(anime_name))
    # estimate(anime_name)
    download_path = 'D:\_Guy\d9anime\downloaded'
    eps = list(range(1, 6))
    download_episodes(anime_name='tokyo ghoul a',
                             path=download_path, episodes_to_download=eps, server_number=0, short_timeout=10,
                             long_timeout=20)
    # download_episodes_by_url(series_url='https://9anime.to/watch/fatezero.2vl', anime_name='fate zero',
    #                          path=download_path, episodes_to_download=eps, server_number=0, short_timeout=10,
    #                          long_timeout=20)
    return

if __name__ == '__main__':
    main()
