from Servers import *
from src.deku_cli_api import *


def main():
    download_path = 'D:\_Guy\d9anime\downloaded'
    anime_name = 'one punch man'
    eps = episodes(1, 2)
    # print(search(anime_name))
    # print(find_series_url_by_name(anime_name))
    # print(debug_src(anime_name))
    download(anime_name, eps, server=RapidVideo)
    return


if __name__ == '__main__':
    main()
