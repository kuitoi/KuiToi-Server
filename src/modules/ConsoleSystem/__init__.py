# -*- coding: utf-8 -*-

# Developed by KuiToi Dev
# File modules.ConsoleSystem
# Written by: SantaSpeen
# Version 1.2
# Licence: FPA
# (c) kuitoi.su 2023
import builtins
import inspect
import logging
from typing import AnyStr

from prompt_toolkit import PromptSession, print_formatted_text, HTML
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.history import FileHistory
try:
    from prompt_toolkit.output.win32 import NoConsoleScreenBufferError
except AssertionError:
    class NoConsoleScreenBufferError(Exception): ...
from prompt_toolkit.patch_stdout import patch_stdout

from core import get_logger
from modules.ConsoleSystem.RCON import RCONSystem


class Console:

    def __init__(self,
                 prompt_in="> ",
                 prompt_out="",
                 not_found="Command \"%s\" not found in alias.",
                 debug=False) -> None:
        self.__logger = get_logger("console")
        self.__is_run = False
        self.no_cmd = False
        self.__prompt_in = prompt_in
        self.__prompt_out = prompt_out
        self.__not_found = not_found
        self.__is_debug = debug
        self.__print = print
        self.__func = dict()
        self.__alias = dict()
        self.__man = dict()
        self.__desc = dict()
        self.__print_logger = get_logger("print")
        self.add_command("man", self.__create_man_message, i18n.man_message_man, i18n.help_message_man,
                         custom_completer={"man": {}})
        self.add_command("help", self.__create_help_message, i18n.man_message_help, i18n.help_message_help,
                         custom_completer={"help": {"--raw": None}})
        self.completer = NestedCompleter.from_nested_dict(self.__alias)
        rcon = RCONSystem
        rcon.console = self
        self.rcon = rcon

    def __debug(self, *x):
        self.__logger.debug(f"{x}")
        # if self.__is_debug:
        #     x = list(x)
        #     x.insert(0, "\r CONSOLE DEBUG:")
        #     self.__print(*x)

    def __getitem__(self, item):
        print(item)

    @staticmethod
    def __get_max_len(arg) -> int:
        i = 0
        arg = list(arg)
        for a in arg:
            ln = len(str(a))
            if ln > i:
                i = ln
        return i

    def __create_man_message(self, argv: list) -> AnyStr:
        if len(argv) == 0:
            return self.__man.get("man")
        x = argv[0]
        if self.__alias.get(x) is None:
            return i18n.man_command_not_found.format(x)

        man_message = self.__man.get(x)
        if man_message:
            return man_message
        else:
            return i18n.man_message_not_found

    # noinspection PyStringFormat
    def __create_help_message(self, argv: list) -> AnyStr:
        self.__debug("creating help message")
        raw = False
        max_len_v = 0
        if "--raw" in argv:
            max_len_v = self.__get_max_len(self.__func.values())
            print()
            raw = True

        message = "\n"
        max_len = self.__get_max_len(self.__func.keys())
        if max_len < 7:
            max_len = 7

        if raw:
            message += f"%-{max_len}s; %-{max_len_v}s; %s\n" % ("Key", "Function", "Description")
        else:
            message += f"   %-{max_len}s : %s\n" % (i18n.help_command, i18n.help_message)

        for k, v in self.__func.items():
            doc = self.__desc.get(k)

            if raw:
                message += f"%-{max_len}s; %-{max_len_v}s; %s\n" % (k, v, doc)

            else:
                if doc is None:
                    doc = i18n.help_message_not_found
                message += f"   %-{max_len}s : %s\n" % (k, doc)

        return message

    def __update_completer(self):
        self.completer = NestedCompleter.from_nested_dict(self.__alias)

    def add_command(self, key: str, func, man: str = None, desc: str = None, custom_completer: dict = None) -> dict:
        key = key.format(" ", "-")

        if not isinstance(key, str):
            raise TypeError("key must be string")
        self.__debug(f"added user command: key={key}; func={func};")
        self.__alias.update(custom_completer or {key: None})
        self.__alias["man"].update({key: None})
        self.__func.update({key: {"f": func}})
        self.__man.update({key: f'html:<seagreen>{i18n.man_for} <b>{key}</b>\n{man}</seagreen>' if man else None})
        self.__desc.update({key: desc})
        self.__update_completer()
        return self.__alias.copy()

    def _write(self, t):
        if self.no_cmd:
            print(t)
            return
        try:
            if t.startswith("html:"):
                print_formatted_text(HTML(t[5:]))
            else:
                print_formatted_text(t)
        except NoConsoleScreenBufferError:
            print("Works in non cmd mode.")
            self.no_cmd = True
            print(t)

    def write(self, s: AnyStr):
        if isinstance(s, (list, tuple)):
            for text in s:
                self._write(text)
        else:
            self._write(s)

    def log(self, s: AnyStr) -> None:
        if isinstance(s, (list, tuple)):
            for text in s:
                self.__logger.info(f"{text}")
        else:
            self.__logger.info(f"{s}")
        # self.write(s)

    def __lshift__(self, s: AnyStr) -> None:
        self.write(s)

    @property
    def alias(self) -> dict:
        return self.__alias.copy()

    def __builtins_print(self,
                         *values: object,
                         sep: str or None = " ",
                         end: str or None = None,
                         file: str or None = None,
                         flush: bool = False) -> None:
        self.__debug(f"Used __builtins_print; is_run: {self.__is_run}")
        val = list(values)
        if len(val) > 0:
            if self.__is_run:
                self.__print_logger.info(f"{' '.join([''.join(str(i)) for i in values])}\r\n{self.__prompt_in}")
            else:
                if end is None:
                    end = "\n"
                self.__print(*tuple(val), sep=sep, end=end, file=file, flush=flush)

    def logger_hook(self) -> None:
        self.__debug("used logger_hook")

        def emit(cls, record):
            try:
                msg = cls.format(record)
                if cls.stream.name == "<stderr>":
                    self.write(f"\r{msg}")
                else:
                    cls.stream.write(msg + cls.terminator)
                cls.flush()
            except RecursionError:
                raise
            except Exception as e:
                cls.handleError(record)

        logging.StreamHandler.emit = emit

    def builtins_hook(self) -> None:
        self.__debug("used builtins_hook")

        builtins.Console = Console
        builtins.console = self

        # builtins.print = self.__builtins_print

    async def read_input(self):
        session = PromptSession(history=FileHistory('./.cmdhistory'))
        while True:
            try:
                with patch_stdout():
                    if self.no_cmd:
                        cmd_in = input(self.__prompt_in)
                    else:
                        try:
                            cmd_in = await session.prompt_async(
                                self.__prompt_in,
                                completer=self.completer,
                                auto_suggest=AutoSuggestFromHistory()
                            )
                        except NoConsoleScreenBufferError:
                            print("Works in non cmd mode.")
                            self.no_cmd = True
                cmd_s = cmd_in.split(" ")
                cmd = cmd_s[0]
                if cmd == "":
                    continue
                else:
                    found_in_lua = False
                    d = ev.call_lua_event("onConsoleInput", cmd_in)
                    if len(d) > 0:
                        for text in d:
                            if text is not None:
                                found_in_lua = True
                                self.log(text)
                    command_object = self.__func.get(cmd)
                    if command_object:
                        func = command_object['f']
                        if inspect.iscoroutinefunction(func):
                            out = await func(cmd_s[1:])
                        else:
                            out = func(cmd_s[1:])
                        if out:
                            self.log(out)
                    else:
                        if not found_in_lua:
                            self.log(self.__not_found % cmd)
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e:
                print(f"Error in console.py: {e}")
                self.__logger.exception(e)

    async def start(self):
        self.__is_run = True
        await self.read_input()

    def stop(self, *args, **kwargs):
        self.__is_run = False
        raise KeyboardInterrupt
