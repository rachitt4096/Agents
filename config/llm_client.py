"""
LLM Client - Wrapper for Groq API
"""
from typing import List, Dict, Optional
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
from config.settings import settings


class LLMClient:
    """Wrapper for Groq API with retry logic"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.client = Groq(api_key=self.api_key)
        self.call_count = 0
        self.total_tokens = 0
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = settings.TEMPERATURE,
        max_tokens: int = settings.MAX_TOKENS,
        **kwargs
    ) -> str:
        """Generate completion with automatic retry logic"""
        try:
            model = model or settings.WORKER_MODEL
            self.call_count += 1
            
            logger.info(f"API Call #{self.call_count} - Model: {model}")
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            result = response.choices[0].message.content
            
            if hasattr(response, 'usage'):
                self.total_tokens += response.usage.total_tokens
            
            logger.success(f"API call successful")
            return result
            
        except Exception as e:
            logger.error(f"LLM API error: {str(e)}")
            raise
    
    def generate_json(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate JSON response with lower temperature"""
        return self.generate(
            messages=messages,
            model=model,
            temperature=0.3,
            **kwargs
        )
    
    def get_stats(self) -> Dict[str, int]:
        """Get usage statistics"""
        return {
            "total_calls": self.call_count,
            "total_tokens": self.total_tokens
        }