import anthropic
import json
import re
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnthropicClient:
    """Enhanced Anthropic client with robust JSON parsing"""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", 
                 max_tokens: int = 4000, temperature: float = 0.3):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.request_count = 0
        self.total_tokens_used = 0
    
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, 
                     max_retries: int = 3) -> str:
        """Generate text response with retry logic"""
        
        for attempt in range(max_retries):
            try:
                self.request_count += 1
                
                logger.debug(f"API Request #{self.request_count} (attempt {attempt + 1}/{max_retries})")
                
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_prompt if system_prompt else "",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # Track token usage
                self.total_tokens_used += message.usage.input_tokens + message.usage.output_tokens
                
                return message.content[0].text
                
            except anthropic.RateLimitError as e:
                wait_time = 2 ** attempt
                logger.warning(f"Rate limit hit, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                
            except anthropic.APIError as e:
                logger.error(f"API error on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)
        
        raise Exception(f"Failed after {max_retries} attempts")
    
    def generate_structured_data(self, prompt: str, system_prompt: Optional[str] = None,
                                max_retries: int = 3) -> Dict[str, Any]:
        """Generate structured JSON data with comprehensive error recovery"""
        
        # VERY STRICT system prompt
        json_system_prompt = (
            "CRITICAL INSTRUCTIONS:\n"
            "1. Return ONLY raw JSON - no explanations, no markdown, no code blocks\n"
            "2. Start your response with { (opening brace)\n"
            "3. End your response with } (closing brace)\n"
            "4. Do NOT include any text before the opening {\n"
            "5. Do NOT include any text after the closing }\n"
            "6. No 'Here is the JSON:', no 'Output:', no prefixes of any kind\n"
            "7. All numeric fields must be single values (no comma-separated lists)\n"
            "8. All strings must be properly quoted\n"
        )
        
        if system_prompt:
            json_system_prompt += "\n" + system_prompt
        
        for attempt in range(max_retries):
            try:
                response_text = self.generate_text(prompt, json_system_prompt)
                
                # Log for debugging on first attempt
                if attempt == 0:
                    logger.debug(f"Raw response length: {len(response_text)} chars")
                    logger.debug(f"First 100 chars: {response_text[:100]}")
                    logger.debug(f"Last 100 chars: {response_text[-100:]}")
                
                # AGGRESSIVE cleaning before parsing
                cleaned_text = self._extract_json_from_response(response_text)
                
                # Repair common issues
                repaired_text = self._repair_json(cleaned_text)
                
                # Parse JSON
                parsed = json.loads(repaired_text)
                
                # Validate structure
                if not isinstance(parsed, dict):
                    raise ValueError("Response is not a JSON object")
                
                logger.debug(f"✓ Successfully parsed JSON (attempt {attempt + 1})")
                return parsed
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error (attempt {attempt + 1}): {str(e)}")
                logger.error(f"Error at line {e.lineno}, column {e.colno}, position {e.pos}")
                
                # Show context around error
                error_start = max(0, e.pos - 50)
                error_end = min(len(response_text), e.pos + 50)
                logger.error(f"Context: ...{response_text[error_start:error_end]}...")
                
                # Save failed response for debugging
                if attempt == max_retries - 1:
                    self._save_failed_response(response_text, cleaned_text, repaired_text, e)
                
                # Try aggressive repair
                if attempt < max_retries - 1:
                    try:
                        repaired = self._aggressive_json_repair(response_text)
                        parsed = json.loads(repaired)
                        logger.info("✓ Aggressive repair successful")
                        return parsed
                    except Exception as repair_error:
                        logger.debug(f"Aggressive repair failed: {repair_error}")
                else:
                    # Last attempt: try json_repair library
                    try:
                        from json_repair import repair_json
                        repaired = repair_json(response_text)
                        parsed = json.loads(repaired)
                        logger.info("✓ json_repair library fixed the JSON")
                        return parsed
                    except Exception as e2:
                        logger.error(f"All repair attempts failed: {str(e2)}")
                        raise ValueError(
                            f"Unable to parse JSON after {max_retries} attempts. "
                            f"Last error: {str(e)}. Check debug file in output directory."
                        )
            
            except Exception as e:
                logger.error(f"Error generating structured data (attempt {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)
        
        raise Exception(f"Failed to generate valid JSON after {max_retries} attempts")
    
    def _extract_json_from_response(self, text: str) -> str:
        """Aggressively extract JSON from response text"""
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove markdown code blocks
        if "```json" in text:
            parts = text.split("```json")
            if len(parts) > 1:
                text = parts[1].split("```")[0].strip()
        elif "```" in text:
            parts = text.split("```")
            if len(parts) >= 3:
                text = parts[1].strip()
                # Remove language identifier
                if text.startswith("json\n"):
                    text = text[5:]
        
        # Remove common prefixes (case insensitive)
        prefix_patterns = [
            r'^Here\s+is\s+the\s+JSON:?\s*',
            r'^Here\'s\s+the\s+JSON:?\s*',
            r'^JSON:?\s*',
            r'^Output:?\s*',
            r'^Result:?\s*',
            r'^Response:?\s*',
            r'^The\s+JSON\s+is:?\s*',
        ]
        
        for pattern in prefix_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Find first { or [
        json_start = -1
        for i, char in enumerate(text):
            if char in ['{', '[']:
                json_start = i
                break
        
        if json_start > 0:
            logger.debug(f"Removed {json_start} chars before JSON start")
            text = text[json_start:]
        elif json_start == -1:
            logger.warning("No JSON start delimiter found!")
        
        # Find last } or ]
        json_end = -1
        open_count = 0
        close_count = 0
        
        for i, char in enumerate(text):
            if char == '{':
                open_count += 1
            elif char == '}':
                close_count += 1
                if open_count > 0 and open_count == close_count:
                    json_end = i + 1
                    break
        
        if json_end > 0 and json_end < len(text):
            removed_suffix = len(text) - json_end
            if removed_suffix > 0:
                logger.debug(f"Removed {removed_suffix} chars after JSON end")
            text = text[:json_end]
        
        return text.strip()
    
    def _repair_json(self, text: str) -> str:
        """Repair common JSON issues"""
        
        # Fix multiple values in single numeric field
        text = re.sub(r'("frequency"\s*:\s*)(\d+\.?\d*),[\d,\.]+', r'\1\2', text)
        text = re.sub(r'("range"\s*:\s*)(\d+\.?\d*)\s*km', r'\1"\2"', text)
        text = re.sub(r'("range_km"\s*:\s*)(\d+\.?\d*),[\d,\.]+', r'\1"\2"', text)
        
        # Fix trailing commas
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        
        # Fix missing commas between fields
        text = re.sub(r'"\s*\n\s*"', '",\n"', text)
        text = re.sub(r'}\s*\n\s*{', '},\n{', text)
        text = re.sub(r']\s*\n\s*\[', '],\n[', text)
        
        # Remove comments
        text = re.sub(r'//.*?\n', '\n', text)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        
        # Fix unquoted null, true, false
        text = re.sub(r':\s*None\s*([,}])', r': null\1', text)
        text = re.sub(r':\s*True\s*([,}])', r': true\1', text)
        text = re.sub(r':\s*False\s*([,}])', r': false\1', text)
        
        return text
    
    def _aggressive_json_repair(self, text: str) -> str:
        """Last resort aggressive repair"""
        
        # Extract JSON aggressively
        text = self._extract_json_from_response(text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        # Apply standard repairs
        text = self._repair_json(text)
        
        # Balance brackets
        text = self._balance_brackets(text)
        
        return text
    
    def _balance_brackets(self, text: str) -> str:
        """Balance brackets and braces"""
        
        open_braces = text.count('{')
        close_braces = text.count('}')
        open_brackets = text.count('[')
        close_brackets = text.count(']')
        
        if open_braces > close_braces:
            text += '}' * (open_braces - close_braces)
        if open_brackets > close_brackets:
            text += ']' * (open_brackets - close_brackets)
        
        return text
    
    def _save_failed_response(self, original: str, cleaned: str, repaired: str, error: Exception):
        """Save failed response for debugging"""
        try:
            from config import OUTPUT_DIR
            debug_file = os.path.join(
                OUTPUT_DIR, 
                f"failed_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("FAILED JSON RESPONSE DEBUG\n")
                f.write("="*80 + "\n\n")
                
                f.write(f"Error: {str(error)}\n")
                f.write(f"Error type: {type(error).__name__}\n\n")
                
                f.write("ORIGINAL RESPONSE:\n")
                f.write("-"*80 + "\n")
                f.write(original)
                f.write("\n\n")
                
                f.write("CLEANED RESPONSE:\n")
                f.write("-"*80 + "\n")
                f.write(cleaned)
                f.write("\n\n")
                
                f.write("REPAIRED RESPONSE:\n")
                f.write("-"*80 + "\n")
                f.write(repaired)
                f.write("\n\n")
            
            logger.error(f"Debug info saved to: {debug_file}")
        except Exception as e:
            logger.debug(f"Could not save debug file: {e}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        return {
            "total_requests": self.request_count,
            "total_tokens": self.total_tokens_used,
            "estimated_cost_usd": self.total_tokens_used * 0.000003
        }