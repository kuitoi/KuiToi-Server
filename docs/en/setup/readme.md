# Greetings from KuiToi Server

## Well, let's start

###### _(Here are the commands for Linux)_

* **Python 3.10.x** is required to run it! Only this version works, it won't work on Python 3.11...
* You can check your Python version like this (you have to laugh here):
```bash
python3 --version  # Python 3.10.6
```
* Clone the repository and navigate to it
* Install everything necessary
* Then, using my "script", remove all unnecessary files and move to the core source
```bash
git clone -b Stable https://github.com/kuitoi/KuiToi-Server.git && cd KuiToi-Server
pip install -r requirements.txt
mv ./src/ $HOME/ktsrc/ && rm -rf ./* && mv $HOME/ktsrc/* . && rm -rf $HOME/ktsrc
```
* Here's how you can check server info and start it:
```bash
python3 main.py --help  # Shows all available commands
python3 main.py # Starts the server
```

## Configuration

* After starting, `kuitoi.yaml` will be created
* By default, it looks like this:
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

* If you set `private: false` and don't set a `key`, the server will request a BeamMP key and won't start without it.
* After entering a BeamMP key, the server will appear in the launcher list.
* You can get the key here: [https://beammp.com/k/keys ↗](https://beammp.com/k/keys)

### Game

* `map` is only the name of the map, i.e. open the mod with the map in `map.zip/levels` - the name of the map will be there, that's what we insert.
* `cars` - Maximum number of cars per player
* `players` - Maximum number of players

### Options

* `debug` - Whether to output debug messages (for experienced users only, slightly reduces performance)
* `encoding` - Which encoding to use to open files
* `language` - Which language the server will start with (currently available: en, ru)
* `log_chat` - Whether to output chat to the console
* `speed_limit` - Download speed limit for mods (in MB/s)
* `use_lua` - Enable lua support
* `use_queue` - Download mods in queue, i.e. only 1 client can download at a time

### Server

* `description` - Server description for the BeamMP launcher
* `name` - Server name for the BeamMP launcher
* `server_ip` - IP address to assign to the server (for experienced users only, defaults to 0.0.0.0)
* `server_port` - On which port the server will work

### WebAPI
##### _Docs are not ready_