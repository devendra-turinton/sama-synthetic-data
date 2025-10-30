import asyncio
import json
import logging
from typing import Dict, Any, List
from anthropic import AsyncAnthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AsyncAnthropicClient:
    """Async wrapper for Anthropic API calls with rate limiting"""
    
    def __init__(self, api_key: str, model: str, max_tokens: int = 16384, 
                 temperature: float = 0.1, max_concurrent: int = 5):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.semaphore = asyncio.Semaphore(max_concurrent)  # Rate limiting
        
    async def generate_structured_data(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """Generate structured data with rate limiting"""
        
        async with self.semaphore:  # Limit concurrent requests
            try:
                messages = [{"role": "user", "content": prompt}]
                
                kwargs = {
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "messages": messages
                }
                
                if system_prompt:
                    kwargs["system"] = system_prompt
                
                response = await self.client.messages.create(**kwargs)
                
                # Extract text from response
                response_text = response.content[0].text
                
                # Clean markdown if present
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                # Parse JSON
                return json.loads(response_text)
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.error(f"Response text: {response_text[:500]}")
                raise
                
            except Exception as e:
                logger.error(f"API call error: {e}")
                raise
    
    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """Generate plain text response"""
        
        async with self.semaphore:
            try:
                messages = [{"role": "user", "content": prompt}]
                
                kwargs = {
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "messages": messages
                }
                
                if system_prompt:
                    kwargs["system"] = system_prompt
                
                response = await self.client.messages.create(**kwargs)
                return response.content[0].text
                
            except Exception as e:
                logger.error(f"API call error: {e}")
                raise