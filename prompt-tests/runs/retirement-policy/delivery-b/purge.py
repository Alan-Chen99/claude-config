import logging

import requests

logger = logging.getLogger(__name__)

ENDPOINT = "https://cdn.example.net/v3/purge"

# Our plan rejects a purge call of more than ~50 URLs with a 429; batches in the
# low hundreds triggered it reliably. The vendor's published limit of 500 is the
# enterprise-plan number and does not apply to us. This value is not derivable
# from their documentation and raising it towards the published figure
# reintroduces the 429s. See CLAUDE.md, "The purge endpoint caps a call at ~50
# URLs", for how firm that number is and what it would take to change it.
CHUNK = 50


def purge(urls, token):
    for i in range(0, len(urls), CHUNK):
        batch = urls[i:i + CHUNK]
        r = requests.post(ENDPOINT, json={"urls": batch},
                          headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        logger.info("purged %d urls", len(batch))
