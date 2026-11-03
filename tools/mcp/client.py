from enum import Enum
from pathlib import Path
from config.config import MCPServeConfig

class MCPServerStatus(str, Enum):
    DISCOUNTED = 'disconnected'
    CONNECTING = 'connecting'
    CONNECTED = 'connected'
    ERROR = 'error'


class MCPClient:
    def __init__(
            self,
            name: str,
            config: MCPServeConfig,
            cwd, Path,
    ) -> None:
        self.name = name
        self.config = config 
        self.cwd = cwd

        

