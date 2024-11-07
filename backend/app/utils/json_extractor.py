import json
import re
from typing import Any, Optional

def extract_json_from_response(response: str) -> Optional[Any]:
    """
    Extract and parse JSON content from a response string that might be wrapped in markdown.
    
    Args:
        response: String that might contain JSON content, possibly wrapped in markdown
        
    Returns:
        Parsed JSON content or None if no valid JSON found
        
    Example:
        >>> text = '```json\n{"key": "value"}\n```'
        >>> extract_json_from_response(text)
        {'key': 'value'}
    """
    # Try to extract content from ```json blocks first
    json_block_match = re.search(r'```(?:json)?\n(.*?)\n```', response, re.DOTALL)
    if json_block_match:
        try:
            return json.loads(json_block_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to find any JSON-like content between curly braces
    json_content_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_content_match:
        try:
            return json.loads(json_content_match.group(0))
        except json.JSONDecodeError:
            pass

    # Try to find any JSON array content between square brackets
    array_match = re.search(r'\[.*\]', response, re.DOTALL)
    if array_match:
        try:
            return json.loads(array_match.group(0))
        except json.JSONDecodeError:
            pass

    # If the entire response is valid JSON, try that
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        return None
    
def extract_code_block_from_response(response: str) -> Optional[str]:
    """
    Extract content including markdown code block formatting from a response string.
    
    Args:
        response: String that might contain content wrapped in markdown code blocks
        
    Returns:
        Complete code block string including backticks or None if no content found
        
    Example:
        >>> text = '```json\n{"key": "value"}\n```'
        >>> extract_code_block_from_response(text)
        '```json\n{"key": "value"}\n```'
    """
    # Try to extract complete code block including backticks
    block_match = re.search(r'(```(?:\w+)?\n.*?\n```)', response, re.DOTALL)
    if block_match:
        return block_match.group(1)

    return response.strip()