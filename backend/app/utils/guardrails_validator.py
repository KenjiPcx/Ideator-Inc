# Have to disable guardrails because its not compatible with the latest llama_index version

from typing import Type, TypeVar, Optional, Generic
from pydantic import BaseModel
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.output_parsers.guardrails import GuardrailsOutputParser
import guardrails as gd

T = TypeVar('T', bound=BaseModel)

class GuardrailsJsonValidator(Generic[T]):
    """
    A utility class that validates JSON outputs using Guardrails and a Pydantic schema.
    """
    def __init__(self,
                 model: Type[T],
                 llm: FunctionCallingLLM,
                 max_retries: int = 3):
        self.model = model
        self.llm = llm
        self.max_retries = max_retries
        
        # Create guard and parser
        self.guard = gd.Guard.from_pydantic(
            output_class=model,
            prompt=self._get_base_prompt()
        )
        self.output_parser = GuardrailsOutputParser(self.guard)
        
    def _get_base_prompt(self) -> str:
        return """
        Fix the following JSON content to match the required schema:
        
        ${input_json}
        
        ${gr.xml_prefix_prompt}
        ${output_schema}
        ${gr.json_suffix_prompt_v2_wo_none}
        """
        
    async def validate_and_fix(self, content: str) -> Optional[T]:
        """
        Validates and fixes JSON content using Guardrails.
        """
        retries = 0
        current_content = content
        
        while retries < self.max_retries:
            try:
                # Attach the output parser to the LLM
                self.llm.output_parser = self.output_parser
                
                # Use Guardrails to validate and correct
                response = await self.llm.acomplete(
                    self.guard.wrap_prompt(input_json=current_content)
                )
                
                # Parse the response using the model
                return self.model.model_validate(response)
                
            except Exception as e:
                print(f"Validation attempt {retries + 1} failed: {str(e)}")
                current_content = response.text if hasattr(response, 'text') else str(response)
                retries += 1
                
        return None 