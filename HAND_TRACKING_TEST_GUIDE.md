# Hand Tracking Troubleshooting Guide

## Quick Start After Fixes

1. **Run the application**:
   ```bash
   python src/main.py
   ```

2. **Calibrate your head** by looking straight at the camera for 3 seconds

3. **Try each feature** with the gestures described below

## Testing Checklist

### ✅ Hand Detection Test
- [ ] Open debug mode: Press 'd'
- [ ] Look at the camera with your hand visible
- [ ] You should see a hand skeleton drawn on-screen
- [ ] When you hide your hand, the skeleton should disappear quickly (not jitter)

### ✅ OK Hand Gesture (System ON/OFF)
- [ ] Make a clear OK sign: thumb and index finger forming a small circle
- [ ] Keep other fingers extended (spread out)
- [ ] **Hold for about 0.5 seconds** until it toggles
- [ ] You should see "🟢 ON" or "🔴 OFF" status change
- [ ] Should NOT trigger from accidental hand positions

### ✅ Swipe Gesture (Tab Switching)
- [ ] With system ON, make a **clear, deliberate swipe**
- [ ] Move your hand at least **150 pixels** across the camera
- [ ] Complete the swipe in **under 1.5 seconds**
- [ ] System should switch tabs left/right

### ✅ Number Selection (Tab Navigation)
- [ ] With system ON, hold up **2-5 fingers clearly**
- [ ] **Keep your hand steady for ~0.7 seconds** (watch counter increment in debug mode)
- [ ] System should recognize the number
- [ ] Different finger counts should switch between different tabs

### ✅ Finger Scroll (Scrolling)
- [ ] With system ON, extend your middle finger
- [ ] Move it up/down on the camera
- [ ] Should scroll the browser page

## Debug Tips

### Enable Debug Mode
Press 'd' while running to see:
- Hand detection count
- Current head angle
- Gesture state information
- Frame counts for stabilization

### Check MediaPipe Detection
In debug mode, look at the hand skeleton:
- **Appears and disappears smoothly**: ✅ Good detection
- **Flickers/jitters**: ⚠️ Detection confidence might be too low
- **Appears when hand is hidden**: ❌ Sensitivity too high

### Verify Gesture Thresholds

The config file has these key parameters:

**For more sensitive/easier gestures**:
```python
DETECTION["hand_detection_confidence"] = 0.75  # lower = easier to detect
OK_HAND["circle_threshold"] = 0.06             # higher = easier to make OK
SWIPE["min_x_movement"] = 100                  # lower = easier to swipe
```

**For less sensitive/stricter gestures**:
```python
DETECTION["hand_detection_confidence"] = 0.95  # higher = harder to detect
OK_HAND["circle_threshold"] = 0.02             # lower = harder to make OK
SWIPE["min_x_movement"] = 200                  # higher = harder to swipe
```

## Common Issues & Solutions

### Issue: "Hand tracking is still losing the hand"
**Solution**: 
- Increase `DETECTION["hand_tracking_confidence"]` to 0.85+
- Ensure good lighting on your hands
- Keep hands in the camera frame
- Move more slowly

### Issue: "Gestures are triggering accidentally"
**Solution**:
- Increase confirmation frames: `OK_HAND["confirm_frames"]` = 20+
- Increase cooldown: `OK_HAND["cooldown"]` = 1.5
- Increase minimum movement: `SWIPE["min_x_movement"]` = 200+

### Issue: "Can't make the OK hand gesture"
**Solution**:
- Make sure thumb and index tips are **very close** (not just touching)
- Spread your other fingers clearly away from center
- Hold the gesture for longer (system will tell you in debug mode)

### Issue: "Number selection is jittery"
**Solution**:
- Hold your hand **very steady** for the full stabilization time
- Extend fingers completely (not half-curled)
- Keep hand in center of frame

### Issue: "Swipes aren't working"
**Solution**:
- Make **bigger, faster swipes** (at least 150px)
- Complete the swipe **within 1.5 seconds**
- Start with hand visible in frame
- Use your index finger for swiping

## Performance Tips

1. **Good Lighting**: Hand detection works better with good, even lighting
2. **Clean Background**: Simpler backgrounds help with detection
3. **Camera Distance**: Sit about 1-2 feet from camera
4. **Hand Position**: Keep hands in the bottom half of the frame for best results
5. **Movement Speed**: Move deliberately, not too fast

## Configuration File Location

Edit these values in `src/config.py`:

```python
# Hand detection (MediaPipe)
DETECTION = { "hand_detection_confidence": 0.85, ... }

# Gesture detection
SWIPE = { "min_x_movement": 150, ... }
OK_HAND = { "circle_threshold": 0.04, ... }
NUMBER_SELECTION = { "stabilization_frames": 20, ... }
```

## Still Having Issues?

1. Check the terminal output for error messages
2. Enable debug mode (press 'd') to see detailed state info
3. Check hand lighting - are your hands clearly visible?
4. Try each gesture slowly and deliberately first
5. Review the config values and compare with the defaults in this guide

The system should now be much more stable. Give it a few test runs to get used to the new, stricter gesture requirements!
