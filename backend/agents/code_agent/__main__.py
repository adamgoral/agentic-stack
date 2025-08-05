"""
Code Agent main entry point
Allows running with: python -m agents.code_agent
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.run_code_agent import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())