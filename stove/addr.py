import random
import socket


_MIN_DYNAMIC_PRIVATE_PORT = 49152
_MAX_DYNAMIC_PRIVATE_PORT = 65535


def rand_dynamic_private_port() -> int:
    return random.randint(_MIN_DYNAMIC_PRIVATE_PORT, _MAX_DYNAMIC_PRIVATE_PORT)


class AddrManager:

    def __init__(self, host: str) -> None:
        self._host = host
        self._current_port = None

        self.get_unused_port()

    @property
    def host(self) -> None:
        return self._host

    @property
    def current_port(self) -> None:
        return self._current_port

    def get_unused_port(self) -> int:
        new_port = rand_dynamic_private_port()
        with socket.socket() as sock:
            res = sock.connect_ex((self.host, new_port))
            if res:
                self._current_port = new_port
                return new_port
            return self.get_unused_port()
