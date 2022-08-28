import dataclasses
import threading
import typing


@dataclasses.dataclass
class SubsystemState:
    name: str
    ready: bool
    start_func: typing.Callable[["SubsystemState"], None]


class SubsystemManager:
    def __init__(self):
        self._threads: typing.List[threading.Thread] = []
        self._systems: typing.List[SubsystemState] = [
        ]

    # Be a singleton FastAPI dependency
    def __call__(self):
        return self

    def launch(self):
        for system in self._systems:
            t = threading.Thread(target=system.start_func, args=(system,), daemon=True)
            t.start()
            self._threads.append(t)

    def ready(self) -> typing.Dict[str, bool]:
        return {system.name: system.ready for system in self._systems}


manager = SubsystemManager()
