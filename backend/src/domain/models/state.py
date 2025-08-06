"""
State models for managing conversation and task state across agents
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ConversationState(BaseModel):
    """
    Shared state across all agents for a conversation
    """

    context_id: str = Field(description="Unique identifier for the conversation context")
    user_preferences: Dict[str, Any] = Field(
        default_factory=dict, description="User preferences and settings"
    )
    current_task: Optional[str] = Field(None, description="Current task being processed")
    task_history: List[Dict[str, Any]] = Field(
        default_factory=list, description="History of all tasks in this conversation"
    )
    agent_outputs: Dict[str, Any] = Field(
        default_factory=dict, description="Outputs from different agents"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the conversation started"
    )
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")

    def update_task(self, task: str):
        """Update the current task and timestamp"""
        self.current_task = task
        self.updated_at = datetime.utcnow()

    def add_to_history(self, task_data: Dict[str, Any]):
        """Add a completed task to history"""
        self.task_history.append({**task_data, "timestamp": datetime.utcnow().isoformat()})
        self.updated_at = datetime.utcnow()

    def store_agent_output(self, agent_name: str, output: Any):
        """Store output from a specific agent"""
        self.agent_outputs[agent_name] = output
        self.updated_at = datetime.utcnow()


class AgentTaskState(BaseModel):
    """
    Individual agent task state
    """

    task_id: str = Field(description="Unique task identifier")
    agent_name: str = Field(description="Name of the agent executing the task")
    status: str = Field(
        "pending", description="Task status: pending, in_progress, completed, failed"
    )
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for the task")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Output data from the task")
    error: Optional[str] = Field(None, description="Error message if task failed")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the task was created"
    )
    started_at: Optional[datetime] = Field(None, description="When the task started executing")
    completed_at: Optional[datetime] = Field(None, description="When the task completed")

    def start(self):
        """Mark task as started"""
        self.status = "in_progress"
        self.started_at = datetime.utcnow()

    def complete(self, output: Dict[str, Any]):
        """Mark task as completed with output"""
        self.status = "completed"
        self.output_data = output
        self.completed_at = datetime.utcnow()

    def fail(self, error: str):
        """Mark task as failed with error"""
        self.status = "failed"
        self.error = error
        self.completed_at = datetime.utcnow()

    @property
    def duration(self) -> Optional[float]:
        """Calculate task duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class AgentMessage(BaseModel):
    """
    Message format for agent communication
    """

    message_id: str = Field(description="Unique message identifier")
    from_agent: str = Field(description="Sender agent name")
    to_agent: str = Field(description="Recipient agent name")
    message_type: str = Field(description="Type of message: request, response, notification, error")
    content: Dict[str, Any] = Field(default_factory=dict, description="Message content")
    context_id: Optional[str] = Field(None, description="Associated conversation context")
    correlation_id: Optional[str] = Field(
        None, description="ID to correlate request/response pairs"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")


class ToolCall(BaseModel):
    """
    Represents a tool call via MCP
    """

    tool_name: str = Field(description="Name of the tool")
    server_name: str = Field(description="MCP server providing the tool")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Arguments for the tool call"
    )
    result: Optional[Any] = Field(None, description="Result from the tool call")
    error: Optional[str] = Field(None, description="Error if tool call failed")
    duration_ms: Optional[float] = Field(None, description="Execution time in milliseconds")


class SystemMetrics(BaseModel):
    """
    System-wide metrics and statistics
    """

    total_conversations: int = Field(0, description="Total number of conversations")
    active_conversations: int = Field(0, description="Currently active conversations")
    total_tasks: int = Field(0, description="Total tasks processed")
    completed_tasks: int = Field(0, description="Successfully completed tasks")
    failed_tasks: int = Field(0, description="Failed tasks")
    average_task_duration: float = Field(0.0, description="Average task duration in seconds")
    connected_agents: List[str] = Field(
        default_factory=list, description="List of connected agents"
    )
    mcp_servers: Dict[str, bool] = Field(default_factory=dict, description="MCP server status")
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="Last metrics update"
    )