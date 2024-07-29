# -*- coding: utf-8 -*-

# Developed by KuiToi Dev
# File modules.PluginsLoader
# Written by: SantaSpeen
# Version 1.1
# Licence: FPA
# (c) kuitoi.su 2023
import asyncio
import inspect
import os
import subprocess
import sys
import time
import types
from contextlib import contextmanager
from pathlib import Path
from threading import Thread

from core import get_logger


class KuiToi:
    _plugins_dir = ""
    _file = ""

    def __init__(self, name):
        if not name:
            raise AttributeError("KuiToi: Name is required")
        self.__log = get_logger(f"Plugin | {name}")
        self.__name = name
        self.__dir = Path(self._plugins_dir) / self.__name
        os.makedirs(self.__dir, exist_ok=True)
        self.__funcs = []
        self.register_event = self.register

    @property
    def log(self):
        return self.__log

    @property
    def name(self):
        return self.__name

    @property
    def dir(self):
        return self.__dir

    @contextmanager
    def open(self, file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
        path = self.__dir / file
        if str(self.__dir) in str(file):
            path = file
        self.log.debug(f'Trying to open "{path}" with mode "{mode}"')
        # Really need?
        # if not os.path.exists(path):
        #     with open(path, 'x'): ...
        f = None
        try:
            f = open(path, mode, buffering, encoding, errors, newline, closefd, opener)
            yield f
        except Exception as e:
            raise e
        finally:
            if f is not None:
                f.close()

    def register(self, event_name, event_func):
        self.log.debug(f"Registering event {event_name}")
        self.__funcs.append(event_func)
        ev.register(event_name, event_func)

    def _unload(self):
        for f in self.__funcs:
            console.del_command(f)
            ev.unregister(f)

    def call_event(self, event_name, *args, **kwargs):
        self.log.debug(f"Called event {event_name}")
        return ev.call_event(event_name, *args, **kwargs)

    async def call_async_event(self, event_name, *args, **kwargs):
        self.log.debug(f"Called async event {event_name}")
        return await ev.call_async_event(event_name, *args, **kwargs)

    def call_lua_event(self, event_name, *args):
        self.log.debug(f"Called lua event {event_name}")
        return ev.call_lua_event(event_name, *args)

    def get_player(self, pid=None, nick=None, cid=None):
        self.log.debug("Requests get_player")
        return ev.call_event("_get_player", cid=cid or pid, nick=nick)[0]

    def get_players(self):
        self.log.debug("Requests get_players")
        return self.get_player(-1)

    def players_counter(self):
        self.log.debug("Requests players_counter")
        return len(self.get_players())

    def is_player_connected(self, pid=None, nick=None):
        self.log.debug("Requests is_player_connected")
        if pid < 0:
            return False
        return bool(self.get_player(cid=pid, nick=nick))

    def add_command(self, key, func, man, desc, custom_completer) -> dict:
        self.log.debug("Requests add_command")
        self.__funcs.append(func)
        return console.add_command(key, func, man, desc, custom_completer)


class PluginsLoader:
    _pip_dir = str(Path("pip-packets").resolve())

    def __init__(self, plugins_dir):
        self.loop = asyncio.get_event_loop()
        self.plugins = {}
        self.plugins_tasks = []
        self.plugins_dir = plugins_dir
        self.log = get_logger("PluginsLoader")
        self.loaded = []
        ev.register("_plugins_start", self.start)
        ev.register("_plugins_unload", self.unload)
        ev.register("_plugins_get", lambda _: "Plugins: " + ", ".join(f"{i[0]}:{'on' if i[1] else 'off'}" for i in self.loaded))
        console.add_command("plugins", self._parse_console, None, "Plugins manipulations", {"plugins": {"reload", "load", "unload", "list"}})
        console.add_command("pl", lambda _: ev.call_event("_plugins_get")[0])
        sys.path.append(self._pip_dir)
        os.makedirs(self._pip_dir, exist_ok=True)
        console.add_command("install", self._pip_install)

    async def _parse_console(self, x):
        usage = 'Usage: plugin [reload <name> | load <file.py> | unload <name> | list]'
        if not x:
            return usage
        match x[0]:
            case 'reload':
                if len(x) == 2:
                    t1 = time.monotonic()
                    ok, _, file, _ = await self._unload_by_name(x[1], True)
                    if ok:
                        if await self._load_by_file(file):
                            self.plugins[x[1]]['plugin'].start()
                            return f"Plugin reloaded ({time.monotonic() - t1:.1f}sec)"
                    return "Plugin not found"
                return usage
            case 'load':
                if len(x) == 2:
                    name = await self._load_by_file(x[1])
                    if name:
                        self.plugins[name]['plugin'].start()
                        return "Plugin loaded"
                return usage
            case 'unload':
                if len(x) == 2:
                    ok, _, _, _ = await self._unload_by_name(x[1], True)
                    if ok:
                        return "Plugin unloaded"
                return usage
            case 'list':
                return ev.call_event("_plugins_get")[0]
        return usage

    def _pip_install(self, x):
        self.log.debug(f"_pip_install {x}")
        if len(x) > 0:
            try:
                subprocess.check_call(['pip', 'install', *x, '--target', self._pip_dir])
                return "Success"
            except subprocess.CalledProcessError as e:
                self.log.debug(f"error: {e}")
                return f"Failed to install packages"
        else:
            return "Invalid syntax"

    async def _load_by_file(self, file):
        file_path = os.path.join(self.plugins_dir, file)
        if os.path.isfile(file_path) and file.endswith(".py"):
            try:
                self.log.info(f"Loading plugin: {file[:-3]}")
                plugin = types.ModuleType(file[:-3])
                plugin.KuiToi = KuiToi
                plugin.KuiToi._plugins_dir = self.plugins_dir
                plugin.KuiToi._file = file
                plugin.print = print
                plugin.__file__ = file_path
                with open(f'{file_path}', 'r', encoding=config.enc) as f:
                    code = f.read()
                    exec(code, plugin.__dict__)

                ok = True
                try:
                    is_func = inspect.isfunction
                    if not is_func(plugin.load):
                        self.log.error(i18n.plugins_not_found_load)
                        ok = False
                    if not is_func(plugin.start):
                        self.log.error(i18n.plugins_not_found_start)
                        ok = False
                    if not is_func(plugin.unload):
                        self.log.error(i18n.plugins_not_found_unload)
                        ok = False
                    if type(plugin.kt) != KuiToi:
                        self.log.error(i18n.plugins_kt_invalid)
                        ok = False
                except AttributeError:
                    ok = False
                if not ok:
                    self.log.error(i18n.plugins_invalid.format(file_path))
                    return

                pl_name = plugin.kt.name
                if self.plugins.get(pl_name) is not None:
                    raise NameError(f'Having plugins with identical names is not allowed; '
                                    f'Plugin name: "{pl_name}"; Plugin file "{file_path}"')

                plugin.open = plugin.kt.open
                is_coro_func = inspect.iscoroutinefunction
                self.plugins.update(
                    {
                        pl_name: {
                            "plugin": plugin,
                            "load": {
                                "func": plugin.load,
                                "async": is_coro_func(plugin.load)
                            },
                            "start": {
                                "func": plugin.start,
                                "async": is_coro_func(plugin.start)
                            },
                            "unload": {
                                "func": plugin.unload,
                                "async": is_coro_func(plugin.unload)
                            }
                        }
                    }
                )
                if self.plugins[pl_name]["load"]['async']:
                    plugin.log.debug(f"I'm async")
                    await plugin.load()
                else:
                    plugin.log.debug(f"I'm sync")
                    th = Thread(target=plugin.load, name=f"{pl_name}.load()")
                    th.start()
                    th.join()
                self.loaded.append((pl_name, True))
                self.log.debug(f"Plugin loaded: {file}. Settings: {self.plugins[pl_name]}")
                return pl_name
            except Exception as e:
                self.loaded.append((file, False))
                self.log.error(i18n.plugins_error_loading.format(file, f"{e}"))
                self.log.exception(e)
        return False

    async def load(self):
        self.log.debug("Loading plugins...")
        for file in os.listdir(self.plugins_dir):
            await self._load_by_file(file)

    async def _unload_by_name(self, name, reload=False):
        t1 = time.monotonic()
        data = self.plugins.get(name)
        if not data:
            return False, name, None, None
        try:
            if reload:
                data['plugin'].kt._unload()
                self.loaded.remove((name, True))
                self.plugins.pop(name)
            if data['unload']['async']:
                self.log.debug(f"Unload async plugin: {name}")
                await data['unload']['func']()
            else:
                self.log.debug(f"Unload sync plugin: {name}")
                th = Thread(target=data['unload']['func'], name=f"Thread {name}")
                th.start()
                th.join()
        except Exception as e:
            self.log.exception(e)
        return True, name, data['plugin'].kt._file, time.monotonic() - t1

    async def start(self, _):
        for pl_name, pl_data in self.plugins.items():
            try:
                if pl_data['start']['async']:
                    self.log.debug(f"Start async plugin: {pl_name}")
                    t = self.loop.create_task(pl_data['start']['func']())
                    self.plugins_tasks.append(t)
                else:
                    self.log.debug(f"Start sync plugin: {pl_name}")
                    th = Thread(target=pl_data['start']['func'], name=f"Thread {pl_name}")
                    th.start()
                    self.plugins_tasks.append(th)
            except Exception as e:
                self.log.exception(e)

    async def unload(self, _):
        t = []
        for n in self.plugins.keys():
            await asyncio.sleep(0.01)
            t.append(self._unload_by_name(n))
        self.log.debug(await asyncio.gather(*t))
        self.log.debug("Plugins unloaded")
