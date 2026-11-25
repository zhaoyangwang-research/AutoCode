from tools.builtin.read_file import ReadFileTool
from tools.builtin.write_file import WriteFileTool
from tools.builtin.edit_file import EditTool
from tools.builtin.shell import ShellTool
from tools.builtin.list_dir import ListDirTool
from tools.memory import MemoryTool

__all__ = [
    "ReadFileTool",
    "WriteFileTool",
    "EditTool",
    "ShellTool", 
    "ListDirTool", 
    "MemoryTool"
    ]


def get_all_builtin_tools() -> list[type]:
    return[
        ReadFileTool, 
        WriteFileTool,
        EditTool,
        ShellTool, 
        ListDirTool,
        MemoryTool
    ]


