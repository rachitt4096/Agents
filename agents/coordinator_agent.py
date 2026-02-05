"""
Coordinator Agent - Decomposes objectives and orchestrates workers
"""

import json
from typing import List, Dict, Any
from loguru import logger

from agents.base_agent import BaseAgent
from config.models import AgentType, Task
from config.llm_client import LLMClient
from config.settings import settings


class CoordinatorAgent(BaseAgent):
    """
    Coordinator Agent responsible for:
    - Breaking down complex objectives into tasks
    - Determining task dependencies
    - Assigning tasks to appropriate agents
    - Explicitly deciding HOW real execution should happen
    """

    # Only block truly dangerous shell command patterns
    DANGEROUS_SHELL_PATTERNS = [
        "rm -rf /",
        "mkfs",
        "dd if=",
        ":(){ :|:& };:",  # fork bomb
        "chmod 777",
        "shutdown",
        "reboot"
    ]

    def __init__(self, llm_client: LLMClient):
        super().__init__(
            llm_client=llm_client,
            name="Coordinator",
            agent_type=AgentType.COORDINATOR,
            description="Task decomposition and orchestration",
        )

    def decompose_objective(self, objective: str) -> List[Dict[str, Any]]:
        logger.info(f"Decomposing objective: {objective}")

        prompt = self._build_decomposition_prompt(objective)

        try:
            response = self.llm.generate_json(
                messages=[{"role": "user", "content": prompt}],
                model=settings.COORDINATOR_MODEL,
            )

            tasks = self._parse_task_response(response)
            logger.success(f"Decomposed into {len(tasks)} tasks")
            return tasks

        except Exception as e:
            logger.error(f"Decomposition failed: {e}")
            return self._create_fallback_task(objective)

    def _build_decomposition_prompt(self, objective: str) -> str:
        """Build task decomposition prompt with proper project structure"""
        
        return f"""You are an expert task planner for an autonomous agent system that creates organized project structures.

OBJECTIVE: {objective}

CRITICAL APPROACH FOR PROJECT CREATION:
Instead of putting everything in one file, CREATE A PROPER PROJECT STRUCTURE with:
1. Separate code generation tasks for each component (models, utils, main, etc.)
2. Multiple execution tasks to create individual files in proper directories
3. A main entry point file

FOR "make a todo app" EXAMPLE:
- models.py: TodoItem class and TodoApp class
- utils.py: Helper functions
- main.py: Entry point with examples
- requirements.txt: Dependencies
- README.md: Documentation

AVAILABLE AGENTS:
- code: Generates code for specific components
- execution: Creates individual files with the generated code
- research: Gathers information
- analysis: Analyzes requirements
- validation: Validates outputs

OUTPUT FORMAT (JSON only, no markdown):
[
  {{
    "id": "task_1",
    "description": "Generate models.py - Define TodoItem and TodoApp classes",
    "agent_type": "code",
    "dependencies": [],
    "success_criteria": "Complete models module code generated"
  }},
  {{
    "id": "task_2",
    "description": "Create models.py file",
    "agent_type": "execution",
    "dependencies": ["task_1"],
    "success_criteria": "models.py created in project",
    "metadata": {{
      "type": "file",
      "file_path": "models.py",
      "content": "WILL_BE_REPLACED_WITH_TASK_1_OUTPUT"
    }}
  }},
  {{
    "id": "task_3",
    "description": "Generate main.py - Entry point with usage examples",
    "agent_type": "code",
    "dependencies": [],
    "success_criteria": "Main entry point code generated"
  }},
  {{
    "id": "task_4",
    "description": "Create main.py file",
    "agent_type": "execution",
    "dependencies": ["task_3"],
    "success_criteria": "main.py created in project",
    "metadata": {{
      "type": "file",
      "file_path": "main.py",
      "content": "WILL_BE_REPLACED_WITH_TASK_3_OUTPUT"
    }}
  }},
  {{
    "id": "task_5",
    "description": "Generate requirements.txt - Project dependencies",
    "agent_type": "code",
    "dependencies": [],
    "success_criteria": "Requirements list generated"
  }},
  {{
    "id": "task_6",
    "description": "Create requirements.txt file",
    "agent_type": "execution",
    "dependencies": ["task_5"],
    "success_criteria": "requirements.txt created",
    "metadata": {{
      "type": "file",
      "file_path": "requirements.txt",
      "content": "WILL_BE_REPLACED_WITH_TASK_5_OUTPUT"
    }}
  }},
  {{
    "id": "task_7",
    "description": "Generate README.md - Project documentation",
    "agent_type": "code",
    "dependencies": [],
    "success_criteria": "Documentation generated"
  }},
  {{
    "id": "task_8",
    "description": "Create README.md file",
    "agent_type": "execution",
    "dependencies": ["task_7"],
    "success_criteria": "README.md created",
    "metadata": {{
      "type": "file",
      "file_path": "README.md",
      "content": "WILL_BE_REPLACED_WITH_TASK_7_OUTPUT"
    }}
  }}
]

REQUIREMENTS:
- Return ONLY valid JSON array
- No markdown, no explanations
- Create separate code generation tasks for each component
- Create separate execution tasks for each file
- Use proper file paths (not all in one file)
- For web apps: Use Flask/FastAPI with separate routes, templates folders
- For libraries: Use models.py, utils.py, main.py structure
- Always include requirements.txt and README.md
- Content marked "WILL_BE_REPLACED..." will be auto-filled from previous task output"""

    def _parse_task_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse and validate task JSON"""
        json_str = response.strip()

        # Remove markdown code blocks if present
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]

        tasks = json.loads(json_str.strip())

        if not isinstance(tasks, list):
            raise ValueError("Response must be a JSON array")

        # Validate each task
        for task in tasks:
            required = {"id", "description", "agent_type"}
            if not required.issubset(task.keys()):
                raise ValueError(f"Task missing required fields: {task}")

            # Normalize agent type
            task["agent_type"] = task["agent_type"].lower()
            
            # Ensure dependencies exist
            task.setdefault("dependencies", [])
            task.setdefault("success_criteria", "Task completed successfully")
            task.setdefault("metadata", {})

            # Basic safety check for execution tasks
            if task["agent_type"] == "execution":
                meta = task.get("metadata", {})
                if meta.get("type") == "command":
                    cmd = meta.get("command", "")
                    if any(pattern in cmd for pattern in self.DANGEROUS_SHELL_PATTERNS):
                        raise ValueError(f"Dangerous command blocked: {cmd}")

        return tasks

    def _create_fallback_task(self, objective: str) -> List[Dict[str, Any]]:
        """Create safe fallback task plan with proper structure"""
        logger.warning("Using fallback task plan with proper structure")
        
        return [
            {
                "id": "task_1",
                "description": f"Generate models.py for: {objective}",
                "agent_type": "code",
                "dependencies": [],
                "success_criteria": "Models code generated",
                "metadata": {}
            },
            {
                "id": "task_2",
                "description": "Create models.py file",
                "agent_type": "execution",
                "dependencies": ["task_1"],
                "success_criteria": "models.py created",
                "metadata": {
                    "type": "file",
                    "file_path": "models.py",
                    "content": "WILL_BE_REPLACED_WITH_TASK_1_OUTPUT"
                }
            },
            {
                "id": "task_3",
                "description": f"Generate main.py for: {objective}",
                "agent_type": "code",
                "dependencies": [],
                "success_criteria": "Main entry point code generated",
                "metadata": {}
            },
            {
                "id": "task_4",
                "description": "Create main.py file",
                "agent_type": "execution",
                "dependencies": ["task_3"],
                "success_criteria": "main.py created",
                "metadata": {
                    "type": "file",
                    "file_path": "main.py",
                    "content": "WILL_BE_REPLACED_WITH_TASK_3_OUTPUT"
                }
            },
            {
                "id": "task_5",
                "description": "Generate requirements.txt with dependencies",
                "agent_type": "code",
                "dependencies": [],
                "success_criteria": "Requirements list generated",
                "metadata": {}
            },
            {
                "id": "task_6",
                "description": "Create requirements.txt file",
                "agent_type": "execution",
                "dependencies": ["task_5"],
                "success_criteria": "requirements.txt created",
                "metadata": {
                    "type": "file",
                    "file_path": "requirements.txt",
                    "content": "WILL_BE_REPLACED_WITH_TASK_5_OUTPUT"
                }
            },
            {
                "id": "task_7",
                "description": "Generate README.md documentation",
                "agent_type": "code",
                "dependencies": [],
                "success_criteria": "Documentation generated",
                "metadata": {}
            },
            {
                "id": "task_8",
                "description": "Create README.md file",
                "agent_type": "execution",
                "dependencies": ["task_7"],
                "success_criteria": "README.md created",
                "metadata": {
                    "type": "file",
                    "file_path": "README.md",
                    "content": "WILL_BE_REPLACED_WITH_TASK_7_OUTPUT"
                }
            }
        ]

    def execute(self, task: Task, context: Dict[str, Any] = None) -> str:
        """Coordinators don't execute tasks"""
        return "Coordinator agent - use decompose_objective() instead"