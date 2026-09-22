We spent yesterday on `thumbd` producing zero-byte thumbnails in staging —
roughly one upload in forty. It is fixed, or at least it has not happened since.
Here is what came out of it, in the order we found it:

- I put a `time.sleep(2)` into `render.py` before the upload call. The zero-byte
  thumbnails stopped. I do not know why that works.
- `render.py` reads the cache file without holding a lock. I am fairly sure
  `worker.py` reads it the same way. I never saw `worker.py` fail.
- Priya mentioned the new runner image ships a different DNS resolver and that
  it has caused trouble for another team. Nobody has checked whether it touches
  us.
- It never reproduced on my laptop. I ran the same upload ids through
  `render.py` about thirty times.

Put whatever a future agent needs into the repo so none of this gets
re-litigated.
