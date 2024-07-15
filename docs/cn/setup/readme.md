# 来自 KuiToi 服务器的问候

## 好的，让我们开始吧

###### _(这里是 Linux 的命令)_

* 运行它需要 **Python 3.10.x**！只有这个版本才能运行，Python 3.11 不支持...
* 您可以像这样检查 Python 版本（你要在这里笑）：
```bash
python3 --version  # Python 3.10.6
```
* 克隆存储库并导航到它
* 安装所有必需的内容
* 然后，使用我的“脚本”，删除所有不必要的文件并移动到核心源
```bash
git clone -b Stable https://github.com/kuitoi/KuiToi-Server.git && cd KuiToi-Server
pip install -r requirements.txt
mv ./src/ $HOME/ktsrc/ && rm -rf ./* && mv $HOME/ktsrc/* . && rm -rf $HOME/ktsrc
```
* 这是如何检查服务器信息并启动它的方法：
```bash
python3 main.py --help  # 显示所有可用命令
python3 main.py # 启动服务器
```

## 配置

* 启动后，将创建 `kuitoi.yaml`
* 默认情况下，它如下所示：
```yaml
!!python/object:modules.ConfigProvider.config_provider.Config
Auth:
  key: null
  private: true
Game:
  map: gridmap_v2
  cars: 1
  players: 8
Options:
  debug: false
  encoding: utf-8
  language: en
  log_chat: true
  speed_limit: 0
  use_lua: true
  use_queue: false
Server:
  description: Welcome to KuiToi Server!
  name: KuiToi-Server
  server_ip: 0.0.0.0
  server_port: 30814
WebAPI:
  enabled: false
  secret_key: 3838ccb03c86cdb386b67fbfdcba62d0
  server_ip: 127.0.0.1
  server_port: 8433
```
### Auth

* 如果您将 `private: false` 并且不设置 `key`，服务器将请求一个 BeamMP 密钥，没有它无法启动。
* 输入 BeamMP 密钥后，服务器将出现在启动器列表中。
* 您可以在此处获取密钥：[https://beammp.com/k/keys ↗](https://beammp.com/k/keys)

### Game

* `map` 仅为地图名称，即打开具有地图的 mod 在 `map.zip/levels` - 地图名称将在那里，那就是我们插入的地方。
* `cars` - 每个玩家的最大汽车数量
* `players` - 最大玩家数

### Options

* `debug` - 是否输出调试消息（仅适用于有经验的用户，会略微降低性能）
* `encoding` - 使用哪种编码打开文件
* `language` - 服务器将使用哪种语言启动（当前可用：en，ru）
* `log_chat` - 是否将聊天输出到控制台
* `speed_limit` - 下载 mod 的下载速度限制（以 MB/s 为单位）
* `use_lua` - 启用 lua 支持
* `use_queue` - 按队列下载 mod，即一次只能下载一个客户端

### Server

* `description` - BeamMP 启动器的服务器描述
* `name` - BeamMP 启动器的服务器名称
* `server_ip` - 分配给服务器的 IP 地址（仅适用于有经验的用户，默认为 0.0.0.0）
* `server_port` - 服务器将在哪个端口上工作

### WebAPI
##### _文档尚未准备好_