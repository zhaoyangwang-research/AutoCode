from tools.base import Tool
from config.config import Config
from dataclasses import dataclass
from pydantic import BaseModel, Field



class SubagentParams(BaseModel):
    goal: str = Field(
        ..., description = "The specific task or goal for the subagent to accomplish"
    )

    
@dataclass
class SubagentDefinition:
    name: str
    desciption: str
    goal_prompt: str
    allowed_tools: list[str] | None= None
    max_turns: int = 20 
    timeout_seconds: float = 600


class SubagentTool(Tool):
    def __init__(self, config: Config,
                 definition: SubagentDefinition):
        super().__init__(config)
        self.definition = definition

    @property 
    def name(self) -> str:
        return f"subagent_{self.definition.description}"

    @property 
    def description(self) -> str:
        return f"subagent_{self.definition.description}"

    schema = SubagentParams

    def is_mutating(self, params: dict[str, Any]) -> bool:
        return True

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = SubagentParams(**invocation.params)
        if not params.goal:
            return ToolResult.error_result("No goal specified for sub-agent")

        config_dict = self.config.to_dict()
        config_dict['max_turns'] = self.definition.max_turns

        if self.definition.allowed_tools:
            config_dict['allowed_tools'] = self.definition.allowed_tools

        subagent_config = Config(**config_dict)

        prompt = f"""you are a specialized sub-agent with a specific task to complete.

        {self.definiton.goal_prompt}

        YOUR TASK:
        {params.goal}

        IMPORTANT:
        - Focus only on completing the specified task
        - Do not enage in unrelated actions
        - Once you have completed the task or have the answer, provide your final response
        - Be concise and direct in your output 
        """
        tool_calls = []
        final_response = None
        error = None
        terminate_response = 'goal'

        try:
            async with Agent(subagent_config) as agent:

                deadline = asyncio.get_event_loop().time + self.definition.timeout_seconds
                async for event in agent.run(prompt):
                    if asyncio.get_event_loop().time() > deadline:
                        terminate_response = "timeout"
                        final_response = "Sub-agent timed out"
                        break


                    if event.type == AgentEvent.tool_call_start:
                        tool_calls.append(event.data.get("name"))
                    elif event.type == AgentEvent.text_complete:
                        final_response = event.data.get("content")
                    elif event.type == AgentEvent.agent_error:
                        terminate_response = "error"
                        error = event.data.get("error", " Unknown")
                        final_response = f"Sub-agent error: {error}"
                        break 
                    
        except Exception as e:
            terminate_response = 'error'
            error = str(e)
            final_response = f"Sub-agent failed: {e}"

        result = f"""Sub-agent '{self.definition.name}' completed.
        Termination: {terminate_response}
        Tools called: {','.join(tool_calls) if tool_calls else 'None'}

        Result:
        {final_response or 'No response'}
        """

        if error:
            return ToolResult.error(result)

        return ToolResult.success_result(result)



CODE_INVESTIGATOR = SubagentDefinition(
    name = "codebase_investigator",
    desciption="Investigates the codebase to answer questions about code structure"
    goal_prompt=""" You are a codebase investigation specialist.
Your job is to explore and understand code to answer questions.
Use read_file, grep, and list_dir to investigate.
DO NOT modify any files.""",
    allowed_tools = ["read_file", "grep", "glob", "list_dir"],
    max_turns = 10,
)
        

CODE_REVIWER = SubagentDefinition(
    name = "code_reviewer",
    desciption="Reviews code changes and provides feedback on quality, and  bugs "
    goal_prompt=""" You are a code review specialist,
Your job is to review code and provide constructive feedback,
Look for bugs, code smells, security issues, and improvement opportunities.
Use read_file, list_dir and grep tp examine the code.
DO NOT modify any files.""",
    allowed_tools = ["read_file", "grep", "list_dir"],
    max_turns = 10,
    timeout_seconds=300,
)
        



    


    

