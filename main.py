import os

from displayer import run_slideshow

local_cache = 'local_cache'
def start():
    #  print('starting download')
    #  if not os.listdir(local_cache):
    #     download_playlist()
     print('running slideshow')
     run_slideshow(local_cache, None)

if __name__ == '__main__':
    print(os.listdir())
    start()