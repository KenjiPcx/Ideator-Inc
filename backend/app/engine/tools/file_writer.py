import logging
import os
from typing import Optional
from llama_index.core.tools.function_tool import FunctionTool

OUTPUT_DIR = "data"

def write_file(
    content: str,
    file_name: str,
    session_id: str,
    subdirectory: Optional[str] = None
) -> str:
    """
    Write content to a file in a specified directory.
    
    Parameters:
        content: str (content to write to the file)
        file_name: str (name of the file) must be a valid file name, with or without extension
        session_id: str (session id) the directory prefix to save the file to
        subdirectory: Optional[str] (additional subdirectory path under session_id)
    
    Returns:
        str: The full path to the written file
    """
    try:
        # Don't allow directory traversal or special characters
        if os.path.isabs(file_name) or not file_name.replace(".", "").replace("_", "").replace("-", "").isalnum():
            raise ValueError("Invalid file name. Use only alphanumeric characters, dots, underscores, and hyphens.")
        
        # Construct the full path
        path_components = [OUTPUT_DIR]
        if subdirectory:
            path_components.append(subdirectory)
        path_components.append(session_id)
        file_path = os.path.join(*path_components, file_name)
        
        # Create directory and write file
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
            
        return file_path
            
    except Exception as e:
        logging.error(f"Failed to write file: {str(e)}")
        raise e

def get_tools(**kwargs):
    return [
        FunctionTool.from_defaults(
            write_file,
            name="write_file",
            description="Write content to a file in the specified directory"
        )
    ] 