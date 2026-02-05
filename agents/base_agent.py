"""
Base Agent - Abstract base class for all agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from config.models import Task, AgentMessage, AgentType
from config.llm_client import LLMClient
from loguru import logger


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        name: str,
        agent_type: AgentType,
        description: str
    ):
        self.llm = llm_client
        self.name = name
        self.agent_type = agent_type
        self.description = description
        self.execution_count = 0
        self.memory: List[AgentMessage] = []
        
    @abstractmethod
    def execute(self, task: Task, context: Dict[str, Any] = None) -> str:
        """
        Execute a task - must be implemented by subclasses
        
        Args:
            task: Task to execute
            context: Shared context from previous tasks
            
        Returns:
            Result string
        """
        pass
    
    def _build_context_string(self, context: Optional[Dict[str, Any]]) -> str:
        """Build context string from dictionary"""
        if not context:
            return ""
        
        context_items = []
        for key, value in context.items():
            if not key.endswith("_feedback"):
                context_items.append(f"- {key}: {value[:200]}..." if len(str(value)) > 200 else f"- {key}: {value}")
        
        if not context_items:
            return ""
        
        return f"\n\nContext from previous tasks:\n" + "\n".join(context_items)
    
    def _build_feedback_string(self, context: Optional[Dict[str, Any]], task_id: str) -> str:
        """Build feedback string if this is a retry"""
        if not context:
            return ""
        
        feedback_key = f"{task_id}_feedback"
        if feedback_key in context:
            return f"\n\nFeedback from previous attempt:\n{context[feedback_key]}\n\nPlease address this feedback in your response."
        
        return ""
    
    def add_to_memory(self, message: AgentMessage):
        """Add message to agent's memory"""
        self.memory.append(message)
        
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "name": self.name,
            "type": self.agent_type.value,
            "executions": self.execution_count,
            "memory_size": len(self.memory)
        }