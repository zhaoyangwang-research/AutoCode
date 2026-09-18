from rich.console import Console
from rich.theme import Theme

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

    def stream_assistant_delta(self, content: str) -> None:
        self.console.print(content, end="", markig=False)

        
        