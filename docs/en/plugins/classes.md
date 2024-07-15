# Passed Classes

## Worth looking at

1. What are `*args` and `**kwargs`? -> [Post on Habr ↗](https://habr.com/ru/companies/ruvds/articles/482464/)

## KuiToi 
_`kt = KuiToi("PluginName"")`_

### kt.log
_Constant_\
Returns a pre-configured logger

### kt.name
_Constant_\
Returns the name of the plugin

### kt.dir
_Constant_\
Returns the directory of the plugin

### kt.open()
_Parameters are the same as for open()_\
Opens a file in kt.dir

### kt.register(event_name: str, event_func: function)
_`event_name: str` -> The name of the event that `event_func` will be called on._\
_`event_func: function` -> The function that will be called._

In `event_func`, you can pass both regular functions and async functions - you don't need to make them async beforehand.\
You can also create your own events with your own names.\
You can register an unlimited number of events.

### kt.call_event(event_name: str, *args, **kwargs) -> list:
_`event_name: str` -> The name of the event to call._\
_`*args, **kwargs` -> Arguments to be passed to the function._

### **async** kt.call_async_event(event_name: str, *args, **kwargs) -> list:
_`event_name: str` -> The name of the event to call._\
_`*args, **kwargs` -> Arguments to be passed to the function._\
_Must be called with `await`_

###### _I recommend familiarizing yourself with *args, **kwargs_, there is a link at the beginning
Data is passed to all events in the form of: `{"event_name": event_name, "args": args, "kwargs": kwargs}`\
`args: list` -> Represents an array of data passed to the event\
`kwargs: dict` -> Represents a dictionary of data passed to the event
The data will be returned from all successful attempts in an array.

### kt.call_lua_event(event_name: str, *args) -> list:
_`event_name: str` -> The name of the event to call._\
_`*args` -> Arguments to be passed to the function._

Added to support backward compatibility.\
The lua function is called with a direct transmission of arguments `lua_func(*args)`

### kt.get_player([pid: int], [nick: str]) -> Player | None:
_`pid: int` -> Player ID - The identifier of the player._\
_`nick: str` -> Player Nickname - The name of the player._

The method returns a player object by their `pid` or `nick`.\
If the player cannot be found, `None` will be returned.

### kt.get_players() -> List[Player] | list:

The method returns an array with all players.\
The array will be empty if there are no players.

### kt.players_counter() -> int:

The method returns the number of players currently online.

### kt.is_player_connected([pid: int], [nick: str]) -> bool:
_`pid: int` -> Player ID - The identifier of the player._\
_`nick: str` -> Player Nickname - The name of the player._

The method returns a player object by their `pid` or `nick`.

## Player (or Client)
_`pl = kt.get_player()`_\
_`pl = event_data['kwargs']['player']`_

### pl.log -> Logger
_Constant_\
Returns a preconfigured logger.

### pl.addr -> str
_Constant_\
Returns the player's IP address.

### pl.pid -> int
### pl.cid -> int
_Constant_\
Returns the client ID _(pid: PlayerId = cid: ClientId)_.

### pl.key -> str
_Constant_\
Returns the key passed during authorization.

### pl.nick -> str
_Variable_\
Nickname passed during authorization from the BeamMP server, can be changed, consequences are not tested.

### pl.roles -> str
_Variable_\
Role passed during authorization from the BeamMP server, can be changed (If the wrong role is set, unexpected behavior may occur.)

### pl.guest -> bool
_Constant_\
Returns whether the player is a guest, passed during authorization from the BeamMP server.

### pl.identifiers -> dict
_Constant_\
Identifiers passed during authorization from the BeamMP server.

### pl.ready -> bool
_Constant, changed by the core_\
Returns a bool value, if True -> player has downloaded all resources and loaded on the map.

### pl.cars -> dict
_Constant, changed by the core_\
Returns a dictionary of cars by type:

```python
{
    1: {
        "packet": car_packet,
        "json": car_json,
        "json_ok": bool(car_json),
        "snowman": snowman,
        "over_spawn": (snowman and allow_snowman) or over_spawn,
        "pos": {
            "pos":[0,0,0],
            "rvel":[0,0,0],
            "rot":[0,0,0],
            "vel":[0,0,0],
            "tim":0,
            "ping":0
        }
    },
    2: ...
}
```
Where `1` - car_id\
Where `pkt` - Unprocessed packet that came from the client (For very experienced users)\
Where `json` - Processed packet stored as dict\
Where `json_ok` - Whether the core was able to process the packet\
Where `snowman` - Is the car a snowman\
Where `over_spawn` - Is the car spawned over the limit (Allowed through plugins)\
Where `pos` - Car position (Passed through UDP)

### pl.last_position -> dict
_Constant, changed by the core_\
Returns the player's last position

### **async** pl.kick([reason: str = "Kicked!"]) -> None
_`reason: str` -> Kick reason. Parameter is optional, by default: `Kicked!`_\
Kicks the player from the server.

### **async** pl.send_message(message: str, [to_all: bool = True]) -> None
_`message: str` -> Message text, sent without "Server:"_\
_`to_all: bool` -> Should this message be sent to everyone? Parameter is optional, by default: `True`_\
Sends a message to the player or everyone.

### **async** pl.send_event(event_name: str, event_data: Any, [to_all: bool = True]) -> None
_`event_name: str` -> Name of the event that will be called_\
_`event_data: Any` -> Data sent to the event._\
_`to_all: bool` -> Should this message be sent to everyone? Parameter is optional, by default: `True`_\
Sends an event to the client.\
If event_data is a tuple, list, dict, then before sending the core converts it to JSON via json.dumps(event_data)\
Otherwise, the data will be a string without regulation.

### **async** pl.delete_car(self, car_id: int) -> None
_`car_id: int` -> Car ID_\
Deletes the player's car.
