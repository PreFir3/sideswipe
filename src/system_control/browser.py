"""
System control module for browser and window management.

Provides keyboard shortcuts for:
- Chrome tab switching and navigation
- Window management
- Scroll control
"""

import subprocess
import time
from typing import Optional
import sys


class SystemController:
    """Controls system actions via keyboard shortcuts."""
    
    def __init__(self):
        """Initialize system controller."""
        self.platform = sys.platform
        self.last_action_time = 0
        self.action_cooldown = 0.1  # Prevent spam
    
    def _can_perform_action(self) -> bool:
        """Check if enough time has passed since last action."""
        current_time = time.time()
        if current_time - self.last_action_time < self.action_cooldown:
            return False
        self.last_action_time = current_time
        return True
    
    def switch_tab_left(self) -> bool:
        """Switch to left tab in browser."""
        if not self._can_perform_action():
            return False
        try:
            # Ctrl+Shift+Tab on Windows/Linux, Cmd+Shift+[ on Mac
            if self.platform == "darwin":
                self._run_applescript('tell application "System Events" to keystroke "[" using {shift down, command down}')
            else:
                subprocess.run(["xdotool", "key", "ctrl+shift+Tab"], check=False)
            return True
        except Exception as e:
            print(f"Error switching left tab: {e}")
            return False
    
    def switch_tab_right(self) -> bool:
        """Switch to right tab in browser."""
        if not self._can_perform_action():
            return False
        try:
            # Ctrl+Tab on Windows/Linux, Cmd+Shift+] on Mac
            if self.platform == "darwin":
                self._run_applescript('tell application "System Events" to keystroke "]" using {shift down, command down}')
            else:
                subprocess.run(["xdotool", "key", "ctrl+Tab"], check=False)
            return True
        except Exception as e:
            print(f"Error switching right tab: {e}")
            return False
    
    def scroll_up(self, amount: int = 3) -> bool:
        """Scroll up."""
        if not self._can_perform_action():
            return False
        try:
            if self.platform == "darwin":
                # Use PyObjC to scroll on macOS
                try:
                    from pynput.mouse import Button, Controller as MouseController
                    mouse = MouseController()
                    # Scroll up
                    mouse.scroll(0, amount)
                except:
                    pass
            return True
        except Exception as e:
            print(f"Error scrolling up: {e}")
            return False
    
    def scroll_down(self, amount: int = 3) -> bool:
        """Scroll down."""
        if not self._can_perform_action():
            return False
        try:
            if self.platform == "darwin":
                try:
                    from pynput.mouse import Controller as MouseController
                    mouse = MouseController()
                    # Scroll down
                    mouse.scroll(0, -amount)
                except:
                    pass
            return True
        except Exception as e:
            print(f"Error scrolling down: {e}")
            return False
    
    def new_tab(self) -> bool:
        """Open new tab."""
        if not self._can_perform_action():
            return False
        try:
            if self.platform == "darwin":
                self._run_applescript('tell application "System Events" to keystroke "t" using {command down}')
            else:
                subprocess.run(["xdotool", "key", "ctrl+t"], check=False)
            return True
        except Exception as e:
            print(f"Error opening new tab: {e}")
            return False
    
    def close_tab(self) -> bool:
        """Close current tab."""
        if not self._can_perform_action():
            return False
        try:
            if self.platform == "darwin":
                self._run_applescript('tell application "System Events" to keystroke "w" using {command down}')
            else:
                subprocess.run(["xdotool", "key", "ctrl+w"], check=False)
            return True
        except Exception as e:
            print(f"Error closing tab: {e}")
            return False
    
    def go_back(self) -> bool:
        """Go back in browser history."""
        if not self._can_perform_action():
            return False
        try:
            if self.platform == "darwin":
                self._run_applescript('tell application "System Events" to keystroke "[" using {command down}')
            else:
                subprocess.run(["xdotool", "key", "alt+Left"], check=False)
            return True
        except Exception as e:
            print(f"Error going back: {e}")
            return False
    
    def go_forward(self) -> bool:
        """Go forward in browser history."""
        if not self._can_perform_action():
            return False
        try:
            if self.platform == "darwin":
                self._run_applescript('tell application "System Events" to keystroke "]" using {command down}')
            else:
                subprocess.run(["xdotool", "key", "alt+Right"], check=False)
            return True
        except Exception as e:
            print(f"Error going forward: {e}")
            return False
    
    def _run_applescript(self, script: str) -> bool:
        """Run AppleScript command on macOS."""
        try:
            subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
            return True
        except Exception as e:
            print(f"AppleScript error: {e}")
            return False


# Singleton instance
system_controller = SystemController()
