"""
Xbox Controller input handling.
Manages Xbox controller detection and input events.
"""

import logging
import threading
from typing import Optional, Callable, Dict, Any
from enum import Enum

try:
    import inputs
except ImportError:
    inputs = None

logger = logging.getLogger(__name__)


class ButtonEvent(Enum):
    """Button event types."""
    PRESSED = "pressed"
    RELEASED = "released"


class XboxController:
    """Xbox controller input manager."""

    def __init__(self):
        """Initialize Xbox controller."""
        self.controller = None
        self.is_connected = False
        self.is_listening = False
        self._listener_thread: Optional[threading.Thread] = None
        self._callbacks: Dict[str, Callable] = {}
        self._axis_states: Dict[str, float] = {
            "LEFT_STICK_X": 0.0,
            "LEFT_STICK_Y": 0.0,
            "RIGHT_STICK_X": 0.0,
            "RIGHT_STICK_Y": 0.0,
            "LEFT_TRIGGER": 0.0,
            "RIGHT_TRIGGER": 0.0,
        }
        self._deadzone = 0.2
        self._button_states: Dict[str, bool] = {}

    def initialize(self) -> bool:
        """Initialize and detect Xbox controller."""
        if inputs is None:
            logger.error("inputs library not available")
            return False

        try:
            # Try to find gamepad
            gamepads = inputs.get_gamepad()
            if gamepads:
                self.controller = gamepads[0]
                self.is_connected = True
                logger.info(f"Xbox controller detected: {self.controller}")
                return True
            else:
                logger.warning("No gamepad found")
                return False
        except Exception as e:
            logger.error(f"Failed to initialize controller: {e}", exc_info=True)
            return False

    def start_listening(self) -> None:
        """Start listening for controller input."""
        if self.is_listening:
            logger.warning("Already listening for input")
            return

        if not self.is_connected:
            if not self.initialize():
                logger.error("Controller not connected")
                return

        self.is_listening = True
        self._listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listener_thread.start()
        logger.info("Started listening for controller input")

    def stop_listening(self) -> None:
        """Stop listening for controller input."""
        self.is_listening = False
        if self._listener_thread:
            self._listener_thread.join(timeout=1.0)
        logger.info("Stopped listening for controller input")

    def _listen_loop(self) -> None:
        """Main loop for listening to controller events."""
        if inputs is None:
            return

        try:
            while self.is_listening:
                try:
                    events = inputs.get_gamepad()
                    for event in events:
                        self._process_event(event)
                except inputs.UnpluggedError:
                    logger.warning("Controller unplugged")
                    self.is_connected = False
                    self.is_listening = False
                    self._trigger_callback("controller_disconnected", {})
                    break
                except Exception as e:
                    logger.error(f"Error reading controller: {e}")
                    break
        except Exception as e:
            logger.error(f"Listener loop error: {e}", exc_info=True)

    def _process_event(self, event) -> None:
        """Process a controller event."""
        try:
            # Map event to button/axis name
            event_code = event.ev_code
            state = event.state

            # Handle analog sticks and triggers
            if event_code == "ABS_X":
                self._handle_axis("LEFT_STICK_X", state)
            elif event_code == "ABS_Y":
                self._handle_axis("LEFT_STICK_Y", state)
            elif event_code == "ABS_RX":
                self._handle_axis("RIGHT_STICK_X", state)
            elif event_code == "ABS_RY":
                self._handle_axis("RIGHT_STICK_Y", state)
            elif event_code == "ABS_Z":
                self._handle_axis("LEFT_TRIGGER", state)
            elif event_code == "ABS_RZ":
                self._handle_axis("RIGHT_TRIGGER", state)

            # Handle buttons
            elif event_code == "BTN_SOUTH":  # A
                self._handle_button("A", state)
            elif event_code == "BTN_EAST":  # B
                self._handle_button("B", state)
            elif event_code == "BTN_NORTH":  # Y
                self._handle_button("Y", state)
            elif event_code == "BTN_WEST":  # X
                self._handle_button("X", state)
            elif event_code == "BTN_TL":  # LB
                self._handle_button("LB", state)
            elif event_code == "BTN_TR":  # RB
                self._handle_button("RB", state)
            elif event_code == "ABS_HAT0X":  # D-Pad left/right
                self._handle_dpad_x(state)
            elif event_code == "ABS_HAT0Y":  # D-Pad up/down
                self._handle_dpad_y(state)
            elif event_code == "BTN_SELECT":  # View/Select
                self._handle_button("VIEW", state)
            elif event_code == "BTN_START":  # Menu
                self._handle_button("MENU", state)
            elif event_code == "BTN_THUMBL":  # Left stick click
                self._handle_button("LEFT_STICK_CLICK", state)
            elif event_code == "BTN_THUMBR":  # Right stick click
                self._handle_button("RIGHT_STICK_CLICK", state)

        except Exception as e:
            logger.error(f"Error processing event: {e}")

    def _handle_axis(self, axis: str, state: int) -> None:
        """Handle analog axis input."""
        # Normalize to -1.0 to 1.0
        normalized = state / 32768.0
        
        # Apply deadzone
        if abs(normalized) < self._deadzone:
            normalized = 0.0
        
        old_state = self._axis_states.get(axis, 0.0)
        self._axis_states[axis] = normalized

        # Trigger callback if significant change
        if abs(normalized - old_state) > 0.1:
            self._trigger_callback("axis_motion", {
                "axis": axis,
                "value": normalized
            })

    def _handle_button(self, button: str, state: int) -> None:
        """Handle button press/release."""
        is_pressed = state == 1
        old_state = self._button_states.get(button, False)

        if is_pressed != old_state:
            self._button_states[button] = is_pressed
            event_type = ButtonEvent.PRESSED if is_pressed else ButtonEvent.RELEASED
            self._trigger_callback("button", {
                "button": button,
                "event": event_type.value
            })

    def _handle_dpad_x(self, state: int) -> None:
        """Handle D-Pad left/right."""
        if state == -1:
            self._trigger_callback("button", {
                "button": "DPAD_LEFT",
                "event": ButtonEvent.PRESSED.value
            })
        elif state == 1:
            self._trigger_callback("button", {
                "button": "DPAD_RIGHT",
                "event": ButtonEvent.PRESSED.value
            })
        else:
            # Release both
            self._trigger_callback("button", {
                "button": "DPAD_LEFT",
                "event": ButtonEvent.RELEASED.value
            })
            self._trigger_callback("button", {
                "button": "DPAD_RIGHT",
                "event": ButtonEvent.RELEASED.value
            })

    def _handle_dpad_y(self, state: int) -> None:
        """Handle D-Pad up/down."""
        if state == -1:
            self._trigger_callback("button", {
                "button": "DPAD_UP",
                "event": ButtonEvent.PRESSED.value
            })
        elif state == 1:
            self._trigger_callback("button", {
                "button": "DPAD_DOWN",
                "event": ButtonEvent.PRESSED.value
            })
        else:
            # Release both
            self._trigger_callback("button", {
                "button": "DPAD_UP",
                "event": ButtonEvent.RELEASED.value
            })
            self._trigger_callback("button", {
                "button": "DPAD_DOWN",
                "event": ButtonEvent.RELEASED.value
            })

    def register_callback(self, event_type: str, callback: Callable) -> None:
        """Register a callback for an event type."""
        self._callbacks[event_type] = callback

    def _trigger_callback(self, event_type: str, data: Dict[str, Any]) -> None:
        """Trigger a registered callback."""
        if event_type in self._callbacks:
            try:
                self._callbacks[event_type](data)
            except Exception as e:
                logger.error(f"Error in callback: {e}")

    def set_deadzone(self, deadzone: float) -> None:
        """Set analog stick deadzone."""
        self._deadzone = max(0.0, min(1.0, deadzone))

    def get_axis_state(self, axis: str) -> float:
        """Get current axis state."""
        return self._axis_states.get(axis, 0.0)

    def get_button_state(self, button: str) -> bool:
        """Get current button state."""
        return self._button_states.get(button, False)