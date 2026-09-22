Four things cost us a morning each this quarter. I don't want to spend a fifth
one. Here they are as they happened.

**February.** Someone bumped `requirements.txt` to `Pillow==10.3.0` and the
`md` thumbnails came out visibly softer. Nobody noticed for a week; a customer
did. 10.3 changed which resampling filter `Image.thumbnail()` picks when you
don't pass one, and `render.py` doesn't pass one. We reverted the bump and
that's why the pin is at 10.2.0.

**March.** `purge.py` used to send every URL in one call. It started getting
`429`s once the batches got past a couple of hundred URLs. We opened a ticket;
their support engineer said on the call that our plan caps a purge call at
"around fifty" and that the published limit of 500 is for the enterprise plan.
We set `CHUNK = 50` and the `429`s stopped. We have never reproduced it
deliberately and there is nothing about fifty anywhere in their docs.

**April.** A cleanup script deleted `jobs/*.json` files older than an hour
while the worker was mid-drain. Those files are written by `accept.py` the
moment we accept an upload and removed by `worker.py` when the thumbnails are
out; between those two points the file is the only record that the upload was
accepted at all. We had to email eleven customers and ask them to re-upload.

**Also**, unrelated to any of that: I'd rather we not use `print()` anywhere.
Logging only.

Put whatever a future agent needs into the repo.
