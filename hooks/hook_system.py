from config.config import Config


class HookSystem:
    def __init__(self, config: Config):
        self.config = config
        self.hooks: list[HookConfig] = []

        if self.config.hooks_enabled:
            self.hooks = [hook for hook in self.config.hooks if hook.enabled]

    async def _run_hook(self, hook: HookConfig)-> None:
        if hook.command:
            process = await asyncio.create_subprocess_exec(
                hook.command,
                stdout = asyncio.subprocess.PIPE,
                stderr = asyncio.subprocess.PIPE,
                cwd = self.config.cwd,
                env = os.environ.copy(),
                start_new_session = True,
                )

            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    process.communicate(),
                    timeout=hook.timeout_sec,
                )
            except asyncio.TimeoutError:
                if sys.platform != "win32":
                    os.killpg(os.getpdig(process.pid), signal.SIGKILL)
                else:
                    process.kill()
                await process.wait()

        else:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write("#!/bin/bash\n")
                f.write(hook.script)
                sc
            

            

    async def trigger_before_agent(self, user_message: str) -> None:
        for hook in self.hooks:
            if hook.trigger == HookTrigger.Before_Agent:
                self._run_hook(hook)

        

