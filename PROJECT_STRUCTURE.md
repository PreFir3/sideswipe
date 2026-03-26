# Project Structure & File Organization

## Directory Layout

```
sideswipe/
│
├── README.md                          # Quick start and overview
├── DESIGN.md                          # Complete system design
├── requirements.txt                   # Python dependencies
│
├── src/                              # Main source code
│   ├── __init__.py
│   ├── main.py                       # Entry point (to be created)
│   ├── config.py                     # Configuration & thresholds ✓
│   ├── gesture_engine.py             # Main gesture processing (to be created)
│   │
│   ├── detectors/                    # Detection layer
│   │   ├── __init__.py               ✓
│   │   ├── hand.py                   # Hand landmark detection ✓
│   │   ├── face.py                   # Face/head tracking ✓
│   │   └── eye_gaze.py               # Eye gaze verification ✓
│   │
│   ├── gestures/                     # Gesture recognition layer
│   │   ├── __init__.py               ✓
│   │   ├── swipe.py                  # Directional swipe detection ✓
│   │   ├── number.py                 # Number selection detection ✓
│   │   ├── clap.py                   # Clap activation detection ✓
│   │   └── head_tilt.py              # Head tilt/scroll detection ✓
│   │
│   ├── system_control/               # System control layer (to be created)
│   │   ├── __init__.py               ✓
│   │   ├── window_manager.py         # Window switching
│   │   ├── tab_manager.py            # Tab switching
│   │   └── scroll_manager.py         # Scroll control
│   │
│   └── utils/                        # Utility modules
│       ├── __init__.py               ✓
│       ├── frame_buffer.py           # Temporal filtering & smoothing ✓
│       └── visualization.py          # Debug visualization ✓
│
└── docs/                             # Documentation
    ├── gesture_specs.md              # Detailed gesture specifications ✓
    ├── api.md                        # API documentation ✓
    └── troubleshooting.md            # Troubleshooting guide (to be created)
```

## File Status

### ✓ Created (Phase 1 - Foundation Complete)

#### Core Documentation
- `README.md` - Project overview and quick start
- `DESIGN.md` - Complete system design document

#### Configuration
- `requirements.txt` - Python package dependencies
- `src/config.py` - All configuration and threshold settings

#### Detection Layer
- `src/detectors/hand.py` - Hand landmark detection (21 landmarks)
- `src/detectors/face.py` - Face/head detection and orientation
- `src/detectors/eye_gaze.py` - Eye gaze validation (safety layer)

#### Gesture Recognition Layer
- `src/gestures/swipe.py` - Directional swipe detector (left/right)
- `src/gestures/number.py` - Number selection detector (1-5 fingers)
- `src/gestures/clap.py` - Clap activation detector (single/double)
- `src/gestures/head_tilt.py` - Head tilt detector (up/down scrolling)

#### Utilities
- `src/utils/frame_buffer.py` - Temporal filtering and smoothing
- `src/utils/visualization.py` - Real-time visualization for debugging

#### Documentation
- `docs/gesture_specs.md` - Complete gesture specifications
- `docs/api.md` - Full API reference and integration guide

---

## Architecture Overview

### Three-Layer Design

```
┌─────────────────────────────────────┐
│    OUTPUT LAYER                     │
│  (System Responses)                 │
│  - Window switching                 │
│  - Tab switching                    │
│  - Scrolling                        │
│  - System on/off                    │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│    PROCESSING LAYER                 │
│  (Gesture Recognition)              │
│  - Swipe detection                  │
│  - Number detection                 │
│  - Clap detection                   │
│  - Head tilt detection              │
│  - Eye gaze validation              │
│  - Temporal filtering               │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│    INPUT LAYER                      │
│  (Detection)                        │
│  - Hand detection (MediaPipe)       │
│  - Face detection (MediaPipe)       │
│  - Landmark extraction              │
│  - Frame smoothing                  │
└─────────────────────────────────────┘
```

### Data Flow

```
Video Input
    ↓
MediaPipe Hand Detection → HandDetector
MediaPipe Face Detection → FaceDetector
    ↓
Landmarks + Head Angles
    ↓
Eye Gaze Validation (Safety Layer)
    ↓
Parallel Gesture Processing:
  ├─ SwipeDetector (hand X-position)
  ├─ NumberDetector (finger count)
  ├─ ClapDetector (hand distance)
  └─ HeadTiltDetector (head pitch angle)
    ↓
Gesture Priority & Deduplication
    ↓
Event Emission
    ↓
System Control (Windows, Tabs, Scrolling)
```

### Detection Points

Each gesture has clear detection points:

| Gesture | Input | Detection Logic | Confirmation |
|---------|-------|-----------------|--------------|
| Swipe | Hand X-position | Compare to initial, check direction | 3 frames same direction |
| Number | Finger positions | Extended vs folded | 10 frames, 80% consistency |
| Clap | Hand distance | Rapid approach/contact/separation | Velocity + distance + timing |
| Head Tilt | Head pitch angle | Angle deviation from neutral | Single frame threshold |
| Eye Gaze | Head/eye position | Angle from screen center | 5 consecutive frames valid |

---

## Module Dependencies

### Hand Detection
- `cv2` (OpenCV)
- `mediapipe`
- `numpy`
- No internal dependencies

### Face Detection
- `cv2` (OpenCV)
- `mediapipe`
- `numpy`
- No internal dependencies

### Gesture Detectors
- `numpy`
- No MediaPipe dependency (work with extracted landmarks)
- No internal dependencies between detectors

### Eye Gaze Validator
- `numpy`
- No MediaPipe dependency

### Utilities
- `cv2` (visualization only)
- `numpy`
- `collections` (standard library)

### Frame Buffer Utilities
- `numpy`
- `collections` (standard library)

---

## Next Steps (Phase 2-4)

### Phase 2: Gesture Recognition Engine
- `src/gesture_engine.py` - Main orchestration logic
- Implement priority system
- Event emission system
- Performance monitoring

### Phase 3: System Control Layer
- `src/system_control/window_manager.py` - macOS window control
- `src/system_control/tab_manager.py` - Tab/app switching
- `src/system_control/scroll_manager.py` - Scroll event generation

### Phase 4: Main Application
- `src/main.py` - Entry point
- Video capture loop
- Real-time processing pipeline
- Debug visualization
- State management

### Phase 5: Machine Learning (Future)
- User-specific head calibration
- Gesture personalization
- Adaptive sensitivity
- Performance optimization

---

## Testing & Validation

Each module includes:
1. ✓ Clear input/output specifications
2. ✓ Dataclass containers for results
3. ✓ State machine implementations
4. ✓ Threshold validation
5. ✓ Configuration parameters

Ready for unit testing and integration testing.

---

## Configuration & Customization

All thresholds are in `src/config.py`:

```python
# Adjust by editing values:
SWIPE["min_x_movement"] = 100      # Sensitivity
NUMBER_SELECTION["confidence_threshold"] = 0.8
CLAP_ACTIVATION["velocity_threshold"] = 0.5
HEAD_TILT["angle_threshold"] = 15
EYE_GAZE["max_gaze_angle"] = 30
```

Or adjust programmatically:

```python
swipe_detector.set_sensitivity(150)
number_detector.set_sensitivity(0.9)
```

---

## Performance Considerations

1. **Real-time Processing**: 30 FPS target
2. **Latency**: <50ms end-to-end
3. **GPU Acceleration**: MediaPipe uses GPU if available
4. **Memory**: ~200MB typical with MediaPipe models
5. **CPU**: Single core typically sufficient

---

## Documentation Reference

- **DESIGN.md** - System architecture and design decisions
- **docs/gesture_specs.md** - Detailed gesture specifications
- **docs/api.md** - Complete API reference
- **README.md** - Quick start and overview
- **src/config.py** - Inline documentation for all settings

All code includes docstrings explaining:
- What the module does
- Algorithm used
- Input/output specifications
- Configuration parameters
- Usage examples

