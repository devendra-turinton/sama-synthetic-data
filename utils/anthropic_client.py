import anthropic
import json
import re
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
        """Generate structured JSON data from Claude with error recovery."""
        structured_system_prompt = (
            "You are tasked with generating structured data for a military intelligence database. "
            "Your response must be strictly valid JSON format only. Do not include any explanatory text, markdown formatting, or code blocks. "
            "Provide only the raw JSON object. CRITICAL: All numeric fields must be single values, not comma-separated lists. "
            "For frequency field, use ONLY ONE NUMBER (e.g., 345.2, not 345.2,5.9)."
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
            # Try to repair common JSON issues
            response_text = self._repair_json(response_text)
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.error(f"Response text: {response_text}")
            # Try aggressive repair
            try:
                repaired = self._aggressive_json_repair(response_text)
                return json.loads(repaired)
            except Exception:
                logger.error("Aggressive repair also failed")
                # Last resort: use json-repair to attempt repair
                try:
                    from json_repair import repair_json
                    fixed = repair_json(response_text)
                    logger.info("json-repair successfully repaired the JSON response.")
                    return json.loads(fixed)
                except Exception as e2:
                    logger.error(f"json-repair repair failed: {str(e2)}")
                    raise
        except Exception as e:
            logger.error(f"Error in generating structured data: {str(e)}")
            raise
    
    def _repair_json(self, text: str) -> str:
        """Repair common JSON issues."""
        # Fix multiple values in single field (e.g., "frequency":346.5,5.9)
        # Pattern: "field":number,number
        text = re.sub(r'("frequency"\s*:\s*)(\d+\.?\d*),\d+\.?\d*', r'\1\2', text)
        text = re.sub(r'("range"\s*:\s*)(\d+\.?\d*),\d+\.?\d*', r'\1\2', text)
        
        # Fix trailing commas before closing braces/brackets
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        
        return text
    
    def _aggressive_json_repair(self, text: str) -> str:
        """Aggressive JSON repair for badly malformed JSON."""
        # Remove all line breaks and extra spaces
        text = ' '.join(text.split())
        
        # Fix common issues
        text = self._repair_json(text)
        
        # Try to extract just the JSON object if there's extra text
        json_start = text.find('{')
        json_end = text.rfind('}')
        if json_start >= 0 and json_end > json_start:
            text = text[json_start:json_end+1]
        
        return text