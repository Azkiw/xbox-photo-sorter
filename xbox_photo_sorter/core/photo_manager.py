"""
Photo manager - Handles loading, caching, and navigating photos.
"""

import logging
from pathlib import Path
from typing import Optional, List
from PIL import Image
import threading

logger = logging.getLogger(__name__)

# Supported image extensions
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"}


class PhotoManager:
    """Manages photo loading, caching, and navigation."""

    def __init__(self, preload_distance: int = 3):
        """Initialize photo manager."""
        self.preload_distance = preload_distance
        self.photos: List[Path] = []
        self.current_index = 0
        self._cache: dict = {}  # Simple in-memory cache
        self._loading_thread: Optional[threading.Thread] = None
        self._loading = False

    def load_folder(self, folder_path: str) -> bool:
        """Load all photos from a folder."""
        try:
            folder = Path(folder_path)
            if not folder.is_dir():
                logger.error(f"Invalid folder path: {folder_path}")
                return False

            # Scan for supported image files
            photos = []
            for ext in SUPPORTED_EXTENSIONS:
                photos.extend(folder.glob(f"*{ext}"))
                photos.extend(folder.glob(f"*{ext.upper()}"))

            # Sort by filename
            self.photos = sorted(set(photos))

            if not self.photos:
                logger.warning(f"No photos found in {folder_path}")
                return False

            self.current_index = 0
            logger.info(f"Loaded {len(self.photos)} photos from {folder_path}")

            # Start preloading nearby images
            self._start_preloading()

            return True

        except Exception as e:
            logger.error(f"Error loading folder: {e}", exc_info=True)
            return False

    def get_current_photo(self) -> Optional[Path]:
        """Get current photo path."""
        if 0 <= self.current_index < len(self.photos):
            return self.photos[self.current_index]
        return None

    def get_current_image(self) -> Optional[Image.Image]:
        """Get current photo as PIL Image."""
        photo_path = self.get_current_photo()
        if photo_path:
            return self._load_image(photo_path)
        return None

    def next_photo(self) -> bool:
        """Move to next photo."""
        if self.current_index < len(self.photos) - 1:
            self.current_index += 1
            self._start_preloading()
            return True
        return False

    def previous_photo(self) -> bool:
        """Move to previous photo."""
        if self.current_index > 0:
            self.current_index -= 1
            self._start_preloading()
            return True
        return False

    def goto_photo(self, index: int) -> bool:
        """Go to specific photo index."""
        if 0 <= index < len(self.photos):
            self.current_index = index
            self._start_preloading()
            return True
        return False

    def _load_image(self, photo_path: Path) -> Optional[Image.Image]:
        """Load image from file with caching."""
        try:
            # Check cache first
            if str(photo_path) in self._cache:
                return self._cache[str(photo_path)]

            # Load image
            image = Image.open(photo_path)
            image.load()  # Force load

            # Cache it
            self._cache[str(photo_path)] = image

            logger.debug(f"Loaded image: {photo_path}")
            return image

        except Exception as e:
            logger.error(f"Error loading image {photo_path}: {e}")
            return None

    def _start_preloading(self) -> None:
        """Start preloading nearby images."""
        if self._loading:
            return

        self._loading = True
        self._loading_thread = threading.Thread(target=self._preload_images, daemon=True)
        self._loading_thread.start()

    def _preload_images(self) -> None:
        """Preload nearby images in background thread."""
        try:
            start = max(0, self.current_index - self.preload_distance)
            end = min(len(self.photos), self.current_index + self.preload_distance + 1)

            for i in range(start, end):
                if i < len(self.photos):
                    photo_path = self.photos[i]
                    # Only preload if not already cached
                    if str(photo_path) not in self._cache:
                        self._load_image(photo_path)

        except Exception as e:
            logger.error(f"Error preloading images: {e}")
        finally:
            self._loading = False

    def clear_cache(self) -> None:
        """Clear image cache to free memory."""
        self._cache.clear()
        logger.info("Image cache cleared")

    def get_progress(self) -> tuple:
        """Get current progress (current, total)."""
        return (self.current_index + 1, len(self.photos))

    def has_photos(self) -> bool:
        """Check if any photos are loaded."""
        return len(self.photos) > 0

    def get_current_filename(self) -> str:
        """Get current photo filename."""
        photo = self.get_current_photo()
        return photo.name if photo else ""