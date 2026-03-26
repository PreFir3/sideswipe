"""
Advanced Screen Control Module
Provides high-level screen interaction based on hand gestures
"""

import time
from typing import Optional, Callable
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key
import threading


class ScreenControlAgent:
    """
    Advanced screen control agent for gesture-based interaction.
    
    Provides:
    - Cursor movement and clicking
    - Scroll control
    - Keyboard shortcuts
    - Multi-gesture combinations
    - Gesture-to-action mapping
    """
    
    def __init__(self, screen_width: int = 1920, screen_height: int = 1080):
        """Initialize screen control agent."""
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Click debouncing
        self.last_click_time = 0
        self.click_cooldown = 0.2  # seconds
        
        # Scroll tracking
        self.last_scroll_time = 0
        self.scroll_cooldown = 0.1  # seconds
        self.scroll_accumulated = 0
        
        # Gesture tracking
        self.last_gesture_time = {}
        self.gesture_cooldowns = {
            'swipe': 0.5,
            'pinch': 0.3,
            'point': 0.0
        }
        
        print("✓ Screen control initialized")
    
    def move_cursor(self, normalized_x: float, normalized_y: float) -> bool:
        """
        Move cursor to position (normalized 0-1 coordinates).
        
        Args:
            normalized_x: X position (0-1, 0 is left, 1 is right)
            normalized_y: Y position (0-1, 0 is top, 1 is bottom)
            
        Returns:
            True if successful
        """
        try:
            # Convert to screen coordinates
            screen_x = int((1.0 - normalized_x) * self.screen_width)  # Flip X
            screen_y = int(normalized_y * self.screen_height)
            
            # Clamp to screen bounds
            screen_x = max(0, min(self.screen_width - 1, screen_x))
            screen_y = max(0, min(self.screen_height - 1, screen_y))
            
            self.mouse.position = (screen_x, screen_y)
            return True
        except Exception as e:
            print(f"Error moving cursor: {e}")
            return False
    
    def click(self, button: Button = Button.left) -> bool:
        """
        Perform mouse click with debouncing.
        
        Args:
            button: Which button to click (left, right, middle)
            
        Returns:
            True if click was performed
        """
        current_time = time.time()
        if current_time - self.last_click_time < self.click_cooldown:
            return False
        
        try:
            self.mouse.click(button, 1)
            self.last_click_time = current_time
            return True
        except Exception as e:
            print(f"Error clicking: {e}")
            return False
    
    def double_click(self) -> bool:
        """Perform double click."""
        try:
            self.mouse.click(Button.left, 2)
            return True
        except Exception as e:
            print(f"Error double clicking: {e}")
            return False
    
    def scroll(self, direction: str, amount: int = 5) -> bool:
        """
        Scroll in direction.
        
        Args:
            direction: 'up' or 'down'
            amount: Scroll amount
            
        Returns:
            True if scroll was performed
        """
        current_time = time.time()
        if current_time - self.last_scroll_time < self.scroll_cooldown:
            return False
        
        try:
            scroll_amount = amount if direction == 'up' else -amount
            self.mouse.scroll(0, scroll_amount)
            self.last_scroll_time = current_time
            return True
        except Exception as e:
            print(f"Error scrolling: {e}")
            return False
    
    def keyboard_shortcut(self, *keys) -> bool:
        """
        Perform keyboard shortcut.
        
        Args:
            *keys: Key objects or strings
            
        Returns:
            True if successful
        """
        try:
            with self.keyboard.pressed(*keys):
                pass
            return True
        except Exception as e:
            print(f"Error with keyboard: {e}")
            return False
    
    def tab_switch(self, direction: str = 'right') -> bool:
        """
        Switch browser tabs.
        
        Args:
            direction: 'left' or 'right'
            
        Returns:
            True if successful
        """
        try:
            if direction == 'left':
                self.keyboard_shortcut(Key.cmd, Key.shift, Key.left)
            else:
                self.keyboard_shortcut(Key.cmd, Key.shift, Key.right)
            return True
        except Exception as e:
            print(f"Error switching tabs: {e}")
            return False
    
    def drag(self, start_x: float, start_y: float, 
             end_x: float, end_y: float, duration: float = 0.5) -> bool:
        """
        Perform click and drag operation.
        
        Args:
            start_x, start_y: Starting position (normalized)
            end_x, end_y: Ending position (normalized)
            duration: Time to complete drag
            
        Returns:
            True if successful
        """
        try:
            # Move to start
            self.move_cursor(start_x, start_y)
            time.sleep(0.1)
            
            # Drag to end
            screen_start_x = int((1.0 - start_x) * self.screen_width)
            screen_start_y = int(start_y * self.screen_height)
            screen_end_x = int((1.0 - end_x) * self.screen_width)
            screen_end_y = int(end_y * self.screen_height)
            
            self.mouse.position = (screen_start_x, screen_start_y)
            self.mouse.press(Button.left)
            
            # Linear interpolation for smooth drag
            steps = int(duration * 30)  # 30 fps
            for i in range(steps):
                progress = i / steps
                x = screen_start_x + (screen_end_x - screen_start_x) * progress
                y = screen_start_y + (screen_end_y - screen_start_y) * progress
                self.mouse.position = (int(x), int(y))
                time.sleep(duration / steps)
            
            self.mouse.position = (screen_end_x, screen_end_y)
            self.mouse.release(Button.left)
            
            return True
        except Exception as e:
            print(f"Error dragging: {e}")
            return False
    
    def gesture_available(self, gesture_name: str) -> bool:
        """
        Check if a gesture is available (not on cooldown).
        
        Args:
            gesture_name: Name of gesture
            
        Returns:
            True if gesture can be performed
        """
        if gesture_name not in self.gesture_cooldowns:
            return True
        
        current_time = time.time()
        last_time = self.last_gesture_time.get(gesture_name, 0)
        cooldown = self.gesture_cooldowns[gesture_name]
        
        return current_time - last_time >= cooldown
    
    def register_gesture(self, gesture_name: str) -> bool:
        """Register that a gesture was performed."""
        if gesture_name in self.gesture_cooldowns:
            self.last_gesture_time[gesture_name] = time.time()
        return True
    
    def get_cursor_position(self) -> tuple:
        """Get current cursor position in pixels."""
        return self.mouse.position
    
    def reset_position(self) -> bool:
        """Reset cursor to center of screen."""
        try:
            center_x = self.screen_width // 2
            center_y = self.screen_height // 2
            self.mouse.position = (center_x, center_y)
            return True
        except Exception as e:
            print(f"Error resetting position: {e}")
            return False


class GestureActionMapper:
    """Maps hand gestures to screen actions."""
    
    def __init__(self, controller: ScreenControlAgent):
        """Initialize gesture mapper."""
        self.controller = controller
        self.action_map = {}
        self._setup_default_mappings()
    
    def _setup_default_mappings(self):
        """Setup default gesture-to-action mappings."""
        self.action_map = {
            'point': self._action_cursor_follow,
            'pinch': self._action_click,
            'pinch_drag': self._action_drag,
            'swipe_left': self._action_tab_left,
            'swipe_right': self._action_tab_right,
            'scroll_up': self._action_scroll_up,
            'scroll_down': self._action_scroll_down,
        }
    
    def _action_cursor_follow(self, hand_pos: tuple):
        """Action: Follow cursor."""
        if hand_pos:
            self.controller.move_cursor(hand_pos[0], hand_pos[1])
    
    def _action_click(self):
        """Action: Click."""
        if self.controller.gesture_available('pinch'):
            self.controller.click()
            self.controller.register_gesture('pinch')
    
    def _action_drag(self, start_pos: tuple, end_pos: tuple):
        """Action: Drag."""
        if start_pos and end_pos:
            self.controller.drag(start_pos[0], start_pos[1], 
                               end_pos[0], end_pos[1])
    
    def _action_tab_left(self):
        """Action: Switch tab left."""
        if self.controller.gesture_available('swipe'):
            self.controller.tab_switch('left')
            self.controller.register_gesture('swipe')
    
    def _action_tab_right(self):
        """Action: Switch tab right."""
        if self.controller.gesture_available('swipe'):
            self.controller.tab_switch('right')
            self.controller.register_gesture('swipe')
    
    def _action_scroll_up(self):
        """Action: Scroll up."""
        self.controller.scroll('up', 5)
    
    def _action_scroll_down(self):
        """Action: Scroll down."""
        self.controller.scroll('down', 5)
    
    def execute_action(self, action_name: str, *args, **kwargs):
        """
        Execute an action by name.
        
        Args:
            action_name: Name of action
            *args, **kwargs: Arguments to action
        """
        if action_name in self.action_map:
            action = self.action_map[action_name]
            if args or kwargs:
                action(*args, **kwargs)
            else:
                action()
    
    def register_custom_action(self, name: str, callback: Callable):
        """Register a custom action."""
        self.action_map[name] = callback
