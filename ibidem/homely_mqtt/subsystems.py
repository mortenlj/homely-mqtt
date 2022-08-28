import dataclasses
import threading
import typing


@dataclasses.dataclass
class SubsystemState:
    name: str
    start_func: typing.Callable[["SubsystemState"], None]
    ready: bool = False


class SubsystemManager:
    def __init__(self):
        self._threads: typing.List[threading.Thread] = []
        self._systems: typing.List[SubsystemState] = []

    # Be a singleton FastAPI dependency
    def __call__(self):
        return self

    def register_subsystem(self, name, func):
        self._systems.append(SubsystemState(name, func))

    def launch(self):
        for system in self._systems:
            t = threading.Thread(target=system.start_func, args=(system,), daemon=True)
            t.start()
            self._threads.append(t)

    def ready(self) -> typing.Dict[str, bool]:
        return {system.name: system.ready for system in self._systems}


manager = SubsystemManager()
