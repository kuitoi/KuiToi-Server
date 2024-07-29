# Developed by KuiToi Dev
# File core.tcp_server.pyi
# Written by: SantaSpeen
# Core version: 0.4.8
# Licence: FPA
# (c) kuitoi.su 2023
import asyncio
from asyncio import StreamWriter, StreamReader
from typing import Tuple

from core import utils, Core
from core.Client import Client
from modules import RateLimiter


class TCPServer:
    def __init__(self, core: Core, host, port):
        self.server = await asyncio.start_server(self.handle_client, "", 0, backlog=int(config.Game["players"] * 2.3))
        self.log = utils.get_logger("TCPServer")
        self.loop = asyncio.get_event_loop()
        self.Core = core
        self.host = host
        self.port = port
        self._connections = set()
        self.run = False
        self.rl = RateLimiter(50, 10, 15)

    async def auth_client(self, reader: StreamReader, writer: StreamWriter) -> Tuple[bool, Client]: ...
    async def set_down_rw(self, reader: StreamReader, writer: StreamWriter) -> bool: ...
    async def handle_code(self, code: str, reader: StreamReader, writer: StreamWriter) -> Tuple[bool, Client]: ...
    async def handle_client(self, reader: StreamReader, writer: StreamWriter) -> None: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...

