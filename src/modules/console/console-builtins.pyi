class Console(object):

    def __init__(self,
                 prompt_in: str = ">",
                 prompt_out: str = "]:",
                 not_found: str = "Command \"%s\" not found in alias.") -> None: ...

    def __getitem__(self, item): ...
    @property
    def alias(self) -> dict: ...
    def add(self, key: str, func: function) -> dict: ...
    def log(self, s: str, r='\r') -> None: ...
    def write(self, s: str, r='\r') -> None: ...
    def __lshift__(self, s: AnyStr) -> None: ...
    def logger_hook(self) -> None: ...
    def builtins_hook(self) -> None: ...
    async def start(self) -> None: ...

class console(object):

    @staticmethod
    def alias() -> dict: ...
    @staticmethod
    def add_command(key: str, func: function) -> dict: ...

    @staticmethod
    async def start() -> None: ...

    @staticmethod
    def builtins_hook() -> None: ...
    @staticmethod
    def logger_hook() -> None: ...

    @staticmethod
    def log(s: str) -> None: ...
    @staticmethod
    def write(s: str) -> None: ...
    @staticmethod
    def __lshift__(s: AnyStr) -> None: ...
