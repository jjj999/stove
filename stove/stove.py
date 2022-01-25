from __future__ import annotations
from collections import deque
from multiprocessing import Process
import signal
import sys
import typing as t

import gileum
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from . import Literal
from .addr import AddrManager
from .router import ProxyHandler, Router
from .utils import (
    import_all_modules_from_path,
    reload_all_modules_from_path,
    search_pkgs_under,
)


Fireable_t = t.Callable[[str, int], None]


class StoveGileum(gileum.BaseGileum):

    glm_name: Literal["main", "test"] = "main"

    fireable: Fireable_t
    host: str = "localhost"
    port: int = 8000
    wrap_fireable: bool = True
    workers: int = 1
    where: str = "."
    recursive: bool = True
    watch_moved: bool = True
    watch_created: bool = True
    watch_deleted: bool = True
    watch_modified: bool = True
    watch_closed: bool = True
    timeout: int = 1
    reload_pkgs: t.List[str] = ["."]
    reload_ignores: t.Set[str] = set()


def _update_glm(glm_file: str, glm_name: str = "main") -> StoveGileum:
    gileum.load_glms_at(glm_file)
    glm = gileum.get_glm(StoveGileum, glm_name=glm_name)
    if glm.host == "localhost":
        glm.host = "127.0.0.1"
    return glm


def _wrap_default_fireable(fireable: Fireable_t) -> Fireable_t:
    parent_stdin = sys.stdin
    parent_stdout = sys.stdout
    parent_stderr = sys.stderr

    def wrapper(host: str, port: int) -> None:

        sys.stdin = parent_stdin
        sys.stdout = parent_stdout
        sys.stderr = parent_stderr

        def server_close(sigalnum, frame):
            sys.exit()

        signal.signal(signal.SIGINT, server_close)
        signal.signal(signal.SIGTERM, server_close)

        fireable(host, port)

    wrapper.__dict__ = fireable.__dict__
    return wrapper


def _serialize_reload_pkgs(
    pkgs: t.List[str],
    ignores: t.Set[str],
) -> t.List[str]:
    results = pkgs.copy()
    for pkg in pkgs:
        results.extend(search_pkgs_under(pkg, ignores=ignores))
    return results


class FileWatcher(FileSystemEventHandler):

    def __init__(
        self,
        glm_first: StoveGileum,
        glm_file: str,
        glm_name: str = "main",
    ) -> None:
        super().__init__()

        self._glm_file = glm_file
        self._glm_name = glm_name
        self._router = Router((glm_first.host, glm_first.port), ProxyHandler)
        self._addrman = AddrManager(glm_first.host)
        self._ps_queue: t.Deque[Process] = deque(maxlen=glm_first.workers)

        if glm_first.watch_moved:
            self.on_moved = self._reload
        if glm_first.watch_created:
            self.on_created = self._reload
        if glm_first.watch_deleted:
            self.on_deleted = self._reload
        if glm_first.watch_modified:
            self.on_modified = self._reload
        if glm_first.watch_closed:
            self.on_closed = self._reload

        for pkg in _serialize_reload_pkgs(
            glm_first.reload_pkgs,
            glm_first.reload_ignores,
        ):
            import_all_modules_from_path(pkg)
        self._launch()

    def _launch(self) -> None:
        glm = _update_glm(self._glm_file, self._glm_name)
        for pkg in _serialize_reload_pkgs(
            glm.reload_pkgs,
            glm.reload_ignores
        ):
            reload_all_modules_from_path(pkg)

        if glm.wrap_fireable:
            glm.fireable = _wrap_default_fireable(glm.fireable)

        for _ in range(glm.workers):
            port = self._addrman.get_unused_port()
            if len(self._ps_queue):
                ps = self._ps_queue.popleft()
                ps.terminate()
                ps.join(glm.timeout)
                if ps.is_alive():
                    ps.kill()
                    ps.join()
                ps.close()

            ps = Process(target=glm.fireable, args=(glm.host, port))
            ps.start()
            self._ps_queue.append(ps)
            self._router.update_port(port)

    def _reload(self, event) -> None:
        self._launch()

    @property
    def router(self) -> Router:
        return self._router


class Stove:

    def __init__(self, glm_file: str, glm_name: str = "main") -> None:
        glm = _update_glm(glm_file, glm_name)
        self._watcher = FileWatcher(glm, glm_file, glm_name)
        self._observer = Observer(timeout=glm.timeout)
        self._observer.schedule(
            self._watcher,
            glm.where,
            recursive=True,
        )

    def start_forever(self) -> None:
        self._observer.start()

        try:
            self._watcher.router.serve_forever()
        finally:
            self._watcher.router.server_close()
            self._observer.stop()
            self._observer.join()


def fire_stove(glm_file: str, glm_name: str = "main") -> None:
    stove = Stove(glm_file, glm_name=glm_name)
    stove.start_forever()
