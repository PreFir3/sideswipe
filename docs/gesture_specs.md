# Gesture Specifications & Technical Details

## Complete Gesture Reference

### 1. Directional Swipe

**File**: `src/gestures/swipe.py`

**Purpose**: Navigate between windows with horizontal hand movement

**Technical Implementation**:
```
Input: Hand X-position tracking across frames
Process: 
  - Track starting X position
  - Monitor X displacement
  - Validate direction consistency over 3+ frames
  - Ensure movement within time window
Output: SwipeGesture(direction="left"/"right", displacement, velocity, confidence)
```

**Configuration Parameters**:
- `min_x_movement`: 100 pixels (default)
- `time_window`: 2.0 seconds
- `confirmation_frames`: 3
- `cooldown`: 0.5 seconds

**Thresholds**:
- Requires minimum 100 pixels horizontal movement
- Must complete within 2 seconds
- Must maintain consistent direction for 3 frames
- 0.5 second cooldown between swipes

**Output Mapping**:
- LEFT swipe → Previous window
- RIGHT swipe → Next window

---

### 2. Number Selection

**File**: `src/gestures/number.py`

**Purpose**: Switch tabs by holding up fingers (1-5)

**Technical Implementation**:
```
Input: Hand landmark positions
Process:
  - Detect extended vs folded fingers
  - Average finger count over 10 frames
  - Validate confidence threshold (80%)
  - Confirm stable count
Output: NumberGesture(number=0-5, is_stable, confidence)
```

**Configuration Parameters**:
- `stabilization_frames`: 10
- `confidence_threshold`: 0.8
- `cooldown`: 1.0 second

**Finger Detection Logic**:
- **Thumb**: Extended if tip X-position < knuckle X-position
- **Other Fingers**: Extended if tip Y-position < knuckle Y-position (higher on frame)

**Output Mapping**:
- 1 finger → Tab 1
- 2 fingers → Tab 2
- 3 fingers → Tab 3
- 4 fingers → Tab 4
- 5 fingers → Tab 5

---

### 3. Clap Activation

**File**: `src/gestures/clap.py`

**Purpose**: Turn system on/off with hand claps

**Technical Implementation**:
```
Input: Distance between hand centers
Process:
  - Detect rapid hand approach (velocity threshold)
  - Detect hand contact (distance < 0.15)
  - Detect hand separation
  - Track clap count and timing
  - Distinguish single vs double clap
Output: ClapGesture(clap_count=1/2, distance, velocity, confidence)
```

**Configuration Parameters**:
- `max_palm_distance`: 0.15 (normalized)
- `velocity_threshold`: 0.5
- `clap_frame_window`: 15 frames
- `double_clap_window`: 0.8 seconds
- `single_clap_delay`: 1.5 seconds
- `cooldown`: 1.0 second

**Clap Detection States**:
1. IDLE → HANDS_APPROACHING (velocity < -threshold)
2. HANDS_APPROACHING → HANDS_CONTACT (distance < max)
3. HANDS_CONTACT → IDLE (velocity > threshold)
4. Count claps and validate timing

**Output Mapping**:
- DOUBLE CLAP → System ON
- SINGLE CLAP → System OFF (sleep mode)

**Notes**:
- Most complex gesture
- Highest false-trigger risk
- Requires significant hand movement
- Cannot be accidental

---

### 4. Head Tilt

**File**: `src/gestures/head_tilt.py`

**Purpose**: Scroll by tilting head up/down

**Technical Implementation**:
```
Input: Head pitch angle from facial landmarks
Process:
  - Calibrate neutral position at startup
  - Track head angle deviation
  - Smooth angle over 5 frames
  - Calculate scroll speed proportional to angle
Output: HeadTiltGesture(direction="up"/"down", scroll_speed, confidence)
```

**Configuration Parameters**:
- `angle_threshold`: 15 degrees
- `scroll_speed_max`: 20 pixels/frame
- `scroll_acceleration`: 1.2
- `smoothing_frames`: 5
- `reset_timeout`: 2.0 seconds

**Head Pitch Angles**:
- Negative angle = head tilted up (scroll up)
- Positive angle = head tilted down (scroll down)
- ±15° from neutral triggers scroll

**Output Mapping**:
- Head tilt UP → Scroll UP
- Head tilt DOWN → Scroll DOWN
- Scroll speed proportional to tilt angle

**Calibration**:
- User looks straight at screen
- System records neutral head position
- Future angles calculated as deviation from neutral

**ML Requirement**:
- Different head shapes/sizes require individual calibration
- Future: Train user-specific head model for accuracy

---

### 5. Eye Gaze Verification

**File**: `src/detectors/eye_gaze.py`

**Purpose**: Safety layer - prevent gestures when not looking at screen

**Technical Implementation**:
```
Input: Head angles OR eye position
Process:
  - Calculate gaze angle from screen center
  - Require 5 consecutive valid frames
  - Block all gestures if gaze invalid
Output: GazeVerification(is_valid, confidence, state)
```

**Configuration Parameters**:
- `max_gaze_angle`: 30 degrees
- `validation_frames`: 5

**Gaze States**:
- LOOKING_AT_SCREEN (gaze valid, all gestures enabled)
- LOOKING_AWAY (gaze invalid, all gestures disabled)
- UNKNOWN (transitioning states)

**Gesture Priority**:
All gestures require eye gaze validation FIRST before being processed.

---

## Detection Pipeline Architecture

### Input Layer
```
Video Frame
    ↓
MediaPipe Hand Detection → HandDetector.detect()
MediaPipe Face Detection → FaceDetector.detect()
    ↓
Hand Landmarks (21 x 2)
Face Landmarks (468 x 2)
```

### Processing Layer
```
Hand Landmarks
    ↓
SwipeDetector     (X-position tracking)
NumberDetector    (Finger counting)
ClapDetector      (Hand distance)
    ↓
Face Landmarks
    ↓
EyeGazeValidator  (Eye position validation)
HeadTiltDetector  (Head pitch angle)
    ↓
Processed Gestures + Eye Gaze Validation
```

### Output Layer
```
All Gestures
    ↓
Eye Gaze Check (blocks if invalid)
    ↓
Gesture Priority (if multiple detected)
    ↓
Event Emission (gesture detected!)
    ↓
System Response (window switch, tab switch, scroll, etc.)
```

---

## Temporal Filtering & Stability

All gestures use multi-frame validation to prevent false triggers:

- **Swipe**: Requires 3 consecutive frames of same direction
- **Number**: Averaged over 10 frames with 80% consistency
- **Clap**: Requires velocity + distance + timing validation
- **Head Tilt**: Smoothed over 5 frames
- **Eye Gaze**: Requires 5 consecutive frames of valid gaze

This ensures all gestures are intentional and not accidental noise.

---

## Sensitivity Tuning

Each gesture detector provides methods to adjust sensitivity:

```python
# Examples
swipe_detector.set_sensitivity(min_movement=150)  # Less sensitive
number_detector.set_sensitivity(confidence_threshold=0.9)  # More strict
clap_detector.set_sensitivity(velocity_threshold=0.3)  # More sensitive
head_tilt_detector.set_sensitivity(angle_threshold=10)  # More sensitive
```

---

## Future Enhancements

1. **Machine Learning**
   - Train user-specific hand models
   - Calibrate head shape for individual users
   - Adaptive sensitivity tuning

2. **Advanced Gestures**
   - Circular motions (volume control)
   - Pinch gestures (zoom)
   - Two-hand gestures

3. **Performance Optimization**
   - GPU acceleration with CUDA
   - Lightweight model variants
   - Multi-threading for processing

4. **User Preferences**
   - Save/load calibration profiles
   - Gesture remapping
   - Custom sensitivity presets

