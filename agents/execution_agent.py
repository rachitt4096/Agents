"""
Execution Agent - Handles command execution, HTTP requests, and server management
REAL execution + sandboxed + streamable logs
"""

import subprocess
import json
import re
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import time

import requests
from loguru import logger

from config.models import Task, AgentType, ActionResult, ActionType
from config.llm_client import LLMClient
from config.settings import settings
from .base_agent import BaseAgent

LOG_FILE = "logs/runtime.log"
WORKSPACE_DIR = Path("workspace").resolve()


class ExecutionAgent(BaseAgent):
    """
    Execution Agent for running shell commands, making HTTP requests,
    and managing servers with REAL execution — sandboxed to workspace/.
    """

    DANGEROUS_PATTERNS = [
        r"rm\s+-rf",
        r"dd\s+if=",
        r":\(\)\s*{\s*:\s*;\s*:\s*}",  # fork bomb
        r"sudo",
        r"chmod.*777",
        r"mkfs",
        r"shred",
        r"tee /proc",
        r">.*</dev/sd",
    ]

    def __init__(self, llm_client: LLMClient):
        super().__init__(
            llm_client=llm_client,
            name="ExecutionAgent",
            agent_type=AgentType.EXECUTION,
            description="Sandboxed real execution engine",
        )

        WORKSPACE_DIR.mkdir(exist_ok=True)

    # ============================================================
    # MAIN ENTRY
    # ============================================================

    def execute(self, task: Task, context: Dict[str, Any] = None) -> str:
        logger.info(f"🔧 ExecutionAgent executing: {task.description}")
        os.makedirs("logs", exist_ok=True)

        exec_type = task.metadata.get("type", "noop")
        start_time = time.time()

        try:
            if exec_type == "noop":
                result = {
                    "success": True,
                    "type": "noop",
                    "message": "No execution required",
                }
                action_result = ActionResult(
                    action_type=ActionType.FILE_WRITE,
                    success=True,
                    output="No execution required"
                )

            elif exec_type == "command":
                result = self._execute_command(task)
                action_result = ActionResult(
                    action_type=ActionType.COMMAND_RUN,
                    success=result.get("success", False),
                    output=result.get("stdout", ""),
                    error=result.get("error"),
                )

            elif exec_type == "http":
                result = self._execute_http(task)
                action_result = ActionResult(
                    action_type=ActionType.API_CALL,
                    success=result.get("success", False),
                    output=result.get("body", ""),
                    error=result.get("error"),
                )

            elif exec_type == "server":
                result = self._execute_server(task)
                action_result = ActionResult(
                    action_type=ActionType.COMMAND_RUN,
                    success=result.get("success", False),
                    output=json.dumps({"pid": result.get("pid")}),
                    error=result.get("error"),
                )

            elif exec_type == "file":
                result = self._execute_file_write(task)
                action_result = ActionResult(
                    action_type=ActionType.FILE_WRITE,
                    success=result.get("success", False),
                    output=f"File created: {result.get('file_path', '')}",
                    files_created=[result.get("file_path")] if result.get("success") else [],
                    error=result.get("error"),
                )

            else:
                result = self._error(f"Unknown execution type: {exec_type}", exec_type)
                action_result = ActionResult(
                    action_type=ActionType.CODE_EXECUTE,
                    success=False,
                    error=result.get("error"),
                )

            # Set execution time
            action_result.execution_time = time.time() - start_time
            
            # Attach action result to task
            task.action_result = action_result

            self.execution_count += 1
            logger.success(f"✅ Execution finished: {task.id}")
            return json.dumps(result, indent=2)

        except Exception as e:
            self.execution_count += 1
            logger.exception("❌ Execution crashed")
            error_action = ActionResult(
                action_type=ActionType.CODE_EXECUTE,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
            task.action_result = error_action
            return json.dumps(
                {
                    "success": False,
                    "error": str(e),
                    "type": "error",
                }
            )

    # ============================================================
    # FILE WRITE (SANDBOXED)
    # ============================================================

    def _execute_file_write(self, task: Task) -> Dict[str, Any]:
        rel_path = task.metadata.get("file_path")
        content = task.metadata.get("content", "")

        if not rel_path:
            return self._error("file_path missing for file execution", "file")

        target_path = (WORKSPACE_DIR / rel_path).resolve()

        if not str(target_path).startswith(str(WORKSPACE_DIR)):
            return self._error("File write outside workspace blocked", "file")

        self._log(task.id, f"📝 Writing file: {rel_path}")

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content)

            self._log(
                task.id,
                f"✅ File written ({len(content)} bytes)",
            )

            logger.info(f"📝 Created file: {rel_path} ({len(content)} bytes)")

            return {
                "success": True,
                "file_path": str(rel_path),
                "bytes_written": len(content),
                "type": "file",
            }

        except Exception as e:
            self._log(task.id, f"❌ FILE WRITE ERROR: {e}")
            return self._error(str(e), "file")

    # ============================================================
    # SHELL COMMAND EXECUTION (STRICT + SANDBOXED)
    # ============================================================

    def _execute_command(self, task: Task) -> Dict[str, Any]:
        command = task.metadata.get("command")

        if not command:
            return self._error(
                "No executable command provided (natural language blocked)",
                "command",
            )

        is_safe, reason = self._validate_command(command)
        if not is_safe:
            self._log(task.id, f"❌ BLOCKED COMMAND: {reason}")
            return self._error(reason, "command", command)

        timeout = task.metadata.get("timeout", settings.TIMEOUT_SECONDS)

        self._log(task.id, f"$ {command}")

        try:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=WORKSPACE_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            stdout = []
            for line in process.stdout:
                stdout.append(line)
                self._log(task.id, line.rstrip())

            process.wait(timeout=timeout)

            return {
                "success": process.returncode == 0,
                "command": command,
                "exit_code": process.returncode,
                "stdout": "".join(stdout),
                "type": "command",
            }

        except subprocess.TimeoutExpired:
            self._log(task.id, "⏰ Command timed out")
            return self._error("Command timeout", "command", command)

    # ============================================================
    # HTTP EXECUTION
    # ============================================================

    def _execute_http(self, task: Task) -> Dict[str, Any]:
        method = task.metadata.get("method", "GET").upper()
        url = task.metadata.get("url")

        if not url:
            return self._error("URL missing for HTTP execution", "http")

        headers = task.metadata.get("headers", {})
        data = task.metadata.get("data")
        timeout = task.metadata.get("timeout", settings.TIMEOUT_SECONDS)

        self._log(task.id, f"🌐 HTTP {method} {url}")

        try:
            response = requests.request(
                method, url, json=data, headers=headers, timeout=timeout
            )

            self._log(task.id, f"Status: {response.status_code}")
            self._log(task.id, response.text)

            return {
                "success": 200 <= response.status_code < 300,
                "method": method,
                "url": url,
                "status_code": response.status_code,
                "body": response.text,
                "type": "http",
            }

        except Exception as e:
            self._log(task.id, f"❌ HTTP ERROR: {e}")
            return self._error(str(e), "http")

    # ============================================================
    # SERVER MANAGEMENT (FAIL-FAST)
    # ============================================================

    def _execute_server(self, task: Task) -> Dict[str, Any]:
        action = task.metadata.get("action")
        command = task.metadata.get("start_command")

        if action != "start":
            return self._error("Unsupported server action", "server")

        if not command:
            return self._error("start_command missing for server start", "server")

        self._log(task.id, f"🖥 Starting server: {command}")

        try:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=WORKSPACE_DIR,
            )

            return {
                "success": True,
                "action": "start",
                "pid": process.pid,
                "type": "server",
            }

        except Exception as e:
            return self._error(str(e), "server")

    # ============================================================
    # SAFETY + LOGGING
    # ============================================================

    def _validate_command(self, command: str) -> Tuple[bool, Optional[str]]:
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command.lower()):
                return False, f"Dangerous pattern detected: {pattern}"
        return True, None

    def _log(self, task_id: str, text: str):
        with open(LOG_FILE, "a") as f:
            f.write(f"[{task_id}] {text}\n")
            f.flush()

    def _error(self, message: str, exec_type: str, command: Optional[str] = None):
        return {
            "success": False,
            "error": message,
            "command": command,
            "type": exec_type,
        }