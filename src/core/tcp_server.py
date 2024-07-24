# Developed by KuiToi Dev
# File core.tcp_server.py
# Written by: SantaSpeen
# Core version: 0.4.5
# Licence: FPA
# (c) kuitoi.su 2023
import asyncio
import traceback

import aiohttp

from core import utils
from modules import RateLimiter


# noinspection PyProtectedMember
class TCPServer:
    def __init__(self, core, host, port):
        self.log = utils.get_logger("TCPServer")
        self.loop = asyncio.get_event_loop()
        self.Core = core
        self.host = host
        self.port = port
        self.run = False
        self.rl = RateLimiter(50, 10, 300)
        console.add_command("rl", self.rl.parse_console, None, "RateLimiter menu",
                            {"rl": {"info": None, "unban": None, "ban": None, "help": None}})

    async def auth_client(self, reader, writer):
        client = self.Core.create_client(reader, writer)
        self.log.info(i18n.core_identifying_connection)
        data = await client._recv(True)
        self.log.debug(f"Version: {data}")
        if data.decode("utf-8") != f"VC{self.Core.client_major_version}":
            await client.kick(i18n.core_player_kick_outdated)
            return False, client
        else:
            # await client._send(b"S")  # Accepted client version
            await client._send(b"A")  # Accepted client version

        data = await client._recv(True)
        self.log.debug(f"Key: {data}")
        if len(data) > 50:
            await client.kick(i18n.core_player_kick_bad_key)
            return False, client
        client._key = data.decode("utf-8")
        ev.call_event("onPlayerSentKey", player=client)
        try:
            async with aiohttp.ClientSession() as session:
                url = 'https://auth.beammp.com/pkToUser'
                async with session.post(url, data={'key': client._key}) as response:
                    res = await response.json()
            self.log.debug(f"res: {res}")
            if res.get("error"):
                await client.kick(i18n.core_player_kick_invalid_key)
                return False, client
            client.nick = res["username"]
            client.roles = res["roles"]
            client._guest = res["guest"]
            client._identifiers = {k: v for s in res["identifiers"] for k, v in [s.split(':')]}
            if not client._identifiers.get("ip"):
                client._identifiers["ip"] = client._addr[0]
            # noinspection PyProtectedMember
            client._update_logger()
        except Exception as e:
            self.log.error("Auth error.")
            self.log.exception(e)
            await client.kick(i18n.core_player_kick_auth_server_fail)
            return False, client

        for _client in self.Core.clients:
            if not _client:
                continue
            if _client.nick == client.nick and _client.guest == client.guest:
                await _client.kick(i18n.core_player_kick_stale)

        allow = True
        reason = i18n.core_player_kick_no_allowed_default_reason

        lua_data = ev.call_lua_event("onPlayerAuth", client.nick, client.roles, client.guest, client.identifiers)
        for data in lua_data:
            if 1 == data:
                allow = False
            elif isinstance(data, str):
                allow = False
                reason = data
        if not allow:
            await client.kick(reason)
            return False, client

        ev.call_event("onPlayerAuthenticated", player=client)
        await ev.call_async_event("onPlayerAuthenticated", player=client)
        if not client.alive:
            await client.kick("Not accepted.")
            return False, client

        if len(self.Core.clients_by_id) > config.Game["players"]:
            await client.kick(i18n.core_player_kick_server_full)
            return False, client
        else:
            await self.Core.insert_client(client)
            client.log.info(i18n.core_identifying_okay)

        return True, client

    async def set_down_rw(self, reader, writer):
        try:
            cid = (await reader.read(1))[0]
            client = self.Core.get_client(cid=cid)
            if client:
                client._down_sock = (reader, writer)
                self.log.debug(f"Client: {client.nick}:{cid} - HandleDownload!")
            else:
                writer.close()
                self.log.debug(f"Unknown client <nick>:{cid} - HandleDownload")
        finally:
            return

    async def handle_code(self, code, reader, writer):
        match code:
            case "C":
                result, client = await self.auth_client(reader, writer)
                if result:
                    await client._looper()
                return result, client
            case "D":
                await self.set_down_rw(reader, writer)
            case "P":
                writer.write(b"P")
                await writer.drain()
                writer.close()
            case _:
                self.log.error(f"Unknown code: {code}")
                self.log.info("Report about that!")
                writer.close()
        return False, None

    async def handle_client(self, reader, writer):
        while True:
            try:
                ip = writer.get_extra_info('peername')[0]
                if self.rl.is_banned(ip):
                    await self.rl.notify(ip, writer)
                    writer.close()
                    break
                data = await reader.read(1)
                if not data:
                    break
                code = data.decode()
                self.log.debug(f"Received {code!r} from {writer.get_extra_info('sockname')!r}")
                # task = asyncio.create_task(self.handle_code(code, reader, writer))
                # await asyncio.wait([task], return_when=asyncio.FIRST_EXCEPTION)
                _, cl = await self.handle_code(code, reader, writer)
                if cl:
                    await cl._remove_me()
                break
            except Exception as e:
                self.log.error("Error while handling connection...")
                self.log.exception(e)
                traceback.print_exc()
                break

    async def start(self):
        self.log.debug("Starting TCP server.")
        self.run = True
        try:
            server = await asyncio.start_server(self.handle_client, self.host, self.port,
                                                backlog=int(config.Game["players"] * 2.3))
            self.log.debug(f"TCP server started on {server.sockets[0].getsockname()!r}")
            while True:
                async with server:
                    await server.serve_forever()
        except OSError as e:
            self.log.error(i18n.core_bind_failed.format(e))
            raise e
        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.log.error(f"Error: {e}")
            raise e
        finally:
            self.run = False
            self.Core.run = False

    def stop(self):
        self.log.debug("Stopping TCP server")
