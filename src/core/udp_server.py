# Developed by KuiToi Dev
# File core.udp_server.py
# Written by: SantaSpeen
# Core version: 0.4.5
# Licence: FPA
# (c) kuitoi.su 2024
import asyncio
import json

from core import utils


# noinspection PyProtectedMember
class UDPServer(asyncio.DatagramTransport):
    transport = None

    def __init__(self, core, host=None, port=None):
        super().__init__()
        self.log = utils.get_logger("UDPServer")
        self.loop = asyncio.get_event_loop()
        self._core = core
        self.host = host
        self.port = port
        self.run = False

    def connection_made(self, *args, **kwargs): ...
    def pause_writing(self, *args, **kwargs): ...
    def resume_writing(self, *args, **kwargs): ...

    async def handle_datagram(self, data, addr):
        try:
            cid = data[0] - 1
            code = data[2:3].decode()
            data = data[2:].decode()

            client = self._core.get_client(cid=cid)
            if client:
                if not client.alive:
                    self.log.debug(f"{client.nick}:{cid} still sending UDP data: {data}")
                match code:
                    case "p":  # Ping packet
                        ev.call_event("onSentPing")
                        self.transport.sendto(b"p", addr)
                    case "Z":  # Position packet
                        if client._udp_sock != (self.transport, addr):
                            client._udp_sock = (self.transport, addr)
                            self.log.debug(f"Set UDP Sock for CID: {cid}")
                        ev.call_event("onChangePosition", data=data)
                        sub = data.find("{", 1)
                        last_pos = data[sub:]
                        try:
                            _, car_id = client._get_cid_vid(data)
                            if client._cars[car_id]:
                                last_pos = json.loads(last_pos)
                                client._last_position = last_pos
                                client._cars[car_id]['pos'] = last_pos
                        except Exception as e:
                            self.log.warning(f"Cannot parse position packet: {e}")
                            self.log.debug(f"data: '{data}', sup: {sub}")
                            self.log.debug(f"last_pos ({type(last_pos)}): {last_pos}")
                        await client._send(data, to_all=True, to_self=False, to_udp=True)
                    case "X":
                        await client._send(data, to_all=True, to_self=False, to_udp=True)
                    case _:
                        self.log.warning(f"UDP [{cid}] Unknown code: {code}; {data}")
            else:
                self.log.debug(f"[{cid}] Client not found.")

        except Exception as e:
            self.log.error(f"Error handle_datagram: {e}")

    def datagram_received(self, *args, **kwargs):
        self.loop.create_task(self.handle_datagram(*args, **kwargs))

    def connection_lost(self, exc):
        if exc is not None and exc != KeyboardInterrupt:
            self.log.debug(f'Connection raised: {exc}')
        self.log.debug(f'Disconnected.')

    def error_received(self, exc):
        self.log.debug(f'error_received: {exc}')
        self.log.exception(exc)
        self.connection_lost(exc)
        self.transport.close()

    async def _start(self):
        self.log.debug("Starting UDP server.")
        while self._core.run:
            try:

                await asyncio.sleep(0.2)

                d = UDPServer
                self.transport, p = await self.loop.create_datagram_endpoint(
                    lambda: d(self._core),
                    local_addr=(self.host, self.port)
                )
                d.transport = self.transport

                self.log.debug(f"UDP server started on {self.transport.get_extra_info('sockname')}")

                self.run = True
                while not self.transport.is_closing():
                    await asyncio.sleep(0.2)

            except OSError as e:
                # self.run = False
                # self.Core.run = False
                self.log.error(f"Cannot bind port or other error: {e}")
            except Exception as e:
                self.log.error(f"Error: {e}")
                self.log.exception(e)

    def _stop(self):
        self.log.debug("Stopping UDP server")
        if self.transport:
            self.transport.close()
