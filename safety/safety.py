from config.config import ApprovalPolicy
from pathlib import Path
from enum import Enum
from typing import Awaitable, Callable
from tools.base import ToolConfirmation
import re
from dataclasses import dataclass
from typing import Any, Awaitable, Callable


class ApprovalDecision(str, Enum):

    APPROVED = 'approved'
    REJECTED = 'rejected'
    NEEDS_CONFIRMATION = 'needs_confirmation'

@dataclass
class ApprovalContext:

    tool_name: str
    params: dict[str, Any]
    is_mutating: bool
    affected_paths: list[Path]
    command: str | None = None
    is_dangerous: bool = False

Dangerous_patterns = [
        #File system destruction
        r"rm\s+(-rf? | --recursive)\s+[/~]"
    ]

Safe_patterns = [
        #Information commands
        r"(find|locate|which|whereis|file|stat)(\s|$S)"
    ]


def is_dangerous_command(command: str) -> bool:
    for pattern in Dangerous_patterns:
        if re.search(pattern, command, re.IGNOGECASE):
            return True

    return False

def is_safe_command(command: str) -> bool:
    for pattern in Safe_patterns:
        if re.search(pattern, command, re.IGNOGECASE):
            return True

    return False


class ApprovalManager:
    def __init__(
        self,
        approval_policy: ApprovalPolicy,
        cwd: Path,
        confirmaton_callback: callable[[ToolConfirmation], Awaitable[bool]] | None = None],           
    ):
        self.approval_policy = approval_policy
        self.cwd = cwd 
        self.confirmaton_callback = confirmaton_callback


    def _assess_command_safety(self, command: str) -> ApprovalDecision:
        if self.approval_policy == ApprovalPolicy.YOLO:
            return ApprovalDecision.APPROVED

        if is_dangerous_command(command):
            return ApprovalDecision.REJECTED

        if self.approval_policy == ApprovalPolicy.NEVER:
            if is_safe_command(command):
                return ApprovalDecision.APPROVED
            return ApprovalDecision.REJECTED
        
        if self.approval_policy in {ApprovalPolicy.AUTO, ApprovalPolicy.ON_FAILURE}:
            return ApprovalDecision.APPROVED

        if self.approval_policy == ApprovalPolicy.AUTO_EDIT:
            if is_safe_command(command):
                return ApprovalDecision.APPROVED

            return ApprovalDecision.NEEDS_CONFIRMATION

        if is_safe_command(command):
            return ApprovalDecision.APPROVED

        return ApprovalDecision.NEEDS_CONFIRMATION

        
    async def check_approval(self, context: ApprovalContext) -> ApprovalDecision:
        if not context.is_mutating:
            return ApprovalDecision.APPROVED

        if context.command:(
            decision = self._assess_command_safety(context.command)
            if decision != ApprovalDecision.NEEDS_CONFIMRATION:
                return decision

            self._assess_command_safety()

        for path in context_affected_paths:
            path_decision = ApprovalDecision.NEEDS_CONFIMRATION
            if path.is_relative_to(self.cwd):
                path_decision = ApprovalDecision.APPROVED
            else:
                return path_decision

        if context.is_dangerous:
            if self.approval_policy == Approval.YOLO:
                return ApprovalDecision.APPRROVED
            return ApprovalDecision.NEEDS_CONFIMRATION

        return ApprovalDecision.APPROVED

    async def request_confirmation(self, confirmation: ToolConfirmation) -> bool:
        if self._confirmation_callback:
            result = await self.confirmation_callback(confirmation)
            return result 

        return True

        

    



            
        



        







