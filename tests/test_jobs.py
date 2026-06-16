import time
import unittest

from app import jobs


class JobsTests(unittest.TestCase):
    def setUp(self):
        with jobs._lock:
            jobs.JOBS.clear()

    def tearDown(self):
        with jobs._lock:
            jobs.JOBS.clear()

    def test_failed_job_records_error(self):
        job_id = jobs.create_job({})

        def fail(_state):
            raise RuntimeError("boom")

        jobs.run_job(job_id, fail, {})
        job = jobs.get_job(job_id)

        self.assertEqual(job["status"], "failed")
        self.assertIn("RuntimeError: boom", job["error"])

    def test_job_cleanup_removes_expired_jobs(self):
        now = time.time()
        with jobs._lock:
            jobs.JOBS["old"] = {
                "job_id": "old",
                "status": "succeeded",
                "result": {},
                "error": None,
                "created_at": now - jobs.JOB_TTL_SECONDS - 10,
                "updated_at": now - jobs.JOB_TTL_SECONDS - 10,
            }

        jobs.create_job({})

        self.assertIsNone(jobs.get_job("old"))


if __name__ == "__main__":
    unittest.main()
