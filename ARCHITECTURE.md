# Sideswipe Architecture Diagrams

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    SIDESWIPE SYSTEM                         │
│              Gesture-Based Window Control                   │
└─────────────────────────────────────────────────────────────┘

                           ┌──────────┐
                           │  CAMERA  │
                           └────┬─────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
              ┌─────▼──────┐         ┌─────▼──────┐
              │    HAND    │         │    FACE    │
              │ DETECTION  │         │ DETECTION  │
              └─────┬──────┘         └─────┬──────┘
                    │                       │
         ┌──────────┴───────────────────────┴──────────┐
         │                                             │
    ┌────▼──────────┐                    ┌────────────▼────┐
    │  LANDMARKS    │                    │ HEAD ANGLES &   │
    │  (21 points)  │                    │ EYE POSITION    │
    └────┬──────────┘                    └────────┬────────┘
         │                                        │
    ┌────┴──────────────────────┬─────────────────┴─────┐
    │                           │                       │
    │         ┌─────────────────▼─────────────────┐     │
    │         │   EYE GAZE VALIDATION (Safety)    │     │
    │         │  ┌─────────────────────────────┐  │     │
    │         │  │ Are eyes on screen?         │  │     │
    │         │  │ BLOCK if NO ❌              │  │     │
    │         │  │ ALLOW if YES ✓              │  │     │
    │         │  └─────────────────────────────┘  │     │
    │         └─────────────────┬─────────────────┘     │
    │                           │                       │
    │    ┌──────────────────────┴──────────────────┐   │
    │    │                                         │   │
    │    │         GESTURE PROCESSING              │   │
    │    │                                         │   │
    │    │  ┌──────────┬──────────┐               │   │
    │    │  │  SWIPE   │  NUMBER  │               │   │
    │    │  │  ← / →   │  1-5     │               │   │
    │    │  └──────────┴──────────┘               │   │
    │    │                                         │   │
    │    │  ┌──────────┬──────────┐               │   │
    │    │  │  CLAP    │ HEAD TLT │               │   │
    │    │  │  👏👏    │  ↑ / ↓   │               │   │
    │    │  └──────────┴──────────┘               │   │
    │    │                                         │   │
    │    └─────────────────┬──────────────────────┘   │
    │                      │                          │
    └──────────────────────┼──────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │   SYSTEM    │
                    │  RESPONSE   │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌─────▼──────┐    ┌────▼────┐
    │ WINDOWS │      │ TABS/APPS  │    │ SCROLL  │
    │ Navigation     │ Switching  │    │ Content │
    └──────────┘      └────────────┘    └─────────┘
```

---

## Detection Pipeline (Detailed)

```
┌─────────────────────────────────────────────────────────┐
│               INPUT LAYER                               │
│          (Video Frame Processing)                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Frame from Camera (1280×720 @ 30 FPS)                │
│         │                                              │
│         ├─► RGB Conversion                            │
│         │                                              │
│         ├─► MediaPipe Hand Detection                  │
│         │   │                                          │
│         │   └─► 21 Hand Landmarks (per hand)          │
│         │       • Wrist (0)                            │
│         │       • Fingers (4, 8, 12, 16, 20 tips)    │
│         │       • Knuckles (3, 7, 11, 15, 19)        │
│         │                                              │
│         └─► MediaPipe Face Detection                  │
│             │                                          │
│             └─► 468 Face Landmarks                    │
│                 • Eyes, nose, mouth                    │
│                 • Head orientation (Euler angles)     │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│          PROCESSING LAYER                               │
│         (Gesture Recognition)                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Hand Landmarks (21 × 2 normalized)                    │
│    │                                                   │
│    ├──► SWIPE DETECTOR                                │
│    │     Input: Index Finger X-position              │
│    │     Logic: Track movement, confirm direction    │
│    │     Output: LEFT/RIGHT + confidence             │
│    │                                                   │
│    ├──► NUMBER DETECTOR                              │
│    │     Input: All finger positions                 │
│    │     Logic: Count extended, average frames       │
│    │     Output: 1-5 + confidence                    │
│    │                                                   │
│    └──► CLAP DETECTOR                                │
│          Input: Hand distance (2 hands)              │
│          Logic: Detect velocity + contact           │
│          Output: 1/2 claps + confidence             │
│                                                       │
│  Face Landmarks + Head Angles (468 + Euler)         │
│    │                                                   │
│    ├──► EYE GAZE VALIDATOR ← BLOCKS ALL GESTURES    │
│    │     Input: Head angle or eye position          │
│    │     Logic: Angle from screen center            │
│    │     Output: VALID/INVALID (5-frame buffer)     │
│    │                                                   │
│    └──► HEAD TILT DETECTOR                          │
│          Input: Head pitch angle (Euler Y)          │
│          Logic: Deviation from neutral              │
│          Output: UP/DOWN + scroll speed             │
│                                                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│           OUTPUT LAYER                                  │
│        (System Response)                                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Gesture Events                                        │
│    │                                                   │
│    ├──► SWIPE LEFT         ──► Window Previous       │
│    │                                                   │
│    ├──► SWIPE RIGHT        ──► Window Next           │
│    │                                                   │
│    ├──► FINGER COUNT (1-5) ──► Switch Tab            │
│    │                                                   │
│    ├──► SINGLE CLAP        ──► System OFF            │
│    │                                                   │
│    ├──► DOUBLE CLAP        ──► System ON             │
│    │                                                   │
│    └──► SCROLL (UP/DOWN)   ──► Scroll Content        │
│                                                       │
└─────────────────────────────────────────────────────────┘
```

---

## Gesture State Machines

### Swipe Gesture
```
                    START
                      │
                      ▼
        ┌─────────────────────────┐
        │   IDLE STATE            │
        │ (Waiting for hand)      │
        └────────┬────────────────┘
                 │
        Hand detected? ──NO──► Continue waiting
                 │
                YES
                 │
                 ▼
        ┌─────────────────────────┐
        │  TRACKING STATE         │
        │  (Recording movement)   │
        └────────┬────────────────┘
                 │
         ┌───────┴────────┐
         │                │
      Direction   Confirm 3 frames
      matches?    of same direction?
         │                │
        YES              YES
         │                │
         ▼                ▼
    Update count    Displacement
    ✓ > threshold?
       │
       NO ──────► Reset
       │
       YES
       │
       ▼
    ┌──────────────────────┐
    │  GESTURE DETECTED!   │
    │  LEFT or RIGHT       │
    │  confidence: X%      │
    └──────────────────────┘
```

### Clap Detection State Machine
```
IDLE
  │
  ├─ Hands approaching (velocity < -threshold)
  │  └─► HANDS_APPROACHING
  │      │
  │      ├─ Contact reached (distance < max)
  │      │  └─► HANDS_CONTACT (record clap #1)
  │      │      │
  │      │      ├─ Hands separating (velocity > threshold)
  │      │      │  └─► IDLE (wait for 2nd clap)
  │      │      │      │
  │      │      │      ├─ 2nd clap within 0.8s?
  │      │      │      │  └─► DOUBLE_CLAP ✓✓
  │      │      │      │
  │      │      │      └─ Timeout 1.5s
  │      │      │         └─► SINGLE_CLAP ✓
  │      │      │
  │      │      └─ Timeout (no separation)
  │      │         └─► IDLE
  │      │
  │      └─ Timeout (no contact)
  │         └─► IDLE
  │
  └─ No motion ──► IDLE
```

### Number Selection Stabilization
```
Frame 1: 2 fingers detected
Frame 2: 2 fingers detected
Frame 3: 3 fingers detected  ← Variation
Frame 4: 2 fingers detected
Frame 5: 2 fingers detected
Frame 6: 2 fingers detected
Frame 7: 2 fingers detected
Frame 8: 2 fingers detected
Frame 9: 2 fingers detected
Frame 10: 2 fingers detected

Buffer: [2,2,3,2,2,2,2,2,2,2]
Most common: 2 (90% of frames)
Confidence: 0.9 (> 0.8 threshold)

Result: GESTURE DETECTED - Switch to Tab 2 ✓
```

---

## Data Flow Example (Swipe Detection)

```
Frame Input
    │
    ▼
HandDetector.detect(frame)
    │
    ├─ results.multi_hand_landmarks[0]
    │   [normalized x,y for 21 points]
    │
    ▼
Extract index finger tip (landmark[8])
    │
    ├─ x = 0.45 (45% across frame)
    │ y = 0.30 (30% down frame)
    │
    ▼
SwipeDetector.add_hand_position(x=0.45)
    │
    ├─ Start tracking:
    │   start_x = 0.45
    │   current_x = 0.45
    │   displacement = 0
    │   direction = NONE
    │
    ▼
Frame 2: x=0.50
    │
    ├─ displacement = 0.50 - 0.45 = 0.05
    ├─ direction = RIGHT (positive)
    ├─ confidence_count = 1
    │
    ▼
Frame 3: x=0.56
    │
    ├─ displacement = 0.56 - 0.45 = 0.11 (11%)
    ├─ direction = RIGHT (still)
    ├─ confidence_count = 2
    │
    ▼
Frame 4: x=0.62
    │
    ├─ displacement = 0.62 - 0.45 = 0.17 (17%)
    ├─ direction = RIGHT (still)
    ├─ confidence_count = 3 ✓
    │
    ├─ Check thresholds:
    │   ✓ abs_displacement (0.17) >= min (0.1)
    │   ✓ duration (0.1s) <= time_window (2s)
    │   ✓ confirmation_frames (3) met
    │   ✓ cooldown (0) = no cooldown
    │
    ▼
Return SwipeGesture(
    direction=RIGHT,
    displacement=0.17,
    duration=0.1,
    velocity=0.056,
    is_confirmed=TRUE,
    confidence=0.85
)
    │
    ▼
GESTURE DETECTED - Switch to next window!
```

---

## Multi-Gesture Simultaneous Processing

```
SINGLE FRAME INPUT

    ↓

    ├─► Hand Detection
    │   ├─► Hand 1: [21 landmarks]
    │   └─► Hand 2: [21 landmarks]
    │
    └─► Face Detection
        └─► [468 landmarks] + head angles

    ↓

    ├─► Swipe Detector (Hand 1 X)      → No gesture
    │
    ├─► Number Detector (Finger count) → Tab 2 stable ✓
    │
    ├─► Clap Detector (2 hand distance) → No contact
    │
    ├─► Head Tilt Detector (Head pitch) → No threshold cross
    │
    └─► Eye Gaze Validator              → VALID ✓

    ↓

PRIORITY EVALUATION (from config):
    1. Eye Gaze          → VALID ✓
    2. Clap              → None
    3. Number            → Tab 2 ✓ TAKE THIS
    4. Swipe             → None
    5. Head Tilt         → None

    ↓

EVENT: Switch to Tab 2 (confidence: 0.92)
```

---

## Eye Gaze Validation Buffer

```
Frame 1: gaze_angle = 15° (valid, < 30°)
         count = 1
         state = UNKNOWN

Frame 2: gaze_angle = 12° (valid)
         count = 2
         state = UNKNOWN

Frame 3: gaze_angle = 18° (valid)
         count = 3
         state = UNKNOWN

Frame 4: gaze_angle = 14° (valid)
         count = 4
         state = UNKNOWN

Frame 5: gaze_angle = 16° (valid)
         count = 5 ✓ (threshold met)
         state = LOOKING_AT_SCREEN

Frames 6+: All gaze valid
           state = LOOKING_AT_SCREEN ✓
           ──► ALL GESTURES ENABLED

If any frame: gaze_angle > 30°
              ──► Decrement counter
              ──► If count = 0
                  ──► state = LOOKING_AWAY
                  ──► ALL GESTURES BLOCKED
```

---

## Configuration Adjustment Impact

```
ORIGINAL CONFIG               ADJUSTED CONFIG

SWIPE:                       SWIPE:
  min_x_movement: 100          min_x_movement: 150
                               (LESS SENSITIVE)
Result: Easy to swipe        Result: Harder to accidentally swipe


NUMBER:                      NUMBER:
  confidence_threshold: 0.8    confidence_threshold: 0.95
                               (MORE STRICT)
Result: Tab switches easily  Result: Must hold fingers longer


HEAD_TILT:                   HEAD_TILT:
  angle_threshold: 15          angle_threshold: 10
                               (MORE SENSITIVE)
Result: Need 15° tilt        Result: Only 10° needed
to scroll
```

---

## Real-Time Processing Loop (Target 30 FPS)

```
┌──────────────────────────────┐
│  FRAME READY (~33ms cycle)   │
└──────────────┬───────────────┘
               │
        ~3ms  ▼
    ┌─────────────────┐
    │ Read frame from │
    │ camera buffer   │
    └────────┬────────┘
             │
        ~15ms ▼
    ┌─────────────────────┐
    │ MediaPipe detection │
    │ (hand + face)       │
    └────────┬────────────┘
             │
        ~8ms ▼
    ┌─────────────────────┐
    │ Extract landmarks & │
    │ head angles         │
    └────────┬────────────┘
             │
        ~4ms ▼
    ┌─────────────────────┐
    │ Eye gaze validation │
    │ (blocks if invalid) │
    └────────┬────────────┘
             │
        ~2ms ▼
    ┌─────────────────────┐
    │ Gesture processing  │
    │ (swipe, number,     │
    │  clap, head tilt)   │
    └────────┬────────────┘
             │
        ~1ms ▼
    ┌─────────────────────┐
    │ Emit events if any  │
    │ gestures detected   │
    └────────┬────────────┘
             │
        ~0ms ▼ (idle time)
    ┌──────────────────────┐
    │ READY FOR NEXT FRAME │
    └──────────────────────┘

Total: ~33ms cycle
Status: ✓ Real-time (within budget)
```

This architecture ensures reliable, low-latency gesture detection!
