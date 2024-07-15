# 插件系统

### 事件：[这里](./events_list.md)
### 类：[这里](./classes.md)

## 使用带有“Dummy”的库
###### （这意味着它没有服务器无法工作，但IDE将指导API）
###### （库还在开发中）

* 使用pip：\
    `$ pip install KuiToi`
* 从源代码安装：\
    `git clone https://github.com/KuiToi/KuiToi-PyLib`

## 示例

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
    # 初始化插件
    ev.register("my_event", my_event_handler)
    log.info("插件已成功加载。")

    
def start():
    # 启动插件进程
    ev.call_event("my_event")
    ev.call_event("my_event", "一些数据", data="一些数据也是")
    log.info("插件已成功启动。")


def unload():
    # 结束所有进程的代码
    log.info("插件已成功卸载。")
```

您还可以在[example.py](examples/example.py)中找到更广泛的示例。

* 建议在`load()`后使用`open()`，否则应使用`kt.load()`-在`plugin/<plugin_name>/<filename>`文件夹中创建一个文件
* 创建自己的事件：`kt.register("my_event", my_event_function)`-
* 调用事件：`kt.call_event("my_event")`
* 使用数据调用事件：`kt.call_event("my_event", data, data2=data2)`
* 基本事件：_稍后会写_

## 异步函数

支持async

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
    # 初始化插件
    ev.register("my_event", my_event_handler)
    log.info("插件已成功加载。")


async def start():
    # 启动插件进程
    await ev.call_async_event("my_event")
    await ev.call_async_event("my_event", "一些数据", data="一些数据也是")
    log.info("插件已成功启动。")


async def unload():
    # 结束所有进程的代码
    log.info("插件已成功卸载。")

```

您还可以在[async_example.py](examples/async_example.py)中找到更广泛的示例。

* 创建自己的事件：`kt.register("my_event", my_event_function)`（在register中检查函数）
* 调用async事件：`kt.call_async_event("my_event")`
* 使用数据调用async事件：`kt.call_async_event("my_event", data, data2=data2)`
* 基本的async事件：_稍后会写_
