from pathlib import Path

WORKSPACE = Path("workspace")

class WriteFileTool:
    def run(self, path: str, content: str) -> str:
        full_path = WORKSPACE / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        return f"File written: {full_path}"
