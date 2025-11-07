import os

from displayer import run_slideshow
from downloader import download_playlist

local_cache = './local_cache'

def clear_cache():
    global local_cache
    if not os.path.exists(local_cache):
        os.makedirs(local_cache)

def start():
     print('starting download')
     if not os.listdir(local_cache):
        download_playlist()
     print('running slideshow')
     run_slideshow(local_cache, None)

if __name__ == '__main__':
    start()