"""
Research Agent - Information gathering and research
"""
from typing import Dict, Any
from agents.base_agent import BaseAgent
from config.models import Task, AgentType
from config.llm_client import LLMClient
from loguru import logger


class ResearchAgent(BaseAgent):
    """
    Research Agent specialized in:
    - Information gathering
    - Fact-finding
    - Research synthesis
    - Knowledge extraction
    """
    
    def __init__(self, llm_client: LLMClient):
        super().__init__(
            llm_client=llm_client,
            name="Researcher",
            agent_type=AgentType.RESEARCH,
            description="Information gathering and research"
        )
    
    def execute(self, task: Task, context: Dict[str, Any] = None) -> str:
        """
        Execute research task
        
        Args:
            task: Research task to execute
            context: Shared context from previous tasks
            
        Returns:
            Research findings
        """
        logger.info(f"Research Agent executing: {task.description}")
        
        # Build context and feedback strings
        context_str = self._build_context_string(context)
        feedback_str = self._build_feedback_string(context, task.id)
        
        # Build prompt
        prompt = f"""You are an expert researcher with deep knowledge across multiple domains.

RESEARCH TASK: {task.description}
{context_str}
{feedback_str}

Provide comprehensive research that:

1. ADDRESSES THE SPECIFIC TASK
   - Focus on exactly what was asked
   - Be thorough and detailed

2. INCLUDES RELEVANT INFORMATION
   - Key facts and data
   - Important context
   - Supporting evidence

3. STRUCTURED CLEARLY
   - Use clear organization
   - Present information logically
   - Highlight key findings

4. ACTIONABLE INSIGHTS
   - Draw meaningful conclusions
   - Provide practical takeaways
   - Suggest next steps if relevant

Respond with well-researched, factual information. Be comprehensive but focused."""

        # Generate response
        result = self.llm.generate(
            messages=[{"role": "user", "content": prompt}]
        )
        
        self.execution_count += 1
        logger.success(f"Research task completed: {task.id}")
        
        return result