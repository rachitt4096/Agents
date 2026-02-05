"""
Complete Agent Testing Suite
Tests every agent independently and in workflow
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path so imports work from tests/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.llm_client import LLMClient
from config.models import Task, AgentType, Objective, ObjectiveStatus, TaskStatus
from agents import (
    BaseAgent,
    CoordinatorAgent,
    ResearchAgent,
    AnalysisAgent,
    CodeAgent,
    ValidationAgent,
    ExecutionAgent
)

class AgentTestSuite:
    """Complete test suite for all agents"""
    
    def __init__(self):
        self.llm = LLMClient()
        self.results = []
        
    def print_test(self, name: str, status: bool, details: str = ""):
        """Print test result"""
        status_str = "✅ PASS" if status else "❌ FAIL"
        print(f"\n{status_str} | {name}")
        if details:
            print(f"   → {details}")
        self.results.append((name, status))
    
    def test_coordinator_agent(self):
        """Test CoordinatorAgent task decomposition"""
        print("\n" + "="*80)
        print("TEST 1: COORDINATOR AGENT")
        print("="*80)
        
        coordinator = CoordinatorAgent(self.llm)
        
        try:
            # Test decomposition
            tasks = coordinator.decompose_objective("make a todo app")
            
            passed = (
                len(tasks) > 0 and
                all("id" in t and "description" in t and "agent_type" in t for t in tasks)
            )
            
            self.print_test(
                "Task Decomposition",
                passed,
                f"Generated {len(tasks)} tasks"
            )
            
            # Verify task structure
            for task in tasks:
                assert "dependencies" in task, "Missing dependencies"
                assert "metadata" in task, "Missing metadata"
            
            self.print_test("Task Structure Validation", True, "All tasks valid")
            
            return tasks
            
        except Exception as e:
            self.print_test("CoordinatorAgent", False, str(e))
            return []
    
    def test_research_agent(self):
        """Test ResearchAgent"""
        print("\n" + "="*80)
        print("TEST 2: RESEARCH AGENT")
        print("="*80)
        
        researcher = ResearchAgent(self.llm)
        
        try:
            task = Task(
                id="test_research",
                description="Research best practices for Python development",
                agent_type=AgentType.RESEARCH,
                dependencies=[],
                metadata={"success_criteria": "Comprehensive research provided"}
            )
            
            result = researcher.execute(task, context={})
            
            passed = (
                result is not None and
                len(result) > 100 and
                researcher.execution_count == 1
            )
            
            self.print_test(
                "Research Task Execution",
                passed,
                f"Generated {len(result)} characters"
            )
            
            return passed
            
        except Exception as e:
            self.print_test("ResearchAgent", False, str(e))
            return False
    
    def test_analysis_agent(self):
        """Test AnalysisAgent"""
        print("\n" + "="*80)
        print("TEST 3: ANALYSIS AGENT")
        print("="*80)
        
        analyzer = AnalysisAgent(self.llm)
        
        try:
            task = Task(
                id="test_analysis",
                description="Analyze the pros and cons of using SQLite vs PostgreSQL",
                agent_type=AgentType.ANALYSIS,
                dependencies=[],
                metadata={"success_criteria": "Detailed analysis provided"}
            )
            
            result = analyzer.execute(task, context={"prev_research": "Database research"})
            
            passed = (
                result is not None and
                len(result) > 100 and
                analyzer.execution_count == 1
            )
            
            self.print_test(
                "Analysis Task Execution",
                passed,
                f"Generated {len(result)} characters"
            )
            
            return passed
            
        except Exception as e:
            self.print_test("AnalysisAgent", False, str(e))
            return False
    
    def test_code_agent(self):
        """Test CodeAgent"""
        print("\n" + "="*80)
        print("TEST 4: CODE AGENT")
        print("="*80)
        
        coder = CodeAgent(self.llm)
        
        try:
            task = Task(
                id="test_code",
                description="Generate a Python calculator class with basic operations",
                agent_type=AgentType.CODE,
                dependencies=[],
                metadata={"success_criteria": "Working calculator code"}
            )
            
            result = coder.execute(task, context={})
            
            passed = (
                result is not None and
                len(result) > 200 and
                ("def" in result.lower() or "class" in result.lower()) and
                coder.execution_count == 1
            )
            
            self.print_test(
                "Code Generation",
                passed,
                f"Generated {len(result)} characters with function definitions"
            )
            
            # Check if result contains Python code
            has_code = "class" in result or "def" in result
            self.print_test("Python Code Detection", has_code, "Found class/function definitions")
            
            return passed
            
        except Exception as e:
            self.print_test("CodeAgent", False, str(e))
            return False
    
    def test_execution_agent(self):
        """Test ExecutionAgent"""
        print("\n" + "="*80)
        print("TEST 5: EXECUTION AGENT")
        print("="*80)
        
        executor = ExecutionAgent(self.llm)
        
        try:
            # Test file creation
            task = Task(
                id="test_exec",
                description="Create a test file",
                agent_type=AgentType.EXECUTION,
                dependencies=[],
                metadata={
                    "type": "file",
                    "file_path": "test_output.txt",
                    "content": "This is a test file created by ExecutionAgent\n\nTest content here."
                }
            )
            
            result = executor.execute(task, context={})
            result_data = json.loads(result)
            
            passed = (
                result_data.get("success") and
                Path("workspace/test_output.txt").exists()
            )
            
            self.print_test(
                "File Creation",
                passed,
                "test_output.txt created successfully"
            )
            
            # Verify action result
            action_passed = (
                task.action_result is not None and
                task.action_result.success and
                "test_output.txt" in task.action_result.files_created
            )
            
            self.print_test(
                "ActionResult Tracking",
                action_passed,
                "Action result properly populated"
            )
            
            return passed and action_passed
            
        except Exception as e:
            self.print_test("ExecutionAgent", False, str(e))
            return False
    
    def test_validation_agent(self):
        """Test ValidationAgent"""
        print("\n" + "="*80)
        print("TEST 6: VALIDATION AGENT")
        print("="*80)
        
        validator = ValidationAgent(self.llm)
        
        try:
            # Test successful execution result
            task = Task(
                id="test_validation",
                description="Validate execution results",
                agent_type=AgentType.EXECUTION,
                dependencies=[],
                metadata={"type": "file"}
            )
            
            success_result = json.dumps({
                "success": True,
                "type": "file",
                "file_path": "test.py",
                "bytes_written": 100
            })
            
            is_valid, feedback = validator.validate(task, success_result, "Test objective")
            
            self.print_test(
                "Validation Pass Detection",
                is_valid,
                feedback
            )
            
            # Test failed execution result
            fail_result = json.dumps({
                "success": False,
                "type": "file",
                "error": "Permission denied"
            })
            
            is_invalid, feedback = validator.validate(task, fail_result, "Test objective")
            
            self.print_test(
                "Validation Fail Detection",
                not is_invalid,
                "Correctly identified failure"
            )
            
            return is_valid and not is_invalid
            
        except Exception as e:
            self.print_test("ValidationAgent", False, str(e))
            return False
    
    def test_workflow_integration(self):
        """Test complete workflow"""
        print("\n" + "="*80)
        print("TEST 7: WORKFLOW INTEGRATION")
        print("="*80)
        
        try:
            coordinator = CoordinatorAgent(self.llm)
            
            # Decompose objective
            tasks = coordinator.decompose_objective("create a simple greeter app")
            
            workflow_passed = (
                len(tasks) > 0 and
                any(t["agent_type"] == "code" for t in tasks) and
                any(t["agent_type"] == "execution" for t in tasks)
            )
            
            self.print_test(
                "Multi-Task Workflow",
                workflow_passed,
                f"Created {len(tasks)} coordinated tasks"
            )
            
            # Check dependencies
            has_dependencies = any(t.get("dependencies") for t in tasks)
            
            self.print_test(
                "Task Dependencies",
                has_dependencies,
                "Tasks have proper dependencies"
            )
            
            return workflow_passed
            
        except Exception as e:
            self.print_test("Workflow Integration", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests and show summary"""
        print("\n")
        print("█████████████████████████████████████████████████████████████████████████████████")
        print("                    MULTI-AGENT SYSTEM TEST SUITE")
        print("█████████████████████████████████████████████████████████████████████████████████")
        
        self.test_coordinator_agent()
        self.test_research_agent()
        self.test_analysis_agent()
        self.test_code_agent()
        self.test_execution_agent()
        self.test_validation_agent()
        self.test_workflow_integration()
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80 + "\n")
        
        passed = sum(1 for _, status in self.results if status)
        total = len(self.results)
        
        print(f"{'Test Name':<40} {'Status':<10}")
        print("-" * 50)
        
        for name, status in self.results:
            status_str = "✅ PASS" if status else "❌ FAIL"
            print(f"{name:<40} {status_str:<10}")
        
        print("-" * 50)
        print(f"\nTotal: {passed}/{total} tests passed ({100*passed//total if total > 0 else 0}%)")
        
        if passed == total:
            print("\n🎉 All agents are working correctly! System ready for production.")
        else:
            print(f"\n⚠️  {total - passed} agent(s) need attention.")
        
        return passed == total


if __name__ == "__main__":
    suite = AgentTestSuite()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)