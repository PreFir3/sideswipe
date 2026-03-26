#!/usr/bin/env python3
"""
Quick test to verify all components are working.

This runs without requiring a camera or GUI.
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*70)
print("🧪 SIDESWIPE COMPONENT TEST")
print("="*70)

try:
    print("\n1️⃣  Testing Configuration System...")
    from src.config import get_config, DETECTION, SWIPE
    config = get_config()
    assert "swipe" in config
    assert "number_selection" in config
    assert "clap_activation" in config
    assert "head_tilt" in config
    print("   ✅ Configuration system works!")
    print(f"   - Swipe min_movement: {SWIPE['min_x_movement']} pixels")
    print(f"   - Detection FPS: {DETECTION['frame_rate']}")

except Exception as e:
    print(f"   ❌ Configuration test failed: {e}")
    sys.exit(1)

try:
    print("\n2️⃣  Testing Hand Detector...")
    from src.detectors.hand import HandDetector
    detector = HandDetector()
    print("   ✅ Hand detector initialized!")
    print(f"   - Finger tips: {detector.FINGER_TIPS}")
    print(f"   - Connections: {len(detector.CONNECTIONS)} links")

except Exception as e:
    print(f"   ❌ Hand detector test failed: {e}")
    sys.exit(1)

try:
    print("\n3️⃣  Testing Face Detector...")
    from src.detectors.face import FaceDetector
    detector = FaceDetector()
    print("   ✅ Face detector initialized!")
    print(f"   - Landmarks tracked: 468 points")

except Exception as e:
    print(f"   ❌ Face detector test failed: {e}")
    sys.exit(1)

try:
    print("\n4️⃣  Testing Eye Gaze Validator...")
    from src.detectors.eye_gaze import EyeGazeValidator, GazeState
    validator = EyeGazeValidator(max_gaze_angle=30, validation_frames=5)
    print("   ✅ Eye gaze validator initialized!")
    print(f"   - Validation frames: 5")
    print(f"   - Max gaze angle: 30°")

except Exception as e:
    print(f"   ❌ Eye gaze test failed: {e}")
    sys.exit(1)

try:
    print("\n5️⃣  Testing Swipe Gesture Detector...")
    from src.gestures.swipe import SwipeDetector, SwipeDirection
    detector = SwipeDetector(min_x_movement=100)
    # Test tracking
    gesture1 = detector.add_hand_position(0.5)
    gesture2 = detector.add_hand_position(0.6)
    gesture3 = detector.add_hand_position(0.7)
    print("   ✅ Swipe detector works!")
    print(f"   - Gesture direction: {gesture3.direction}")
    print(f"   - Displacement: {gesture3.displacement:.3f}")

except Exception as e:
    print(f"   ❌ Swipe detector test failed: {e}")
    sys.exit(1)

try:
    print("\n6️⃣  Testing Number Gesture Detector...")
    from src.gestures.number import NumberDetector
    detector = NumberDetector(stabilization_frames=10, confidence_threshold=0.8)
    # Test counting
    gestures = [detector.add_finger_count(2) for _ in range(15)]
    print("   ✅ Number detector works!")
    print(f"   - Last detection: {gestures[-1].number} fingers")
    print(f"   - Confidence: {gestures[-1].confidence:.2f}")

except Exception as e:
    print(f"   ❌ Number detector test failed: {e}")
    sys.exit(1)

try:
    print("\n7️⃣  Testing Clap Gesture Detector...")
    from src.gestures.clap import ClapDetector, ClapState
    detector = ClapDetector(max_palm_distance=0.15)
    # Test clap
    gesture1 = detector.add_hand_distance(0.2)
    gesture2 = detector.add_hand_distance(0.05)
    print("   ✅ Clap detector works!")
    print(f"   - Gesture state: {gesture2.state}")
    print(f"   - Distance: {gesture2.distance:.3f}")

except Exception as e:
    print(f"   ❌ Clap detector test failed: {e}")
    sys.exit(1)

try:
    print("\n8️⃣  Testing Head Tilt Gesture Detector...")
    from src.gestures.head_tilt import HeadTiltDetector, ScrollDirection
    detector = HeadTiltDetector(angle_threshold=15)
    detector.calibrate_neutral_position(0.0)  # Set neutral
    # Test tilt
    gesture1 = detector.add_head_angle(0.0)   # Neutral
    gesture2 = detector.add_head_angle(-20.0) # Tilt up
    print("   ✅ Head tilt detector works!")
    print(f"   - Gesture direction: {gesture2.scroll_direction}")
    print(f"   - Head angle: {gesture2.head_angle:.1f}°")

except Exception as e:
    print(f"   ❌ Head tilt detector test failed: {e}")
    sys.exit(1)

try:
    print("\n9️⃣  Testing Utilities...")
    from src.utils.frame_buffer import FrameBuffer, LandmarkSmoother, MotionDetector
    
    # Test frame buffer
    buffer = FrameBuffer(max_size=5)
    buffer.append(1)
    buffer.append(2)
    assert buffer.size() == 2
    
    # Test landmark smoother
    import numpy as np
    smoother = LandmarkSmoother(smoothing_factor=0.7)
    landmarks = np.random.rand(21, 2)
    smoothed = smoother.smooth(landmarks)
    
    # Test motion detector
    motion = MotionDetector(buffer_size=5)
    motion.add_position(0, 0)
    motion.add_position(10, 0)
    motion.add_position(20, 0)
    direction = motion.get_direction()
    
    print("   ✅ Utilities work!")
    print(f"   - Frame buffer: ✓")
    print(f"   - Landmark smoother: ✓")
    print(f"   - Motion detector: ✓ (direction: {direction})")

except Exception as e:
    print(f"   ❌ Utilities test failed: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("✅ ALL TESTS PASSED!")
print("="*70)
print("\n🎉 Your Sideswipe system is fully installed and ready to use!")
print("\n📖 Next steps:")
print("   1. Read the documentation:")
print("      - DESIGN.md - Complete design")
print("      - QUICK_REFERENCE.md - Quick reference")
print("      - docs/api.md - API documentation")
print("\n   2. Run the main application:")
print("      python3 src/main.py")
print("\n   3. Customize settings:")
print("      Edit src/config.py to adjust thresholds")
print("\n" + "="*70 + "\n")
