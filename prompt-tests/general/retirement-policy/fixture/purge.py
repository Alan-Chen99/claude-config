import requests

ENDPOINT = "https://cdn.example.net/v3/purge"
CHUNK = 50


def purge(urls, token):
    for i in range(0, len(urls), CHUNK):
        batch = urls[i:i + CHUNK]
        r = requests.post(ENDPOINT, json={"urls": batch},
                          headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
