# Hand-Controlled Screen Agent - Setup & Usage Guide

## What Changed?

You now have a **completely new hand control system** that:

✅ Works with hands at ANY angle (not just flat/lowered)  
✅ Detects pointing, pinching, and palm gestures  
✅ Controls your cursor and clicks directly  
✅ Works with natural finger movements  
✅ Real-time screen interaction  

## Installation

### 1. Install Required Package

```bash
pip install pynput
```

This enables mouse and keyboard control.

### 2. Verify Setup

```bash
python src/agent.py
```

You should see:
```
🤖 Initializing Hand Gesture Control Agent...
✓ Hand detectors initialized
✓ Camera initialized

📋 GESTURE CONTROLS:
  • POINT (index up): Move cursor
  • PINCH (thumb + index): Click
  • OPEN PALM: Activate mode
  • TWO FINGERS UP: Scroll up
  • SWIPE LEFT/RIGHT: Change tabs

🎯 Press SPACE to toggle, 'd' for debug, 'q' to quit
```

## Controls

### Activation
- Press **SPACE** to toggle agent ON/OFF
- Status shows in top-right: 🟢 ACTIVE or 🔴 INACTIVE

### Cursor Control
1. **Point with index finger** (other fingers down)
2. Your cursor follows the index finger tip
3. Move hand naturally - it works at any angle!

### Click
1. Make a **pinch gesture** (thumb + index together)
2. System automatically clicks
3. Works like a mouse click

### Scroll
1. Hold up **two fingers** (index + middle extended)
2. Move hand up to scroll up
3. Move hand down to scroll down

### Palm Recognition
- **Open palm** (all fingers extended) is detected
- Can be used for special actions

## How It Works

### Detection Workflow
```
Camera Feed
    ↓
ImprovedHandDetector
    ↓
Extracts:
  - Hand position
  - Finger positions
  - Gesture states (pointing/pinching/flat)
  - Movement velocity
    ↓
Screen Control
  - Cursor movement
  - Clicks
  - Scroll events
```

### Key Improvements Over Old System

| Feature | Old | New |
|---------|-----|-----|
| **Hand Angle** | Must be flat | Any angle ✅ |
| **Movement** | Restricted | Natural ✅ |
| **Tracking** | Loses easily | Robust ✅ |
| **Control** | Gesture-only | Direct mouse ✅ |
| **Responsiveness** | Delayed | Real-time ✅ |

## Testing

### Test 1: Hand Detection
1. Run: `python src/agent.py`
2. Press 'd' for debug
3. Show hand to camera
4. You should see hand skeleton
5. No jitter or flickering

### Test 2: Cursor Control
1. Press SPACE to activate
2. Point with index finger
3. Move your hand around
4. Cursor should follow smoothly
5. Try at different angles!

### Test 3: Click
1. System is active (🟢)
2. Make a pinch (thumb + index close)
3. Click should register
4. Try clicking buttons in browser

### Test 4: Debug Mode
1. Press 'd'
2. See real-time info:
   - Hands detected
   - Hand position
   - Gesture states

## Configuration

Edit `src/config.py` to adjust:

```python
DETECTION = {
    "hand_detection_confidence": 0.8,   # 0-1, higher = stricter
    "hand_tracking_confidence": 0.8,    # 0-1, higher = stricter
}
```

## Common Issues & Fixes

### Issue: Cursor jumps around
**Fix**: Increase detection confidence
```python
DETECTION["hand_detection_confidence"] = 0.85
```

### Issue: Can't make pinch gesture
**Fix**: Hold thumb and index tip very close (touching)
- Should be <5cm distance (normalized 0.05)

### Issue: Pointing not detected
**Fix**: Make sure other fingers are clearly down
- Index finger should be notably above other fingers

### Issue: Pynput not found
**Fix**: Install it
```bash
pip install pynput
```

## Gesture Reference

### Pointing
```
     👆 Index up
 👇  (others down)
```

### Pinching
```
    Thumb & Index
    very close
    (touching)
```

### Palm Open
```
    ✋ All fingers
       extended
```

## Screen Coordinates

The system maps hand position to screen:
- Hand X position (0-1) → Cursor X (0-1920)
- Hand Y position (0-1) → Cursor Y (0-1080)
- Camera is mirrored (X flipped)

If cursor moves opposite to your hand:
- Check the `normalize_to_screen()` function in agent.py
- Adjust width/height constants if needed

## Performance Tips

1. **Good Lighting**: Better hand detection
2. **Clean Background**: Fewer false detections
3. **1-2 feet from camera**: Optimal distance
4. **Hand in frame**: Keep hand visible
5. **Smooth movements**: Avoid jerky motions

## Real-World Use Cases

✅ **Browser Control**: Navigate websites, scroll, click
✅ **Presentation Control**: Point at slides, advance
✅ **Desktop Control**: Move files, open programs
✅ **Gaming**: Gesture-based game control
✅ **Accessibility**: Hands-free mouse alternative

## Switching Back to Old System

If you want the old gesture system:
```bash
python src/main.py
```

The old system is still available for comparison.

## Next Steps

1. Install pynput: `pip install pynput`
2. Run the agent: `python src/agent.py`
3. Test each gesture
4. Adjust config if needed
5. Enjoy hands-free control! 🎉

## Advanced: Gesture Customization

Each gesture has a threshold you can adjust in `ImprovedHandDetector`:

```python
PINCH_THRESHOLD = 0.05        # Thumb-index distance for pinch
POINT_INDEX_THRESHOLD = 0.03  # Index extension distance
PALM_THRESHOLD = 0.08         # Palm openness
```

Decrease thresholds = easier to trigger  
Increase thresholds = harder to trigger

## Troubleshooting

Check the debug output (press 'd'):
- `Hands: 0` = Detection not working
- `Hands: 1` = Hand detected
- Gestures shown in real-time

Look at the hand skeleton:
- Should appear only when hand visible
- Should not flicker
- Should track smoothly

## Support

If something isn't working:
1. Check `DETECTION` config values
2. Test with debug mode on
3. Verify hand is in frame
4. Try adjusting gesture thresholds
5. Check console for error messages

---

**Status**: Ready to use! 🚀

Install pynput and run `python src/agent.py` to start controlling your screen with your hands!
