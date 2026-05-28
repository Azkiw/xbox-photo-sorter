"""
Session history tracking.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class HistoryEntry:
    """Represents a history entry."""

    def __init__(
        self,
        action_type: str,
        source_file: str,
        destination_folder: str,
        timestamp: datetime,
    ):
        """Initialize history entry."""
        self.action_type = action_type
        self.source_file = source_file
        self.destination_folder = destination_folder
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action_type": self.action_type,
            "source_file": self.source_file,
            "destination_folder": self.destination_folder,
            "timestamp": self.timestamp.isoformat(),
        }


class History:
    """Session history tracker."""

    def __init__(self, max_entries: int = 10000):
        """Initialize history tracker."""
        self.max_entries = max_entries
        self.entries: List[HistoryEntry] = []

    def add_entry(
        self,
        action_type: str,
        source_file: str,
        destination_folder: str,
    ) -> None:
        """Add a history entry."""
        entry = HistoryEntry(
            action_type=action_type,
            source_file=source_file,
            destination_folder=destination_folder,
            timestamp=datetime.now(),
        )
        self.entries.append(entry)

        # Limit history size
        if len(self.entries) > self.max_entries:
            self.entries.pop(0)

        logger.debug(f"History entry added: {action_type} - {source_file}")

    def get_entries(self) -> List[HistoryEntry]:
        """Get all history entries."""
        return self.entries

    def get_recent(self, count: int = 10) -> List[HistoryEntry]:
        """Get recent history entries."""
        return self.entries[-count:]

    def clear(self) -> None:
        """Clear all history."""
        self.entries.clear()
        logger.info("History cleared")

    def save_to_file(self, file_path: str) -> bool:
        """Save history to JSON file."""
        try:
            data = {
                "entries": [entry.to_dict() for entry in self.entries],
                "total": len(self.entries),
                "saved_at": datetime.now().isoformat(),
            }
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"History saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
            return False

    def load_from_file(self, file_path: str) -> bool:
        """Load history from JSON file."""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            self.entries.clear()
            for entry_data in data.get("entries", []):
                entry = HistoryEntry(
                    action_type=entry_data["action_type"],
                    source_file=entry_data["source_file"],
                    destination_folder=entry_data["destination_folder"],
                    timestamp=datetime.fromisoformat(entry_data["timestamp"]),
                )
                self.entries.append(entry)

            logger.info(f"History loaded from {file_path}: {len(self.entries)} entries")
            return True
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return False