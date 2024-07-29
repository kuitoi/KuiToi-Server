# Developed by KuiToi Dev
# File core.core.py
# Written by: SantaSpeen
# Version: 0.4.8
# Licence: FPA
# (c) kuitoi.su 2023
import asyncio
import math
import os
import random
import statistics
import time
from collections import deque

import aiohttp

from core import utils, __version__
from core.Client import Client
from core.tcp_server import TCPServer
from core.udp_server import UDPServer
from modules import PluginsLoader


def calc_ticks(ticks, duration):
    while ticks and ticks[0] < time.monotonic() - duration:
        ticks.popleft()
    return len(ticks) / duration


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


# noinspection PyProtectedMember
class Core:

    def __init__(self):
        self.tick_counter = 0
        self.log = utils.get_logger("core")
        self.loop = asyncio.get_event_loop()
        self.start_time = time.monotonic()
        self.run = False
        self.direct = False
        self.clients = []
        self.clients_by_id = {}
        self.clients_by_nick = {}
        self.mods_dir = "./mods"
        self.mods_list = [0, ]
        self.server_ip = config.Server["server_ip"]
        self.server_port = config.Server["server_port"]
        self.tcp = TCPServer
        self.udp = UDPServer

        self.tcp_pps = 0
        self.udp_pps = 0

        self.tps = 10
        self.target_tps = 60

        self.lock_upload = False

        self.client_major_version = "2.0"
        self.BeamMP_version = "3.4.1"  # 16.07.2024

        ev.register("_get_BeamMP_version", lambda x: tuple([int(i) for i in self.BeamMP_version.split(".")]))
        ev.register("_get_player", lambda x: self.get_client(**x['kwargs']))

    def get_client(self, cid=None, nick=None):
        if (cid, nick) == (None, None):
            return None
        if cid is not None:
            if cid == -1:
                return [i for i in self.clients if i is not None and i.synced]
            return self.clients_by_id.get(cid)
        if nick:
            return self.clients_by_nick.get(nick)

    async def insert_client(self, client):
        await asyncio.sleep(random.randint(3, 9) * 0.01)
        cid = 0
        for _client in self.clients:
            if not _client:
                break
            if _client.cid == cid:
                cid += 1
            else:
                break
        await asyncio.sleep(random.randint(3, 9) * 0.01)
        if not self.clients[cid]:
            client._cid = cid
            self.clients_by_nick.update({client.nick: client})
            self.log.debug(f"Inserting client: {client.nick}:{client.cid}")
            self.clients_by_id.update({client.cid: client})
            self.clients[client.cid] = client
            # noinspection PyProtectedMember
            client._update_logger()
            return
        await self.insert_client(client)

    def create_client(self, *args, **kwargs):
        self.log.debug(f"Create client")
        client = Client(core=self, *args, **kwargs)
        return client

    def get_clients_list(self, need_cid=False):
        out = ""
        for client in self.clients:
            if not client:
                continue
            out += f"{client.nick}"
            if need_cid:
                out += f":{client.cid}"
            out += ","
        if out:
            out = out[:-1]
        return out

    async def _check_alive(self, _):
        # self.log.debug("alive checker.")
        try:
            for client in self.clients:
                if not client:
                    continue
                if not client.ready:
                    client.is_disconnected()
                    continue
                if not client.alive:
                    await client.kick("You are not alive!")
        except Exception as e:
            self.log.error("Error in _check_alive.")
            self.log.exception(e)

    async def _send_online(self, _):
        try:
            for client in self.clients:
                ca = f"Ss{len(self.clients_by_id)}/{config.Game['players']}:{self.get_clients_list()}"
                if not client or not client.alive:
                    continue
                await client._send(ca)
        except Exception as e:
            self.log.error("Error in _send_online.")
            self.log.exception(e)

    async def __gracefully_kick(self):
        for client in self.clients:
            if not client:
                continue
            await client.kick("Server shutdown!")

    async def __gracefully_remove(self):
        for client in self.clients:
            if not client:
                continue
            await client._remove_me()

    # noinspection SpellCheckingInspection,PyPep8Naming
    async def heartbeat(self, test=False):
        try:
            self.log.debug("Starting heartbeat.")
            if config.Auth["private"] or self.direct:
                if test:
                    self.log.info(i18n.core_direct_mode)
                self.direct = True
                return

            BEAM_backend = ["backend.beammp.com", "backup1.beammp.com", "backup2.beammp.com"]
            _map = config.Game['map'] if "/" in config.Game['map'] else f"/levels/{config.Game['map']}/info.json"
            tags = config.Server['tags'].replace(", ", ";").replace(",", ";")
            self.log.debug(f"[heartbeat] {_map=}")
            self.log.debug(f"[heartbeat] {tags=}")
            if tags and tags[-1:] != ";":
                tags += ";"
            modlist = "".join(f"/{os.path.basename(mod['path'])};" for mod in self.mods_list[1:])
            modstotalsize = self.mods_list[0]
            modstotal = len(self.mods_list) - 1
            self.log.debug(f"[heartbeat] {modlist=}")
            self.log.debug(f"[heartbeat] {modstotalsize=}")
            self.log.debug(f"[heartbeat] {modstotal=}")
            while self.run:
                playerslist = "".join(f"{client.nick};" for client in self.clients if client and client.alive)
                data = {
                    "uuid": config.Auth["key"],
                    "players": len(self.clients_by_id),
                    "maxplayers": config.Game["players"],
                    "port": config.Server["server_port"],
                    "map": _map,
                    "private": config.Auth['private'],
                    "version": self.BeamMP_version,
                    "clientversion": self.client_major_version,
                    "name": config.Server["name"],
                    "tags": tags,
                    "guests": not config.Auth["private"],
                    "modlist": modlist,
                    "modstotalsize": modstotalsize,
                    "modstotal": modstotal,
                    "playerslist": playerslist,
                    "desc": config.Server['description'],
                    "pass": False
                }

                body = {}
                for server_url in BEAM_backend:
                    url = "https://" + server_url + "/heartbeat"
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.post(url, data=data, headers={"api-v": "2"}) as response:
                                code = response.status
                                # text = await response.text()
                                # self.log.debug(f"[HB] res={text}")
                                body = await response.json()
                        break
                    except Exception as e:
                        self.log.debug(f"Auth: Error `{e}` while auth with `{server_url}`")
                        continue

                if body:
                    if not (body.get("status") is not None and
                            body.get("code") is not None and
                            body.get("msg") is not None):
                        self.log.error(i18n.core_auth_server_error)
                        return

                    status = body.get("status")
                    msg = body.get("msg")
                    if status == "2000":
                        if test:
                            self.log.debug(f"Authenticated! {msg}")
                    elif status == "200":
                        if test:
                            self.log.debug(f"Resumed authenticated session. {msg}")
                    else:
                        self.log.debug(f"Auth: data {data}")
                        self.log.debug(f"Auth: code {code}, body {body}")

                        self.log.error(i18n.core_auth_server_refused.format(
                            msg or i18n.core_auth_server_refused_no_reason))
                        self.log.info(i18n.core_auth_server_refused_direct_node)
                        self.direct = True
                else:
                    self.direct = True
                    if test:
                        self.log.error(i18n.core_auth_server_no_response)
                        self.log.info(i18n.core_auth_server_refused_direct_node)
                    # if not config.Auth['private']:
                    #     raise KeyboardInterrupt

                if test:
                    return bool(body)

                await asyncio.sleep(15)
        except Exception as e:
            self.log.error(f"Error in heartbeat: {e}")

    async def kick_cmd(self, args):
        if not len(args) > 0:
            return "\nUsage: kick <nick>|:<id> [reason]\nExamples:\n\tkick admin bad boy\n\tkick :0 bad boy"
        reason = "kicked by console."
        if len(args) > 1:
            reason = " ".join(args[1:])
        cl = args[0]
        if cl.startswith(":") and cl[1:].isdigit():
            client = self.get_client(cid=int(cl[1:]))
        else:
            client = self.get_client(nick=cl)
        if client:
            await client.kick(reason)
        else:
            return "Client not found."

    async def _useful_ticks(self, _):
        tasks = []
        self.tick_counter += 1
        events = {
            0.5: "serverTick_0.5s",
            1: "serverTick_1s",
            2: "serverTick_2s",
            3: "serverTick_3s",
            4: "serverTick_4s",
            5: "serverTick_5s",
            10: "serverTick_10s",
            30: "serverTick_30s",
            60: "serverTick_60s"
        }
        for interval in sorted(events.keys(), reverse=True):
            if self.tick_counter % (interval * self.target_tps) == 0:
                ev.call_event(events[interval])
                tasks.append(ev.call_async_event(events[interval]))
        await asyncio.gather(*tasks)
        if self.tick_counter == (60 * self.target_tps):
            self.tick_counter = 0

    async def _tick(self):
        try:
            ticks = 0
            target_tps = self.target_tps
            last_tick_time = time.monotonic()
            ev.register("serverTick", self._useful_ticks)
            ticks_2s = deque(maxlen=2 * int(target_tps) + 1)
            ticks_5s = deque(maxlen=5 * int(target_tps) + 1)
            ticks_30s = deque(maxlen=30 * int(target_tps) + 1)
            ticks_60s = deque(maxlen=60 * int(target_tps) + 1)
            console.add_command("tps", lambda _: f"{calc_ticks(ticks_2s, 2):.2f}TPS; For last 5s, 30s, 60s: "
                                                 f"{calc_ticks(ticks_5s, 5):.2f}, "
                                                 f"{calc_ticks(ticks_30s, 30):.2f}, "
                                                 f"{calc_ticks(ticks_60s, 60):.2f}.",
                                None, "Print TPS", {"tps": None})
            _add_to_sleep = deque([0.0, 0.0, 0.0,], maxlen=3 * int(target_tps))
            _t0 = []

            self.log.debug("tick system started")
            while self.run:
                target_interval = 1 / self.target_tps
                start_time = time.monotonic()

                ev.call_event("serverTick")
                await ev.call_async_event("serverTick")

                # Calculate the time taken for this tick
                end_time = time.monotonic()
                tick_duration = end_time - start_time
                _t0.append(tick_duration)

                # Calculate the time to sleep to maintain target TPS
                sleep_time = target_interval - tick_duration - statistics.fmean(_add_to_sleep)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

                # Update tick count and time
                ticks += 1
                current_time = time.monotonic()
                ticks_2s.append(current_time)
                ticks_5s.append(current_time)
                ticks_30s.append(current_time)
                ticks_60s.append(current_time)

                # Calculate TPS
                elapsed_time = current_time - last_tick_time
                if elapsed_time >= 1:
                    self.tps = ticks / elapsed_time
                    # if self.tps < 5:
                    #     self.log.warning(f"Low TPS: {self.tps:.2f}")
                    # Reset for next calculation
                    _t0s = max(_t0), min(_t0), statistics.fmean(_t0)
                    _tw = max(_add_to_sleep), min(_add_to_sleep), statistics.fmean(_add_to_sleep)
                    self.log.debug(f"[{'OK' if sleep_time > 0 else "CHECK"}] TPS: {self.tps:.2f}; Tt={_t0s}; Ts={sleep_time}; Tw={_tw}")
                    _t0 = []
                    last_tick_time = current_time
                    ticks = 0

                _add_to_sleep.append(time.monotonic() - start_time - sleep_time)
            self.log.debug("tick system stopped")
        except Exception as e:
            self.log.exception(e)

    async def main(self):
        self.tcp = self.tcp(self, self.server_ip, self.server_port)
        self.udp = self.udp(self, self.server_ip, self.server_port)
        console.add_command(
            "list",
            lambda x: f"Players list: {self.get_clients_list(True)}"
        )
        console.add_command("kick", self.kick_cmd)

        pl_dir = "plugins"
        self.log.debug("Initializing PluginsLoaders...")
        if not os.path.exists(pl_dir):
            os.mkdir(pl_dir)
        pl = PluginsLoader(pl_dir)
        await pl.load()
        if config.Options['use_lua']:
            from modules.PluginsLoader.lua_plugins_loader import LuaPluginsLoader
            lpl = LuaPluginsLoader(pl_dir)
            lpl.load()

        try:
            # Mods handler
            self.log.debug("Listing mods..")
            if not os.path.exists(self.mods_dir):
                os.mkdir(self.mods_dir)
            for file in os.listdir(self.mods_dir):
                path = os.path.join(self.mods_dir, file).replace("\\", "/")
                if os.path.isfile(path) and path.endswith(".zip"):
                    size = os.path.getsize(path)
                    self.mods_list.append({"path": path, "size": size})
                    self.mods_list[0] += size
            self.log.debug(f"mods_list: {self.mods_list}")
            len_mods = len(self.mods_list) - 1
            if len_mods > 0:
                self.log.info(i18n.core_mods_loaded.format(len_mods, round(self.mods_list[0] / MB, 2)))
            self.log.info(i18n.init_ok)

            await self.heartbeat(True)
            for i in range(int(config.Game["players"] * 4)):  # * 4 For down sock and buffer.
                self.clients.append(None)
            tasks = []
            ev.register("serverTick_1s", self._check_alive)
            ev.register("serverTick_1s", self._send_online)
            # ev.register("serverTick_5s", self.heartbeat)
            f_tasks = [self.tcp.start, self.udp._start, console.start, self._tick, self.heartbeat]
            if config.RCON['enabled']:
                console.rcon.version = f"KuiToi {__version__}"
                rcon = console.rcon(config.RCON['password'], config.RCON['server_ip'], config.RCON['server_port'])
                f_tasks.append(rcon.start)
            for task in f_tasks:
                tasks.append(asyncio.create_task(task()))
            t = asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

            await ev.call_async_event("_plugins_start")

            self.run = True
            self.log.info(i18n.start)
            ev.call_event("onServerStarted")
            await ev.call_async_event("onServerStarted")
            await t  # Wait end.
        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.log.error(f"Exception in main:")
            self.log.exception(e)
        finally:
            await self.stop()

    def start(self):
        asyncio.run(self.main())

    async def stop(self):
        self.run = False
        ev.call_lua_event("onShutdown")
        await ev.call_async_event("onServerStopped")
        ev.call_event("onServerStopped")
        try:
            await self.__gracefully_kick()
            await self.__gracefully_remove()
            self.tcp.stop()
            self.udp._stop()
            await ev.call_async_event("_plugins_unload")
            if config.Options['use_lua']:
                await ev.call_async_event("_lua_plugins_unload")
            self.run = False
            total_time = time.monotonic() - self.start_time
            hours = int(total_time // 3600)
            minutes = int((total_time % 3600) // 60)
            seconds = math.ceil(total_time % 60)
            t = f"{'' if not hours else f'{hours} hours, '}{'' if not hours else f'{minutes} min., '}{seconds} sec."
            self.log.info(f"Working time: {t}")
            self.log.info(i18n.stop)
        except Exception as e:
            self.log.error("Error while stopping server:")
            self.log.exception(e)
