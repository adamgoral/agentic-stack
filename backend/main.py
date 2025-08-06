"""
Main application entry point - Compatibility layer
This file is kept for backward compatibility with existing scripts and Docker setup
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import from new structure
from src.main import app, settings

# Re-export for compatibility
__all__ = ["app", "settings"]

if __name__ == "__main__":
    import uvicorn
    
    # Run the application using settings from new structure
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )