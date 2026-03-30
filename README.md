# Sideswipe - Hand Gesture Control System

A stable hand tracking system for macOS that lets you control your computer using hand gestures. Built with MediaPipe and optimized for natural hand movements at any angle.

## Collaborators
- Daniel Fitzpatrick (Response lead) (Vice Project Manager)
- Dylan Eytan (Integration Lead) (State Engine Lead)
- Greyson Mackle (Detection Lead) (Project Manager)

## Features

✨ **Hand Gesture Recognition**
- � **Clap Detection** - Clap twice to toggle activation
- � **Swipe Gestures** - Left/right swipes to switch browser tabs
- � **Pinch Scrolling** - Pinch thumb+index and move up/down to scroll
- 🎯 **Real-time Tracking** - 30 FPS hand detection at any hand angle

## Requirements

- macOS (tested on M4)
- Python 3.9+
- Webcam

## Quick Start

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd sideswipe
```

### 2. Create virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the agent
```bash
python3 src/agent.py
```

## How to Use

1. **Activate the system**: Clap your hands together twice (👏👏)
   - You'll see `🟢 ACTIVE` indicator
   
2. **Switch browser tabs**: Swipe your hand left or right
   - Works with Cmd+Option+Left/Right Arrow keyboard shortcuts
   
3. **Scroll webpages**: 
   - Pinch your thumb and index finger together
   - Move your pinched hand up or down
    - Smooth, continuous scrolling (native scroll events when available)

4. **Jump to a tab number (1–5)**:
    - Hold up 1–5 fingers steadily for ~1 second
    - Tip: this is automatically disabled while you're swiping or scrolling, so those gestures won't be misread as a tab-jump

4. **Deactivate**: Clap twice again to turn off

## Controls

| Gesture | Action |
|---------|--------|
| 👏👏 Clap Twice | Toggle on/off |
| 🔄 Swipe Left/Right | Switch tabs |
| 📜 Pinch + Move | Scroll up/down |
| 📌 Hold up 1–5 fingers (hold ~1s) | Jump to that tab number |
| 'q' Key | Quit application |

## Project Structure

```
sideswipe/
├── src/
│   ├── agent.py              # Main hand tracking agent
│   ├── config.py             # Configuration settings
│   ├── detectors/            # Hand/face detection modules
│   │   ├── hand.py
│   │   ├── face.py
│   │   ├── improved_hand.py
│   │   └── eye_gaze.py
│   ├── gestures/             # Gesture recognition modules
│   │   ├── clap.py
│   │   ├── swipe.py
│   │   ├── finger_scroll.py
│   │   ├── ok_hand.py
│   │   ├── head_tilt.py
│   │   └── number.py
│   ├── system_control/       # macOS automation
│   │   ├── browser.py
│   │   └── advanced_control.py
│   └── utils/                # Utilities
│       ├── visualization.py
│       └── frame_buffer.py
├── requirements.txt          # Python dependencies
├── hand_landmarker.task      # MediaPipe hand model
├── face_landmarker.task      # MediaPipe face model
├── .gitignore               # Git ignore rules
└── README.md                 # This file
```

## Technical Details

### Hand Detection
- **Model**: MediaPipe Hand Landmarker (21 landmarks per hand)
- **Confidence Thresholds**: 
  - Detection: 0.6
  - Presence: 0.6
  - Tracking: 0.5
- **Resolution**: 1280x720 @ 30 FPS

### Gesture Detection
- **Swipe**: Horizontal hand movement < 0.1 normalized distance, disabled during pinch
- **Pinch**: Thumb-index distance < 0.06 (normalized coordinates)
- **Clap**: Two hands < 0.15 distance apart
- **Swipe Cooldown**: 1 second between swipes
- **Scroll Cooldown**: 0.3 seconds between scroll events

### macOS Integration
- Uses AppleScript (osascript) for keyboard events
- Page Up/Down keys for universal scrolling
- Cmd+Option+Arrow keys for tab switching

## Troubleshooting

### Hand tracking is lost easily
- Ensure good lighting
- Face the camera directly
- Keep hands in view

### Scrolling doesn't work
- Make sure you're pinching (thumb touching index)
- Focus Chrome window on the webpage
- Check that Page Up/Down work manually in your app

### Swiping not detected
- Use exaggerated hand movements initially
- Ensure you're not pinching (pinch disables swipes)
- Keep hand movement horizontal

## Dependencies

See `requirements.txt` for all dependencies. Main packages:
- `opencv-python` - Video capture and display
- `mediapipe` - Hand and face detection
- `numpy` - Numerical operations

## Development

To extend with new gestures:

1. Add gesture detection method to `SimpleHandTracker` class in `agent.py`
2. Add handler in the main loop
3. Call `self.controller` methods for automation

Example:
```python
def detect_custom_gesture(self, hand):
    # Your gesture detection logic
    if gesture_detected:
        return "GESTURE_NAME"
    return None
```

## Notes

- Hand tracking works at any hand angle - no need for flat palms
- MediaPipe models are downloaded automatically on first run
- System requires camera access permissions
- Currently optimized for Chrome but works with other apps

## Setup for Team

1. Extract the zip file
2. Create virtual environment: `python3 -m venv .venv`
3. Activate: `source .venv/bin/activate`
4. Install: `pip install -r requirements.txt`
5. Run: `python3 src/agent.py`

## License

MIT License - See LICENSE file for details

## Contributors

- Grayson Mackle - Initial development

---

**Happy hand gesturing!** 🖐️✨
│   ├── detectors/
│   │   ├── hand.py       # Hand landmark detection
│   │   ├── face.py       # Face/head tracking
│   │   └── eye_gaze.py   # Eye gaze verification
│   ├── gestures/
│   │   ├── swipe.py      # Directional swipe logic
│   │   ├── number.py     # Number selection logic
│   │   ├── clap.py       # Clap activation logic
│   │   └── head_tilt.py  # Head tilt/scroll logic
│   ├── system_control/
│   │   ├── window_manager.py  # Window switching
│   │   ├── tab_manager.py     # Tab switching
│   │   └── scroll_manager.py  # Scroll control
│   └── utils/
│       ├── visualization.py   # Debug visualization
│       └── frame_buffer.py    # Temporal filtering
└── docs/
    ├── gesture_specs.md   # Detailed gesture specifications
    ├── api.md            # System API documentation
    └── troubleshooting.md # Common issues and solutions
```

## Development Status

### Phase 1: Foundation ✓
- [x] Project structure created
- [x] Design documentation complete
- [ ] Video capture setup
- [ ] Detection pipeline

### Phase 2: Hand Gestures
- [ ] Directional Swipe detection
- [ ] Number Selection detection
- [ ] Clap Activation detection

### Phase 3: Head Control
- [ ] Head tilt angle calculation
- [ ] Eye gaze verification
- [ ] Scroll response mapping

### Phase 4: System Integration
- [ ] Window/tab control API
- [ ] Event emission system
- [ ] Performance optimization

## Configuration

Edit `src/config.py` to adjust gesture thresholds and sensitivity:

```python
# Example threshold adjustments
SWIPE_MIN_X_MOVEMENT = 100  # pixels
SWIPE_TIME_WINDOW = 2.0     # seconds
NUMBER_STABILIZATION_FRAMES = 10
HEAD_TILT_ANGLE_THRESHOLD = 15  # degrees
```

## Contributing

This project follows these principles:
- **Non-Sensitivity**: High thresholds prevent false triggers
- **Multi-Frame Validation**: All gestures require temporal confirmation
- **User Safety**: Eye gaze verification for all interactions

## License

MIT

## References

- [MediaPipe Hand Tracking](https://google.github.io/mediapipe/solutions/hands)
- [MediaPipe Face Detection](https://google.github.io/mediapipe/solutions/face_detection)
- [OpenCV Documentation](https://docs.opencv.org/)
