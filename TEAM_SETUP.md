# Team Setup Guide - Sideswipe

Welcome to Sideswipe! This guide will help you get started quickly.

## What is Sideswipe?

A hand gesture control system for macOS that lets you:
- 👏 Clap to toggle on/off
- 🔄 Swipe left/right to switch browser tabs
- 📜 Pinch and move up/down to scroll webpages
- All at 30 FPS with real-time hand tracking

## One-Minute Setup

### Step 1: Extract and Navigate
```bash
unzip sideswipe.zip
cd sideswipe
```

### Step 2: Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run
```bash
python3 src/agent.py
```

That's it! You should see the hand tracking window open.

## Using Sideswipe

### Quick Controls
1. **Start**: Run `python3 src/agent.py`
2. **Activate**: Clap twice 👏👏
3. **Swipe**: Move your hand left/right (1 second cooldown between swipes)
4. **Scroll**: Pinch thumb+index together and move up/down
5. **Quit**: Press 'q' in the window

### What You'll See
```
🤖 Initializing Hand Tracker...
✓ Hand detector initialized
✓ macOS control initialized
✓ Camera initialized (1280x720)

🎥 Hand tracking started...
FPS: 30.0 | Hands: 1 | Status: 🔴 INACTIVE
```

- **🔴 INACTIVE** = System is off (clap to activate)
- **🟢 ACTIVE** = System is on and detecting gestures
- **FPS** = Frames per second (should be ~30)
- **Hands** = Number of hands detected

## Development

### Project Structure
```
src/
├── agent.py              # Main gesture tracking (this is what you run!)
├── config.py            # Settings and thresholds
├── detectors/           # Hand/face detection
├── gestures/            # Gesture recognition
├── system_control/      # macOS automation
└── utils/               # Helper functions
```

### Key Files for Customization
- `src/config.py` - Adjust detection sensitivity and thresholds
- `src/agent.py` - Main loop and gesture handlers
- `src/system_control/browser.py` - Tab/window switching logic

## Common Issues

### "Hand tracking lost easily"
- Check lighting - hand needs good contrast
- Keep hands within frame
- Face camera directly

### "Scrolling doesn't work"
- Make sure you're pinching (thumb touching index)
- Try Page Up/Down keys manually to verify they work
- Focus the Chrome window on a webpage

### "Swiping doesn't trigger"
- Use larger hand movements initially
- Make sure you're NOT pinching
- Swipe should be mostly horizontal

### "ModuleNotFoundError"
```bash
# Reactivate virtual environment
source .venv/bin/activate
# Then run again
python3 src/agent.py
```

## Customization Examples

### Change swipe sensitivity
Edit `src/agent.py`, find `detect_swipe()` method:
```python
# Lower threshold = more sensitive
self.swipe_threshold = 0.1  # Change to 0.08 for more sensitivity
```

### Change scroll amount
Edit `src/agent.py`, find where `scroll()` is called:
```python
self.controller.scroll(scroll_dir, 5)  # Change 5 to 10 for more scrolling
```

### Change clap sensitivity
Edit `src/agent.py`, find `detect_clap()` method:
```python
self.clap_threshold = 0.15  # Lower = more sensitive
```

## Team Collaboration

### Pushing Changes
```bash
git add .
git commit -m "Description of changes"
git push origin main
```

### Pulling Latest
```bash
git pull origin main
```

### Creating New Branch
```bash
git checkout -b feature/my-feature
# Make changes
git add .
git commit -m "Added new feature"
git push origin feature/my-feature
```

## Architecture Overview

```
Hand Detection (MediaPipe)
    ↓
Hand Landmarks (21 points per hand)
    ↓
Gesture Recognition (Clap, Swipe, Pinch)
    ↓
macOS Control (AppleScript/Keyboard Events)
    ↓
Browser Actions (Tab Switch, Scroll)
```

## Performance Tips

- Best FPS on M1/M2/M4 Macs
- Ensure good lighting
- Close other heavy apps
- Use built-in camera when possible

## Support

If you encounter issues:
1. Check the terminal output for error messages
2. Try the troubleshooting section above
3. Review `config.py` for threshold values
4. Check that your Python version is 3.9+

## Next Steps

1. Get the system running smoothly on your machine
2. Explore the gesture detection in `src/agent.py`
3. Try customizing thresholds in `config.py`
4. Contribute improvements back to the team!

---

**Questions?** Check the main README.md or ask your team lead!

Happy gesturing! 🖐️✨
