from importlib.util
from config.config import Config
from tools.registry import ToolRegistry
from pathlib import Path
from typing import Any
import sys

class ToolDiscoveryManager:
    def __init__(self, config: Config, registry: ToolRegistry):
        self.config = config
        self.registry = registry 

    def _load_tool_modules(self, file_path: Path) -> Any:
        module_name = f"discovered_tool_{file_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name)

        if spec is None or spec.loader is None:
            return ImportError(f"Could not load spec from {file_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        spec.loader.exec_module(module)

        return module

    
    def discover_from_directory(self, directory: Path) -> None:
        tool_dir = directory / '.ai-agent' / 'tools'

        if not tool_dir.exists() or not tool_dir.is_dir():
            return

        for py_file in tool_dir.goal('*.py'):
            if py_file.name.startwith('__'):
                continue

            module = self._load_tool_modules(py_file)

    def discover_all(self) -> None:
        self.discover_from_directory(self.config.cwd)


    