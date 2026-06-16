import threading
import uuid
import time
import traceback

JOBS: dict[str, dict] = {}
_lock = threading.Lock()
JOB_TTL_SECONDS = 60 * 60 * 6
MAX_JOBS = 200


def _cleanup_locked(now: float):
    expired = [
        job_id
        for job_id, job in JOBS.items()
        if now - job.get("updated_at", job.get("created_at", now)) > JOB_TTL_SECONDS
    ]
    for job_id in expired:
        JOBS.pop(job_id, None)

    overflow = len(JOBS) - MAX_JOBS
    if overflow > 0:
        oldest = sorted(JOBS.items(), key=lambda item: item[1].get("updated_at", 0))
        for job_id, _job in oldest[:overflow]:
            JOBS.pop(job_id, None)


def create_job(payload: dict) -> str:
    job_id = uuid.uuid4().hex[:16]
    now = time.time()
    with _lock:
        _cleanup_locked(now)
        JOBS[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "result": None,
            "error": None,
            "created_at": now,
            "updated_at": now,
        }
    return job_id


def update_job(job_id: str, **kwargs):
    with _lock:
        if job_id in JOBS:
            JOBS[job_id].update(kwargs)
            JOBS[job_id]["updated_at"] = time.time()


def get_job(job_id: str) -> dict | None:
    with _lock:
        _cleanup_locked(time.time())
        j = JOBS.get(job_id)
        if j is None:
            return None
        return {k: v for k, v in j.items()}


def run_job(job_id: str, invoke_fn, payload):
    """Run graph.invoke in background thread."""
    try:
        from app.schemas.requests import GenerateRequest
        req = GenerateRequest(**payload)
        state = req.to_state()
        update_job(job_id, status="running")
        result = invoke_fn(state)
        # Clean out large internal fields for storage
        clean = {k: v for k, v in result.items()
                 if k not in ("images", "image_roles", "user_specs",
                              "user_selling_points", "user_constraints",
                              "asset_types_requested")}
        update_job(job_id, status="succeeded", result=clean)
    except Exception as e:
        tb = traceback.format_exc()
        update_job(job_id, status="failed", error=f"{type(e).__name__}: {e}\n{tb}")
