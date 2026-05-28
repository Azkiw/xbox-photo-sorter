"""
Settings and configuration management for Xbox Photo Sorter.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
import os

logger = logging.getLogger(__name__)


@dataclass
class Category:
    """Represents a destination category/folder."""
    name: str
    folder: str
    button: str
    color: str = "#0078D4"


@dataclass
class ControllerMapping:
    """Xbox controller button mappings."""
    navigate_prev: str = "LEFT_STICK_LEFT"
    navigate_next: str = "LEFT_STICK_RIGHT"
    navigate_prev_alt: str = "DPAD_LEFT"
    navigate_next_alt: str = "DPAD_RIGHT"
    undo: str = "VIEW"
    settings: str = "MENU"
    category_1: str = "A"
    category_2: str = "B"
    category_3: str = "X"
    category_4: str = "Y"
    category_5: str = "LB"
    category_6: str = "RB"
    category_7: str = "LT"
    category_8: str = "RT"


@dataclass
class Settings:
    """Application settings."""
    
    # File operations
    file_operation: str = "copy"  # "copy" or "move"
    last_folder: str = ""
    
    # Display
    fullscreen: bool = False
    window_width: int = 1200
    window_height: int = 800
    
    # Performance
    preload_distance: int = 3  # Number of photos to preload
    
    # Controller
    controller_mapping: ControllerMapping = field(default_factory=ControllerMapping)
    controller_deadzone: float = 0.2
    
    # Categories
    categories: List[Category] = field(default_factory=lambda: [
        Category("Selected", "Selected", "A"),
        Category("Rejected", "Rejected", "B"),
        Category("Participants", "Participants", "X"),
        Category("Teachers", "Teachers", "Y"),
    ])
    
    _config_dir: Path = field(default_factory=lambda: Path(os.getenv("APPDATA", Path.home())) / "XboxPhotoSorter")
    _config_file: Path = field(default_factory=lambda: Path(os.getenv("APPDATA", Path.home())) / "XboxPhotoSorter" / "config.json")

    def __post_init__(self):
        """Initialize config directory."""
        self._config_dir = Path(os.getenv("APPDATA", Path.home())) / "XboxPhotoSorter"
        self._config_file = self._config_dir / "config.json"
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Ensure config directory exists."""
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> None:
        """Load settings from config file."""
        try:
            if self._config_file.exists():
                with open(self._config_file, "r") as f:
                    data = json.load(f)
                    self._load_from_dict(data)
                logger.info(f"Loaded settings from {self._config_file}")
            else:
                logger.info("No config file found, using defaults")
        except Exception as e:
            logger.error(f"Failed to load settings: {e}", exc_info=True)

    def save(self) -> None:
        """Save settings to config file."""
        try:
            self._ensure_config_dir()
            data = self._to_dict()
            with open(self._config_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved settings to {self._config_file}")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}", exc_info=True)

    def _load_from_dict(self, data: Dict[str, Any]) -> None:
        """Load settings from dictionary."""
        if "file_operation" in data:
            self.file_operation = data["file_operation"]
        if "last_folder" in data:
            self.last_folder = data["last_folder"]
        if "fullscreen" in data:
            self.fullscreen = data["fullscreen"]
        if "window_width" in data:
            self.window_width = data["window_width"]
        if "window_height" in data:
            self.window_height = data["window_height"]
        if "preload_distance" in data:
            self.preload_distance = data["preload_distance"]
        if "controller_deadzone" in data:
            self.controller_deadzone = data["controller_deadzone"]
        
        # Load controller mapping
        if "controller_mapping" in data:
            mapping_data = data["controller_mapping"]
            self.controller_mapping = ControllerMapping(**mapping_data)
        
        # Load categories
        if "categories" in data:
            self.categories = [
                Category(**cat) for cat in data["categories"]
            ]

    def _to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "file_operation": self.file_operation,
            "last_folder": self.last_folder,
            "fullscreen": self.fullscreen,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "preload_distance": self.preload_distance,
            "controller_deadzone": self.controller_deadzone,
            "controller_mapping": asdict(self.controller_mapping),
            "categories": [asdict(cat) for cat in self.categories],
        }

    def get_category_by_button(self, button: str) -> Optional[Category]:
        """Get category by button name."""
        for cat in self.categories:
            if cat.button == button:
                return cat
        return None

    def add_category(self, category: Category) -> None:
        """Add a new category."""
        # Check if button is already used
        for cat in self.categories:
            if cat.button == category.button:
                logger.warning(f"Button {category.button} already assigned to {cat.name}")
                return
        self.categories.append(category)
        self.save()

    def remove_category(self, button: str) -> None:
        """Remove a category by button."""
        self.categories = [cat for cat in self.categories if cat.button != button]
        self.save()

    def update_category(self, button: str, **kwargs) -> None:
        """Update a category."""
        for i, cat in enumerate(self.categories):
            if cat.button == button:
                # Update fields
                for key, value in kwargs.items():
                    if hasattr(cat, key):
                        setattr(cat, key, value)
                self.save()
                return