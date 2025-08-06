"""Task-related domain exceptions."""


class TaskError(Exception):
    """Base exception for task-related errors."""


class TaskNotFoundError(TaskError):
    """Raised when a task is not found."""

    def __init__(self, task_id: str) -> None:
        super().__init__(f"Task with ID {task_id} not found")
        self.task_id = task_id


class InvalidTaskStateError(TaskError):
    """Raised when a task operation is invalid for its current state."""

    def __init__(self, task_id: str, current_state: str, operation: str) -> None:
        super().__init__(
            f"Cannot perform {operation} on task {task_id} in state {current_state}"
        )
        self.task_id = task_id
        self.current_state = current_state
        self.operation = operation


class TaskExecutionError(TaskError):
    """Raised when a task execution fails."""

    def __init__(self, task_id: str, reason: str) -> None:
        super().__init__(f"Task {task_id} execution failed: {reason}")
        self.task_id = task_id
        self.reason = reason