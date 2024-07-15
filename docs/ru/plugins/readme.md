# Система плагинов

### Ивенты: [тут](./events_list.md)
### Классы: [тут](./classes.md)

## Установка библиотеки с "Заглушками"
###### (Это значит, что не будет работать без сервера, но IDE подскажет API)
###### (Библиотека ещё в разработке)

* Используя pip:\
    `$ pip install KuiToi`
* Из исходников:\
    `git clone https://github.com/KuiToi/KuiToi-PyLib`

## Пример

```python
try:
    import KuiToi
except ImportError:
    pass

kt = KuiToi("ExamplePlugin")
log = kt.log

def my_event_handler(event_data):
    log.info(f"{event_data}")

def load():
    # Инициализация плагина
    ev.register("my_event", my_event_handler)
    log.info("Плагин загружен успешно.")

    
def start():
    # Запуск процессов плагина
    ev.call_event("my_event")
    ev.call_event("my_event", "Some data", data="some data too")
    log.info("Плагин запустился успешно.")


def unload():
    # Код завершающий все процессы
    log.info("Плагин выгружен успешно.")
```
Так же более обширный пример можно найти в [example.py](examples/example.py)

* Рекомендуется использовать `open()` после `load()`, иначе стоит использовать `kt.load()` - Создаёт файл в папке `plugin/<plugin_name>/<filename>`
* Создание своего ивента : `kt.register("my_event", my_event_function)` - 
* Вызов ивента: `kt.call_event("my_event")`
* Вызов ивента с данными: `kt.call_event("my_event", data, data2=data2)`
* Базовые ивенты: _Позже напишу_

## Async функции

Поддержка async есть

```python
try:
    import KuiToi
except ImportError:
    pass

kt = KuiToi("Example")
log = kt.log


async def my_event_handler(event_data):
    log.info(f"{event_data}")

    
async def load():
    # Инициализация плагина
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

```

Так же более обширный пример можно найти в [async_example.py](examples/async_example.py)

* Создание своего ивента: `kt.register("my_event", my_event_function)` (в register стоит проверка на функцию)
* Вызов async ивента: `kt.call_async_event("my_event")`
* Вызов async ивента: `kt.call_async_event("my_event", data, data2=data2)`
* Базовые async ивенты: _Позже напишу_
