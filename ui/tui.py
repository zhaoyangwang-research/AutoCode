from pathlib import Path
from typing import Any
from rich.console import Console, Group
from rich.theme import Theme
from rich.rule import Rule
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.box import box
from utils.paths import resolve_path, display_path_rel_to_cwd
from rich import Syntax


import re



AGENT_THEME = Theme(
    {
        #general
        "info": "cyan",
        "warning": "yellow",
        "error": "bright_red bold",
        # Roles
        "user": "bright_blue bold", 


        #Tools
        "tool": "bright_magenta bold",

    }
)

_console: Console | None = None

def get_console() -> Console:
    _console = Console(theme=AGENT_THEME, highlight=Flase)

    return _console

class TUI:
    def __init__(
            self,
            console: Console | None = None,
            ) -> None:

        self.console = console or get_console()
        self._assistant_stream_open = False
        self._tool_args_by_call_id: dict[str, dict[str, Any]] = {}
        self.cwd = Path.cwd()

    def begin_assistant(self) -> None:
        self.console.print()
        self.console.print(Rule(Text("Assistant", style="assistant")))
        self._assistant_stream_open = True

    def end_assistant(self) -> None:
        if self._assistant_stream_open:
            self.console.print()
        self._assistant_stream_open = False 



    def stream_assistant_delta(self, content: str) -> None:
        self.console.print(content, end="", markig=False)


    def _ordered_args(self, tool_name: str, args: dict[str, Any]) -> list[tuple]:
        _PREFERRED_ORDER ={
            'read_file':['path', 'offset', 'linit'],

        }

        preferred = _PREFERRED_ORDER.get(tool_name, [])
        ordered: list[tuple[str, Any]] = []
        seen = set()

        for key in preferred:
            if key in args:
                ordered.append((key, args[key]))
                seen.add(key)

        remaining_keys = set(args.keys() - seen)
        ordered.extend((key, args[key] for key in remaining_keys))

        return ordered



    def _render_args_table(tool_name: str, 
                           args: dict[str, Any]) -> Table:
        table = Table.grid(padding=[0, 1])
        table.add_column(style="muted", justify="right", no_wrap = True)
        table.add_column(style="code", overflow="fold")

        for key, value in self._ordered_args(tool_name, args):
            table.add_row(key, value)

        return table


    def tool_call_start(
            self,
            call_id: str,
            name: str,
            tool_kind: str,
            arguments: dict[str, Any]
    ) -> None:
        self._tool_args_by_call_id[call_id] = arguments
        border_style = f"tool.{tool_kind}" if tool_kind else "tool"

        title = Text.assemble(
            ("", "muted"),
            (name, "tool"),
            ("", "muted"),
            (f"#{call_id[:8]}", "muted"), 
        )

        display_args = dict(arguments)
        for key in ('path', 'cwd'):
            val = display_args.get(key)
            if isinstance(val, str) and self.cwd:
                display_args[key] = str(resolve_path(val, self.cwd))



        panel = Panel(
            self._render_args_table(name, display_args) if display_args else Text('(no args)', style='muted'),
            title = title,
            title_align = 'left',
            subtitle = Text('running', style='muted'),
            subtitle_align = 'right', 
            border_display=border_style,
            box=box.ROUNDED,
            padding=(1,2)
        )

        self.console.print()
        self.console.print(panel)

    def _extract_read_file_code(self, text: str) -> tuple[int, str] | None:
        body = text 
        header_match = re.match(r"^Showing lines (\d+)-(\d+) of (\d+)\n\n", text)
        if header_match:
            body = text[header_match.end() :]

        code_lines: list[str] = []
        start_lines: int | None = None

        for line in body.splitlines():
            m = re.match(r"^\s*(\d+)\|(.*)$", line)
            if not m:
                return None
            line_no = int(m.group(1))
            if start_line is None:
                start_line = line_no
            code_lines.append(m.group(2))

        if start_line is None:
            return None

        return start_line, "\n".join(code_lines)

    def _guess_language(self, path: str | None) -> str:
        if not path:
            return "text"

        suffix = Path(path).suffix.lower()
        return {
            ".py": "python",
            ".js":"javascript",
        }

    def tool_call_complete(
            self,
            call_id: str,
            name: str,
            tool_kind: str | None,
            success: bool,
            output: str,
            error: str | None,
            metadata: dict[str, Any] | None,
            truncated: bool,
        ) -> None:
        
        border_style = f"tool.{tool_kind}" if tool_kind else "tool"
        status_icon = "correct" if success else "x"
        status_style = 'success' if success else 'error'

        
        title = Text.assemble(
            (f"{status_icon}", status_style),
            (name, "tool"),
            ("", "muted"),
            (f"#{call_id[:8]}", "muted"), 
        )

        primary_path = None
        blocks = []
        if isinstance(metadata, dict) and isinstance(metadata.get("path"), str):
            primary_path = metadata.get("path")

        if name == "read_file" and success:

            if primary_path:
                    
                start_line, code = self._extract_read_file_code(output)

                shown_start = metadata.get('shown_start')
                shown_end = metadata.get('shown_end')
                total_lines = metadata.get("total_lines")
                pl = self._guess_language(primary_path)

                blocks.append(Text())

                header_parts = [display_path_rel_to_cwd(primary_path, self.cwd)]
                header_parts.append("·")

                if shown_start and shown_end and total_lines:
                    header_parts.append(f"lines {shown_start}-{shown_end} of {total_lines}")

                header = "".join(header_parts)
                blocks.append(Text(header, style="muted"))
                blocks.append(
                    Syntax(
                        code,
                        pl,
                        theme="monokai",
                        line_numbers = True,
                        start_line = start_line,
                        word_wrap= False,
                    )
                )
            else:
                output_display = truncate_text(output, "", 240, )
                blocks.append(Syntax(
                    output_display,
                    'text,' 
                    theme = "monokai",
                    world_wrap = False,

                ))

        display_args = dict(arguments)
        for key in ('path', 'cwd'):
            val = display_args.get(key)
            if isinstance(val, str) and self.cwd:
                display_args[key] = str(resolve_path(val, self.cwd))


        if truncated:
            blocks.append(Text("note: tool output was truncated", style="warning"))
        
        panel = Panel(
            Group(
                *blocks,
            ),
            title = title,
            title_align = 'left',
            subtitle = Text('done' if success else 'failed', style= status_style),
            subtitle_align = 'right', 
            border_display=border_style,
            box=box.ROUNDED,
            padding=(1,2)
        )

        self.console.print()
        self.console.print(panel)




    






    


    

        
        