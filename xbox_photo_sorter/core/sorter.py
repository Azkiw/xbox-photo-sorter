"""
Photo sorting engine - Handles moving/copying photos to categories.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from xbox_photo_sorter.core.undo_manager import UndoManager
from xbox_photo_sorter.core.history import History
from xbox_photo_sorter.config.settings import Category

logger = logging.getLogger(__name__)


class Sorter:
    """Handles photo sorting and file operations."""

    def __init__(self, undo_manager: UndoManager, history: History):
        """Initialize sorter."""
        self.undo_manager = undo_manager
        self.history = history
        self.source_folder: Optional[Path] = None

    def set_source_folder(self, folder_path: str) -> bool:
        """Set the source photo folder."""
        try:
            self.source_folder = Path(folder_path)
            if not self.source_folder.is_dir():
                logger.error(f"Invalid source folder: {folder_path}")
                return False
            logger.info(f"Source folder set to: {folder_path}")
            return True
        except Exception as e:
            logger.error(f"Error setting source folder: {e}")
            return False

    def sort_photo(
        self,
        photo_path: Path,
        category: Category,
        operation: str = "copy",
    ) -> bool:
        """Sort a photo to a category.
        
        Args:
            photo_path: Path to the photo
            category: Destination category
            operation: "copy" or "move"
        """
        if not self.source_folder:
            logger.error("Source folder not set")
            return False

        try:
            # Create destination folder if it doesn't exist
            dest_folder = self.source_folder / category.folder
            dest_folder.mkdir(exist_ok=True)

            # Determine destination path
            dest_path = dest_folder / photo_path.name

            # Handle file conflicts
            if dest_path.exists():
                dest_path = self._get_unique_path(dest_path)

            # Perform file operation
            if operation == "move":
                shutil.move(str(photo_path), str(dest_path))
                logger.info(f"Moved {photo_path.name} to {category.folder}")
            else:  # copy
                shutil.copy2(str(photo_path), str(dest_path))
                logger.info(f"Copied {photo_path.name} to {category.folder}")

            # Record in history
            self.history.add_entry(
                action_type=f"{operation.upper()} to {category.name}",
                source_file=photo_path.name,
                destination_folder=category.folder,
            )

            # Record undo action
            def undo_sort(data: Dict[str, Any]):
                """Undo the sort operation."""
                undo_path = Path(data["destination_path"])
                original_path = Path(data["original_path"])

                if undo_path.exists():
                    if operation == "move":
                        shutil.move(str(undo_path), str(original_path))
                    else:  # copy
                        undo_path.unlink()
                    logger.info(f"Undone sort: {undo_path.name}")

            self.undo_manager.record_action(
                "sort_photo",
                {
                    "destination_path": str(dest_path),
                    "original_path": str(photo_path),
                    "category": category.name,
                },
                undo_sort,
            )

            return True

        except Exception as e:
            logger.error(f"Error sorting photo: {e}", exc_info=True)
            return False

    def _get_unique_path(self, path: Path) -> Path:
        """Get unique filename to avoid overwriting."""
        if not path.exists():
            return path

        stem = path.stem
        suffix = path.suffix
        parent = path.parent

        counter = 1
        while True:
            new_name = f"{stem}_({counter}){suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1

    def create_category_folders(self, categories: list) -> bool:
        """Create destination folders for all categories."""
        if not self.source_folder:
            logger.error("Source folder not set")
            return False

        try:
            for category in categories:
                folder = self.source_folder / category.folder
                folder.mkdir(exist_ok=True)
                logger.debug(f"Created/verified folder: {folder}")
            return True
        except Exception as e:
            logger.error(f"Error creating folders: {e}")
            return False

    def get_folder_stats(self, categories: list) -> Dict[str, int]:
        """Get file counts for each category folder."""
        stats = {}
        if not self.source_folder:
            return stats

        try:
            for category in categories:
                folder = self.source_folder / category.folder
                if folder.exists():
                    file_count = len(list(folder.glob("*.*")))
                    stats[category.name] = file_count
            return stats
        except Exception as e:
            logger.error(f"Error getting folder stats: {e}")
            return stats