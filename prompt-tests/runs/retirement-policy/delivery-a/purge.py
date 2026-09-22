import requests

ENDPOINT = "https://cdn.example.net/v3/purge"

# The vendor's published per-call limit of 500 URLs applies to the enterprise
# plan; on our plan the cap is around fifty and larger batches draw 429s.
# Sourced from a support call, not from their docs -- see DECISIONS.md
# "CDN purge batch size" before raising this.
CHUNK = 50


def purge(urls, token):
    for i in range(0, len(urls), CHUNK):
        batch = urls[i:i + CHUNK]
        r = requests.post(ENDPOINT, json={"urls": batch},
                          headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
