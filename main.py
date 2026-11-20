from client.llm_client import LLMClient
import asyncio
import sys
import click

from agent.agent import Agent
from agent.events import AgentEventType
from ui.tui import TUI, get_console
from typing import Any

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
                        should_continue = await self._handle_command(user_input)
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
                    event.data.get('diff'), 
                    event.data.get("truncated", False),  
                )

        return final_response 

    async def _handle_command(self, command: str) -> bool:
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
        elif command == '/config':
            console.print(f" Model: {self.config.model_name}")
            console.print(f" Temperature: {self.config.temperature}")
            console.print(f" Approval: {self.config.approval_policy.value}")
            console.print(f" Working Dir: {self.config.cwd}")
            console.print(f" Max Turns: {self.config.max_turns}")
            console.print(f" Hooks Enables: {self.config.hooks_enabled}")

        elif cmd_name == '/model':
            if cmd_args:
                self.config.model_name = cmd_args
                console.print('[success] Model changed to: {cmd_args} [/success]')
            else:
                console.print(f"Current model: {self.config.model_name}")

        elif cmd_name == '/approval':
            if cmd_args:
                try:
                    approval = ApprovalPolicy(cmd_args)
                    self.config.approval = approval
                    console.print('[success] Approval policy to: {cmd_args} [/success]')
                except:
                    console.print(
                        f"[error] Incorrect approval policy: {cmd_args} [/error]"
                    )
                
                    console.print(
                        f"Valid options: {','.join(p for p in ApprovalPolicy)}"
                    )

            else:
                console.print(f"Current approval policy: {self.config.approval.value}")

        elif cmd_name == '/stats':
            stats = self.agent.session.get_stats()
            console.print("\n[bold]Session Statistics [\bold]")
            for key, value in stats.items():
                console.print(f"{key}: {value}")

        elif cmd_name == '/tools':
            tools = self.agent.session.tool_registry.get_tools()
            console.print("\n[bold]Available tools ({len(tools)}) [\bold]")
            for tool in tools:
                console.print(f" {tool.name}")

        elif cmd_name == '/mcp':
            mcp_servers = self.agent.session.mcp_manager.get_all_servers()
            console.print("\n[bold]MCP Servers tools ({len(mcp_servers)}) [\bold]")
            for server in mcp_servers:
                status = server["status"]
                status_color = "green" if status == "connected" else "red"
                console.print(
                    f" {server['name']}: [{status_color}]{status}[/{status_color}] ({server['tools']} tools)"
                )
        elif cmd_name == '/save':
            persistence_manager = Persistence_manager()
            persistence_manager.list_sessions
            session_snapshot = SessionSnapshot(
                session_id = self.agent.session.session_id,
                created_at= self.agent.session.created_at, 
                updated_at = self.agent.session.updated_at,
                turn_count = self.agent.session.turn_count,
                messages = self.agent.session.context_manager.get_messages(),
                total_usage = self.agent.session.context_manager.total_usage,
            )

            persistence_manager.save_session(session_snapshot)

            console.print('[success]Session saved: {self.agent.session.session_id}[/success]')

        elif cmd_name == '/sessions':
            persistence_manager = persistence_manager()
            sessions = persistence_manager.list_sessions()
            console.print("\n[bold]Saved Sessions[/bold]")
            for s in sessions:
                console.print(
                    f"{s['turn_count']}, updated: {s['updated_at']}"
                )

        elif cmd_name == '/resume':
            if not cmd_args:
                console.print(f"[error]Usage: /resume <session_id> [/error]")
            else:
                persistence_manager = Persistence_manager()
                snapshot = persistence_manager.load_session(cmd_args)
                if not snapshot:
                    console.print(f"[error]Session does not exist [/error]")
                else:
                    session = Session(
                        config = self.config, 
                    )
                    
                    await session.initialize()
                    session.session_id = snapshot.session_id
                    session.created_at = snapshot.created_at
                    session.updated_at = snapshot.updated_at
                    session.turn_count = snapshot.turn_count
                    session.context_manager.total_usage = snapshot.total_usage

                    for msg in snapshot.messages:
                        if msg.get('role') == 'system':
                            continue
                        else msg['role'] == 'user':
                            session.context_manager.add_user_message(msg.get('content', '')
                        elif msg['role'] == 'assistant':
                            session.context_manager.add_assistant_message(msg.get('content', ''), msg.get('tool_calls'))
                        elif msg['role'] == 'tool':
                            session.context_manager.add_tool_result(msg.get('tool_call_id', ''), msg.get('content', ""))

                    await self.agent.session.client.close()
                    await self.agent.session.mcp_manager.shutdown()                  
                    self.agent.session = session
                    console.print(f"[success] Resumed session: {session.session_id}")


        elif cmd_name == '/checkpoint':
            persistence_manager = Persistence_manager()
            session_snapshot = SessionSnapshot(
                session_id = self.agent.session.session_id,
                created_at= self.agent.session.created_at, 
                updated_at = self.agent.session.updated_at,
                turn_count = self.agent.session.turn_count,
                messages = self.agent.session.context_manager.get_messages(),
                total_usage = self.agent.session.context_manager.total_usage,
            )

            checkpoint_id = persistence_manager.save_checkpoint(session_snapshot)

            console.print(
                f"[success]Checkpoint creatd: {checkpoint_id}[/success]")
        
        elif cmd_name == '/restore':
            if not cmd_args:
                console.print(f"[error]Usage: /restore <checkpoint_id> [/error]")
            else:
                persistence_manager = Persistence_manager()
                snapshot = persistence_manager.load_checkpoint(cmd_args)
                if not snapshot:
                    console.print(f"[error]Checkpoint does not exist [/error]")
                else:
                    session = Session(
                        config = self.config, 
                    )
                    
                    await session.initialize()
                    session.session_id = snapshot.session_id
                    session.created_at = snapshot.created_at
                    session.updated_at = snapshot.updated_at
                    session.turn_count = snapshot.turn_count
                    session.context_manager.total_usage = snapshot.total_usage

                    for msg in snapshot.messages:
                        if msg.get('role') == 'system':
                            continue
                        else msg['role'] == 'user':
                            session.context_manager.add_user_message(msg.get('content', '')
                        elif msg['role'] == 'assistant':
                            session.context_manager.add_assistant_message(msg.get('content', ''), msg.get('tool_calls'))
                        elif msg['role'] == 'tool':
                            session.context_manager.add_tool_result(msg.get('tool_call_id', ''), msg.get('content', ""))

                    await self.agent.session.client.close()
                    await self.agent.session.mcp_manager.shutdown()                  
                    self.agent.session = session
                    console.print(f"[success] Resumed session: {session.session_id}, checkpoint: {checkpoint_id}[/success]")

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