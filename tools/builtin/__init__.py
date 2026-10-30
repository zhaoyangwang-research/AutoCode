from tools.builtin.read_file import ReadFileTool
from tools.memory import    MemoryTool



__all__ = [
    "ReadFileTool"
    "MemoryTool"
    ]

def get_all_builtin_tools() -> list[type]:
    return[
        ReadFileTool, 
        MemoryTool
    ]