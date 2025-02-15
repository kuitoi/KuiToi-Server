# Developed by KuiToi Dev
# File core.udp_server
# Written by: SantaSpeen
# Core version: 0.4.7
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

    async def handle_datagram(self, packet, addr):
        try:
            cid = packet[0] - 1
            client = self._core.get_client(cid=cid)
            if client:
                if not client.alive:
                    client.log.debug(f"Still sending UDP data: {packet}")
                if client._udp_sock != (self.transport, addr):
                    client._udp_sock = (self.transport, addr)
                    self.log.debug(f"Set UDP Sock for CID: {cid}")
                await client._udp_put(packet)
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
                self.run = False
                self._core.run = False
                self.log.error(f"Cannot bind port or other error: {e}")
            except Exception as e:
                self.log.error(f"Error: {e}")
                self.log.exception(e)

    def _stop(self):
        self.log.debug("Stopping UDP server")
        if self.transport:
            self.transport.close()
