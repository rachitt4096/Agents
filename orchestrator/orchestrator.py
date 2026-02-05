"""
Action-Oriented Multi-Agent Orchestrator
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from loguru import logger

from config.models import Objective, Task, TaskStatus, ObjectiveStatus, AgentType
from config.llm_client import LLMClient
from config.settings import settings
from agents import (
    CoordinatorAgent, 
    ExecutionAgent,
    CodeAgent,
    ResearchAgent,
    AnalysisAgent,
    ValidationAgent
)


class ActionOrchestrator:
    """Orchestrator that executes REAL actions"""
    
    def __init__(self, api_key: Optional[str] = None, progress_callback: Callable = None):
        self.llm_client = LLMClient(api_key=api_key)
        self.progress_callback = progress_callback  # For streaming to UI
        
        # Initialize agents
        self.coordinator = CoordinatorAgent(self.llm_client)
        self.executor = ExecutionAgent(self.llm_client)
        self.code_agent = CodeAgent(self.llm_client)
        self.research_agent = ResearchAgent(self.llm_client)
        self.analysis_agent = AnalysisAgent(self.llm_client)
        self.validation_agent = ValidationAgent(self.llm_client)
        
        self.objectives: Dict[str, Objective] = {}
        logger.info("Action Orchestrator initialized")
    
    def _emit_progress(self, message: str, type: str = "status", metadata: dict = None):
        """Emit progress update to UI"""
        if self.progress_callback:
            self.progress_callback({
                "type": type,
                "message": message,
                "metadata": metadata or {},
                "timestamp": datetime.now()
            })
    
    def execute_objective(self, objective_description: str) -> Objective:
        """Execute objective with REAL actions"""
        logger.info("="*80)
        logger.info(f"NEW OBJECTIVE: {objective_description}")
        logger.info("="*80)
        
        self._emit_progress(f"🎯 Starting: {objective_description}", "objective_start")
        
        # Step 1: Decompose into tasks
        self._emit_progress("🧠 Decomposing objective into tasks...", "decomposing")
        task_specs = self.coordinator.decompose_objective(objective_description)
        
        # Step 2: Create tasks
        tasks = self._create_tasks(task_specs)
        
        # Step 3: Create objective
        objective = Objective(
            description=objective_description,
            tasks=tasks,
            status=ObjectiveStatus.IN_PROGRESS
        )
        self.objectives[objective.id] = objective
        
        self._emit_progress(
            f"✅ Created {len(tasks)} tasks",
            "tasks_created",
            {"task_count": len(tasks)}
        )
        
        # Step 4: Execute tasks
        context = {}
        
        for i, task in enumerate(tasks, 1):
            self._emit_progress(
                f"📋 Task {i}/{len(tasks)}: {task.description}",
                "task_start",
                {"task_id": task.id, "task_number": i}
            )
            
            # Check dependencies
            if not self._check_dependencies(task, tasks):
                task.status = TaskStatus.FAILED
                task.error = "Dependencies not met"
                self._emit_progress(
                    f"⚠️ Task {i} skipped - dependencies not met",
                    "task_skipped"
                )
                continue
            
            # Execute with retries
            success = self._execute_task(task, objective_description, context)
            
            if success:
                context[task.id] = task.result
                if task.action_result:
                    objective.actions_executed.append(task.action_result)
                    if task.action_result.files_created:
                        objective.files_generated.extend(task.action_result.files_created)
                
                self._emit_progress(
                    f"✅ Task {i} completed",
                    "task_complete",
                    {"task_id": task.id, "result": task.result[:200] if len(task.result) > 200 else task.result}
                )
            else:
                self._emit_progress(
                    f"❌ Task {i} failed: {task.error}",
                    "task_failed",
                    {"task_id": task.id, "error": task.error}
                )
        
        # Step 5: Finalize
        objective.final_result = self._aggregate_results(objective)
        objective.status = self._determine_status(objective)
        objective.completed_at = datetime.now()
        
        self._emit_progress(
            f"🎉 Objective {objective.status}",
            "objective_complete",
            {
                "status": objective.status,
                "files_created": len(objective.files_generated),
                "actions": len(objective.actions_executed)
            }
        )
        
        logger.success("OBJECTIVE COMPLETED")
        return objective
    
    def _create_tasks(self, specs: List[Dict[str, Any]]) -> List[Task]:
        """Convert specs to Task objects, preserving metadata"""
        tasks = []
        for spec in specs:
            agent_type_str = spec.get("agent_type", "execution")
            try:
                agent_type = AgentType(agent_type_str)
            except ValueError:
                agent_type = AgentType.EXECUTION
            
            # Preserve metadata from coordinator
            metadata = spec.get("metadata", {})
            metadata.setdefault("success_criteria", spec.get("success_criteria", "Task completed"))
            
            task = Task(
                id=spec["id"],
                description=spec["description"],
                agent_type=agent_type,
                dependencies=spec.get("dependencies", []),
                metadata=metadata
            )
            tasks.append(task)
        return tasks
    
    def _check_dependencies(self, task: Task, all_tasks: List[Task]) -> bool:
        """Check if dependencies are met"""
        if not task.dependencies:
            return True
        for dep_id in task.dependencies:
            dep_task = next((t for t in all_tasks if t.id == dep_id), None)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True
    
    def _replace_task_placeholders(self, task: Task, context: Dict[str, Any]):
        """Replace placeholder content with actual task results from dependencies"""
        metadata = task.metadata
        
        if not metadata.get("content"):
            return
        
        content = metadata["content"]
        
        # Replace placeholders like "WILL_BE_REPLACED_WITH_task_1_OUTPUT"
        for dep_id in task.dependencies:
            placeholder = f"WILL_BE_REPLACED_WITH_{dep_id.upper()}_OUTPUT"
            if placeholder in content:
                # Get the result from the context
                dep_result = context.get(dep_id)
                if dep_result:
                    content = content.replace(placeholder, str(dep_result))
                    logger.info(f"✅ Replaced placeholder with output from {dep_id}")
        
        metadata["content"] = content
    
    def _get_agent_for_task(self, task: Task):
        """Get the appropriate agent based on task type"""
        agents_map = {
            AgentType.EXECUTION: self.executor,
            AgentType.CODE: self.code_agent,
            AgentType.RESEARCH: self.research_agent,
            AgentType.ANALYSIS: self.analysis_agent,
            AgentType.VALIDATION: self.validation_agent,
            AgentType.COORDINATOR: self.coordinator,
        }
        
        agent = agents_map.get(task.agent_type)
        if not agent:
            logger.warning(f"No agent found for type {task.agent_type}, using executor")
            return self.executor
        
        return agent
    
    def _execute_task(
        self,
        task: Task,
        objective: str,
        context: Dict[str, Any]
    ) -> bool:
        """Execute task with appropriate agent"""
        try:
            task.status = TaskStatus.IN_PROGRESS
            
            self._emit_progress(
                f"⚙️ Executing: {task.description}",
                "executing",
                {"task_id": task.id}
            )
            
            # Replace placeholders in metadata with actual task results
            self._replace_task_placeholders(task, context)
            
            # Get the appropriate agent for this task
            agent = self._get_agent_for_task(task)
            
            # Execute task with appropriate agent
            result = agent.execute(task, context)
            task.result = result
            
            # Check if action was performed
            if task.action_result:
                if task.action_result.success:
                    self._emit_progress(
                        f"✨ Action completed: {task.action_result.action_type.value}",
                        "action_complete",
                        {
                            "action_type": task.action_result.action_type.value,
                            "output": task.action_result.output[:200] if task.action_result.output else ""
                        }
                    )
                else:
                    self._emit_progress(
                        f"⚠️ Action failed: {task.action_result.error}",
                        "action_failed",
                        {"error": task.action_result.error}
                    )
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self._emit_progress(
                f"❌ Task error: {str(e)}",
                "task_error",
                {"task_id": task.id, "error": str(e)}
            )
            return False
    
    def _aggregate_results(self, objective: Objective) -> str:
        """Aggregate task results"""
        completed = [t for t in objective.tasks if t.status == TaskStatus.COMPLETED]
        
        parts = [
            f"# Results for: {objective.description}\n",
            f"\n## Summary",
            f"- Tasks completed: {len(completed)}/{len(objective.tasks)}",
            f"- Actions executed: {len(objective.actions_executed)}",
            f"- Files created: {len(objective.files_generated)}\n"
        ]
        
        if objective.files_generated:
            parts.append("\n## Files Generated:")
            for f in objective.files_generated:
                parts.append(f"- {f}")
        
        parts.append("\n## Task Results:\n")
        for i, task in enumerate(completed, 1):
            parts.append(f"### {i}. {task.description}")
            parts.append(f"{task.result}\n")
        
        return "\n".join(parts)
    
    def _determine_status(self, objective: Objective) -> ObjectiveStatus:
        """Determine objective status"""
        statuses = [t.status for t in objective.tasks]
        if all(s == TaskStatus.COMPLETED for s in statuses):
            return ObjectiveStatus.COMPLETED
        elif any(s == TaskStatus.COMPLETED for s in statuses):
            return ObjectiveStatus.PARTIAL
        else:
            return ObjectiveStatus.FAILED
    
    def get_objective(self, objective_id: str) -> Optional[Objective]:
        """Get objective by ID"""
        return self.objectives.get(objective_id)
    
    def list_objectives(self) -> List[Objective]:
        """List all objectives"""
        return list(self.objectives.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        return {
            "total_objectives": len(self.objectives),
            "llm_stats": self.llm_client.get_stats(),
            "executor_stats": self.executor.get_stats(),
            "code_agent_stats": self.code_agent.get_stats(),
        }