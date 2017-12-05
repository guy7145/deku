from Servers import *
from deku import *


def main():
    download_path = 'D:\_Guy\d9anime\downloaded'
    anime_name = 'shokugeki no souma san no sara'
    eps = [10]

    download_episodes(anime_name, eps, download_path, server=RapidVideo())
    return


if __name__ == '__main__':
    main()
