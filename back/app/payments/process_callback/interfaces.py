from typing import Protocol


class ProcessCallbackServiceInterface(Protocol):
    def execute(self, payload: dict, signature: str) -> None: ...
