from deku import *
from deku_cli_api import estimate


def main():
    anime_name = "shokugeki no souma san no sara"
    print(find_series_urls_by_keywords(anime_name))
    estimate(anime_name)
    download_path = 'D:\_Guy\d9anime\downloaded'
    eps = [1, 2, 3]
    download_episodes(anime_name, path=download_path, episodes_to_download=eps,
                      server_number=0, short_timeout=10, long_timeout=20)
    return

if __name__ == '__main__':
    main()
