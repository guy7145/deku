from deku import *


def main():
    anime_name = "black clover tv"
    download_path = 'D:\_Guy\d9anime\downloaded'
    eps = [2]
    download_episodes(anime_name, path=download_path, episodes_to_download=eps,
                      short_timeout=10, long_timeout=20, server_number=0)
    return

if __name__ == '__main__':
    main()
