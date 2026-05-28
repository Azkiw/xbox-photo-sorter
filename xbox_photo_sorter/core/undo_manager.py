"""
Undo/Redo management system.
"""

import logging
from typing import List, Optional, Callable, Any, Dict

logger = logging.getLogger(__name__)


class UndoAction:
    """Represents an undoable action."""

    def __init__(self, action_type: str, data: Dict[str, Any], undo_fn: Callable):
        """Initialize undo action."""
        self.action_type = action_type
        self.data = data
        self.undo_fn = undo_fn

    def undo(self) -> bool:
        """Execute undo operation."""
        try:
            self.undo_fn(self.data)
            return True
        except Exception as e:
            logger.error(f"Error undoing action: {e}", exc_info=True)
            return False


class UndoManager:
    """Manages undo/redo stack."""

    def __init__(self, max_history: int = 1000):
        """Initialize undo manager."""
        self.max_history = max_history
        self.undo_stack: List[UndoAction] = []
        self.redo_stack: List[UndoAction] = []

    def record_action(self, action_type: str, data: Dict[str, Any], undo_fn: Callable) -> None:
        """Record an action for undo."""
        action = UndoAction(action_type, data, undo_fn)
        self.undo_stack.append(action)

        # Clear redo stack when new action is recorded
        self.redo_stack.clear()

        # Limit history size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

        logger.debug(f"Recorded action: {action_type}")

    def undo(self) -> bool:
        """Undo last action."""
        if not self.undo_stack:
            logger.debug("Nothing to undo")
            return False

        action = self.undo_stack.pop()
        if action.undo():
            self.redo_stack.append(action)
            logger.info(f"Undone action: {action.action_type}")
            return True

        return False

    def redo(self) -> bool:
        """Redo last undone action."""
        if not self.redo_stack:
            logger.debug("Nothing to redo")
            return False

        action = self.redo_stack.pop()
        # Note: Redo would need to re-execute the action
        # For now, we don't implement full redo
        logger.info(f"Redo not implemented for: {action.action_type}")
        return False

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.redo_stack) > 0

    def get_undo_count(self) -> int:
        """Get number of actions in undo stack."""
        return len(self.undo_stack)

    def clear(self) -> None:
        """Clear all undo/redo history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        logger.info("Undo history cleared")

    def get_history(self) -> List[str]:
        """Get list of action descriptions."""
        return [f"{i+1}. {action.action_type}" for i, action in enumerate(self.undo_stack)]