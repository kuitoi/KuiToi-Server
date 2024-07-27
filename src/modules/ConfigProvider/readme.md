### Builtins

```python
class Config:
    Auth: Dict[str, object]
    Game: Dict[str, object]
    Server: Dict[str, object]
    RCON: Dict[str, object]
    Options: Dict[str, object]
    enc: str | None
    def __repr__(self):
        return "%s(Auth=%r, Game=%r, Server=%r)" % (self.__class__.__name__, self.Auth, self.Game, self.Server)
class config (Config): ...
```