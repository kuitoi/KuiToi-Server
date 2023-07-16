# -*- coding: utf-8 -*-

# Developed by KuiToi Dev
# File modules.PluginsLoader.plugins_loader.py
# Written by: SantaSpeen
# Version 1.0
# Licence: FPA
# (c) kuitoi.su 2023
import asyncio
import inspect
import os
import types
from contextlib import contextmanager
from threading import Thread

from core import get_logger


# TODO: call_client_event, get_player, get_players, GetPlayerCount
class KuiToi:
    _plugins_dir = ""

    def __init__(self, name=None):
        if name is None:
            raise AttributeError("KuiToi: Name is required")
        self.log = get_logger(f"Plugin | {name}")
        self.__name = name
        self.__dir = os.path.join(self._plugins_dir, self.__name)
        if not os.path.exists(self.__dir):
            os.mkdir(self.__dir)

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        # You chell not pass
        pass

    @property
    def dir(self):
        return self.__dir

    @dir.setter
    def dir(self, value):
        # You chell not pass
        pass

    @contextmanager
    def open(self, file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
        path = os.path.join(self.__dir, file)
        self.log.debug(f'Trying to open "{path}" with mode "{mode}"')
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

    def register_event(self, event_name, event_func):
        self.log.debug(f"Registering event {event_name}")
        ev.register_event(event_name, event_func)

    def call_event(self, event_name, *data, **kwargs):
        self.log.debug(f"Called event {event_name}")
        ev.call_event(event_name, *data, **kwargs)


class PluginsLoader:

    def __init__(self, plugins_dir):
        self.loop = asyncio.get_event_loop()
        self.plugins = {}
        self.plugins_tasks = []
        self.plugins_dir = plugins_dir
        self.log = get_logger("PluginsLoader")
        self.loaded_str = "Plugins: "
        ev.register_event("_plugins_start", self.start)
        ev.register_event("_plugins_unload", self.unload)
        console.add_command("plugins", lambda x: self.loaded_str[:-2])
        console.add_command("pl", lambda x: self.loaded_str[:-2])

    async def load(self):
        self.log.debug("Loading plugins...")
        files = os.listdir(self.plugins_dir)
        for file in files:
            if file.endswith(".py"):
                try:
                    self.log.debug(f"Loading plugin: {file[:-3]}")
                    plugin = types.ModuleType(file[:-3])
                    plugin.KuiToi = KuiToi
                    plugin.KuiToi._plugins_dir = self.plugins_dir
                    plugin.print = print
                    file_path = os.path.join(self.plugins_dir, file)
                    plugin.__file__ = file_path
                    with open(f'{file_path}', 'r', encoding="utf-8") as f:
                        code = f.read()
                        exec(code, plugin.__dict__)

                    ok = True
                    try:
                        isfunc = inspect.isfunction
                        if not isfunc(plugin.load):
                            self.log.error('Function "def load():" not found.')
                            ok = False
                        if not isfunc(plugin.start):
                            self.log.error('Function "def start():" not found.')
                            ok = False
                        if not isfunc(plugin.unload):
                            self.log.error('Function "def unload():" not found.')
                            ok = False
                        if type(plugin.kt) != KuiToi:
                            self.log.error(f'Attribute "kt" isn\'t KuiToi class. Plugin file: "{file_path}"')
                            ok = False
                    except AttributeError:
                        ok = False
                    if not ok:
                        self.log.error(f'Plugin file: "{file_path}" is not a valid KuiToi plugin.')
                        return

                    pl_name = plugin.kt.name
                    if self.plugins.get(pl_name) is not None:
                        raise NameError(f'Having plugins with identical names is not allowed; '
                                        f'Plugin name: "{pl_name}"; Plugin file "{file_path}"')

                    plugin.open = plugin.kt.open
                    iscorfunc = inspect.iscoroutinefunction
                    self.plugins.update(
                        {
                            pl_name: {
                                "plugin": plugin,
                                "load": {
                                    "func": plugin.load,
                                    "async": iscorfunc(plugin.load)
                                },
                                "start": {
                                    "func": plugin.start,
                                    "async": iscorfunc(plugin.start)
                                },
                                "unload": {
                                    "func": plugin.unload,
                                    "async": iscorfunc(plugin.unload)
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
                    self.loaded_str += f"{pl_name}:ok, "
                    self.log.debug(f"Plugin loaded: {file}. Settings: {self.plugins[pl_name]}")
                except Exception as e:
                    # TODO: i18n
                    self.loaded_str += f"{file}:no, "
                    self.log.error(f"Error while loading plugin: {file}; Error: {e}")
                    self.log.exception(e)

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
        for pl_name, pl_data in self.plugins.items():
            try:
                if pl_data['unload']['async']:
                    self.log.debug(f"Unload async plugin: {pl_name}")
                    await pl_data['unload']['func']()
                else:
                    self.log.debug(f"Unload sync plugin: {pl_name}")
                    th = Thread(target=pl_data['unload']['func'], name=f"Thread {pl_name}")
                    th.start()
                    th.join()
            except Exception as e:
                self.log.exception(e)
