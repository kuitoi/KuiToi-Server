# -*- coding: utf-8 -*-
# Developed by KuiToi Dev
# File modules.PermsSystem
# Written by: SantaSpeen
# Version 1.0
# Licence: FPA
# (c) kuitoi.su 2024
from core import get_logger
import sqlite3


class PermsSystem:
    _db_name = "users.db3"

    def __init__(self):
        self.log = get_logger("PermsSystem")
        self._create_base()
        self._completer_permissions = Completer({})
        # set <permission | group> | unset <permission | group>
        self._completer_group = Completer({})  # <group_name> info | permission

        _completer_after_user = Completer({
            "info": None,
            "permission": {"set": self._completer_permissions, "unset": self._completer_permissions}
        })
        self._completer_user = Completer({}, on_none=_completer_after_user)  # <nick> info | permission
        ev.register("add_perm_to_alias", lambda ev: self._completer_permissions.options.update({ev['args'][0]: None}))

        ev.call_event("add_perm_to_alias", "cmd.perms")
        console.add_command("perms", self._parse_console,
                            None,
                            "Permission module",
                            {"perms": {
                                "groups": {
                                    "create": None,
                                    "delete": None,
                                    "list": None
                                },
                                "user": self._completer_user,
                                "group": self._completer_group,
                                "reload": None,
                            }})
        ev.register("onChatReceive", self._parse_chat)
        ev.register("onPlayerJoin", self._process_new_player)

    def _create_base(self):
        con = sqlite3.connect(self._db_name)
        cursor = con.cursor()

        # Create table for users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mp_id INTEGER UNIQUE,
                nick TEXT NOT NULL,
                playtime INTEGER
            )
        ''')

        # Create table for perms
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS perms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mp_id INTEGER,
                rule TEXT,
                `group` TEXT,
                FOREIGN KEY(mp_id) REFERENCES users(mp_id)
            )
        ''')

        # Create table for groups
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                rules TEXT NOT NULL
            )
        ''')

        con.commit()
        con.close()

    def _parse_console(self, x):
        pass

    def _parse_chat(self, ev):
        pass

    def add_player(self, player):
        self._completer_user.options.update({player.nick: None})
        self.log.debug(f'Added user: {player.nick}')

    def have_permission(self, ev):
        player = ev['kwargs']['player']

    def _process_new_player(self, ev):
        player = ev['kwargs']['player']
        self.add_player(player)
