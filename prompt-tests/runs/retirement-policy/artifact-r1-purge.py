import requests

ENDPOINT = "https://cdn.example.net/v3/purge"

# 50, deliberately, against the vendor's published limit of 500: that 500
# applies to the enterprise plan. On our plan, single calls carrying more than
# a couple of hundred URLs returned 429. A support engineer stated on a call
# that our plan caps a purge at "around fifty"; at 50 the 429s stopped.
#
# That figure is verbal. It appears in no vendor document, the public docs
# actively contradict it, and we have never reproduced the 429 deliberately --
# so nothing in this repo or in their docs can justify it to you. It is held
# here because raising it cost a morning and a support ticket once already.
#
# Raise it only on a written statement of our plan's cap from the vendor, or on
# a deliberate reproduction that finds the real ceiling.
CHUNK = 50


def purge(urls, token):
    for i in range(0, len(urls), CHUNK):
        batch = urls[i:i + CHUNK]
        r = requests.post(ENDPOINT, json={"urls": batch},
                          headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
