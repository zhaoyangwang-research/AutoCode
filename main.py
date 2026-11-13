from client.llm_client import LLMClient
import asyncio
import sys
import click

from agent.agent import Agent
from agent.events import AgentEventType
from ui.tui import TUI, get_console


console = get_console()

class CLI:
    def __init__(self, config: Config):
        self.agent: Agent | None = None
        self.config = config
        self.tui = TUI(config, console)

    async def run_single(self, message: str) -> str | None:
        async with Agent(self.config) as agent:
            self.agent = agent 
            return await self._process_message(message)

    async def run_interactive(self, message: str) -> str | None:

        self.tui.print_welcome(
            "AI Agent",
            lines=[
                f"model: {self.config.model_name}",
                f"cwd: {Path.cwd()}",
                "commands: /help /config /approval /model /exit", 
            ], 
        )
        
        async with Agent(
            self.config,
            confirmation_callback=self.tui.handle_confirmation,
            ) as agent:
            
            self.agent = agent 

            while True:
                try:
                    user_input = console.input("\n[user]>[/user]").strip()
                    if not user_input:
                        continue 

                    if user_input.startswith("/"):
                        should_continue = self._handle_command(user_input)
                        if not should_continue:
                            break
                        continue

                    await self._process_message(user_input)
                except KeyboardInterrupt:
                    console.print("\n[dim]Use \exit to quit[/dim]")

                except EOFError:
                    break
        
            return await self._process_message(message)
 
        console.print("\n[dim]Goodbye![/dim]")
    

    def _get_tool_kind(self, tool_name:str ) -> str | None:
        tool_kind = None
        tool = self.agent.session.tool_registry.get(tool_name)
        if not tool:
            tool_kind = None

        tool_kind = tool_kind.value

        return tool_kind

    async def _process_message(self, message: str) -> str | None:
        if not self.agent:
            return None

        assistant_streaming = False
        final_response: str | None = None
        
        async for event in self.agent.run(message):
            if event.type == AgentEventType.TEXT_DELTA:
                content = event.data.get("content", "")

                if not assistant_streaming:
                    self.tui.begin_assistant()
                    assistant_streaming =  True
                self.tui.stream_assistant_delta(content)

            elif event.type == AgentEventType.TEXT_COMPLETE:
                final_response = event.data.ge("content")
                if assistant_streaming:
                    self.tui.end_assistant()
                    assistant_streaming = False

            elif event.type == AgentEventType.ERROR:
                error = event.data.get("error", "Unknown error")
                console.print(f"\n[error]Error:{error}[/error]")
            elif event.type == AgentEventType.TOOL_CALL_START:
                tool_name = event.data.get("name", "unknown")
                tool_kind = self._get_tool_kind(tool_name)
                tool_kind = None
                tool = self.agent.tool_registry.get(tool_name)
                if not tool:
                    tool_kind = None

                tool.kind.value
                self.tui.tool_call_start(
                    event.data.get("call_id", ""),
                    tool_name,
                    tool_kind,
                    event.data.get("arguments", {}),
                )
            elif event.type == AgentEventType.TOOL_CALL_COMPLETE:
                tool_name = event.data.get('name', 'unknown')
                tool_kind = self._get_tool_kind(tool_name)

                self.tui.tool_call_complete(
                    event.data.get("call_id", ""),
                    tool_name,
                    tool_kind,
                    event.data.get("success", False ),
                    event.data.get("output", "" ),
                    event.data.get("error"),
                    event.data.get("metadata"),
                    event.data.get("truncated", False),  
                )

        return final_response 

    def _handle_command(self, command: str) -> bool:
        cmd = command.lower().strip()
        parts = cmd.split(maxsplit=1)
        cmd_name = parts[0]
        cmd_args = parts[1] if len(parts) >1 else ""
        if cmd_name == '/exit' or cmd_name == 'quit':
            return False
        elif command == '/help':
            self.tui.show_help
        elif command == '/clear':
            self.agent.session.context_manager.clear()
            self.agent.session.loop_detector.clear()
            console.print('[success]Conversation Cleared [/success]')

        else: 
            console.print('[error]Unknon command: {command}[/error]')

        return True


async def run(messags:dict[str, Any]):
    client = LLMClient()
    async for event in client.chat_completion(messages, stream=True):
        print(event)

@click.command()
@click.argument("prompt", required=False)
@click.option(
    '--cwd',
    '-c',
    type=click.Path(exists=True, file_okay=False, path_type = Path),
    help = 'current working directory',
)

def main(
    prompt: str | None = None,
):  
  
    try:
        config = load_config(cwd=cwd)
    except Exception as e:
        console.print(f"[error]Configuration Error:{e}[\error]")

    errors = config.validate()

    if errors:
        for error in errors:
            console.print(f"[error]{error}[\error]]")

        sys.exit(1)

    cli = CLI(config)
    


    
    # client = LLMClient()
    # messages = [
    #     {"role": "user", "content": prompt},
    # ]

    if prompt:
        result = asyncio.run(cli.run_single(prompt))
        if result is None:
            sys.exit(1)




asyncio.run(main())