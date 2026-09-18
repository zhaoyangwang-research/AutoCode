from rich.console import Console
from rich.theme import Theme
from rich.rule import Rule
from rich.text import Text


AGENT_THEME = Theme(
    {
        #general
        "info": "cyan",
        "warning": "yellow",
        "error": "bright_red bold",
        # Roles
        "user": "bright_blue bold"


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

        
        