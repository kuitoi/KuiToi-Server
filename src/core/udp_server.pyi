# Developed by KuiToi Dev
# File core.udp_server.py
# Written by: SantaSpeen
# Core version: 0.4.5
# Licence: FPA
# (c) kuitoi.su 2023
import asyncio
from asyncio import DatagramTransport
from typing import Tuple, List

from core import utils
from core.core import Core


class UDPServer(asyncio.DatagramTransport):
    transport: DatagramTransport = None

    def __init__(self, core: Core, host=None, port=None, transport=None):
        self.log = utils.get_logger("UDPServer")
        self.loop = asyncio.get_event_loop()
        self._core = core
        self.host = host
        self.port = port
        self.run = False
        # self.transport: DatagramTransport = None
    def connection_made(self, transport: DatagramTransport): ...
    async def handle_datagram(self, data: bytes, addr: Tuple[str, int]):
    def datagram_received(self, data: bytes, addr: Tuple[str, int]): ...
    async def _print_pps(self) -> None: ...
    async def _start(self) -> None: ...
    async def _stop(self) -> None: ...