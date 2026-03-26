# Sideswipe API Documentation

## Core Modules Overview

### Detection Layer

#### HandDetector (`src/detectors/hand.py`)

Detects hand landmarks using MediaPipe.

```python
from src.detectors.hand import HandDetector

# Initialize
detector = HandDetector(
    detection_confidence=0.7,
    tracking_confidence=0.6,
    max_num_hands=2
)

# Detect in frame
detections = detector.detect(frame)  # List[HandDetection]

# Access results
for detection in detections:
    landmarks = detection.landmarks  # (21 x 2) normalized coordinates
    hand = detection.handedness  # "Left" or "Right"
    if detection.present:
        # Hand detected
        finger_count = detector.get_finger_count(landmarks)
        center = detector.get_hand_center(landmarks)
        palm = detector.get_palm_center(landmarks)

# Utility methods
index_tip = detector.get_index_finger_tip(landmarks)
distance = detector.get_hand_distance(hand1_landmarks, hand2_landmarks)
velocity = detector.get_hand_velocity(current, previous)
```

---

#### FaceDetector (`src/detectors/face.py`)

Detects face landmarks and head orientation.

```python
from src.detectors.face import FaceDetector

# Initialize
detector = FaceDetector(detection_confidence=0.7)

# Detect in frame
detection = detector.detect(frame)  # FaceDetection

if detection.present:
    landmarks = detection.landmarks  # (468 x 2)
    pitch, yaw, roll = detection.head_euler_angles  # Degrees
    
    # Check if looking at screen
    is_looking = detector.is_looking_at_screen(landmarks, max_angle=30)
    
    # Get head tilt
    vertical_tilt = detector.get_head_tilt_vertical(landmarks)
    horizontal_tilt = detector.get_head_tilt_horizontal(landmarks)

# Calibration
detector.calibrate_neutral_head_position(landmarks)
deviation = detector.get_head_angle_deviation(landmarks)
```

---

#### EyeGazeValidator (`src/detectors/eye_gaze.py`)

Validates eye gaze for safety layer.

```python
from src.detectors.eye_gaze import EyeGazeValidator, GazeState

validator = EyeGazeValidator(
    max_gaze_angle=30.0,
    validation_frames=5
)

# Validate using head angles
verification = validator.validate_from_head_angles(pitch, yaw)
# or from eye position
verification = validator.validate_from_eye_position(eye_center)

# Check results
if verification.is_valid:
    print("Eyes on screen - gestures enabled")
else:
    print("Look at screen to use gestures")

# Current state
if validator.is_valid():
    # Process gestures
    pass
```

---

### Gesture Recognition Layer

#### SwipeDetector (`src/gestures/swipe.py`)

Detects left/right directional swipes.

```python
from src.gestures.swipe import SwipeDetector, SwipeDirection

detector = SwipeDetector(
    min_x_movement=100,
    time_window=2.0,
    confirmation_frames=3
)

# Each frame
gesture = detector.add_hand_position(x_pos, frame_index)

if gesture.is_confirmed:
    if gesture.direction == SwipeDirection.LEFT:
        # Go to previous window
        print("Swipe LEFT detected")
    elif gesture.direction == SwipeDirection.RIGHT:
        # Go to next window
        print("Swipe RIGHT detected")

# Sensitivity adjustment
detector.set_sensitivity(min_movement=150)
```

---

#### NumberDetector (`src/gestures/number.py`)

Detects finger count for tab switching.

```python
from src.gestures.number import NumberDetector

detector = NumberDetector(
    stabilization_frames=10,
    confidence_threshold=0.8
)

# Each frame
gesture = detector.add_finger_count(finger_count)

if gesture.is_stable:
    print(f"Switch to tab {gesture.number}")
    print(f"Confidence: {gesture.confidence}")

# Sensitivity adjustment
detector.set_sensitivity(confidence_threshold=0.9)
```

---

#### ClapDetector (`src/gestures/clap.py`)

Detects hand claps for system on/off.

```python
from src.gestures.clap import ClapDetector, ClapState

detector = ClapDetector(
    max_palm_distance=0.15,
    velocity_threshold=0.5
)

# Each frame
gesture = detector.add_hand_distance(distance)

if gesture.is_confirmed:
    if gesture.clap_count == 1:
        print("Single clap - turn OFF")
    elif gesture.clap_count == 2:
        print("Double clap - turn ON")

# State tracking
print(f"Clap state: {gesture.state}")  # ClapState enum
```

---

#### HeadTiltDetector (`src/gestures/head_tilt.py`)

Detects head tilt for scrolling.

```python
from src.gestures.head_tilt import HeadTiltDetector, ScrollDirection

detector = HeadTiltDetector(
    angle_threshold=15.0,
    scroll_speed_max=20.0
)

# Calibration (once at startup)
detector.calibrate_neutral_position(pitch_angle)

# Each frame
gesture = detector.add_head_angle(current_pitch)

if gesture.is_active:
    if gesture.scroll_direction == ScrollDirection.UP:
        print(f"Scroll UP at {gesture.scroll_speed} px/frame")
    elif gesture.scroll_direction == ScrollDirection.DOWN:
        print(f"Scroll DOWN at {gesture.scroll_speed} px/frame")

# Sensitivity adjustment
detector.set_sensitivity(angle_threshold=12)
detector.set_max_scroll_speed(25)
```

---

### Utility Layer

#### FrameBuffer (`src/utils/frame_buffer.py`)

Temporal data storage for multi-frame analysis.

```python
from src.utils.frame_buffer import FrameBuffer, LandmarkSmoother, MotionDetector

# Frame buffer for storing recent data
buffer = FrameBuffer(max_size=10)
buffer.append(data)
if buffer.is_full():
    all_data = buffer.get_all()
    latest = buffer.get_latest(n=3)

# Smooth landmarks across frames
smoother = LandmarkSmoother(smoothing_factor=0.7)
smoothed = smoother.smooth(landmarks)
smoother.reset()

# Detect motion patterns
motion = MotionDetector(buffer_size=5)
motion.add_position(x, y)
velocity = motion.get_velocity()
direction = motion.get_direction()  # "left", "right", "up", "down"
displacement = motion.get_total_displacement()

# Validate thresholds
from src.utils.frame_buffer import ThresholdValidator
is_valid = ThresholdValidator.validate_movement(
    displacement=150,
    min_displacement=100,
    velocity=5.0,
    min_velocity=1.0
)

count = ThresholdValidator.validate_count_stability(
    values=[2, 2, 2, 2, 3],
    confidence_threshold=0.8
)
```

---

#### GestureVisualizer (`src/utils/visualization.py`)

Real-time visualization for debugging.

```python
from src.utils.visualization import GestureVisualizer

viz = GestureVisualizer(frame_width=1280, frame_height=720)

# Draw hand landmarks
frame = viz.draw_hand_landmarks(
    frame,
    landmarks,
    connections=HandDetector.CONNECTIONS
)

# Draw gesture status
frame = viz.draw_gesture_status(
    frame,
    gesture_states={
        "swipe": {"state": "idle"},
        "clap": {"state": "in_progress"}
    }
)

# Draw thresholds
frame = viz.draw_threshold_lines(frame, swipe_threshold=100, scroll_threshold=50)

# Draw hand distance (for clap)
frame = viz.draw_hand_distance(frame, hand1_pos, hand2_pos, distance, threshold)

# Draw head tilt
frame = viz.draw_head_tilt_indicator(frame, head_angle, threshold, "up")

# Draw gaze indicator
frame = viz.draw_gaze_indicator(frame, gaze_valid=True, gaze_angle=5)

# Draw FPS
frame = viz.draw_fps(frame, fps=30.0)
```

---

## Configuration System

### Using Configuration

```python
from src.config import get_config, SWIPE, NUMBER_SELECTION

# Get all config
config = get_config()

# Access specific gesture config
print(SWIPE["min_x_movement"])  # 100
print(NUMBER_SELECTION["confidence_threshold"])  # 0.8

# Modify configuration
from src.config import SWIPE
SWIPE["min_x_movement"] = 150
```

### Configuration Structure

```python
{
    "swipe": { ... },
    "number_selection": { ... },
    "clap_activation": { ... },
    "head_tilt": { ... },
    "eye_gaze": { ... },
    "detection": { ... },
    "visualization": { ... },
    "system": { ... },
    "gesture_priority": [ ... ],
    "performance": { ... }
}
```

---

## Data Structures

### HandDetection

```python
@dataclass
class HandDetection:
    landmarks: np.ndarray  # (21 x 2), normalized 0-1
    handedness: str  # "Left" or "Right"
    confidence: float  # 0-1
    present: bool  # Whether hand detected
```

### FaceDetection

```python
@dataclass
class FaceDetection:
    landmarks: np.ndarray  # (468 x 2), normalized 0-1
    head_euler_angles: Tuple[float, float, float]  # (pitch, yaw, roll)
    confidence: float  # 0-1
    present: bool
```

### SwipeGesture

```python
@dataclass
class SwipeGesture:
    direction: SwipeDirection  # LEFT or RIGHT
    displacement: float  # pixels
    duration: float  # seconds
    velocity: float  # px/frame
    is_confirmed: bool
    confidence: float  # 0-1
```

### NumberGesture

```python
@dataclass
class NumberGesture:
    number: int  # 0-5
    is_stable: bool
    confidence: float  # 0-1
    frame_count: int
```

### ClapGesture

```python
@dataclass
class ClapGesture:
    state: ClapState  # Current detection state
    clap_count: int  # 1 or 2
    is_confirmed: bool
    distance: float  # Normalized 0-1
    confidence: float  # 0-1
```

### HeadTiltGesture

```python
@dataclass
class HeadTiltGesture:
    scroll_direction: ScrollDirection  # UP or DOWN
    head_angle: float  # degrees from neutral
    scroll_speed: float  # px/frame
    is_active: bool
    confidence: float  # 0-1
```

### GazeVerification

```python
@dataclass
class GazeVerification:
    state: GazeState  # LOOKING_AT_SCREEN, LOOKING_AWAY, UNKNOWN
    gaze_angle: float  # degrees
    horizontal_angle: float  # degrees
    vertical_angle: float  # degrees
    confidence: float  # 0-1
    is_valid: bool
```

---

## System Integration Example

```python
# Pseudo-code for full integration
from src.detectors.hand import HandDetector
from src.detectors.face import FaceDetector
from src.detectors.eye_gaze import EyeGazeValidator
from src.gestures.swipe import SwipeDetector
from src.gestures.number import NumberDetector
from src.gestures.clap import ClapDetector
from src.gestures.head_tilt import HeadTiltDetector

# Initialize all detectors
hand_detector = HandDetector()
face_detector = FaceDetector()
gaze_validator = EyeGazeValidator()
swipe_detector = SwipeDetector()
number_detector = NumberDetector()
clap_detector = ClapDetector()
head_tilt_detector = HeadTiltDetector()

# Calibration
face_detector.calibrate_neutral_head_position(first_frame_landmarks)
head_tilt_detector.calibrate_neutral_position(first_pitch_angle)

# Main loop
while True:
    frame = camera.read()
    
    # Detection
    hand_detections = hand_detector.detect(frame)
    face_detection = face_detector.detect(frame)
    
    # Eye gaze validation (first check!)
    gaze = gaze_validator.validate_from_head_angles(
        face_detection.head_euler_angles[0],
        face_detection.head_euler_angles[1]
    )
    
    if not gaze.is_valid:
        # Skip gesture processing
        continue
    
    # Process hand gestures
    for hand in hand_detections:
        if hand.present:
            # Swipe
            swipe = swipe_detector.add_hand_position(
                hand.landmarks[8][0]  # index finger tip
            )
            if swipe.is_confirmed:
                handle_swipe(swipe.direction)
            
            # Number selection
            number = number_detector.add_finger_count(
                detector.get_finger_count(hand.landmarks)
            )
            if number.is_stable:
                handle_tab_switch(number.number)
    
    # Clap detection (both hands)
    if len(hand_detections) == 2:
        distance = hand_detector.get_hand_distance(
            hand_detections[0].landmarks,
            hand_detections[1].landmarks
        )
        clap = clap_detector.add_hand_distance(distance)
        if clap.is_confirmed:
            handle_clap(clap.clap_count)
    
    # Head tilt (scrolling)
    if face_detection.present:
        pitch = face_detection.head_euler_angles[0]
        head_tilt = head_tilt_detector.add_head_angle(pitch)
        if head_tilt.is_active:
            handle_scroll(head_tilt.scroll_direction, head_tilt.scroll_speed)
```

