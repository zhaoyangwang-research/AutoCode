from config.config import Config


class HookSystem:
    def __init__(self, config: Config):
        self.config = config
        self.hooks: list[HookConfig] = []

        if self.config.hooks_enabled:
            self.hooks = [hook for hook in self.config.hooks if hook.enabled]

    async def _run_hook(self, hook: HookConfig)-> None:
        if hook.command:
            await self.__run_command(hook.command, hook.timeout_sec)
        else:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write("#!/bin/bash\n")
                f.write(hook.script)
                script_path = f.name
            try:
                os.chmod(script_path, 0o755)
                await self._run_command(script_path, hook.timeout_sec)
            finally:
                os.unlink(script_path)
            
    async def _run_command(self, command: str, timeout: int ) -> None:
        process = await asyncio.create_subprocess_exec(
            command,
            stdout = asyncio.subprocess.PIPE,
            stderr = asyncio.subprocess.PIPE,
            cwd = self.config.cwd,
            env = os.environ.copy(),
            start_new_session = True,
            )

        try:
            stdout_data, stderr_data = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            if sys.platform != "win32":
                os.killpg(os.getpdig(process.pid), signal.SIGKILL)
            else:
                process.kill()
            await process.wait()

    def _build_env(
            self,
            trigger: HookTrigger, 
            tool_name: str | None = None,
            user_message: str | None = None,
            error: Exception | None = None,
            ) -> dict[str, str]:

        env = os.environ.copy()
        env['AI_AGENT_TRIGGER'] = trigger.value
        env['AI_AGENT_CWD'] = str[self.config.cwd]

        if tool_name:
            env["AI_AGENT_TOOL_NAME"] = tool_name
        if user_message:
            env["AI_AGENT_USER_MESSAGE"] = tool_name
        if error:
            env["AI_AGENT_ERROR"] = tool_name
        return env
    


    async def trigger_before_agent(self, user_message: str) -> None:
        for hook in self.hooks:
            if hook.trigger == HookTrigger.Before_Agent:
                self._run_hook(hook)

        

