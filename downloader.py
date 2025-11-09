import os

import requests

SERVER_IP = '192.168.1.169' # <-- Put Rasp Pi 5 IP address or Mac address here
SERVER_URL = f'http://{SERVER_IP}:5000'
LOCAL_CACHE_DIR = './local_cache'
if not os.path.exists(LOCAL_CACHE_DIR):
    os.makedirs(LOCAL_CACHE_DIR)

# Clear Cache
if os.listdir(LOCAL_CACHE_DIR):
    for item in os.listdir(LOCAL_CACHE_DIR):
        os.remove(os.path.join(LOCAL_CACHE_DIR, item))

def fetch_playlist():
    try:
        response = requests.get(SERVER_URL + '/api/playlist')
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(e)
        return []

def download_image(filename):
    local_path = f'{LOCAL_CACHE_DIR}/{filename}'
    try:
        response = requests.get(SERVER_URL + '/api/download/' + filename)
        response.raise_for_status()
        with open(local_path, 'wb') as f:
            f.write(response.content)
    except requests.exceptions.RequestException as e:
        print(e)
        return []

def download_playlist():
    data = fetch_playlist()
    for item in data:
        filepath = item['filepath']
        download_image(filepath)
