# -*- coding: utf-8 -*-
import copy
# Developed by KuiToi Dev
# File modules.ConfigProvider
# Written by: SantaSpeen
# Version 1.0
# Licence: FPA
# (c) kuitoi.su 2023
import os
import secrets

import yaml


class Config:
    def __init__(self, auth=None, game=None, server=None, rcon=None, options=None):
        self.Auth = auth or {"key": None, "private": True}
        self.Game = game or {"map": "gridmap_v2", "players": 8, "cars": 1}
        self.Server = server or {"name": "KuiToi-Server", "description": "Welcome to KuiToi Server!", "tags": "Freroam",
                                 "server_ip": "0.0.0.0", "server_port": 30814}
        self.Options = options or {"language": "en", "speed_limit": 0, "use_queue": False,
                                   "use_lua": False, "log_chat": True}
        self.RCON = rcon or {"enabled": False, "server_ip": "127.0.0.1", "server_port": 10383,
                             "password": secrets.token_hex(6)}

    def __repr__(self):
        return (f"{self.__class__.__name__}(Auth={self.Auth!r}, Game={self.Game!r}, Server={self.Server!r}, "
                f"RCON={self.RCON!r}, Options={self.Options!r})")


class ConfigProvider:

    def __init__(self, config_path):
        self.config_path = config_path
        self.config = Config()

    def read(self, _again=False):
        if not os.path.exists(self.config_path):
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f)
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.load(f.read(), yaml.Loader)
        except yaml.YAMLError:
            print("You have errors in the YAML syntax.")
            print("Stopping server.")
            exit(1)
        if not self.config:
            if _again:
                print("Error: empty configuration.")
                exit(1)
            print("Reconfig: empty configuration.")
            os.remove(self.config_path)
            self.config = Config()
            return self.read(True)

        if not self.config.Options.get("debug"):
            self.config.Options['debug'] = False
        if not self.config.Options.get("encoding"):
            self.config.Options['encoding'] = "utf-8"

        return self.config

    def save(self):
        _config = copy.deepcopy(self.config)
        del _config.enc
        del _config.Options['debug']
        del _config.Options['encoding']
        os.remove(self.config_path)
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(_config, f)
