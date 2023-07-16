# Developed by KuiToi Dev
# File core.tcp_server.py
# Written by: SantaSpeen
# Core version: 0.2.3
# Licence: FPA
# (c) kuitoi.su 2023
import asyncio
from asyncio import StreamReader, StreamWriter
from logging import Logger
from typing import Tuple

from core import Core, utils


class Client:

    def __init__(self, reader: StreamReader, writer: StreamWriter, core: Core) -> "Client":
        self.__reader = reader
        self.__writer = writer
        self._down_rw: Tuple[StreamReader, StreamWriter] | Tuple[None, None] = (None, None)
        self._log = utils.get_logger("client(id: )")
        self._addr = writer.get_extra_info("sockname")
        self._loop = asyncio.get_event_loop()
        self.__Core = core
        self._cid: int = -1
        self._key: str = None
        self.nick: str = None
        self.roles: str = None
        self._guest = True
        self.__alive = True
        self._ready = False
        self._cars = []
    @property
    def _writer(self) -> StreamWriter: ...
    @property
    def log(self) -> Logger: ...
    @property
    def addr(self) -> Tuple[str, int]: ...
    @property
    def cid(self) -> int: ...
    @property
    def key(self) -> str: ...
    @property
    def guest(self) -> bool: ...
    @property
    def ready(self) -> bool: ...
    @property
    def cars(self) -> list: ...
    def is_disconnected(self) -> bool: ...
    async def kick(self, reason: str) -> None: ...
    async def _send(self, data: bytes | str, to_all: bool = False, to_self: bool = True, to_udp: bool = False, writer: StreamWriter = None) -> None: ...
    async def _sync_resources(self) -> None: ...
    async def _recv(self) -> bytes: ...
    async def _split_load(self, start: int, end: int, d_sock: bool, filename: str) -> None: ...
    async def _looper(self) -> None: ...
    def _update_logger(self) -> None: ...
    async def _remove_me(self) -> None: ...
