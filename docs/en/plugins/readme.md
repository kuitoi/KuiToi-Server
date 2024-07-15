Это описание системы плагинов для KuiToi сервера на Python:

## Events
### Events list: [here](./events_list.md)

## Classes
### Classes list: [here](./classes.md)

## Installing the library with "stubs"
###### (This means it won't work without the server, but your IDE will suggest the API)
###### (The library is still in development)

* Using pip:\
    `$ pip install KuiToi`
* From source:\
    `git clone https://github.com/KuiToi/KuiToi-PyLib`

## Example

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
    # Plugin initialization
    kt.register("my_event", my_event_handler)
    log.info("Plugin loaded successfully.")

    
def start():
    # Starting plugin processes
    kt.call_event("my_event")
    kt.call_event("my_event", "Some data", data="some data too")
    log.info("Plugin started successfully.")


def unload():
    # Code that ends all processes
    log.info("Plugin unloaded successfully.")
```

A more comprehensive example can also be found in [example.py](examples/example.py)

* It is recommended to use `open()` after `load()`, otherwise use `kt.load()` - It creates a file in the `plugin/<plugin_name>/<filename>` folder.
* Creating your own event: `kt.register("my_event", my_event_function)` - 
* Calling an event: `kt.call_event("my_event")`
* Calling an event with data: `kt.call_event("my_event", data, data2=data2)`
* Base events: _To be added later_

## Async functions

Async support is available

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
    # Plugin initialization
    kt.register("my_event", my_event_handler)
    log.info("Plugin loaded successfully.")


async def start():
    # Starting plugin processes
    await kt.call_async_event("my_event")
    await kt.call_async_event("my_event", "Some data", data="some data too")
    log.info("Plugin started successfully.")


async def unload():
    # Code that ends all processes
    log.info("Plugin unloaded successfully.")

```

A more comprehensive example can also be found in [async_example.py](examples/async_example.py)

* Creating your own event: `kt.register("my_event", my_event_function)` (register has a function check)
* Calling an async event: `kt.call_async_event("my_event")`
* Calling an async event with data: `kt.call_async_event("my_event", data, data2=data2)`
* Base async events: _To be added later_