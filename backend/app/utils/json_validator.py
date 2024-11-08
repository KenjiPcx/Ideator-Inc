from typing import Type, Optional, Any, Generic, TypeVar
from app.utils.json_extractor import extract_json_from_response
from pydantic import BaseModel
from textwrap import dedent
from llama_index.core.llms.function_calling import FunctionCallingLLM

T = TypeVar('T', bound=BaseModel)

class JsonValidationHelper(Generic[T]):
    """
    A utility class that helps validate and correct JSON outputs against a Pydantic schema.
    """
    def __init__(self, 
                 model: Type[T],
                 llm: FunctionCallingLLM,
                 max_retries: int = 3):
        self.model = model
        self.llm = llm
        self.max_retries = max_retries
        
    async def validate_and_fix(self, content: str) -> Optional[T]:
        """
        Attempts to validate JSON content against the schema, retrying with AI assistance if needed.
        """
        retries = 0
        last_error = None
        current_content = extract_json_from_response(content)
        if current_content is None:
            current_content = content

        while retries < self.max_retries:
            try:
                # Try to validate the current content
                return self.model.model_validate(current_content)
            except Exception as e:
                last_error = str(e)
                
                # Generate a reflection prompt to fix the JSON
                prompt = self._generate_reflection_prompt(current_content, last_error)
                print(prompt)
                
                # Get corrected JSON from LLM
                response = await self.llm.acomplete(prompt)
                print(response)
                current_content = extract_json_from_response(response.text.strip())
                retries += 1
        
        # If we've exhausted retries, return None
        return None
    
    def _generate_reflection_prompt(self, wrong_output: str, error: str) -> str:
        return dedent(f"""
            You are a JSON correction assistant. The following JSON output failed validation:
            ---------------------
            {wrong_output}
            ---------------------

            The validation error was: {error}

            The JSON must follow this schema:
            {self.model.model_json_schema()}

            Return ONLY the corrected JSON object. Do not include any explanations or additional text.
            Make sure the output is valid JSON that matches the schema exactly and that no other content is modified or summarized.
        """).strip()