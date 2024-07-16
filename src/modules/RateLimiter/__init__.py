import asyncio
import textwrap
from collections import defaultdict, deque
from datetime import datetime, timedelta

from core import utils


class RateLimiter:
    def __init__(self, max_calls: int, period: float, ban_time: float):
        self.log = utils.get_logger("RateLimiter")
        self.max_calls = max_calls
        self.period = timedelta(seconds=period)
        self.ban_time = timedelta(seconds=ban_time)
        self._calls = defaultdict(deque)
        self._banned_until = defaultdict(lambda: datetime.min)
        self._notified = {}

    def parse_console(self, x):
        help_msg = textwrap.dedent("""\
        
        RateLimiter menu:
            info - list banned ip's
            ban - put ip in banlist
            unban - force remove ip from banlist
            help - print that message""")
        _banned_ips = [i for i in self._banned_until if self.is_banned(i, False)]
        if len(x) > 0:
            match x[0]:
                case "info":
                    self.log.info(f"Trigger {self.max_calls}req/{self.period}. IP will be banned for {self.ban_time}.")
                    if len(_banned_ips) == 0:
                        return "No one ip in banlist."
                    else:
                        _msg = f"Banned ip{'' if len(_banned_ips) == 1 else 's'}: "
                        for ip in _banned_ips:
                            _msg += f"{ip}; "
                        return _msg
                case "unban":
                    if len(x) == 2:
                        ip = x[1]
                        if ip in _banned_ips:
                            self._notified[ip] = False
                            self._calls[ip].clear()
                            self._banned_until[ip] = datetime.now()
                            return f"{ip} removed from banlist."
                        return f"{ip} not banned."
                    else:
                        return 'rl unban <IP>'
                case "ban":
                    if len(x) == 3:
                        ip = x[1]
                        sec = x[2]
                        if not sec.isdigit():
                            return f"{sec!r} is not digit."
                        self._notified[ip] = False
                        self._calls[ip].clear()
                        self._banned_until[ip] = datetime.now() + timedelta(seconds=int(sec))
                        return f"{ip} banned until {self._banned_until[ip]}"
                    else:
                        return 'rl ban <IP> <sec>'
                case _:
                    return help_msg
        else:
            return help_msg

    async def notify(self, ip, writer):
        if not self._notified[ip]:
            self._notified[ip] = True
            self.log.warning(f"{ip} banned until {self._banned_until[ip]}.")
            try:
                writer.write(b'\x0b\x00\x00\x00Eip banned.')
                await writer.drain()
            except Exception:
                pass

    def is_banned(self, ip: str, _add_call=True) -> bool:
        now = datetime.now()
        if now < self._banned_until[ip]:
            return True

        if _add_call:
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
    rate_limiter.parse_console(["info"])


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
