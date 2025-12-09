from pathlib import Path

def find_repo_root() -> Path:
    """
    Finds the root directory of the Git repository by searching upwards 
    from the location of the current script for the closest .git folder.

    Returns:
        Path: The absolute path to the repository root directory (str).
    """
    
    try:
        # Start the search from the directory containing the current file
        # resolve() converts to an absolute path
        current_path = Path(__file__).resolve().parent
    except NameError:
        # Fallback for interactive environments (Jupyter, plain interpreter)
        current_path = Path.cwd().resolve()
        
    # Iterate through the directory and its parents
    for parent in [current_path] + list(current_path.parents):
        if (parent / ".git").is_dir():
            return parent
    
    # If the root is not found
    raise FileNotFoundError(
        "Could not find the Git repository root (.git directory) in any parent folders of the script's location."
    )


REPO_ROOT = find_repo_root()
    