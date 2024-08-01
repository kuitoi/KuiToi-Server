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

from prompt_toolkit import PromptSession, print_formatted_text, HTML, ANSI
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, WordCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory

try:
    from prompt_toolkit.output.win32 import NoConsoleScreenBufferError
except AssertionError:
    class NoConsoleScreenBufferError(Exception):
        ...
from prompt_toolkit.patch_stdout import patch_stdout

from core import get_logger
from modules.ConsoleSystem.RCON import RCONSystem


class BadCompleter(Exception): ...


class MyNestedCompleter(Completer):
    def __init__(self, options, ignore_case=True):
        self.options = self._from_nested_dict(options)
        self.ignore_case = ignore_case

    def __repr__(self) -> str:
        return f"MyNestedCompleter({self.options!r}, ignore_case={self.ignore_case!r})"

    @classmethod
    def _from_nested_dict(cls, data, r=False):
        options: dict[str, Completer | None] = {}
        for key, value in data.items():
            if isinstance(value, Completer):
                options[key] = value
            elif isinstance(value, dict):
                options[key] = cls._from_nested_dict(value, True)
            elif isinstance(value, set):
                options[key] = cls._from_nested_dict({item: None for item in value}, True)
            elif isinstance(value, bool):
                if value:
                    options[key] = None
            else:
                if isinstance(value, str) and value == "<playerlist>":
                    options[key] = players_completer
                else:
                    if value is not None:
                        raise BadCompleter(f"{value!r} for key {key!r} have not valid type.")
                    options[key] = None
        if r:
            return cls(options)
        return options

    def load(self, data):
        self.options = self._from_nested_dict(data)

    def get_completions(self, document, complete_event):
        # Split document.
        text = document.text_before_cursor.lstrip()
        stripped_len = len(document.text_before_cursor) - len(text)

        # If there is a space, check for the first term, and use a
        # subcompleter.
        if " " in text:
            first_term = text.split()[0]
            completer = self.options.get(first_term)

            # If we have a sub completer, use this for the completions.
            if completer is not None:
                remaining_text = text[len(first_term):].lstrip()
                move_cursor = len(text) - len(remaining_text) + stripped_len

                new_document = Document(
                    remaining_text,
                    cursor_position=document.cursor_position - move_cursor,
                )

                yield from completer.get_completions(new_document, complete_event)

        # No space in the input: behave exactly like `WordCompleter`.
        else:
            completer = WordCompleter(
                list(self.options.keys()), ignore_case=self.ignore_case
            )
            yield from completer.get_completions(document, complete_event)

    def tick_players(self, _):
        clients = ev.call_event("_get_player", raw=True)[0]
        self.options = {}
        for k in clients.keys():
            self.options[k] = None


players_completer = MyNestedCompleter({})


class Console:

    def __init__(self,
                 prompt_in="> ",
                 prompt_out="",
                 not_found="Command \"%s\" not found in alias.",
                 debug=False) -> None:
        self.__logger = get_logger("console")
        self.__run = False
        try:
            self.session = PromptSession(history=FileHistory('./.cmdhistory'))
            self.__legacy_mode = False
        except NoConsoleScreenBufferError:
            self.__legacy_mode = True
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
        self.completer = MyNestedCompleter(self.__alias)
        self.add_command("man", self.__create_man_message, i18n.man_message_man, i18n.help_message_man,
                         custom_completer={"man": {}})
        self.add_command("help", self.__create_help_message, i18n.man_message_help, i18n.help_message_help,
                         custom_completer={"help": {"--raw": False}})
        rcon = RCONSystem
        rcon.console = self
        self.rcon = rcon

    def __debug(self, *x):
        self.__logger.debug(' '.join(x))
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
        if x not in self.__alias:
            return i18n.man_command_not_found.format(x)
        return self.__man.get(x)

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

    def del_command(self, func):
        self.__debug(f"delete command: func={func};")
        keys = []
        for k, v in self.__func.items():
            if v['f'] is func:
                keys.append(k)
        for key in keys:
            self.__debug(f"Delete: key={key}")
            self.__alias.pop(key)
            self.__alias["man"].pop(key)
            self.__func.pop(key)
            self.__man.pop(key)
            self.__desc.pop(key)
        self.__debug("Deleted.")
        self.completer.load(self.__alias)

    def add_command(self, key: str, func, man: str = None, desc: str = None, custom_completer: dict = None) -> dict:
        if not isinstance(key, str):
            raise TypeError("key must be string")

        key = key.replace(" ", "-")
        self.__debug(f"added user command: key={key}; func={func};")
        self.__alias.update(custom_completer or {key: None})
        self.__alias["man"].update({key: None})
        self.__func.update({key: {"f": func}})
        self.__man.update({key: f'html:<seagreen>{i18n.man_for} <b>{key}</b>\n{man if man else "No page"}</seagreen>'})
        self.__desc.update({key: desc})
        self.completer.load(self.__alias)
        return self.__alias.copy()

    def _write(self, text):
        # https://python-prompt-toolkit.readthedocs.io/en/master/pages/printing_text.html#formatted-text
        if self.__legacy_mode:
            print(text)
            return
        assert isinstance(text, str)
        _type = text.split(":")[0]
        match _type:
            case "html":
                print_formatted_text(HTML(text[5:]))
            case "ansi":
                print_formatted_text(ANSI(text[5:]))
            case _:
                print_formatted_text(text)

    def write(self, s: AnyStr):
        if isinstance(s, (list, tuple)):
            for text in s:
                self._write(text)
        else:
            self._write(s)

    def log(self, s: AnyStr) -> None:
        # if isinstance(s, (list, tuple)):
        #     for text in s:
        #         self.__logger.info(f"{text}")
        # else:
        #     self.__logger.info(f"{s}")
        self.write(s)

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
        self.__debug(f"Used __builtins_print; is_run: {self.__run}")
        val = list(values)
        if len(val) > 0:
            if self.__run:
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
                print(e)
                cls.handleError(record)

        logging.StreamHandler.emit = emit

    def builtins_hook(self) -> None:
        self.__debug("used builtins_hook")

        builtins.Console = Console
        builtins.console = self

        # builtins.print = self.__builtins_print

    async def _parse_input(self, inp):
        cmd_s = inp.split(" ")
        cmd = cmd_s[0]
        if cmd == "":
            return True
        else:
            found_in_lua = False
            d = ev.call_lua_event("onConsoleInput", inp)
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

    async def _read_input(self):
        with patch_stdout():
            while self.__run:
                try:
                    inp = await self.session.prompt_async(
                        self.__prompt_in, completer=self.completer, auto_suggest=AutoSuggestFromHistory()
                    )
                    if await self._parse_input(inp):
                        continue
                except EOFError:
                    pass
                except KeyboardInterrupt:
                    self.__run = False
                except Exception as e:
                    self.__logger.error("Exception in console.py:")
                    self.__logger.exception(e)

    async def _read_input_legacy(self):
        while self.__run:
            try:
                inp = input(self.__prompt_in)
                if await self._parse_input(inp):
                    continue
            except UnicodeDecodeError:
                self.__logger.error("UnicodeDecodeError")
                self.__run = False
            except KeyboardInterrupt:
                self.__run = False
            except Exception as e:
                self.__logger.error("Exception in console.py:")
                self.__logger.exception(e)

    async def start(self):
        ev.register("serverTick_0.5s", players_completer.tick_players)
        # ev.register("get_players_completer", lambda _: players_completer)
        self.__run = True
        if self.__legacy_mode:
            await self._read_input_legacy()
        else:
            await self._read_input()
        self.__debug("Closing console.")
        raise KeyboardInterrupt

    def stop(self, *args, **kwargs):
        self.__run = False
