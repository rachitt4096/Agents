import subprocess
from pathlib import Path

WORKSPACE = Path("workspace")

class RunCommandTool:
    def run(self, command: str) -> dict:
        result = subprocess.run(
            command,
            cwd=WORKSPACE,
            shell=True,
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
