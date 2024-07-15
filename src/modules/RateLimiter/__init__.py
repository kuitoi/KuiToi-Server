import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta

from core import utils


class RateLimiter:
    def __init__(self, max_calls: int, period: float, ban_time: float):
        self.log = utils.get_logger("DOSProtect")
        self.max_calls = max_calls
        self.period = timedelta(seconds=period)
        self.ban_time = timedelta(seconds=ban_time)
        self._calls = defaultdict(deque)
        self._banned_until = defaultdict(lambda: datetime.min)
        self._notified = {}

    async def notify(self, ip, writer):
        if not self._notified[ip]:
            self._notified[ip] = True
            self.log.warning(f"{ip} banned until {self._banned_until[ip]}.")
            try:
                writer.write(b'\x0b\x00\x00\x00Eip banned.')
                await writer.drain()
                writer.close()
            except Exception:
                pass

    def is_banned(self, ip: str) -> bool:
        now = datetime.now()
        if now < self._banned_until[ip]:
            return True

        now = datetime.now()
        self._calls[ip].append(now)

        while self._calls[ip] and self._calls[ip][0] + self.period < now:
            self._calls[ip].popleft()

        if len(self._calls[ip]) > self.max_calls:
            self._banned_until[ip] = now + self.ban_time
            self._calls[ip].clear()
            return True

        self._notified[ip] = False
        return False


async def handle_request(ip: str, rate_limiter: RateLimiter):
    if rate_limiter.is_banned(ip):
        print(f"Request from {ip} is banned at {datetime.now()}")
        print(f"{rate_limiter._banned_until[ip]}")
        return


async def server_simulation():
    rate_limiter = RateLimiter(max_calls=5, period=10, ban_time=30)

    # Симулируем несколько запросов от разных IP-адресов
    tasks = [
        handle_request("192.168.1.1", rate_limiter),
        handle_request("192.168.1.2", rate_limiter),
        handle_request("192.168.1.1", rate_limiter),
        handle_request("192.168.1.1", rate_limiter),
        handle_request("192.168.1.3", rate_limiter),
        handle_request("192.168.1.2", rate_limiter),
        handle_request("192.168.1.1", rate_limiter),
        handle_request("192.168.1.2", rate_limiter),
        handle_request("192.168.1.3", rate_limiter),
        handle_request("192.168.1.1", rate_limiter),
        handle_request("192.168.1.1", rate_limiter),  # This request should trigger a ban
        handle_request("192.168.1.1", rate_limiter),  # This request should trigger a ban
        handle_request("192.168.1.1", rate_limiter),  # This request should trigger a ban
    ]

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(server_simulation())
