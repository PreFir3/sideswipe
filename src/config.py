"""
Configuration and threshold settings for Sideswipe gesture recognition system.

All thresholds are set to be NON-SENSITIVE to avoid accidental triggers.
Adjust these values based on testing and user feedback.
"""

# ============================================================================
# DIRECTIONAL SWIPE (Window Navigation)
# ============================================================================

SWIPE = {
    "enabled": True,
    "min_x_movement": 150,              # pixels - minimum horizontal movement (INCREASED for stability)
    "time_window": 1.5,                 # seconds - time to complete swipe (TIGHTER window)
    "confirmation_frames": 6,           # frames - must confirm direction (MORE for stability)
    "cooldown": 1.0,                    # seconds - between swipes (LONGER to prevent accidental repeats)
    "reset_timeout": 3.0,               # seconds - reset state if no hand detected
}

# ============================================================================
# NUMBER SELECTION (Tab Switching)
# ============================================================================

NUMBER_SELECTION = {
    "enabled": True,
    "stabilization_frames": 20,         # frames - average finger count over this many frames (INCREASED)
    "confidence_threshold": 0.9,        # 0-1 - consistency required to trigger (MORE STRICT)
    "cooldown": 1.5,                    # seconds - between number changes (LONGER)
    "finger_position_threshold": 0.025, # normalized distance - raised fingers must clearly beat the knuckle
    "thumb_horizontal_margin": 0.035,   # normalized distance - thumb must clearly point away from the hand
    "thumb_reach_margin": 0.015,        # normalized distance - thumb tip must extend past the folded pose
}

# ============================================================================
# CLAP ACTIVATION (System On/Off)
# ============================================================================

CLAP_ACTIVATION = {
    "enabled": True,
    "max_palm_distance": 0.1,           # meters - hands must be within this distance
    "velocity_threshold": 0.5,          # m/s - rate of hand approach/separation
    "clap_frame_window": 15,            # frames - time window to detect clap motion
    "double_clap_window": 0.8,          # seconds - time between claps for double clap
    "single_clap_delay": 1.5,           # seconds - delay before registering single clap
    "cooldown": 1.0,                    # seconds - after clap detected
    "min_clap_velocity": 0.3,           # m/s - minimum hand speed to register
}

# ============================================================================
# OK HAND GESTURE (System Control)
# ============================================================================

OK_HAND = {
    "enabled": True,
    "circle_threshold": 0.04,           # 0-1 normalized - distance between thumb and index (MORE STRICT)
    "confirm_frames": 15,               # frames to hold for confirmation (MORE FRAMES FOR STABILITY)
    "cooldown": 1.0,                    # seconds between OK gestures (LONGER cooldown)
}

# ============================================================================
# FINGER SCROLL (Vertical Scrolling)
# ============================================================================

FINGER_SCROLL = {
    "enabled": True,
    "min_movement": 0.035,              # 0-1 normalized - averaged movement needed before scrolling
    "smoothing_frames": 7,              # frames for smoothing
    "activation_frames": 4,             # frames - require a short stable gesture before scrolling
    "dead_zone": 0.006,                 # 0-1 normalized - ignore tiny pinch movement jitter
    "velocity_smoothing": 0.8,          # 0-1 - higher means smoother, less twitchy scrolling
    "velocity_scale": 150,              # multiplier - maps gesture speed to scroll strength
    "max_scroll_amount": 5,             # lines per event - cap for comfortable scrolling
    "history_size": 8,                  # frames kept for smooth velocity estimation
    "pinch_threshold": 0.05,            # 0-1 normalized - thumb/index distance for pinch scrolling
    "scroll_amount": 2,                 # pixels per scroll event in the legacy runtime
}

# ============================================================================
# HEAD TILT CONTROL (Scrolling & Navigation)
# ============================================================================

HEAD_TILT = {
    "enabled": True,
    "calibration_frames": 30,           # frames - samples for neutral position setup
    "angle_threshold_up_down": 15,      # degrees - tilt angle for up/down scroll
    "angle_threshold_left_right": 20,   # degrees - tilt angle for left/right nav
    "scroll_speed_max": 20,             # pixels per frame - max scroll velocity
    "scroll_acceleration": 1.2,         # multiplier - scroll faster with larger tilt
    "reset_timeout": 2.0,               # seconds - return to neutral after no movement
    "smoothing_frames": 5,              # frames - smooth angle calculations
}

# ============================================================================
# EYE GAZE VERIFICATION (Safety Layer)
# ============================================================================

EYE_GAZE = {
    "enabled": False,
    "required_for_gestures": False,     # No longer required - finger scroll doesn't need it
    "max_gaze_angle": 30,               # degrees - max angle considered "looking at screen"
    "validation_frames": 5,             # frames - consecutive frames required
    "timeout": 3.0,                     # seconds - disable if no face detected
}

# ============================================================================
# DETECTION & PROCESSING
# ============================================================================

DETECTION = {
    "hand_detection_confidence": 0.85,  # 0-1 - MediaPipe hand detection threshold (STRICT for stability)
    "hand_tracking_confidence": 0.8,    # 0-1 - MediaPipe hand tracking threshold (STRICT for stability)
    "face_detection_confidence": 0.7,   # 0-1 - MediaPipe face detection threshold
    "frame_rate": 30,                   # FPS - target frame rate
    "resolution_width": 1280,           # pixels
    "resolution_height": 720,           # pixels
    "frame_buffer_size": 30,            # number of frames to buffer for temporal filtering
    "calibration_frames": 90,           # frames for head calibration (3 seconds at 30fps)
}

# ============================================================================
# VISUALIZATION & DEBUG
# ============================================================================

VISUALIZATION = {
    "enabled": True,
    "show_hand_landmarks": True,        # Draw hand skeleton
    "show_face_landmarks": False,       # Draw face landmarks (can slow down)
    "show_gaze_indicator": True,        # Draw eye gaze direction
    "show_gesture_state": True,         # Show current gesture being detected
    "show_thresholds": True,            # Show threshold lines on video
    "color_hand": (0, 255, 0),         # BGR - hand landmark color
    "color_face": (255, 0, 0),         # BGR - face landmark color
    "color_gesture_active": (0, 255, 255),  # BGR - active gesture color
}

# ============================================================================
# SYSTEM RESPONSE & OUTPUT
# ============================================================================

SYSTEM = {
    "platform": "macos",                # Platform: macos, windows, linux
    "sleep_mode_enabled": True,         # System starts in sleep after clap-off
    "window_switch_animation": 0.3,     # seconds - transition animation
    "vibration_feedback": False,        # Haptic feedback on gesture (if supported)
    "audio_feedback": False,            # Audio cues on gesture
}

# ============================================================================
# GESTURE PRIORITY & STATE
# ============================================================================

# Priority order when multiple gestures detected (highest to lowest)
GESTURE_PRIORITY = [
    "eye_gaze",           # Must validate first
    "clap_activation",    # System control - highest
    "number_selection",   # Explicit input
    "directional_swipe",  # Window nav
    "head_tilt",         # Continuous input
]

# ============================================================================
# PERFORMANCE & OPTIMIZATION
# ============================================================================

PERFORMANCE = {
    "use_gpu": True,                    # Use GPU for MediaPipe if available
    "async_processing": True,           # Process frames asynchronously
    "max_hand_detections": 2,           # Max hands to track
    "landmark_smoothing": True,         # Smooth landmarks across frames
}

# ============================================================================
# Helper function to get all settings
# ============================================================================

def get_config():
    """Returns a dictionary of all configuration settings."""
    return {
        "swipe": SWIPE,
        "number_selection": NUMBER_SELECTION,
        "clap_activation": CLAP_ACTIVATION,
        "head_tilt": HEAD_TILT,
        "eye_gaze": EYE_GAZE,
        "detection": DETECTION,
        "visualization": VISUALIZATION,
        "system": SYSTEM,
        "gesture_priority": GESTURE_PRIORITY,
        "performance": PERFORMANCE,
    }


def print_config():
    """Pretty print all configuration values."""
    config = get_config()
    for section, values in config.items():
        print(f"\n{section.upper()}")
        print("=" * 60)
        if isinstance(values, dict):
            for key, value in values.items():
                print(f"  {key:<35} {value}")
        elif isinstance(values, list):
            for item in values:
                print(f"  - {item}")
