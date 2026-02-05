"""
Data models for the multi-agent system
"""
from pydantic import BaseModel, Field
from typing import Optional, Union, List, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATING = "validating"
    RETRYING = "retrying"


class AgentType(str, Enum):
    """Types of specialized agents"""
    COORDINATOR = "coordinator"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    CODE = "code"
    VALIDATION = "validation"
    INTEGRATION = "integration"
    EXECUTION = "execution"


class ActionType(str, Enum):
    """Types of actions that can be executed"""
    FILE_WRITE = "file_write"
    FILE_READ = "file_read"
    COMMAND_RUN = "command_run"
    CODE_EXECUTE = "code_execute"
    API_CALL = "api_call"


class ActionResult(BaseModel):
    """Result of an action execution"""
    action_type: ActionType
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    files_created: List[str] = Field(default_factory=list)
    execution_time: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Task(BaseModel):
    """Represents a single executable task"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str
    agent_type: AgentType
    dependencies: List[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    action_result: Optional[ActionResult] = None
    retry_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class ObjectiveStatus(str, Enum):
    """Overall objective status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class Objective(BaseModel):
    """Represents a high-level objective"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str
    tasks: List[Task] = Field(default_factory=list)
    status: ObjectiveStatus = ObjectiveStatus.PENDING
    final_result: Optional[str] = None
    actions_executed: List[ActionResult] = Field(default_factory=list)
    files_generated: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class AgentMessage(BaseModel):
    """Message format for agent communication"""
    role: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Result from validation agent"""
    is_valid: bool
    score: float = Field(ge=0, le=10)
    feedback: str
    improvement_suggestions: Optional[Union[str, List[str]]] = None


class ToolCall(BaseModel):
    """Represents a tool execution"""
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None