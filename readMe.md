# X52 Pro Joystick to Mouse & Throttle Mapper

A Linux utility that maps Saitek X52 Pro HOTAS joystick axis inputs to mouse movement and throttle controls to keyboard keys for games that do not natively support joysticks.

---

## Features

- Translates joystick X and Y axis movement to relative mouse movement.
- Maps throttle axis to simulate throttle increase/decrease via keyboard keys.
- Supports rudder axis mapped to keyboard keys (e.g., Q and E) with smooth hold/release behavior.
- Toggle input processing on/off with a dedicated joystick button.
- Configuration via JSON file for easy customization of axis mapping, sensitivity, deadzones, and key bindings.
- Automatically detects your joystick device on Linux.

---

## Requirements

- Linux (tested on Linux Mint and Ubuntu)
- Python 3.8 or higher
- Python packages:
  - `evdev`
  - `asyncio` (built-in)
- `uinput` kernel module enabled (usually enabled by default on most distros)
- Permissions to read `/dev/input/event*` devices and write to uinput device (`/dev/uinput`)

---

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/x52-mouse-and-throttle.git
cd x52-mouse-and-throttle
```

### Install Python dependencies


It's recommended to use a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you don’t have a requirements.txt, install manually:
```bash
pip install evdev
```
### Enable permissions

You may need to run the program as root or give your user permission to access input devices:
```bash
sudo usermod -aG input $USER
```
Log out and back in after this.

Alternatively, run with sudo:
```bash
sudo python3 app.py
```
### Usage

1. Edit config.json to customize your joystick axes, throttle keys, sensitivities, and deadzones.

2. Run the program
```bash
python3 app.py
```
3. Toggle input processing

Press the configured throttle button (BTN_TRIGGER_HAPPY15 by default) to enable or disable input mapping.

### Configuration (config.json)

Example structure:
```json
{
  "joystick": {
    "x_axis": "ABS_X",
    "y_axis": "ABS_Y",
    "center": 511,
    "deadzone": 100,
    "sensitivity": 0.01,
    "poll_interval": 0.01,
    "invert_y": true
  },
  "throttle": {
    "axis": "ABS_Z",
    "increase_key": "KEY_PAGEUP",
    "decrease_key": "KEY_PAGEDOWN",
    "change_threshold": 5,
    "press_duration_multiplier": 0.005,
    "min_threshold": 50,
    "max_threshold": 970
  },
  "rudder": {
    "axis": "ABS_RZ",
    "left_key": "KEY_Q",
    "right_key": "KEY_E",
    "center": 511,
    "deadzone": 50,
    "poll_interval": 0.01
  },
  "toggle_key": "BTN_TRIGGER_HAPPY15"
}
```
Troubleshooting

    Joystick not detected:
    Make sure your joystick is plugged in and identified correctly.
    Check /dev/input/by-id/ and update the device detection logic if needed.

    Permission errors:
    Ensure your user has permission to access input devices or run the script with sudo.

    Throttle or rudder keys stuck:
    Verify key codes in the config match those from evtest.

### License

MIT License
Contributions

Feel free to fork, open issues, and submit pull requests!

### Contact:

Created by Qazzman

GitHub: https://github.com/Qazzman987