from __future__ import annotations
from collections import deque
import io
import socket
from socketserver import (
    BaseServer,
    TCPServer,
    StreamRequestHandler,
)
import typing as t

import http.server
class TargetPortNotFoundError(Exception):
    pass


class ProxyHandler(StreamRequestHandler):

    BUF_SIZE = 8192

    def __init__(
        self,
        request: socket.socket,
        client_address: t.Tuple[str, int],
        server: Router,
    ) -> None:
        self.server: Router = server
        super().__init__(request, client_address, server)

    def setup(self) -> None:
        super().setup()
        self._host = self.server.server_address[0]
        self._target_port = self.server.target_port

    @property
    def target_addr(self) -> t.Tuple[str, int]:
        return (self._host, self._target_port)

    def handle(self) -> None:
        super().handle()
        response = io.BytesIO()

        sock = socket.socket()
        sock.connect(self.target_addr)
        while True:
            chunk = self.rfile.read(self.BUF_SIZE)
            if not len(chunk):
                break
            sock.send(chunk)
            if len(chunk) < self.BUF_SIZE:
                break

        while True:
            chunk = sock.recv(self.BUF_SIZE)
            if not len(chunk):
                break
            response.write(chunk)
        sock.close()

        response.flush()
        self.request.sendall(response.getvalue())


class Router(TCPServer):

    def __init__(
        self,
        server_address: t.Tuple[str, int],
        RequestHandlerClass: t.Callable[..., ProxyHandler],
        bind_and_activate: bool = True,
    ) -> None:
        # NOTE
        #   Extending the TCPServer.__init__() such as the router
        #   can reuse the address.
        BaseServer.__init__(self, server_address, RequestHandlerClass)
        self.socket = socket.socket(self.address_family, self.socket_type)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if bind_and_activate:
            try:
                self.server_bind()
                self.server_activate()
            except:
                self.server_close()
                raise

        # NOTE
        #   IN  --> append()
        #   OUT --> popleft()
        self._rooting2: t.Deque[int] = deque()

    @property
    def target_port(self) -> t.Optional[int]:
        return self._rooting2[0] if len(self._rooting2) else None

    def update_port(self, new_port: int) -> None:
        if len(self._rooting2):
            self._rooting2.popleft()
        self._rooting2.append(new_port)

    def serve_forever(self, poll_interval: float = 0.5) -> None:
        print(f"[Stove] Hosting at {self.server_address}")
        return super().serve_forever(poll_interval=poll_interval)
