# Sideswipe: Gesture-Based Window Control System

## Overview
Sideswipe is a computer vision-based gesture recognition system that uses hand and head tracking to control window navigation, tab switching, and scrolling. The system prioritizes **non-sensitivity** (high activation thresholds) to avoid accidental triggers.

## Core Architecture

### Detection Pipeline
```
Video Input → Hand/Face Detection → Landmark Extraction → 
Gesture Recognition → Interpretation → System Response
```

### Input Detection Layer
Tracks three primary input sources:
1. **Hand Landmarks** - 21 points per hand using MediaPipe
2. **Face Landmarks** - Head orientation and eye gaze from facial landmarks
3. **Frame Context** - Temporal data for smoothing and threshold confirmation

### Interpretation Layer
Applies thresholds and logic to convert raw tracking data into meaningful gestures:
- **Temporal Filtering** - Multi-frame averaging to stabilize detections
- **Threshold Validation** - Minimum movement/distance requirements
- **State Management** - Tracking gesture start/end conditions

### Output Layer
Maps interpreted gestures to system actions (window switching, tab changes, scrolling)

---

## Gesture Specifications

### 1. Directional Swipe (Window Navigation)

| Aspect | Details |
|--------|---------|
| **User Action** | Horizontal hand movement (left or right) |
| **Visible Indication** | Hand tracked on X-axis showing directional movement |
| **Detection Input** | Index finger or palm center X-position across frames |
| **Processing** | Compare initial vs. final position with threshold |
| **Sensitivity** | High threshold to prevent accidental swipes |
| **Output** | Switch to previous (left) or next (right) window |
| **Constraints** | Must detect clear, sustained movement |

**Technical Specs:**
- **X-axis Threshold**: Minimum 100 pixels movement (adjustable)
- **Time Window**: Movement must complete within 0.5-2.0 seconds
- **Stabilization**: Require 3+ frames confirming direction before triggering
- **Reset**: Returns to initial state after 3 seconds of no hand detection

---

### 2. Number Selection (Tab Switching)

| Aspect | Details |
|--------|---------|
| **User Action** | Hold up fingers (1-5) to switch to corresponding tab |
| **Visible Indication** | Extended fingers clearly visible |
| **Detection Input** | Hand landmarks distinguish extended vs. folded fingers |
| **Processing** | Count extended fingers, stabilize across frames |
| **Sensitivity** | Frame averaging (10 frames) to confirm number |
| **Output** | Switch to tab matching finger count |
| **Constraints** | Requires clear visibility, consistent lighting |

**Technical Specs:**
- **Finger Detection**: Y-position comparison (tip above knuckle = extended)
- **Stabilization Window**: 10 frames averaging
- **Threshold Confidence**: 80% consistency required
- **Cooldown**: 1 second between number changes

---

### 3. Clap Activation (System On/Off)

| Aspect | Details |
|--------|---------|
| **User Action** | Double clap (ON) or single clap (OFF) |
| **Visible Indication** | Rapid hand contact without audio input |
| **Detection Input** | Both hands tracked, measuring palm-to-palm distance |
| **Processing** | Detect rapid distance decrease then increase |
| **Sensitivity** | Most complex - requires velocity + distance thresholds |
| **Output** | Toggle system ON/OFF (sleep mode when OFF) |
| **Constraints** | Prevents false triggers from other hand movements |

**Technical Specs:**
- **Clap Distance Threshold**: Hands within 10cm to register contact
- **Velocity Threshold**: Rate of change must be significant
- **Time Between Claps**: 0.3-0.8 seconds for double clap detection
- **Cooldown After Clap**: 1 second to avoid re-triggering

---

### 4. Head Tilt Control (Scrolling)

| Aspect | Details |
|--------|---------|
| **User Action** | Tilt head up/down for scrolling |
| **Visible Indication** | Head position change on Y-axis |
| **Detection Input** | Facial landmarks tracking head orientation angles |
| **Processing** | Calculate head angle deviation from neutral position |
| **Sensitivity** | Angle threshold required (adjustable) |
| **Output** | Scroll up/down in active window |
| **Constraints** | Requires ML model for individual head shape/size calibration |

**Technical Specs:**
- **Head Calibration**: User establishes neutral position on startup
- **Y-axis Threshold**: ±15 degrees from neutral for scroll triggering
- **Scroll Speed**: Proportional to head tilt angle (max 20 pixels per frame)
- **Reset**: Returns to neutral after 2 seconds of stationary head
- **Eye Gaze Check**: System only responds if eyes looking at screen

---

### 5. Eye Gaze Verification (Safety Layer)

**Purpose**: Prevent accidental gestures when user isn't looking at the system

| Aspect | Details |
|--------|---------|
| **Detection** | Track eye position relative to face/screen |
| **Logic** | Disable gesture interpretation if eyes not on screen |
| **Constraint** | All gestures require eyes-on-screen validation |

**Technical Specs:**
- **Gaze Angle Threshold**: ±30 degrees considered "looking at screen"
- **Validation Frames**: Require 5+ consecutive frames of valid gaze

---

## Configuration & Thresholds

### Sensitivity Settings

```yaml
Swipe:
  min_x_movement: 100  # pixels
  time_window: 2.0     # seconds
  confirmation_frames: 3

NumberSelection:
  stabilization_frames: 10
  confidence_threshold: 0.8
  cooldown: 1.0  # seconds

ClapActivation:
  max_palm_distance: 0.1  # meters
  velocity_threshold: 0.5  # m/s
  double_clap_window: 0.8  # seconds
  cooldown: 1.0  # seconds

HeadTilt:
  angle_threshold: 15  # degrees
  scroll_max_pixels: 20  # per frame
  reset_timeout: 2.0  # seconds

EyeGaze:
  max_gaze_angle: 30  # degrees
  validation_frames: 5
```

---

## Processing Priority & State Management

### Gesture Priority (when multiple detected)
1. **Eye Gaze Check** (blocks all if invalid)
2. **Clap Activation** (highest priority system control)
3. **Number Selection** (explicit tab switching)
4. **Directional Swipe** (window navigation)
5. **Head Tilt** (continuous scrolling)

### State Machine
```
STARTUP → SLEEP (waiting for double clap)
SLEEP → ACTIVE (double clap detected)
ACTIVE → Process gestures normally
ACTIVE → SLEEP (single clap detected)
SLEEP → ACTIVE (double clap detected)
```

---

## Implementation Roadmap

### Phase 1: Foundation
- [ ] Core video capture and hand/face detection setup
- [ ] Landmark extraction and visualization
- [ ] Basic frame averaging and temporal filtering

### Phase 2: Hand Gestures
- [ ] Directional Swipe detection
- [ ] Number Selection detection
- [ ] Clap Activation detection
- [ ] Hand gesture integration tests

### Phase 3: Head Control
- [ ] Head calibration system
- [ ] Head tilt angle calculation
- [ ] Eye gaze verification
- [ ] Scroll response mapping

### Phase 4: System Integration
- [ ] Window/tab control API
- [ ] Event emission system
- [ ] Configuration management
- [ ] Performance optimization

### Phase 5: Machine Learning (Future)
- [ ] User-specific head shape learning
- [ ] Gesture personalization
- [ ] Adaptive sensitivity tuning

---

## Technical Stack

- **Computer Vision**: OpenCV, MediaPipe
- **Gesture Recognition**: Custom logic with temporal filtering
- **System Control**: Platform-specific APIs (macOS/Windows/Linux)
- **UI Feedback**: Visual indicators for detected gestures

---

## Key Design Principles

1. **Non-Sensitivity First**: High thresholds prevent accidental triggers
2. **Multi-Frame Validation**: All gestures require temporal confirmation
3. **Graceful Degradation**: System handles poor lighting/visibility
4. **User Safety**: Eye gaze verification ensures intentional use
5. **Modular Architecture**: Easy to add/modify gestures and thresholds
6. **Clear Feedback**: Users always see what the system detected

