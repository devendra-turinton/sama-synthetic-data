import anthropic
import json
from typing import Dict, List, Any, Optional
import os
import logging
from config import ANTHROPIC_API_KEY, MODEL_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnthropicClient:
    def __init__(self, api_key: str = ANTHROPIC_API_KEY):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = MODEL_CONFIG["model"]
        self.max_tokens = MODEL_CONFIG["max_tokens"]
        self.temperature = MODEL_CONFIG["temperature"]
    
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text response from Claude."""
        try:
            logger.info(f"Sending prompt to Claude. Length: {len(prompt)} characters")
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt if system_prompt else "",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
        except Exception as e:
            logger.error(f"Error in generating text: {str(e)}")
            raise
    
    def generate_structured_data(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate structured JSON data from Claude."""
        structured_system_prompt = (
            "You are tasked with generating structured data for a military intelligence database. "
            "Your response must be strictly valid JSON format only. Do not include any explanatory text, markdown formatting, or code blocks. Provide only the raw JSON object. "
            "The output must be compact, minified JSON (no extra whitespace or indentation), with no trailing commas, missing delimiters, or omitted punctuation. "
            "Double-check that all brackets, braces, and commas are present and correct. Do not include any comments or explanations—only the raw JSON object."
        )
        if system_prompt:
            structured_system_prompt += "\n\n" + system_prompt
        try:
            response_text = self.generate_text(prompt, structured_system_prompt)
            # Clean up the response if it has markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.error(f"Response text: {response_text}")
            raise
        except Exception as e:
            logger.error(f"Error in generating structured data: {str(e)}")
            raise