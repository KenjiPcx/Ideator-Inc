from pathlib import Path
import os

def get_project_root() -> Path:
    """
    Returns the absolute path to the project root directory.
    Assumes this file is in backend/app/utils/paths.py
    """
    current_file = Path(__file__)  # Gets path to this file
    return current_file.parent.parent.parent

def get_session_data_path(session_id: str) -> Path:
    """
    Resolves the absolute path for session-specific data storage.
    
    Args:
        session_id (str): The unique session identifier
        
    Returns:
        Path: The absolute path for the session data
    """
    root_path = get_project_root()
    return (root_path / "data" / session_id).resolve() 

if __name__ == "__main__":
    print(get_session_data_path("123"))