import json

try:
    import KuiToi
except ImportError:
    pass

kt = KuiToi("Example")
log = kt.log
config = {"config_version": 0.1, "sql": {"enabled": False, "host": "127.0.0.1", "port": 3363, "database": "fucklua"}}
cfg_file = "config.json"


async def my_event_handler(event_data):
    log.info(f"{event_data}")


async def load():
    # Инициализация плагина
    with open(cfg_file, 'w') as f:
        json.dump(config, f)
        cgf = config
    log.info(cgf)
    ev.register("my_event", my_event_handler)
    log.info("Плагин загружен успешно.")


async def start():
    # Запуск процессов плагина
    await ev.call_async_event("my_event")
    await ev.call_async_event("my_event", "Some data", data="some data too")
    log.info("Плагин запустился успешно.")


async def unload():
    # Код завершающий все процессы
    log.info("Плагин выгружен успешно.")
