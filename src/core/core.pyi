# Developed by KuiToi Dev
# File core.core.pyi
# Written by: SantaSpeen
# Core version: 0.4.5
# Licence: FPA
# (c) kuitoi.su 2023
import asyncio
import time
from threading import Thread
from typing import Callable, List, Dict

from core import utils
from .Client import Client
from .tcp_server import TCPServer
from .udp_server import UDPServer


class Core:
    def __init__(self):
        self.target_tps = 50
        self.tick_counter = 0
        self.tps = 10
        self.start_time = time.monotonic()
        self.log = utils.get_logger("core")
        self.loop = asyncio.get_event_loop()
        self.run = False
        self.direct = False
        self.clients: List[Client | None]= []
        self.clients_by_id: Dict[{int: Client}]= {}
        self.clients_by_nick: Dict[{str: Client}] = {}
        self.clients_counter: int = 0
        self.mods_dir: str = "mods"
        self.mods_list: list = []
        self.server_ip = config.Server["server_ip"]
        self.server_port = config.Server["server_port"]
        self.tcp = TCPServer
        self.udp = UDPServer
        self.web_thread: Thread = None
        self.web_stop: Callable = lambda: None
        self.lock_upload = False
        self.client_major_version = "2.0"
        self.BeamMP_version = "3.4.1"
    def get_client(self, cid=None, nick=None) -> Client | None: ...
    async def insert_client(self, client: Client) -> None: ...
    def create_client(self, *args, **kwargs) -> Client: ...
    def get_clients_list(self, need_cid=False) -> str: ...
    async def _check_alive(self) -> None: ...
    async def _send_online(self) -> None: ...
    async def _useful_ticks(self, _) -> None: ...
    async def __gracefully_kick(self): ...
    async def __gracefully_remove(self): ...
    def _tick(self) -> None: ...
    async def heartbeat(self, test=False) -> None: ...
    async def kick_cmd(self, args: list) -> None | str: ...
    async def main(self) -> None: ...
    def start(self) -> None: ...
    async def stop(self) -> None: ...
