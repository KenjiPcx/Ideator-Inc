import logging
import os
from typing import List, Optional, Dict, Any, Union
import json

from llama_index.core.tools import FunctionTool
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy

logger = logging.getLogger("uvicorn")


class WebReaderResult(BaseModel):
    content: str | None = None
    url: str
    is_error: bool
    error_message: Optional[str] = None

class DefaultSchema(BaseModel):
    content: str = Field(description="The main content of the page, filtering out all the noise, do not summarize the content, include all important details including statistics, quotes, examples, stories, etc")

async def read_webpage(
    url: str,
    instruction: str = "Extract the main content of the page, do not summarize the content, include all important details including statistics, quotes, examples, stories, etc",
    provider: str = "openai/gpt-4o-mini",
    schema: Dict | None = DefaultSchema.model_json_schema(),
    openai_api_key: Optional[str] = None,
) -> WebReaderResult:
    """
    Read and extract structured content from a webpage using crawl4ai.
    
    Parameters:
        url (str): The URL to read content from
        schema (Dict): Pydantic model schema defining the structure to extract
        instruction (str): Instructions for the LLM on what to extract
        provider (str): LLM provider to use
        openai_api_key (Optional[str]): OpenAI API key. If not provided, will try to get from env
    """
    api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required for LLM extraction")

    try:
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(
                url=url,
                remove_overlay_elements=True,
                strategy=LLMExtractionStrategy(
                    instruction=instruction,
                    schema=schema,
                    provider=provider,
                    openai_api_key=api_key
                ),
                magic=True,
                bypass_cache=True,
            )
        
        return WebReaderResult(
            content=result.extracted_content,
            url=url,
            is_error=False
        )
            
    except Exception as e:
        error_message = f"Error reading webpage: {str(e)}"
        logger.error(error_message)
        return WebReaderResult(
            content="Error reading webpage",
            url=url,
            is_error=True,
            error_message=error_message
        )

def get_tools(**kwargs):
    return [FunctionTool.from_defaults(
        async_fn=lambda url, instruction, schema, provider="openai/gpt-4o-mini": read_webpage(
            url=url,
            # instruction=instruction,
            # schema=schema,
            provider=provider,
            openai_api_key=kwargs.get('openai_api_key')
        ),
        description="Read and extract structured content from a webpage given specific instructions on what to extract. It requires detailed context, but it does not have access to your memory so you have to provide it yourself. For example, if you are using it to find competitors, you need to first provide the context of the product you are researching."
    )]
