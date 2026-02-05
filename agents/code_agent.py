"""
Code Agent - Code generation and technical implementation
FIXED: Generates ONLY clean code, NO markdown
"""
from typing import Dict, Any
import re
from agents.base_agent import BaseAgent
from config.models import Task, AgentType
from config.llm_client import LLMClient
from loguru import logger


class CodeAgent(BaseAgent):
    """
    Code Agent specialized in:
    - Code generation
    - Script writing
    - Technical implementation
    - Algorithm design
    """
    
    def __init__(self, llm_client: LLMClient):
        super().__init__(
            llm_client=llm_client,
            name="Coder",
            agent_type=AgentType.CODE,
            description="Code generation and technical implementation"
        )
    
    def execute(self, task: Task, context: Dict[str, Any] = None) -> str:
        """
        Execute code generation task
        
        Args:
            task: Code task to execute
            context: Shared context including requirements
            
        Returns:
            Generated clean production-ready code (ZERO MARKDOWN)
        """
        logger.info(f"Code Agent executing: {task.description}")
        
        # Build context and feedback strings
        context_str = self._build_context_string(context)
        feedback_str = self._build_feedback_string(context, task.id)
        
        # Build prompt - CRITICAL: Prevent markdown entirely
        prompt = f"""You are a professional software engineer. Generate ONLY executable code.

TASK: {task.description}
{context_str}
{feedback_str}

CRITICAL RULES - FOLLOW EXACTLY:
1. Output ONLY Python code
2. NO markdown formatting (no ``` or **text**)
3. NO titles, headers, or section labels
4. NO explanations outside the code
5. NO "Explanation" sections
6. NO "Usage Examples" sections
7. Start with imports, end with code
8. Every line must be valid Python

Write production-ready, executable code. Nothing else."""

        # Generate response
        result = self.llm.generate(
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Aggressive markdown cleanup
        result = self._clean_markdown_aggressive(result)
        
        self.execution_count += 1
        logger.success(f"Code task completed: {task.id}")
        
        return result
    
    def _clean_markdown_aggressive(self, text: str) -> str:
        """Aggressively remove ALL markdown artifacts"""
        lines = text.split("\n")
        cleaned = []
        in_code_block = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip markdown code block markers
            if "```" in line:
                in_code_block = not in_code_block
                continue
            
            # Skip markdown headers (but keep python comments)
            if stripped.startswith(("**", "###", "##")) and not stripped.startswith("# "):
                continue
            
            # Skip lines that are just explanations/documentation headers
            if any(stripped.startswith(x) for x in [
                "Usage:", "Example:", "Explanation:", "Testing:",
                "Notes:", "Important:", "**Usage", "**Example",
                "**Explanation", "**Testing", "**Notes"
            ]):
                continue
            
            # Skip lines with markdown bold that aren't code
            if stripped.startswith("**") and stripped.endswith("**"):
                if not any(c in stripped for c in ["def ", "class ", "import ", "="]):
                    continue
            
            cleaned.append(line)
        
        # Remove empty lines at start/end
        while cleaned and not cleaned[0].strip():
            cleaned.pop(0)
        while cleaned and not cleaned[-1].strip():
            cleaned.pop()
        
        result = "\n".join(cleaned)
        
        # Final cleanup: remove any remaining markdown code block markers
        result = result.replace("```python", "").replace("```", "")
        
        # Clean excessive blank lines (more than 2 consecutive)
        result = re.sub(r'\n\n\n+', '\n\n', result)
        
        return result.strip()
    
    def _build_context_string(self, context: Dict[str, Any] = None) -> str:
        """Build context string from dictionary"""
        if not context:
            return ""
        
        context_items = []
        for key, value in context.items():
            if not key.endswith("_feedback"):
                value_str = str(value)[:200] + "..." if len(str(value)) > 200 else str(value)
                context_items.append(f"- {key}: {value_str}")
        
        if not context_items:
            return ""
        
        return f"\n\nContext from previous tasks:\n" + "\n".join(context_items)
    
    def _build_feedback_string(self, context: Dict[str, Any] = None, task_id: str = "") -> str:
        """Build feedback string if this is a retry"""
        if not context:
            return ""
        
        feedback_key = f"{task_id}_feedback"
        if feedback_key in context:
            return f"\n\nFeedback from previous attempt:\n{context[feedback_key]}\n\nPlease fix these issues."
        
        return ""