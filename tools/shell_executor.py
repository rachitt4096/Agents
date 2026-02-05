"""
Shell Command Executor - Safely executes shell commands
"""
import subprocess
import shlex
from typing import List, Optional
from config.settings import settings
from config.models import ActionResult, ActionType
from loguru import logger


class ShellExecutor:
    """Execute shell commands safely"""
    
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = workspace_dir or settings.WORKSPACE_DIR
        self.allowed_commands = settings.ALLOWED_COMMANDS
        self.blocked_commands = settings.BLOCKED_COMMANDS
    
    def is_safe_command(self, command: str) -> tuple[bool, Optional[str]]:
        """
        Check if command is safe to execute
        
        Returns:
            (is_safe, reason)
        """
        # Check for blocked patterns
        for blocked in self.blocked_commands:
            if blocked in command:
                return False, f"Blocked command pattern: {blocked}"
        
        # Extract base command
        try:
            parts = shlex.split(command)
            if not parts:
                return False, "Empty command"
            
            base_cmd = parts[0]
            
            # Check if base command is allowed
            if base_cmd not in self.allowed_commands:
                return False, f"Command not in allowed list: {base_cmd}"
            
            return True, None
            
        except Exception as e:
            return False, f"Invalid command syntax: {e}"
    
    def execute(
        self,
        command: str,
        timeout: int = settings.TIMEOUT_SECONDS
    ) -> ActionResult:
        """
        Execute shell command safely
        
        Args:
            command: Shell command to execute
            timeout: Execution timeout
            
        Returns:
            ActionResult with command output
        """
        logger.info(f"Executing command: {command}")
        
        # Safety check
        is_safe, reason = self.is_safe_command(command)
        if not is_safe:
            logger.warning(f"Command blocked: {reason}")
            return ActionResult(
                action_type=ActionType.SHELL_COMMAND,
                success=False,
                error=f"Command blocked: {reason}"
            )
        
        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace_dir
            )
            
            success = result.returncode == 0
            
            logger.info(f"Command execution {'successful' if success else 'failed'}")
            
            return ActionResult(
                action_type=ActionType.SHELL_COMMAND,
                success=success,
                output=result.stdout,
                error=None if success else result.stderr,
                metadata={
                    "returncode": result.returncode,
                    "command": command
                }
            )
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout: {command}")
            return ActionResult(
                action_type=ActionType.SHELL_COMMAND,
                success=False,
                error=f"Command timeout after {timeout}s"
            )
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return ActionResult(
                action_type=ActionType.SHELL_COMMAND,
                success=False,
                error=str(e)
            )
    
    def execute_multiple(
        self,
        commands: List[str],
        stop_on_error: bool = True
    ) -> List[ActionResult]:
        """
        Execute multiple commands in sequence
        
        Args:
            commands: List of commands
            stop_on_error: Stop if any command fails
            
        Returns:
            List of ActionResults
        """
        results = []
        
        for cmd in commands:
            result = self.execute(cmd)
            results.append(result)
            
            if stop_on_error and not result.success:
                logger.warning(f"Stopping execution due to error in: {cmd}")
                break
        
        return results