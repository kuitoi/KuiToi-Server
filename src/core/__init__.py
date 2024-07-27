# Developed by KuiToi Dev
# File core.__init__.py
# Written by: SantaSpeen
# Version 1.5
# Core version: 0.4.5
# Licence: FPA
# (c) kuitoi.su 2024

__title__ = 'KuiToi-Server'
__description__ = 'BeamingDrive Multiplayer server compatible with BeamMP clients.'
__url__ = 'https://github.com/kuitoi/kuitoi-Server'
__version__ = '0.4.8 (pre)'
__build__ = 2511  # Я это считаю лог файлами
__author__ = 'SantaSpeen'
__author_email__ = 'admin@kuitoi.su'
__license__ = "FPA"
__copyright__ = 'Copyright 2024 © SantaSpeen (Maxim Khomutov)'

import asyncio
import builtins
import webbrowser

import prompt_toolkit.shortcuts as shortcuts

from .utils import get_logger
from core.core import Core
from main import parser
from modules import ConfigProvider, EventsSystem
from modules import Console
from modules import MultiLanguage

args, _ = parser.parse_known_args()
if args.version:
    print(f"{__title__}:\n\tVersion: {__version__}\n\tBuild: {__build__}")
    exit(0)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
log = get_logger("core.init")

# Config file init
config_path = "kuitoi.yml"
if args.config:
    config_path = args.config
config_provider = ConfigProvider(config_path)
config = config_provider.read()
builtins.config = config
config.enc = config.Options['encoding']
if config.Options['debug'] is True:
    utils.set_debug_status()
    log = get_logger("core.init")
    log.info("Debug mode enabled!")
log.debug(f"Server config: {config}")
# i18n init
log.debug("Initializing i18n...")
ml = MultiLanguage()
ml.set_language(args.language or config.Options['language'])
ml.builtins_hook()

log.debug("Initializing EventsSystem...")
ev = EventsSystem()
ev.builtins_hook()
ev.register("get_version", lambda _: {"version": __version__, "build": __build__})

log.info(i18n.hello)
log.info(i18n.config_path.format(config_path))

log.debug("Initializing BeamMP Server system...")
# Key handler..
if not config.Auth['private'] and not config.Auth['key']:
    log.warn(i18n.auth_need_key)
    url = "https://keymaster.beammp.com/login"
    if shortcuts.yes_no_dialog(
            title='BeamMP Server Key',
            text=i18n.GUI_need_key_message,
            yes_text=i18n.GUI_yes,
            no_text=i18n.GUI_no).run():
        try:
            log.debug("Opening browser...")
            webbrowser.open(url, new=2)
        except Exception as e:
            log.error(i18n.auth_cannot_open_browser.format(e))
            log.info(i18n.auth_use_link.format(url))
            shortcuts.message_dialog(
                title='BeamMP Server Key',
                text=i18n.GUI_cannot_open_browser.format(url),
                ok_text=i18n.GUI_ok).run()

    config.Auth['key'] = shortcuts.input_dialog(
        title='BeamMP Server Key',
        text=i18n.GUI_enter_key_message,
        ok_text=i18n.GUI_ok,
        cancel_text=i18n.GUI_cancel).run()
    config_provider.save()
if not config.Auth['private'] and not config.Auth['key']:
    log.error(i18n.auth_empty_key)
    log.info(i18n.stop)
    exit(1)

# Console Init
log.debug("Initializing console...")
console = Console()
console.builtins_hook()
console.logger_hook()
console.add_command("stop", console.stop, i18n.man_message_stop, i18n.help_message_stop)
console.add_command("exit", console.stop, i18n.man_message_exit, i18n.help_message_exit)

builtins.B = 1
builtins.KB = B * 1024
builtins.MB = KB * 1024
builtins.GB = MB * 1024
builtins.TB = GB * 1024
