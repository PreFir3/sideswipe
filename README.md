# Sideswipe - Hand Gesture Control System

A stable hand tracking system for macOS that lets you control your computer using hand gestures. Built with MediaPipe and optimized for natural hand movements at any angle.

## Demo Link
https://sideswipe-demo.netlify.app/

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

## Submission

**Due:** April 2 by 11:59pm | **Points:** 25

Submit **one document per team (PDF or Google Doc)** containing the following three links:

1. **Deployed link** — Live prototype hosted on Netlify, Cloudflare Pages, or GitHub Pages
2. **GitHub repo link** — This repo, with a clean staged commit history and a README that includes:
   - Which states from the Control Language Map are implemented
   - How detection works for each state (plain language, not just code)
   - Calibration log (thresholds tried, adjusted, and settled on)
   - Diptych pole note (which pole this prototype serves, and what the other would require)
   - Known limitations
3. **Screen recording link** — Under 2 minutes, one team member demoing the implemented states live while narrating what the system senses and how it responds

## Control Language & Detection

### 1. Which Control Table States Are Implemented

Six gesture categories are active in the current build, covering eight distinct states:

- **Double Clap** — Toggles the entire system on or off. Two claps in quick succession wake the system (showing a green ACTIVE indicator) or put it back to sleep.
- **Single Clap** — Registers as a separate, slower activation signal. After one clap, the system waits 1.5 seconds to confirm no second clap is coming before acting.
- **Swipe Left** — Sends the keyboard shortcut Cmd+Option+Left Arrow, which switches to the previous browser tab.
- **Swipe Right** — Sends Cmd+Option+Right Arrow, switching to the next browser tab.
- **Number Selection (1–5)** — Hold up one to five fingers steadily for roughly one second and the system jumps directly to that numbered tab. This state is automatically disabled while swiping or scrolling so those gestures are not misread as a finger count.
- **Finger Scroll Up / Down** — Pinch your thumb and index finger together, then move your hand upward or downward. The page scrolls in the corresponding direction. Scrolling continues as long as the pinch is held and the hand is moving.
- **OK Hand** — Form a circle with your thumb and index finger while keeping at least two of the remaining fingers extended. Hold the shape for about half a second to trigger a system control action.
- **Head Tilt Up / Down** — Tilt your head up or down past a threshold angle to scroll the active page. The further the tilt, the faster the scroll. Returning your head to neutral stops scrolling.

Eye Gaze is implemented in the code but is currently disabled. It was originally designed as a safety layer that would require the user to be looking at the screen before any gesture could fire, but that requirement has been turned off.

---

### 2. How Detection Works for Each State

**Double Clap and Single Clap**

The system watches the straight-line distance between both hand centers, frame by frame. When two hands come within roughly a tenth of the camera frame's width of each other while moving toward each other faster than a set velocity threshold, the detector records a potential clap. It then waits for the hands to separate again. After separation, it listens for up to 0.8 seconds to see whether a second clap arrives — if it does, a double clap is confirmed immediately. If only one clap happened, the system waits a full 1.5 seconds before confirming the single clap, giving the user time to follow up with a second if they meant to double-clap. The clap module notes that this is a particularly easy gesture to trigger accidentally, which is why the approach-and-separation motion must both exceed the velocity floor.

**Swipe Left and Swipe Right**

The system records the horizontal position of the wrist joint at the start of any hand movement. Each subsequent frame, it measures how far that position has shifted left or right from the starting point. Before firing, it checks three things in combination: the total horizontal displacement must exceed 150 pixels, the entire motion must complete within 1.5 seconds, and the hand must have been moving consistently in one direction for at least 6 consecutive frames. If the time window closes before all three conditions are met, the tracking resets and the system waits for a fresh attempt. A one-second cooldown prevents the same swipe from registering twice.

**Number Selection (1–5)**

The system determines how many fingers are extended by comparing each fingertip's position to the knuckle below it — if the tip sits above the knuckle by more than a small threshold, that finger counts as extended. It collects this count over a rolling window of 20 frames. A tab jump only triggers when every single frame in that window shows the same count, which amounts to roughly two-thirds of a second of absolute consistency. The confidence requirement is set to 0.9, meaning almost no frame-to-frame variation is tolerated. After firing, a 1.5-second cooldown prevents accidental jumps caused by shifting fingers.

**Finger Scroll Up and Down**

The system tracks the vertical (Y-axis) position of the middle finger tip. It keeps a short rolling average of the last 5 frames to smooth out camera jitter. On each new frame, it compares the smoothed current position to the smoothed previous position. If that change exceeds 0.05 in normalized screen coordinates (roughly a few percent of the frame height), the system fires a scroll event in that direction. This check runs continuously while the pinch is held, so scrolling is ongoing rather than a single triggered event. Speed is proportional to how quickly the finger moves.

**OK Hand**

The system measures the Euclidean distance between the tip of the thumb and the tip of the index finger using their normalized coordinates. It simultaneously checks whether at least two of the three remaining fingers — middle, ring, and pinky — sit clearly above the base of the thumb. Both conditions must be true at the same time for the gesture to be considered present. The detector then keeps a sliding window of 15 frames. The gesture is confirmed only if all but at most one of those 15 frames show the OK shape — a single dropped frame is forgiven for robustness, but any more resets the counter.

**Head Tilt Up and Down**

At startup, the system records a calibration baseline by sampling the head's pitch angle for 90 frames (about 3 seconds at 30 FPS) while the user holds still. From then on, it computes how far the current head angle deviates from that baseline on every frame. Those deviations are smoothed over a 5-frame window to filter out small wobbles. When the smoothed deviation exceeds 15 degrees upward or downward, scrolling begins. The scroll speed is not fixed — it scales with how far past the threshold the head has tilted, up to a cap of 20 pixels per frame accelerated by a 1.2 multiplier. If the head stays within the threshold zone for more than 2 seconds, the neutral baseline is quietly recalibrated to wherever the head has settled, so the system stays accurate even as the user shifts posture.

---

### 3. Calibration Log

The following records every threshold that carries a calibration comment in src/config.py, noting what the comment indicates was observed and in which direction the value was adjusted.

**Swipe Left / Right**

The minimum horizontal movement required was increased (from an unstated lower value) for stability — the original threshold was catching small incidental hand drifts as deliberate swipes. The time window for completing a swipe was tightened from a wider default — slow passive arm movement was being read as a swipe attempt. The number of frames required to confirm a direction was increased for stability — the system was firing on brief direction ambiguity before the hand had committed to one side. The cooldown between swipes was lengthened to prevent accidental repeats — consecutive swipes were registering when the hand rebounded after a single gesture.

| Parameter | Settled value | Direction adjusted | Problem indicated |
|---|---|---|---|
| min_x_movement | 150 pixels | Increased | Accidental triggers from small hand drifts |
| time_window | 1.5 seconds | Tightened | Slow passive movement counted as swipes |
| confirmation_frames | 6 frames | Increased | Direction was confirmed too early |
| cooldown | 1.0 second | Lengthened | Back-to-back swipes from single gesture |

**Number Selection (1–5)**

The stabilization frame window was increased — fewer frames meant the finger count flickered and sent users to wrong tabs. The confidence threshold was made more strict — the system was confirming counts that had occasional misread frames mixed in. The cooldown was lengthened — rapid re-triggering between different finger counts was happening when the user shifted fingers.

| Parameter | Settled value | Direction adjusted | Problem indicated |
|---|---|---|---|
| stabilization_frames | 20 frames | Increased | Finger count was flickering; wrong tabs triggered |
| confidence_threshold | 0.9 (0–1 scale) | Stricter | Inconsistent counts still confirmed |
| cooldown | 1.5 seconds | Lengthened | Rapid re-triggering between finger counts |

**Clap Activation**

The clap module's header explicitly notes this is a very sensitive gesture requiring high thresholds to avoid false triggers. The overall config file header states that all thresholds are intentionally set to be non-sensitive. The single clap delay is long (1.5 seconds) to prevent a double-clap attempt from accidentally resolving as a single clap.

| Parameter | Settled value | Direction adjusted | Problem indicated |
|---|---|---|---|
| single_clap_delay | 1.5 seconds | Long by design | Single clap firing before double-clap could complete |
| double_clap_window | 0.8 seconds | Set conservatively | Must balance fast double-claps with false doubles |
| min_clap_velocity | 0.3 m/s | Set as floor | Slow hand movements near each other should not register |

**OK Hand**

The circle threshold (distance between thumb and index tips) was made more strict — a loose, imprecise pinch was triggering the gesture. The number of confirmation frames was increased for stability — the gesture was firing on brief, unintentional hand shapes. The cooldown was lengthened — rapid re-triggering was occurring after a confirmed gesture.

| Parameter | Settled value | Direction adjusted | Problem indicated |
|---|---|---|---|
| circle_threshold | 0.04 (normalized) | Stricter | Loose pinches accidentally confirmed |
| confirm_frames | 15 frames | Increased | Brief shapes triggered gesture prematurely |
| cooldown | 1.0 second | Lengthened | Gesture re-triggered immediately after confirmation |

**Global Detection**

Both MediaPipe confidence thresholds were raised for stability — lower settings produced phantom hand detections or lost tracking on cluttered backgrounds.

| Parameter | Settled value | Direction adjusted | Problem indicated |
|---|---|---|---|
| hand_detection_confidence | 0.85 | Raised | False hand detections in complex backgrounds |
| hand_tracking_confidence | 0.80 | Raised | Tracking lost too easily between frames |

Head Tilt and Finger Scroll carry no explicit adjustment comments in config.py — their values appear to be first-pass settings that have not yet been revised.

---

### 4. Diptych Pole Note

This prototype sits squarely at the pressure/extraction/control pole. Every design decision — the high confidence thresholds, the confirmation-frame requirements, the cooldowns, the priority order — is oriented toward making the body a cleaner, more reliable input device. The user's hand movements are parsed for correctness against a command grammar, and the calibration history is entirely a record of reducing noise so that commands fire only when the system is certain. The gestures do not invite exploration or ambiguity; they are evaluated as either valid commands or discarded errors. The body is enrolled into efficient computer control, and the success criterion is whether the intended command executed accurately.

The opposite pole would invert that relationship: instead of the system judging whether the body produced the correct command, the system would respond to continuous, unclassified movement with continuous, ambient change — perhaps altering the visual or sonic environment in proportion to the hand's trajectory, speed, or shape, without any binary pass/fail threshold. There would be no cooldowns, no confirmation frames, and no concept of an accidental trigger, because every movement would be meaningful on its own terms.
