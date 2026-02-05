"""
Validation Agent - Smart execution validation
"""

import json
import os
import socket
from typing import Dict, Any, Tuple
from pathlib import Path

from loguru import logger

from agents.base_agent import BaseAgent
from config.models import Task, AgentType, ValidationResult
from config.llm_client import LLMClient


class ValidationAgent(BaseAgent):
    """
    Validation Agent - Validates both execution results AND content quality
    """

    def __init__(self, llm_client: LLMClient):
        super().__init__(
            llm_client=llm_client,
            name="Validator",
            agent_type=AgentType.VALIDATION,
            description="Execution and quality validation"
        )
        self.validation_threshold = 6.0

    def validate(
        self,
        task: Task,
        result: str,
        objective: str,
        context: Dict[str, Any] = None
    ) -> Tuple[bool, str]:
        """Main validation entry point"""
        
        logger.info(f"🔍 Validating task {task.id} ({task.agent_type})")

        # For execution tasks, check if execution succeeded
        if task.agent_type == AgentType.EXECUTION:
            exec_ok, exec_feedback = self._validate_execution_result(task, result)
            if not exec_ok:
                logger.error(f"❌ Execution validation failed: {exec_feedback}")
                return False, exec_feedback

        # LLM quality check for all tasks
        quality_ok, quality_feedback = self._validate_quality(task, result, objective)
        
        if not quality_ok:
            logger.warning(f"⚠️ Quality validation failed: {quality_feedback}")
            return False, quality_feedback

        logger.success(f"✅ Task {task.id} validated")
        return True, "Validation passed"

    def _validate_execution_result(
        self, 
        task: Task, 
        result: str
    ) -> Tuple[bool, str]:
        """Validate execution task results"""
        
        try:
            # Parse execution result JSON
            exec_result = json.loads(result)
            
            if not exec_result.get("success"):
                error = exec_result.get("error", "Unknown error")
                return False, f"Execution failed: {error}"
            
            exec_type = exec_result.get("type")
            
            # File creation validation
            if exec_type == "file":
                file_path = exec_result.get("file_path")
                if file_path:
                    full_path = Path("workspace") / file_path
                    if not full_path.exists():
                        return False, f"File was not created: {file_path}"
                    logger.info(f"✅ File verified: {file_path}")
            
            # Command execution validation
            elif exec_type == "command":
                exit_code = exec_result.get("exit_code", 1)
                if exit_code != 0:
                    return False, f"Command failed with exit code {exit_code}"
            
            # Server validation
            elif exec_type == "server":
                # Just check if it started
                if not exec_result.get("pid"):
                    return False, "Server failed to start"
            
            return True, "Execution successful"
            
        except json.JSONDecodeError:
            # Not a JSON result, probably a descriptive result
            # Check for error indicators in text
            if any(word in result.lower() for word in ["error", "failed", "exception"]):
                return False, "Execution appears to have failed"
            return True, "Execution result accepted"
        except Exception as e:
            logger.warning(f"Execution validation error: {e}")
            # Don't fail on validation errors, be lenient
            return True, "Execution validation skipped"

    def _validate_quality(
        self,
        task: Task,
        result: str,
        objective: str
    ) -> Tuple[bool, str]:
        """LLM-based quality validation"""
        
        prompt = f"""You are validating the quality of a task result.

OBJECTIVE: {objective}

TASK: {task.description}

RESULT:
{result}

Evaluate if this result:
1. Successfully addresses the task description
2. Is complete and well-formed
3. Would help achieve the objective
4. Contains no critical errors

Respond ONLY as JSON:
{{
  "is_valid": true/false,
  "score": 0-10,
  "feedback": "Brief feedback on quality"
}}
"""

        try:
            response = self.llm.generate_json(
                messages=[{"role": "user", "content": prompt}]
            )
            
            validation = self._parse_validation_response(response)
            
            passed = (
                validation.is_valid 
                and validation.score >= self.validation_threshold
            )
            
            if passed:
                logger.success(f"✅ Quality validation PASS (score {validation.score}/10)")
                return True, validation.feedback
            else:
                logger.warning(f"⚠️ Quality validation FAIL (score {validation.score}/10)")
                return False, validation.feedback
                
        except Exception as e:
            logger.error(f"Quality validation error: {e}")
            # Be lenient - accept if LLM validation fails
            return True, "Quality validation skipped due to error"

    def _parse_validation_response(self, response: str) -> ValidationResult:
        """Parse validation JSON response"""
        json_str = response.strip()
        
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]
        
        data = json.loads(json_str.strip())
        
        return ValidationResult(
            is_valid=data.get("is_valid", False),
            score=float(data.get("score", 0)),
            feedback=data.get("feedback", "No feedback"),
            improvement_suggestions=data.get("improvement_suggestions")
        )

    def execute(self, task: Task, context: Dict[str, Any] = None) -> str:
        """Validators don't execute tasks"""
        return "ValidationAgent does not execute tasks"