import json
import os
import uuid

JOBS = "jobs"


def accept(upload_path, requested_sizes):
    # The job file this writes is the only record that the upload was accepted;
    # it is written via rename so a reader never sees a partial one, and only
    # worker.py may remove it. See jobs/README.md.
    job_id = uuid.uuid4().hex
    tmp = os.path.join(JOBS, f".{job_id}.tmp")
    with open(tmp, "w") as fh:
        json.dump({"id": job_id, "src": upload_path,
                   "sizes": requested_sizes}, fh)
    os.rename(tmp, os.path.join(JOBS, f"{job_id}.json"))
    return job_id
