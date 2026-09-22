import json
import os
import uuid

JOBS = "jobs"


def accept(upload_path, requested_sizes):
    job_id = uuid.uuid4().hex
    tmp = os.path.join(JOBS, f".{job_id}.tmp")
    with open(tmp, "w") as fh:
        json.dump({"id": job_id, "src": upload_path,
                   "sizes": requested_sizes}, fh)
    os.rename(tmp, os.path.join(JOBS, f"{job_id}.json"))
    return job_id
