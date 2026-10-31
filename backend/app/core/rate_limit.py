"""Tiny in-memory sliding-window rate limiter, exposed as a FastAPI dependency."""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from ..config import settings


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_s: int = 60):
        self.limit, self.window = limit, window_s
        self.hits: dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self.lock:
            q = self.hits[key]
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.limit:
                retry = int(self.window - (now - q[0])) + 1
                raise HTTPException(429, f"Rate limit exceeded. Try again in {retry}s.",
                                    headers={"Retry-After": str(retry)})
            q.append(now)


def make_rate_limit_dependency(limit: int | None = None):
    limiter = SlidingWindowLimiter(limit or settings.RATE_LIMIT_PER_MINUTE)

    def dependency(request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        limiter.check(client)

    return dependency
