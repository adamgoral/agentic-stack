"""
AG-UI Protocol Handler
Manages the agent-to-UI communication protocol
"""

import json
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI

logger = logging.getLogger(__name__)


def setup_ag_ui_routes(app: FastAPI) -> None:
    """
    Setup AG-UI routes on the FastAPI application
    This is currently a placeholder as the actual routes are defined in main.py
    """
    logger.info("AG-UI routes setup complete")


class AGUIHandler:
    """
    Handler for AG-UI protocol messages
    Formats and validates messages between agents and the UI
    """

    @staticmethod
    def format_message(
        type: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format a message for AG-UI protocol
        
        Args:
            type: Message type (e.g., 'text', 'state_update', 'error')
            content: Message content
            metadata: Optional metadata
            
        Returns:
            JSON formatted message string
        """
        message = {
            "type": type,
            "content": content,
            "metadata": metadata or {}
        }
        return json.dumps(message)

    @staticmethod
    def format_state_update(
        state: str,
        progress: Optional[float] = None,
        details: Optional[str] = None
    ) -> str:
        """
        Format a state update message
        
        Args:
            state: Current state (e.g., 'thinking', 'executing', 'complete')
            progress: Optional progress percentage (0-100)
            details: Optional details about the current state
            
        Returns:
            JSON formatted state update message
        """
        content = {
            "state": state,
            "progress": progress,
            "details": details
        }
        return AGUIHandler.format_message("state_update", content)

    @staticmethod
    def format_result(
        result: Any,
        success: bool = True,
        error: Optional[str] = None
    ) -> str:
        """
        Format a result message
        
        Args:
            result: The result data
            success: Whether the operation was successful
            error: Optional error message if not successful
            
        Returns:
            JSON formatted result message
        """
        content = {
            "result": result,
            "success": success,
            "error": error
        }
        return AGUIHandler.format_message("result", content)

    @staticmethod
    def format_visualization(
        visualization_type: str,
        data: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format a visualization message
        
        Args:
            visualization_type: Type of visualization (e.g., 'graph', 'chart', 'table')
            data: Visualization data
            options: Optional visualization options
            
        Returns:
            JSON formatted visualization message
        """
        content = {
            "visualization_type": visualization_type,
            "data": data,
            "options": options or {}
        }
        return AGUIHandler.format_message("visualization", content)