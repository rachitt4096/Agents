"""
Analysis Agent - Data analysis and insights generation
"""
from typing import Dict, Any
from agents.base_agent import BaseAgent
from config.models import Task, AgentType
from config.llm_client import LLMClient
from loguru import logger


class AnalysisAgent(BaseAgent):
    """
    Analysis Agent specialized in:
    - Data analysis
    - Pattern recognition
    - Insights generation
    - Recommendations
    """
    
    def __init__(self, llm_client: LLMClient):
        super().__init__(
            llm_client=llm_client,
            name="Analyzer",
            agent_type=AgentType.ANALYSIS,
            description="Data analysis and insights generation"
        )
    
    def execute(self, task: Task, context: Dict[str, Any] = None) -> str:
        """
        Execute analysis task
        
        Args:
            task: Analysis task to execute
            context: Shared context including data to analyze
            
        Returns:
            Analysis results and insights
        """
        logger.info(f"Analysis Agent executing: {task.description}")
        
        # Build context and feedback strings
        context_str = self._build_context_string(context)
        feedback_str = self._build_feedback_string(context, task.id)
        
        # Build prompt
        prompt = f"""You are an expert data analyst with strong analytical reasoning skills.

ANALYSIS TASK: {task.description}
{context_str}
{feedback_str}

Provide thorough analysis that:

1. IDENTIFIES KEY PATTERNS
   - Recognize important trends
   - Spot anomalies or outliers
   - Find correlations

2. GENERATES INSIGHTS
   - Draw meaningful conclusions
   - Explain what the data shows
   - Contextualize findings

3. PROVIDES RECOMMENDATIONS
   - Suggest actionable next steps
   - Prioritize by impact
   - Consider tradeoffs

4. STRUCTURES CLEARLY
   - Organize findings logically
   - Use clear headings
   - Support claims with evidence

Be analytical, evidence-based, and practical. Focus on insights that drive decisions."""

        # Generate response
        result = self.llm.generate(
            messages=[{"role": "user", "content": prompt}]
        )
        
        self.execution_count += 1
        logger.success(f"Analysis task completed: {task.id}")
        
        return result