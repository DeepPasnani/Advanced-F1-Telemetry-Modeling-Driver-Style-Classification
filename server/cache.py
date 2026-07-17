"""
In-memory job store with TTL-based eviction.
"""

import uuid
import time
from typing import Dict, Any, Optional
from threading import Lock


class JobStore:
    def __init__(self, ttl_minutes: int = 30):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self._ttl_seconds = ttl_minutes * 60

    def create_job(self) -> str:
        job_id = str(uuid.uuid4())
        with self._lock:
            self._store[job_id] = {
                "status": "queued",
                "progress": 0,
                "step": "Initializing...",
                "result": None,
                "error": None,
                "created_at": time.time(),
                "updated_at": time.time()
            }
        return job_id

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            job = self._store.get(job_id)
            if job and time.time() - job["created_at"] > self._ttl_seconds:
                del self._store[job_id]
                return None
            return job

    def update_job(self, job_id: str, status: str, progress: int, step: str, 
                   result: Any = None, error: str = None) -> None:
        with self._lock:
            if job_id in self._store:
                self._store[job_id]["status"] = status
                self._store[job_id]["progress"] = progress
                self._store[job_id]["step"] = step
                self._store[job_id]["updated_at"] = time.time()
                if result is not None:
                    self._store[job_id]["result"] = result
                if error is not None:
                    self._store[job_id]["error"] = error

    def set_result(self, job_id: str, result: Any) -> None:
        with self._lock:
            if job_id in self._store:
                self._store[job_id]["result"] = result
                self._store[job_id]["status"] = "done"
                self._store[job_id]["progress"] = 100
                self._store[job_id]["step"] = "Complete"
                self._store[job_id]["updated_at"] = time.time()

    def set_error(self, job_id: str, error: str) -> None:
        with self._lock:
            if job_id in self._store:
                self._store[job_id]["status"] = "error"
                self._store[job_id]["error"] = error
                self._store[job_id]["step"] = "Error"
                self._store[job_id]["updated_at"] = time.time()

    def cleanup_expired(self) -> None:
        current_time = time.time()
        with self._lock:
            expired = [
                job_id for job_id, job in self._store.items()
                if current_time - job["created_at"] > self._ttl_seconds
            ]
            for job_id in expired:
                del self._store[job_id]


job_store = JobStore()