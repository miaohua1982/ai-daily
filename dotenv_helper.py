#!/usr/bin/env python3
"""
Dotenv Helper — Simple .env file parser without external dependencies.

Usage:
    from dotenv_helper import load_dot_env
    
    env_vars = load_dot_env(Path(__file__).parent / ".env")
    api_key = os.environ.get("API_KEY") or env_vars.get("API_KEY", "")
"""

from pathlib import Path
from typing import Dict


def load_dot_env(path: Path) -> Dict[str, str]:
    """
    Very simple .env parser — no dependency needed.
    
    Parses KEY=VALUE lines from .env file.
    Supports:
    - Comments (lines starting with #)
    - Quoted values (single or double quotes are stripped)
    - Empty lines (ignored)
    
    Args:
        path: Path to the .env file
        
    Returns:
        Dictionary of key-value pairs
    """
    result: Dict[str, str] = {}
    
    if not path.is_file():
        return result
    
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue
        
        # Parse KEY=VALUE
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            result[key] = value
    
    return result
