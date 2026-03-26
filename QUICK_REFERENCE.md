# Sideswipe Quick Reference

## 5-Second Overview

**Gesture control system** using hand tracking and head detection to:
- **Swipe** → Navigate windows
- **Fingers** → Switch tabs
- **Clap** → Turn on/off
- **Head Tilt** → Scroll
- **Eye Gaze** → Safety validation

---

## Key Thresholds (Non-Sensitive Design)

| Gesture | Threshold | Notes |
|---------|-----------|-------|
| **Swipe** | 100 pixels | Minimum movement |
| **Number** | 80% consistency | Over 10 frames |
| **Clap** | 0.15m distance | + velocity check |
| **Head Tilt** | ±15 degrees | From neutral |
| **Eye Gaze** | ±30 degrees | From center |

---

## File Structure

```
src/
  ├── config.py                 # ⚙️ Adjust all thresholds here
  ├── detectors/
  │   ├── hand.py              # Hand landmarks (21 points)
  │   ├── face.py              # Face + head angle
  │   └── eye_gaze.py          # Gaze validation (safety)
  ├── gestures/
  │   ├── swipe.py             # ← → (windows)
  │   ├── number.py            # 1-5 (tabs)
  │   ├── clap.py              # 👏 (on/off)
  │   └── head_tilt.py         # ↑ ↓ (scroll)
  └── utils/
      ├── frame_buffer.py      # Smoothing & filtering
      └── visualization.py     # Debug visualization
```

---

## Quick Start Example

```python
from src.detectors.hand import HandDetector
from src.gestures.swipe import SwipeDetector

# Initialize
hand_detector = HandDetector()
swipe_detector = SwipeDetector()

# Each frame
detections = hand_detector.detect(frame)
for hand in detections:
    if hand.present:
        gesture = swipe_detector.add_hand_position(
            hand.landmarks[8][0]  # index finger X
        )
        if gesture.is_confirmed:
            print(f"Swipe {gesture.direction} detected!")
```

---

## Configuration Example

```python
# Edit src/config.py:

SWIPE = {
    "min_x_movement": 100,      # ← Increase to make less sensitive
    "time_window": 2.0,
    "confirmation_frames": 3,
}

# Or adjust in code:
swipe_detector.set_sensitivity(150)
```

---

## Processing Pipeline

```
Video Frame
    ↓
Hand Detection ──→ Swipe Detector ──→ LEFT/RIGHT
Hand Detection ──→ Number Detector ──→ 1-5
Hand Distance ──→ Clap Detector ───→ 1/2 claps
Face Detection ──→ Eye Gaze Check ─→ VALID/INVALID
Face Detection ──→ Head Tilt ──────→ UP/DOWN scroll
    ↓
Output Event
```

---

## Gesture Specifications

### 1️⃣ Swipe (Window Navigation)
- Input: Hand X-position
- Trigger: ±100 pixels, 3 frames consistent
- Output: LEFT or RIGHT
- Time: 0.5-2.0 seconds

### 2️⃣ Number (Tab Switching)
- Input: Extended fingers
- Trigger: 10 frames, 80% consistency
- Output: 1-5
- Time: ~0.3 seconds to stabilize

### 3️⃣ Clap (System On/Off)
- Input: Hand distance
- Trigger: Velocity + distance + timing
- Output: 1=OFF, 2=ON
- Time: Single/double clap detection

### 4️⃣ Head Tilt (Scrolling)
- Input: Head pitch angle
- Trigger: ±15° from neutral
- Output: UP or DOWN
- Time: Real-time while tilting

### 5️⃣ Eye Gaze (Safety)
- Input: Head angle or eye position
- Trigger: 5 consecutive valid frames
- Output: VALID or INVALID
- Blocks all gestures if invalid

---

## All Classes & Functions

### Detectors
```
HandDetector.detect(frame) → List[HandDetection]
HandDetector.get_finger_count(landmarks) → int
HandDetector.get_hand_distance(hand1, hand2) → float

FaceDetector.detect(frame) → FaceDetection
FaceDetector.calibrate_neutral_head_position(landmarks)
FaceDetector.get_head_tilt_vertical(landmarks) → float

EyeGazeValidator.validate_from_head_angles(pitch, yaw) → GazeVerification
EyeGazeValidator.is_valid() → bool
```

### Gesture Detectors
```
SwipeDetector.add_hand_position(x_pos) → SwipeGesture
SwipeDetector.set_sensitivity(min_movement)

NumberDetector.add_finger_count(count) → NumberGesture
NumberDetector.set_sensitivity(threshold)

ClapDetector.add_hand_distance(distance) → ClapGesture
ClapDetector.set_sensitivity(velocity_threshold)

HeadTiltDetector.calibrate_neutral_position(pitch)
HeadTiltDetector.add_head_angle(pitch) → HeadTiltGesture
HeadTiltDetector.set_sensitivity(angle_threshold)
```

### Utilities
```
FrameBuffer(max_size) - Circular data buffer
LandmarkSmoother(factor) - Smooth landmarks
MotionDetector(buffer_size) - Analyze motion
GestureVisualizer(width, height) - Debug drawing
```

---

## Output Data Structures

```python
# Each gesture returns a dataclass

SwipeGesture:
  ├─ direction: "left" / "right" / "none"
  ├─ displacement: float (pixels)
  ├─ velocity: float (px/frame)
  ├─ is_confirmed: bool
  └─ confidence: 0-1

NumberGesture:
  ├─ number: 0-5
  ├─ is_stable: bool
  ├─ confidence: 0-1
  └─ frame_count: int

ClapGesture:
  ├─ clap_count: 1 or 2
  ├─ state: ClapState enum
  ├─ distance: float
  ├─ is_confirmed: bool
  └─ confidence: 0-1

HeadTiltGesture:
  ├─ scroll_direction: "up" / "down" / "none"
  ├─ scroll_speed: float (px/frame)
  ├─ head_angle: float (degrees)
  ├─ is_active: bool
  └─ confidence: 0-1

GazeVerification:
  ├─ is_valid: bool
  ├─ state: GazeState enum
  ├─ gaze_angle: float (degrees)
  └─ confidence: 0-1
```

---

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| **FPS** | 30 | Real-time processing |
| **Latency** | <50ms | End-to-end |
| **Memory** | 200MB | With MediaPipe models |
| **CPU** | Single core | Usually sufficient |

---

## Configuration Location

📝 **Single file to adjust all settings**:

**`src/config.py`** - Edit this file to:
- Adjust gesture thresholds
- Change detection confidence
- Modify visualization
- Set system parameters
- Adjust sensitivity

```python
# Examples of what you can change:
SWIPE["min_x_movement"] = 150              # Less sensitive
NUMBER_SELECTION["confidence_threshold"] = 0.9  # More strict
CLAP_ACTIVATION["velocity_threshold"] = 0.3    # More sensitive
HEAD_TILT["angle_threshold"] = 12          # More sensitive
EYE_GAZE["max_gaze_angle"] = 25            # Stricter gaze requirement
```

---

## Documentation Quick Links

- 📘 **DESIGN.md** - Complete system design
- 📗 **README.md** - Project overview
- 📙 **docs/gesture_specs.md** - Gesture details
- 📕 **docs/api.md** - Full API reference
- 📓 **PROJECT_STRUCTURE.md** - File organization
- 📔 **IMPLEMENTATION_SUMMARY.md** - What was created

---

## Dependencies

```
opencv-python      # Computer vision
mediapipe         # Hand & face detection
numpy             # Numerical computing
```

Install with:
```bash
pip install -r requirements.txt
```

---

## Next Steps

### Phase 1 ✓ Complete
- All detection and gesture recognition modules
- Complete documentation and API
- Configuration system

### Phase 2 (Next)
- Gesture orchestration engine
- Event emission system
- Performance monitoring

### Phase 3
- System control (window/tab/scroll)
- Platform-specific integration

### Phase 4
- Main application entry point
- Real-time processing loop
- User interface

---

## Troubleshooting

### Detection not working?
1. Check `config.py` detection confidence values
2. Ensure good lighting
3. Check camera positioning
4. Verify MediaPipe installation

### Gestures too sensitive?
1. Increase thresholds in `config.py`
2. Use `.set_sensitivity()` methods
3. Check `confirmation_frames` / `stabilization_frames`

### Gestures not responding?
1. Check eye gaze validation (must look at screen)
2. Ensure enough frames have passed for stabilization
3. Check cooldown timers
4. Verify gesture is within threshold

### Performance issues?
1. Reduce detection frequency
2. Disable visualization
3. Check camera resolution
4. Monitor CPU usage

---

## Key Design Principles

1. **🛡️ Safety First** - High thresholds, eye gaze validation
2. **🎯 Intentional** - Multi-frame confirmation required
3. **⚙️ Configurable** - All thresholds adjustable
4. **📦 Modular** - Easy to extend
5. **📊 Observable** - Debug visualization
6. **⚡ Real-time** - 30 FPS target

---

## Support

- Read DESIGN.md for architecture explanation
- Check docs/api.md for code examples
- Review gesture_specs.md for technical details
- Examine src/config.py for all settings
- Look at docstrings in source files

All code is well-documented and ready to integrate!
