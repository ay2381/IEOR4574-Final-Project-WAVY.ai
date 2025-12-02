"""
LLM provider interface and implementations
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from openai import OpenAI, AzureOpenAI
import time

from src.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate_completion(self, prompt: str, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Generate a completion from the LLM"""
        pass
    
    @abstractmethod
    def generate_json_completion(self, prompt: str, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Generate a JSON-formatted completion"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"
        logger.info("Initialized OpenAI provider")
    
    def generate_completion(self, prompt: str, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Generate completion with retry logic"""
        max_tokens = max_tokens or settings.MAX_TOKENS
        
        for attempt in range(settings.LLM_RETRY_ATTEMPTS):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional nutritionist and meal planning expert."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=settings.TEMPERATURE
                )
                
                return {
                    "content": response.choices[0].message.content,
                    "token_usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens
                    }
                }
            except Exception as e:
                logger.error(f"LLM request failed (attempt {attempt + 1}): {str(e)}")
                if attempt == settings.LLM_RETRY_ATTEMPTS - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def generate_json_completion(self, prompt: str, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Generate JSON completion"""
        max_tokens = max_tokens or settings.MAX_TOKENS
        
        for attempt in range(settings.LLM_RETRY_ATTEMPTS):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional nutritionist. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=settings.TEMPERATURE,
                    response_format={"type": "json_object"}
                )
                
                return {
                    "content": response.choices[0].message.content,
                    "token_usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens
                    }
                }
            except Exception as e:
                logger.error(f"LLM JSON request failed (attempt {attempt + 1}): {str(e)}")
                if attempt == settings.LLM_RETRY_ATTEMPTS - 1:
                    raise
                time.sleep(2 ** attempt)


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI provider"""
    
    def __init__(self):
        if not settings.AZURE_OPENAI_API_KEY or not settings.AZURE_OPENAI_ENDPOINT:
            raise ValueError("Azure OpenAI credentials not configured")
        
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version="2024-02-15-preview",
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
        logger.info("Initialized Azure OpenAI provider")
    
    def generate_completion(self, prompt: str, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Generate completion using Azure OpenAI"""
        max_tokens = max_tokens or settings.MAX_TOKENS
        
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "You are a professional nutritionist and meal planning expert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=settings.TEMPERATURE
        )
        
        return {
            "content": response.choices[0].message.content,
            "token_usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            }
        }
    
    def generate_json_completion(self, prompt: str, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Generate JSON completion using Azure OpenAI"""
        return self.generate_completion(prompt, max_tokens)


def get_llm_provider() -> LLMProvider:
    """Factory function to get the configured LLM provider"""
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "openai":
        return OpenAIProvider()
    elif provider == "azure":
        return AzureOpenAIProvider()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
