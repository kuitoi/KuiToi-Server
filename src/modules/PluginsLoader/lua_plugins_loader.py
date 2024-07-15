import asyncio
import json
import os
import platform
import random
import re
import shutil
import threading
import time

import toml
from lupa.lua53 import LuaRuntime

from core import get_logger


class EventTimer:
    def __init__(self, event_name, interval_ms, mp, strategy=None):
        self.log = get_logger(f"EventTimer | {mp.name}")
        self.mp = mp
        self.event_name = event_name
        self.interval_ms = interval_ms
        self.strategy = strategy
        self.timer = None
        self.stopped = False

    def start(self):
        def callback():
            if not self.stopped:
                self.start()
            self.trigger_event()

        self.timer = threading.Timer(self.interval_ms / 1000.0, callback)
        self.timer.start()

    def stop(self):
        self.stopped = True
        if self.timer is not None:
            self.timer.cancel()

    def trigger_event(self):
        self.log.debug(f"Event '{self.event_name}' triggered")
        self.mp.TriggerLocalEvent(self.event_name)


# noinspection PyPep8Naming,PyProtectedMember
class MP:

    def __init__(self, name: str, lua: LuaRuntime):
        self.loaded = False
        self._event_waiters = []
        self.loop = asyncio.get_event_loop()
        self.log = get_logger(f"LuaPlugin | {name}")
        self.name = name
        self.tasks = []
        self._lua = lua
        self._local_events = {
            "onInit": [], "onShutdown": [], "onPlayerAuth": [], "onPlayerConnecting": [], "onPlayerJoining": [],
            "onPlayerJoin": [], "onPlayerDisconnect": [], "onChatMessage": [], "onVehicleSpawn": [],
            "onVehicleEdited": [], "onVehicleDeleted": [], "onVehicleReset": [], "onFileChanged": []
        }
        self._event_timers = {}

    def _print(self, *args):
        args = list(args)
        for i, arg in enumerate(args):
            if isinstance(arg, str):
                try:
                    text = arg.encode("CP1251").decode(config.enc).replace("\u001b", "\x1b")
                    args[i] = re.sub(r'\x1b\[.*?m', '', text)
                except UnicodeEncodeError:
                    pass
            if "LuaTable" in str(type(arg)):
                args[i] = self._lua.globals().Util.JsonEncode(arg)
        s = " ".join(map(str, args))
        self.log.info(s)

    def GetOSName(self) -> str:
        self.log.debug("request MP.GetOSName()")
        pl = platform.system()
        if pl in ["Linux", "Windows"]:
            return pl
        return "Other"

    def GetServerVersion(self) -> tuple[int, int, int]:
        self.log.debug("request MP.GetServerVersion()")
        return ev.call_event("_get_BeamMP_version")[0]

    def RegisterEvent(self, event_name: str, function_name: str) -> None:
        self.log.debug("request MP.RegisterEvent()")
        ev.register(event_name, function_name, lua=self._lua)
        if event_name not in self._local_events:
            self._local_events.update({str(event_name): [function_name]})
        else:
            self._local_events[event_name].append(function_name)
        self.log.debug("Register ok (local)")

    def CreateEventTimer(self, event_name: str, interval_ms: int, strategy: int = None):
        self.log.debug("request CreateEventTimer()")
        event_timer = EventTimer(event_name, interval_ms, self, strategy)
        self._event_timers[event_name] = event_timer
        event_timer.start()

    def CancelEventTimer(self, event_name: str):
        self.log.debug("request CancelEventTimer()")
        if event_name in self._event_timers:
            event_timer = self._event_timers[event_name]
            event_timer.stop()
            del self._event_timers[event_name]

    def TriggerLocalEvent(self, event_name, *args):
        if event_name != "getTable":
            self.log.debug("request TriggerLocalEvent()")
            self.log.debug(f"Calling local lua event: '{event_name}{args}'")
        funcs_data = []
        if event_name in self._local_events.keys():
            for func_name in self._local_events[event_name]:
                try:
                    func = self._lua.globals()[func_name]
                    if not func:
                        self.log.warning(i18n.events_lua_function_not_found.format(i18n.events_lua_local, func_name))
                        continue
                    fd = func(*args)
                    funcs_data.append(fd)
                except Exception as e:
                    self.log.error(i18n.events_lua_calling_error.format(f"{e}", event_name, func_name, f"{args}"))

        else:
            self.log.warning(i18n.events_not_found.format(event_name, "ev.call_lua_event(), MP.Trigger<>Event()"))

        return self._lua.table_from(funcs_data)

    def TriggerGlobalEvent(self, event_name, *args):
        self.log.debug("request TriggerGlobalEvent()")
        return self._lua.table(
            IsDone=lambda: True,
            GetResults=lambda: self._lua.table_from(ev.call_lua_event(event_name, *args))
        )

    def Sleep(self, time_ms):
        self.log.debug(f"request Sleep(); Thread: {threading.current_thread().name}")
        time.sleep(time_ms * 0.001)

    def SendChatMessage(self, player_id, message):
        self.log.debug("request SendChatMessage()")
        client = ev.call_event("_get_player", cid=player_id)[0]
        to_all = False
        if player_id < 0:
            to_all = True
            client = client[0]
        if client and message:
            t = self.loop.create_task(client.send_message(f"Server: {message}", to_all=to_all))
            self.tasks.append(t)

    def TriggerClientEvent(self, player_id, event_name, data):
        self.log.debug("request TriggerClientEvent()")
        client = ev.call_event("_get_player", cid=player_id)[0]
        to_all = False
        if player_id < 0:
            to_all = True
            client = client[0] if len(client) > 0 else None
        if client and event_name and data:
            t = self.loop.create_task(client.send_event(event_name, data, to_all=to_all))
            self.tasks.append(t)
            return True, None
        elif not client:
            return False, "Client expired"
        else:
            return False, "Can't found event_name or data"

    def TriggerClientEventJson(self, player_id, event_name, data):
        self.log.debug(f"request TriggerClientEventJson({player_id, event_name, data})")
        data = self._lua.globals().Util.JsonEncode(data)
        self.TriggerClientEvent(player_id, event_name, data)

    def GetPlayerCount(self):
        self.log.debug("request GetPlayerCount()")
        return len(ev.call_event("_get_player", cid=-1)[0])

    def GetPositionRaw(self, player_id, car_id):
        self.log.debug("request GetPositionRaw()")
        if player_id < 0:
            return self._lua.table(), "Bad client"
        client = ev.call_event("_get_player", cid=player_id)[0]
        if client:
            car = client._cars[car_id]
            if car:
                return self._lua.table_from(car['pos'])
            return self._lua.table(), "Vehicle not found"
        return self._lua.table(), "Client expired"

    def IsPlayerConnected(self, player_id):
        self.log.debug("request IsPlayerConnected()")
        if player_id < 0:
            return False
        return bool(ev.call_event("_get_player", cid=player_id)[0])

    def GetPlayerName(self, player_id):
        self.log.debug("request GetPlayerName()")
        if player_id < 0:
            return None
        client = ev.call_event("_get_player", cid=player_id)[0]
        if client:
            return client.nick
        return

    def GetPlayerIDByName(self, player_name):
        self.log.debug("request GetPlayerIDByName()")
        if not isinstance(player_name, str):
            return None
        client = ev.call_event("_get_player", nick=player_name)[0]
        if client:
            return client.cid
        return

    def RemoveVehicle(self, player_id, vehicle_id):
        self.log.debug("request RemoveVehicle()")
        if player_id < 0:
            return
        client = ev.call_event("_get_player", cid=player_id)[0]
        if client:
            t = self.loop.create_task(client._delete_car(car_id=vehicle_id))
            self.tasks.append(t)

    def GetPlayerVehicles(self, player_id):
        self.log.debug("request GetPlayerVehicles()")
        if player_id < 0:
            return self._lua.table()
        client = ev.call_event("_get_player", cid=player_id)[0]
        if client:
            return self._lua.table_from([f'{v["json"]}' for d in [i for i in client._cars if i is not None]
                                         for k, v in d.items() if k == "json"])

    def GetPlayers(self):
        self.log.debug("request GetPlayers()")
        clients = ev.call_event("_get_player", cid=-1)[0]
        return self._lua.table_from([i.nick for i in clients])

    def IsPlayerGuest(self, player_id) -> bool:
        self.log.debug("request IsPlayerGuest()")
        if player_id < 0:
            return True
        client = ev.call_event("_get_player", cid=player_id)[0]
        if client:
            return client.guest
        return False

    def DropPlayer(self, player_id, reason="Kicked"):
        self.log.debug("request DropPlayer()")
        if player_id < 0:
            return
        client = ev.call_event("_get_player", cid=player_id)[0]
        if client:
            t = self.loop.create_task(client.kick(reason))
            self.tasks.append(t)

    def GetStateMemoryUsage(self):
        self.log.debug("request GetStateMemoryUsage()")
        return self._lua.get_memory_used()

    def GetLuaMemoryUsage(self):
        self.log.debug("request GetStateMemoryUsage()")
        lua_plugins = ev.call_event("_lua_plugins_get")[0]
        return sum(pl['lua'].get_memory_used() for pls in lua_plugins.values() for pl in pls.values())

    def GetPlayerIdentifiers(self, player_id):
        self.log.debug("request GetStateMemoryUsage()")
        client = ev.call_event("_get_player", cid=player_id)[0]
        if client:
            return self._lua.table_from(client.identifiers)
        return self._lua.table()

    def Set(self, *_):
        self.log.debug("request Set")
        self.log.warning("KuiToi cannot support this: MP.Set()")


# noinspection PyPep8Naming
class Util:
    def __init__(self, name, lua):
        self.log = get_logger(f"LuaPlugin | Util | {name}")
        self.name = name
        self._lua = lua

    def _recursive_list_encode(self, table):
        new_list = list(table.values())
        for i, v in enumerate(list(table.values())):
            if not isinstance(v, (int, float, bool, str, dict, list)) and "LuaTable" not in str(type(v)):
                new_list[i] = None
                continue
            if "LuaTable" in str(type(v)):
                d = dict(v)
                if all(isinstance(ii, int) for ii in d.keys()):
                    new_list[i] = self._recursive_list_encode(d)
                    continue
                else:
                    new_list[i] = self._recursive_dict_encode(d)
        return [i for i in new_list if i is not None]

    def _recursive_dict_encode(self, table):
        new_dict = dict(table)
        for k, v in table.items():
            if not isinstance(v, (int, float, bool, str, dict, list)) and "LuaTable" not in str(type(v)):
                new_dict[k] = None
                continue
            if "LuaTable" in str(type(v)):
                d = dict(v)
                if all(isinstance(i, int) for i in d.keys()):
                    new_dict[k] = self._recursive_list_encode(d)
                    continue
                else:
                    new_dict[k] = self._recursive_dict_encode(d)
        return {k: v for k, v in new_dict.items() if v is not None}

    def JsonEncode(self, table):
        data = {}
        try:
            self.log.debug("requesting JsonEncode()")
            if all(isinstance(k, int) for k in table.keys()):
                data = self._recursive_list_encode(table)
            else:
                data = self._recursive_dict_encode(table)
        except Exception as e:
            self.log.exception(e)
        data = json.dumps(data)
        self.log.debug(f"Encoded: {data}")
        return data

    def JsonDecode(self, string):
        self.log.debug("requesting JsonDecode()")
        return self._lua.table_from(json.loads(string))

    def JsonPrettify(self, string):
        self.log.debug("requesting JsonPrettify()")
        data = json.loads(string)
        return json.dumps(data, indent=4, sort_keys=True)

    def JsonMinify(self, string):
        self.log.debug("requesting JsonMinify()")
        data = json.loads(string)
        return json.dumps(data, separators=(',', ':'))

    def JsonFlatten(self, json_str):
        self.log.debug("request JsonFlatten()")
        json_obj = json.loads(json_str)
        flat_obj = {}

        def flatten(obj, path=''):
            if isinstance(obj, dict):
                for key in obj:
                    flatten(obj[key], path + '/' + key)
            elif isinstance(obj, list):
                for i in range(len(obj)):
                    flatten(obj[i], path + '/' + str(i))
            else:
                flat_obj[path] = obj

        flatten(json_obj)
        flat_json = json.dumps(flat_obj)
        return flat_json

    def JsonUnflatten(self, flat_json):
        self.log.debug("request JsonUnflatten")
        flat_obj = json.loads(flat_json)

        def unflatten(obj):
            result = {}
            for key in obj:
                parts = key.split('/')
                d = result
                for part in parts[:-1]:
                    if part not in d:
                        # create a new node in the dictionary
                        # if the path doesn't exist
                        d[part] = {}
                    d = d[part]
                # assign the value to the last part of the path
                d[parts[-1]] = obj[key]
            return result

        json_obj = unflatten(flat_obj)
        return json.dumps(json_obj)

    def JsonDiff(self, a: str, b: str) -> str:
        self.log.debug("requesting JsonDiff()")
        a_obj = json.loads(a)
        b_obj = json.loads(b)
        diff = []
        for k, v in b_obj.items():
            if k not in a_obj:
                diff.append({"op": "add", "path": "/" + k, "value": v})
            elif a_obj[k] != v:
                diff.append({"op": "replace", "path": "/" + k, "value": v})
        for k in a_obj.keys() - b_obj.keys():
            diff.append({"op": "remove", "path": "/" + k})
        return json.dumps(diff)

    @staticmethod
    def _apply_patch(base_obj, patch_obj):
        for patch in patch_obj:
            op = patch['op']
            path = patch['path']
            value = patch.get('value', None)
            tokens = path.strip('/').split('/')
            obj = base_obj
            for i, token in enumerate(tokens):
                if isinstance(obj, list):
                    token = int(token)
                if i == len(tokens) - 1:
                    if op == 'add':
                        if isinstance(obj, list):
                            obj.insert(int(token), value)
                        else:
                            obj[token] = value
                    elif op == 'replace':
                        obj[token] = value
                    elif op == 'remove':
                        if isinstance(obj, list):
                            obj.pop(int(token))
                        else:
                            del obj[token]
                else:
                    obj = obj[token]
        return base_obj

    def JsonDiffApply(self, base: str, diff: str) -> str:
        self.log.debug("requesting JsonDiffApply()")
        base_obj = json.loads(base)
        diff_obj = json.loads(diff)
        result = self._apply_patch(base_obj, diff_obj)
        return json.dumps(result)

    def Random(self) -> float:
        self.log.debug("requesting Random()")
        return random.random()

    def RandomIntRange(self, min_v, max_v) -> int:
        self.log.debug("requesting RandomIntRange()")
        return random.randint(min_v, max_v)

    def RandomRange(self, min_v, max_v) -> float:
        self.log.debug("requesting RandomRange()")
        return random.uniform(min_v, max_v)


# noinspection PyPep8Naming
class FS:

    def __init__(self, name: str, lua: LuaRuntime):
        self.log = get_logger(f"LuaPlugin | FP | {name}")
        self.name = name
        self._lua = lua

    def CreateDirectory(self, path):
        self.log.debug("requesting CreateDirectory()")
        try:
            os.makedirs(path)
            return True, None
        except FileExistsError:
            return True, None
        except FileNotFoundError | NotADirectoryError as e:
            return False, f"{e}"
        except PermissionError as e:
            return False, f"{e}"
        except OSError as e:
            return False, f"{e}"
        except TypeError as e:
            return False, f"{e}"
        except ValueError as e:
            return False, f"{e}"

    def Remove(self, path):
        self.log.debug("requesting Remove()")
        try:
            if os.path.isdir(path):
                os.rmdir(path)
            else:
                os.remove(path)
            return True, None
        except (FileNotFoundError, NotADirectoryError) as e:
            return False, f"{e}"
        except PermissionError as e:
            return False, f"{e}"
        except OSError as e:
            return False, f"{e}"
        except TypeError as e:
            return False, f"{e}"

    def Rename(self, path_from, path_to):
        self.log.debug("requesting Rename()")
        try:
            os.rename(path_from, path_to)
            return True, None
        except (FileNotFoundError, NotADirectoryError) as e:
            return False, f"{e}"
        except PermissionError as e:
            return False, f"{e}"
        except OSError as e:
            return False, f"{e}"
        except TypeError as e:
            return False, f"{e}"

    def Copy(self, path_from, path_to):
        self.log.debug("requesting Copy()")
        try:
            if os.path.isfile(path_from):
                shutil.copy2(path_from, path_to)
            elif os.path.isdir(path_from):
                shutil.copytree(path_from, path_to)
            else:
                raise ValueError("Invalid path: {}".format(path_from))
            return True, None
        except (FileNotFoundError, NotADirectoryError, shutil.Error) as e:
            return False, f"{e}"
        except PermissionError as e:
            return False, f"{e}"
        except OSError as e:
            return False, f"{e}"
        except TypeError as e:
            return False, f"{e}"

    def GetFilename(self, path):
        self.log.debug("requesting GetFilename()")
        return os.path.basename(path)

    def GetExtension(self, path):
        self.log.debug("requesting GetExtension()")
        return os.path.splitext(path)[1]

    def GetParentFolder(self, path):
        self.log.debug("requesting GetParentFolder()")
        return os.path.dirname(path)

    def Exists(self, path):
        self.log.debug("requesting Exists()")
        return os.path.exists(path)

    def IsDirectory(self, path):
        self.log.debug("requesting IsDirectory()")
        return os.path.isdir(path)

    def IsFile(self, path):
        self.log.debug("requesting IsFile()")
        return os.path.isfile(path)

    def ListDirectories(self, path):
        self.log.debug("requesting ListDirectories()")
        directories = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                directories.append(item)
        return self._lua.table_from(directories)

    def ListFiles(self, path):
        self.log.debug("requesting ListFiles()")
        files = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                files.append(item)
        return self._lua.table_from(files)

    def ConcatPaths(self, *args):
        self.log.debug("requesting ConcatPaths()")
        return os.path.join(*args)


# noinspection PyProtectedMember
class LuaPluginsLoader:

    def __init__(self, plugins_dir):
        self.loop = asyncio.get_event_loop()
        self.plugins_dir = plugins_dir
        self.lua_plugins = {}
        self.lua_plugins_tasks = []
        self.lua_dirs = set()
        self.log = get_logger("LuaPluginsLoader")
        self.loaded_str = "Lua plugins: "
        ev.register("_lua_plugins_get", lambda x: self.lua_plugins)
        ev.register("_lua_plugins_unload", self.unload)
        console.add_command("lua_plugins", lambda x: self.loaded_str[:-2])
        console.add_command("lua_pl", lambda x: self.loaded_str[:-2])

    def load(self):
        self.log.debug("Loading Lua plugins...")
        self.log.info(i18n.plugins_lua_enabled)
        self.log.warning(i18n.plugins_lua_nuances_warning)
        self.log.warning(i18n.plugins_lua_legacy_config_create_warning)
        self.log.info(i18n.plugins_lua_legacy_config_create)
        data = {
            "info": "ServerConfig.toml is created solely for backward compatibility support. "
                    "This file will be updated every time the program is launched.",
            "General": {
                "Name": config.Server['name'],
                "Port": config.Server['server_port'],
                "AuthKey": config.Auth['key'],
                "LogChat": config.Options['log_chat'],
                "Debug": config.Options['debug'],
                "Private": config.Auth['private'],
                "MaxCars": config.Game['max_cars'],
                "MaxPlayers": config.Game['players'],
                "Map": f"/levels/{config.Game['map']}/info.json",
                "Description": config.Server['description'],
                "ResourceFolder": "plugins/"
            },
            "Misc": {
                "ImScaredOfUpdates": False,
                "SendErrorsShowMessage": False,
                "SendErrors": False
            },
            "HTTP": {
                "HTTPServerIP": config.WebAPI['server_ip'],
                "HTTPServerPort": config.WebAPI['server_port'],
                "SSLKeyPath": None,
                "SSLCertPath": None,
                "UseSSL": False,
                "HTTPServerEnabled": config.WebAPI['enabled'],
            }
        }
        with open("ServerConfig.toml", "w") as f:
            toml.dump(data, f)
        self.log.warning("KuiToi will not support at all: MP.Set()")
        py_folders = ev.call_event("_plugins_get")[0]
        for name in os.listdir(self.plugins_dir):
            path = os.path.join(self.plugins_dir, name)
            if os.path.isdir(path) and name not in py_folders and name not in "__pycache__":
                plugin_path = os.path.join(self.plugins_dir, name)
                for file in os.listdir(plugin_path):
                    path = f"plugins/{name}/{file}"
                    if os.path.isfile(path) and path.endswith(".lua"):
                        self.lua_dirs.add(name)

        self.log.debug(f"py_folders {py_folders}, lua_dirs {self.lua_dirs}")

        for name in self.lua_dirs:
            # noinspection PyArgumentList
            lua = LuaRuntime(encoding="CP1251", source_encoding=config.enc, unpack_returned_tuples=True)
            lua_globals = lua.globals()
            lua_globals.printRaw = lua.globals().print
            lua_globals.exit = lambda x: self.log.info(f"KuiToi: You can't disable server..")
            mp = MP(name, lua)
            lua_globals.MP = mp
            lua_globals.print = mp._print
            lua_globals.Util = Util(name, lua)
            lua_globals.FS = FS(name, lua)
            pa = os.path.abspath(self.plugins_dir)
            p0 = os.path.join(pa, name, "?.lua")
            p1 = os.path.join(pa, name, "lua", "?.lua")
            lua_globals.package.path += f';{p0};{p1}'
            with open("modules/PluginsLoader/add_in.lua", "r") as f:
                lua.execute(f.read())
            self.lua_plugins.update({name: {"lua": lua, "ok": False}})
            plugin_path = os.path.join(self.plugins_dir, name)
            for file in os.listdir(plugin_path):
                path = f"plugins/{name}/{file}"
                if os.path.isfile(path) and path.endswith(".lua"):
                    try:
                        lua_globals.loadfile(path)()
                    except Exception as e:
                        self.loaded_str += f"{name}:no, "
                        self.log.error(f"Cannot load lua plugin from `{path}`: {e}")
            try:
                lua_globals.MP.loaded = True
                lua_globals.MP.TriggerLocalEvent("onInit")
                lua_globals.onInit()
                self.lua_plugins[name]['ok'] = True
                self.loaded_str += f"{name}:ok, "
            except Exception as e:
                self.loaded_str += f"{name}:no, "
                self.log.error(f"Exception onInit from `{name}`: {e}")
                self.log.exception(e)

    def unload(self, _):
        self.log.debug("Unloading lua plugins")
        for name, data in self.lua_plugins.items():
            if data['ok']:
                self.log.info(i18n.plugins_lua_unload.format(name))
                for _, timer in data['lua'].globals().MP._event_timers.items():
                    timer.stop()
