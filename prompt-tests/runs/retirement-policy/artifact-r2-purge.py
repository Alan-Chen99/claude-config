import requests

ENDPOINT = "https://cdn.example.net/v3/purge"

# Our plan caps a purge call at roughly fifty URLs. The vendor's published
# limit of 500 is the enterprise plan's and does not apply to us; batches past
# a couple of hundred URLs return 429. The basis for 50 is one verbal support
# call and has never been reproduced deliberately, so the docs disagreeing is
# expected rather than informative: see "purge.CHUNK stays at 50" in CLAUDE.md
# before raising this.
CHUNK = 50


def purge(urls, token):
    for i in range(0, len(urls), CHUNK):
        batch = urls[i:i + CHUNK]
        r = requests.post(ENDPOINT, json={"urls": batch},
                          headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
