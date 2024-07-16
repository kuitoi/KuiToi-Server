# -*- coding: utf-8 -*-

# Developed by KuiToi Dev
# File modules.i18n
# Written by: SantaSpeen
# Version 1.3
# Licence: FPA
# (c) kuitoi.su 2023
import builtins
import json
import os
from json import JSONDecodeError

import requests

from core.utils import get_logger


class i18n:
    data = {}

    def __init__(self, data):
        i18n.data = data

    def __getattribute__(self, key):
        return i18n.data[key]


class MultiLanguage:

    def __init__(self, language: str = None, files_dir="translates/", encoding=None):
        if encoding is None:
            encoding = config.enc
        if language is None:
            language = "en"
        self.__data = {
            "hello": "Hello from KuiToi-Server!",
            "config_path": "Use {} to configure.",
            "init_ok": "Initialization completed.",
            "start": "Server started!",
            "stop": "Server stopped!",
            "auth_need_key": "BeamMP key is required to run!",
            "auth_empty_key": "BeamMP key is empty!",
            "auth_cannot_open_browser": "Failed to open browser: {}",
            "auth_use_link": "Use this link: {}",
            "GUI_yes": "Yes",
            "GUI_no": "No",
            "GUI_ok": "OK",
            "GUI_cancel": "Cancel",
            "GUI_need_key_message": "BeamMP key is required to run!\nDo you want to open the link in your browser to get the key?",
            "GUI_enter_key_message": "Please enter the key:",
            "GUI_cannot_open_browser": "Failed to open browser.\nUse this link: {}",
            "web_start": "WebAPI started on {} (CTRL+C to stop)",
            "core_bind_failed": "Failed to bind port. Error: {}",
            "core_direct_mode": "Server started in direct connection mode.",
            "core_auth_server_error": "Received invalid response from BeamMP authentication server.",
            "core_auth_server_refused": "The BeamMP authentication server refused your key. Reason: {}",
            "core_auth_server_refused_no_reason": "The BeamMP authentication server did not provide a reason.",
            "core_auth_server_refused_direct_node": "The server is still running, but in direct connection mode.",
            "core_auth_server_no_response": "Failed to authenticate the server.",
            "core_mods_loaded": "Loaded {} mods. {}Mb",
            "core_identifying_connection": "Processing new connection...",
            "core_player_kick_outdated": "Incorrect version of BeamMP.",
            "core_player_kick_bad_key": "Invalid key passed!",
            "core_player_kick_invalid_key": "Invalid key! Please restart your game.",
            "core_player_kick_auth_server_fail": "BeamMP authentication server failed! Please try to connect again in 5 minutes.",
            "core_player_kick_stale": "Stale client. (Replaced by new connection)",
            "core_player_kick_no_allowed_default_reason": "You are not welcome on this server. Access denied.",
            "core_player_kick_server_full": "Server is full.",
            "core_identifying_okay": "Successful login.",
            "game_welcome_message": "Welcome {}!",
            "client_mod_request": "Requested mod: {}",
            "client_mod_sent": "Mod sent: Size: {}mb, Speed: {}Mb/s ({}sec)",
            "client_mod_sent_limit": " (limit {}Mb/s)",
            "client_mod_sent_error": "Error sending mod: {}",
            "client_sync_time": "Sync time {}sec.",
            "client_kicked": "Kicked for reason: \"{}\"",
            "client_event_invalid_data": "Invalid data returned from event: {}",
            "client_player_disconnected": "Left the server. Playtime: {} min",
            "events_not_callable": "Unable to add event \"{}\". Use \"{}\" instead. Skipping...",
            "events_not_found": "Event \"{}\" is not registered. Maybe {}? Skipping...",
            "events_calling_error": "Error calling \"{}\" in function \"{}\".",
            "events_lua_function_not_found": "Unable to call {}lua event - \"{}\" not found.",
            "events_lua_local": "local ",
            "events_lua_calling_error": "Error: \"{}\" - calling lua event \"{}\", function: \"{}\", arguments: {}",
            "plugins_not_found_load": "Function \"def load():\" not found.",
            "plugins_not_found_start": "Function \"def start():\" not found.",
            "plugins_not_found_unload": "Function \"def unload():\" not found.",
            "plugins_kt_invalid": "\"kt\" variable does not belong to the KuiToi class.",
            "plugins_invalid": "Plugin \"{}\" cannot be run in KuiToi.",
            "plugins_error_loading": "An error occurred while loading the plugin {}: {}",
            "plugins_lua_enabled": "You have enabled Lua plugin support.",
            "plugins_lua_nuances_warning": "There are some nuances when working with Kuiti. If you have a suggestion for their solution, and it is related to KuiToi, please contact the developer.",
            "plugins_lua_legacy_config_create_warning": "Some BeamMP plugins require a properly configured ServerConfig.toml file to function.",
            "plugins_lua_legacy_config_create": "Creating it.",
            "plugins_lua_unload": "Stopping Lua plugin: {}",
            "man_message_man": "man - Shows the help page for COMMAND.\nUsage: man COMMAND",
            "help_message_man": "Shows the help page for COMMAND.",
            "man_for": "Help page for",
            "man_message_not_found": "man: Help page not found.",
            "man_command_not_found": "man: Command \"{}\" not found!",
            "man_message_help": "help - Shows the names and brief descriptions of commands.\nUsage: help [--raw]\nThe `help` command displays a list of all available commands, with a brief description for each command.",
            "help_message_help": "Shows the names and brief descriptions of commands",
            "help_command": "Command",
            "help_message": "Text",
            "help_message_not_found": "No text found",
            "man_message_stop": "stop - Stops the server.\nUsage: stop",
            "help_message_stop": "Stops the server.",
            "man_message_exit": "exit - Stops the server.\nUsage: exit",
            "help_message_exit": "Stops the server."
        }
        self.__en_data = self.__data.copy()
        self.__i18n = None
        self.__encoding = encoding
        self.language = language
        if not os.path.exists(files_dir):
            os.makedirs(files_dir)
        if not os.path.exists(files_dir + "en.json"):
            with open(files_dir + "en.json", "w") as f:
                f.write(json.dumps(self.__en_data, indent=2))
        self.files_dir = files_dir
        self.log = get_logger("i18n")
        self.fi = False
        self.lang_url = "https://raw.githubusercontent.com/KuiToi/KuiToi-Server/Stable/src/translates/"

    def set_language(self, language):
        if self.__i18n and language == self.language:
            return
        self.log.debug(f"set_language({language})")
        self.language = language
        self.open_file()
        self.__i18n = i18n(self.__data)

    def open_file(self):
        self.log.debug("open_file")
        file = self.files_dir + self.language + ".json"
        try:
            with open(file, encoding=self.__encoding) as f:
                self.__data.update(json.load(f))
            return
        except JSONDecodeError:
            self.log.error(
                f"Localisation \"{file}\" have JsonDecodeError. Using default localisation: en.")
        except FileNotFoundError:
            r = requests.get(f"{self.lang_url}{self.language}.json")
            if r.status_code != 404:
                self.log.info(f"Downloaded new localisation: {self.language}")
                loc = r.json()
                with open(file, "w", encoding=self.__encoding) as f:
                    json.dump(loc, f)
                self.__data.update(loc)
                return
            else:
                self.log.warning(f"Localisation \"{file}\" not found; Using default localisation: en.")
        self.set_language("en")

    def builtins_hook(self) -> None:
        self.log.debug("used builtins_hook")
        builtins.i18n = self.__i18n
        builtins.i18n_data = self.__data
