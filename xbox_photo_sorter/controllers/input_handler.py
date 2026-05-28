"""
Input handler - Maps controller input to application actions.
"""

import logging
from typing import Optional, Callable, Dict, Any
from xbox_photo_sorter.controllers.xbox_controller import XboxController
from xbox_photo_sorter.config.settings import Settings

logger = logging.getLogger(__name__)


class InputHandler:
    """Handles mapping controller input to application actions."""

    def __init__(self, settings: Settings):
        """Initialize input handler."""
        self.settings = settings
        self.controller = XboxController()
        self._action_callbacks: Dict[str, Callable] = {}
        self._stick_move_timer = 0
        self._stick_move_delay = 0.2  # Delay before triggering repeat moves

    def initialize(self) -> bool:
        """Initialize controller and register callbacks."""
        if not self.controller.initialize():
            logger.warning("Failed to initialize controller")
            return False

        # Set deadzone from settings
        self.controller.set_deadzone(self.settings.controller_deadzone)

        # Register input callbacks
        self.controller.register_callback("button", self._on_button_event)
        self.controller.register_callback("axis_motion", self._on_axis_motion)
        self.controller.register_callback("controller_disconnected", self._on_controller_disconnected)

        return True

    def start(self) -> None:
        """Start listening for input."""
        self.controller.start_listening()

    def stop(self) -> None:
        """Stop listening for input."""
        self.controller.stop_listening()

    def register_action(self, action: str, callback: Callable) -> None:
        """Register callback for an action."""
        self._action_callbacks[action] = callback
        logger.debug(f"Registered action: {action}")

    def _on_button_event(self, data: Dict[str, Any]) -> None:
        """Handle button press/release events."""
        button = data.get("button")
        event = data.get("event")

        if event != "pressed":
            return

        # Map button to action
        mapping = self.settings.controller_mapping

        action = None
        if button == mapping.navigate_prev or button == mapping.navigate_prev_alt:
            action = "navigate_previous"
        elif button == mapping.navigate_next or button == mapping.navigate_next_alt:
            action = "navigate_next"
        elif button == mapping.undo:
            action = "undo"
        elif button == mapping.settings:
            action = "open_settings"
        elif button == mapping.category_1:
            action = "sort_category_1"
        elif button == mapping.category_2:
            action = "sort_category_2"
        elif button == mapping.category_3:
            action = "sort_category_3"
        elif button == mapping.category_4:
            action = "sort_category_4"
        elif button == mapping.category_5:
            action = "sort_category_5"
        elif button == mapping.category_6:
            action = "sort_category_6"
        elif button == mapping.category_7:
            action = "sort_category_7"
        elif button == mapping.category_8:
            action = "sort_category_8"

        if action:
            self._trigger_action(action, {"button": button})

    def _on_axis_motion(self, data: Dict[str, Any]) -> None:
        """Handle analog stick motion."""
        axis = data.get("axis")
        value = data.get("value", 0.0)

        mapping = self.settings.controller_mapping

        # Handle left stick navigation
        if axis == "LEFT_STICK_X":
            if value < -0.5:
                self._trigger_action("navigate_previous", {"axis": axis, "value": value})
            elif value > 0.5:
                self._trigger_action("navigate_next", {"axis": axis, "value": value})

    def _on_controller_disconnected(self, data: Dict[str, Any]) -> None:
        """Handle controller disconnection."""
        logger.warning("Controller disconnected")
        self._trigger_action("controller_disconnected", data)

    def _trigger_action(self, action: str, data: Dict[str, Any]) -> None:
        """Trigger an action callback."""
        if action in self._action_callbacks:
            try:
                self._action_callbacks[action](data)
            except Exception as e:
                logger.error(f"Error executing action {action}: {e}", exc_info=True)