# 传递的类

## 值得一读

1. 什么是“*args”和“**kwargs”？ -> [habr上的文章 ↗](https://habr.com/ru/companies/ruvds/articles/482464/)

## KuiToi 
_`kt = KuiToi("PluginName"")`_

### kt.log
_常量_\
返回预配置的记录器

### kt.name
_常量_\
返回插件名称

### kt.dir
_常量_\
返回插件文件夹

### kt.open()
_与open()参数相同_\
在kt.dir中打开文件

### kt.register(event_name: str, event_func: function)
_`event_name: str` -> 作为`event_func`调用的事件名称._\
_`event_func: function` -> 要调用的函数._

在`event_func`中，可以传递普通函数或async - 不需要提前进行await。\
您也可以创建自己的事件，并使用自己的名称注册任意数量的事件。

### kt.call_event(event_name: str, *args, **kwargs) -> list:
_`event_name: str` -> 要调用的事件名称._\
_`*args, **kwargs` -> 要传递给函数的参数._

### **async** kt.call_async_event(event_name: str, *args, **kwargs) -> list:
_`event_name: str` -> 要调用的事件名称._\
_`*args, **kwargs` -> 要传递给函数的参数._\
_需要用`await`调用_

###### _建议阅读*args, **kwargs，链接在开头_
所有事件的数据都以以下格式传递：`{"event_name": event_name, "args": args, "kwargs": kwargs}`\
`args: list` -> 表示传递到事件中的数据数组\
`kwargs: dict` -> 表示传递到事件中的数据字典
数据将以数组形式从所有成功的波动中返回。

### kt.call_lua_event(event_name: str, *args) -> list:
_`event_name: str` -> 要调用的事件名称._\
_`*args` -> 要传递给函数的参数._

添加用于向后兼容性。\
lua函数使用直接传递参数`lua_func(*args)`进行调用。

### kt.get_player([pid: int], [nick: str]) -> Player | None:
_`pid: int` -> Player ID - 玩家标识符._\
_`nick: str` -> Player Nick - 玩家昵称._

该方法通过其`pid`或`nick`返回玩家对象。\
如果无法找到玩家，则返回 `None`。

### kt.get_players() -> List[Player] | list:

该方法返回所有玩家的数组。\
如果没有玩家，则数组将为空。

### kt.players_counter() -> int:

该方法返回在线的玩家数量。

### kt.is_player_connected([pid: int], [nick: str]) -> bool:
_`pid: int` -> Player ID - 玩家标识符._\
_`nick: str` -> Player Nick - 玩家昵称._

该方法通过其`pid`或`nick`返回玩家对象。

## Player (或 Client)
_`pl = kt.get_player()`_\
_`pl = event_data['kwargs']['player']`_

### pl.log -> Logger
_常量_\
返回预配置的记录器

### pl.addr -> str
_常量_\
返回玩家的 IP 地址

### pl.pid -> int
### pl.cid -> int
_常量_\
返回客户端的 ID _(pid: PlayerId = cid: ClientId)_

### pl.key -> str
_常量_\
返回在身份验证期间传递的密钥

### pl.nick -> str
_变量_\
从 BeamMP 服务器传递的昵称，可以更改，后果未知

### pl.roles -> str
_变量_\
从 BeamMP 服务器传递的角色，可以更改（如果设置了不正确的角色，可能会发生意外情况。）

### pl.guest -> bool
_常量_\
返回玩家是否为游客，从 BeamMP 服务器传递

### pl.identifiers -> dict
_常量_\
标识符，从 BeamMP 服务器传递。

### pl.ready -> bool
_常量，由核心更改_\
返回布尔值，如果为 True-> 玩家已下载所有资源，在地图上加载

### pl.cars -> dict
_常量，由核心更改_\
按类型返回汽车字典：

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
其中 `1` - car_id\
其中 `pkt` - 未处理的从客户端收到的数据包（仅供非常有经验的用户使用）\
其中 `json` - 以 dict 形式存储的已处理的数据包\
其中 `json_ok` - 核心是否能够处理数据包\
其中 `snowman` - 车辆是否为雪人\
其中 `over_spawn` - 车辆是否超过了生成限制（通过插件允许）\
其中 `pos` - 车辆位置（通过 UDP 传递）

### pl.last_position -> dict
_常量，由核心更改_
返回玩家的最后位置


### **async** pl.kick([reason: str = "Kicked!"]) -> None
_`reason: str` -> 踢出理由，参数可选，默认值为 `Kicked!`_
将玩家踢出服务器

### **async** pl.send_message(message: str, [to_all: bool = True]) -> None
_`message: str` -> 消息文本，不带 "Server:"_
_`to_all: bool` -> 是否向所有人发送此消息？参数可选，默认值为 `True`_
向玩家或所有人发送消息

### **async** pl.send_event(event_name: str, event_data: Any, [to_all: bool = True]) -> None
_`event_name: str` -> 要调用的事件名称_
_`event_data: Any` -> 发送到事件的数据。_
_`to_all: bool` -> 是否向所有人发送此消息？参数可选，默认值为 `True`_
将事件发送到客户端。\
如果 event_data 是 tuple、list、dict，则核心会通过 json.dumps(event_data) 将其转换为 json，然后再发送。\
否则，数据将是字符串，不受限制；

### **async** pl.delete_car(self, car_id: int) -> None
_`car_id: int` -> 要删除的车辆的 ID_
删除玩家的车辆