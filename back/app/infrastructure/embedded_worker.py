"""Lifecycle adapter for running the existing outbox worker in one web instance."""

from threading import Event, Thread

from app.worker import run_worker


class EmbeddedEmailWorker:
    def __init__(self) -> None:
        self._stop = Event()
        self._thread = Thread(
            target=run_worker, args=(self._stop,), name="foodify-email-outbox", daemon=True
        )

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join()
