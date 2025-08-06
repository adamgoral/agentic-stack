"""Task domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Task:
    """Domain entity representing a task to be executed by an agent."""

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    agent_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    parent_task_id: Optional[UUID] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate task after initialization."""
        if not self.title:
            raise ValueError("Task title is required")

    def start(self) -> None:
        """Mark task as started."""
        if self.status != TaskStatus.PENDING:
            raise ValueError(f"Cannot start task in {self.status} status")
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()

    def complete(self, output: Optional[Dict[str, Any]] = None) -> None:
        """Mark task as completed."""
        if self.status != TaskStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete task in {self.status} status")
        self.status = TaskStatus.COMPLETED
        if output:
            self.output_data = output
        self.completed_at = datetime.utcnow()

    def fail(self, error: str) -> None:
        """Mark task as failed."""
        if self.status not in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS):
            raise ValueError(f"Cannot fail task in {self.status} status")
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()

    def cancel(self) -> None:
        """Cancel the task."""
        if self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            raise ValueError(f"Cannot cancel task in {self.status} status")
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.utcnow()

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate task duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_finished(self) -> bool:
        """Check if task is in a terminal state."""
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        )