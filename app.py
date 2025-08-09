import asyncio
from evdev import InputDevice, UInput, ecodes
import os
import json

# Load config file
with open("config.json","r") as f:
    config = json.load(f)

# Set config constants for joystick
joystick_cfg = config["joystick"]
AXIS_X = getattr(ecodes, joystick_cfg["x_axis"])
AXIS_Y = getattr(ecodes, joystick_cfg["y_axis"])
CENTER = joystick_cfg["center"]
DEADZONE = joystick_cfg["deadzone"]
SENSITIVITY = joystick_cfg["sensitivity"]
POLL_INTERVAL = joystick_cfg["poll_interval"]
INVERT_Y = joystick_cfg.get("invert_y", False) 

# Set config constants for throttle
throttle_cfg = config["throttle"]
AXIS_Z = getattr(ecodes, throttle_cfg["axis"])
INCREASE_KEY = getattr(ecodes, throttle_cfg["increase_key"])
DECREASE_KEY = getattr(ecodes, throttle_cfg["decrease_key"])
THROTTLE_CHANGE_THRESHOLD = throttle_cfg["change_threshold"]
PRESS_DURATION_MULTIPLIER = throttle_cfg["press_duration_multiplier"]
MAX_THRESHOLD = throttle_cfg.get("max_threshold", 950)
MIN_THRESHOLD = throttle_cfg.get("min_threshold", 50)

# Set config constants for rudder
rudder_cfg = config.get("rudder", {})
AXIS_RUDDER = getattr(ecodes, rudder_cfg.get("axis", "ABS_RZ"))
LEFT_KEY = getattr(ecodes, rudder_cfg.get("left_key", "KEY_Q"))
RIGHT_KEY = getattr(ecodes, rudder_cfg.get("right_key", "KEY_E"))
RUDDER_DEADZONE = rudder_cfg.get("deadzone", 100)
RUDDER_CHANGE_THRESHOLD = rudder_cfg.get("change_threshold", 20)
RUDDER_PRESS_DURATION_MULTIPLIER = rudder_cfg.get("press_duration_multiplier", 0.01)


TOGGLE_KEY = getattr(ecodes, config.get("toggle_key", "BTN_TRIGGER_HAPPY15"))

enabled = False  # Start enabled

# Check if we need to invert y movement
modiferY = 1
if INVERT_Y:
    modiferY = -modiferY

# Finds joystick wiht by-id to get event id
def find_joystick_by_symlink():
    base = "/dev/input/by-id/"
    for fname in os.listdir(base):
        if "X52_Professional" in fname and "event-joystick" in fname:
            path = os.path.realpath(os.path.join(base, fname))
            print(f"Found joystick via symlink: {path}")
            return InputDevice(path)
    raise RuntimeError("Joystick not found!")

gamepad = find_joystick_by_symlink()

# Uinput set up
capabilities = {
    ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y],
    ecodes.EV_KEY: [
        ecodes.BTN_LEFT, ecodes.BTN_RIGHT,  
        INCREASE_KEY, DECREASE_KEY,
        LEFT_KEY, RIGHT_KEY
    ],
}

ui = UInput(capabilities, name="X52 Virtual Mouse + Throttle") 

# Store axis state
axis_state = {
    AXIS_X: CENTER,
    AXIS_Y: CENTER,
    AXIS_Z: 128,
    AXIS_RUDDER: CENTER
}

async def reader():
    """Reads input events and updates axis state."""
    global enabled
    async for event in gamepad.async_read_loop():
        if event.type == ecodes.EV_KEY and event.code == TOGGLE_KEY and event.value == 1:
            enabled = not enabled
            print(f"Input enabled: {enabled}")

        if not enabled:
            continue  # Skip processing other events when disabled

        if event.type == ecodes.EV_ABS and event.code in axis_state:
            axis_state[event.code] = event.value

async def mover():
    """Moves the mouse continuously based on axis state."""
    while True:
        if not enabled:
            await asyncio.sleep(POLL_INTERVAL)
            continue

        dx = axis_state[AXIS_X] - CENTER
        dy = axis_state[AXIS_Y] - CENTER

        if abs(dx) > DEADZONE:
            ui.write(ecodes.EV_REL, ecodes.REL_X, int(dx * SENSITIVITY)) 
        if abs(dy) > DEADZONE:
            ui.write(ecodes.EV_REL, ecodes.REL_Y, int(dy * SENSITIVITY * modiferY))

        ui.syn()
        await asyncio.sleep(POLL_INTERVAL)

#Throttle Range 0-255
last_throttle_value = 128
last_throttle_zone = None  # "max", "min", "middle"  

async def throttle_handler():
    global last_throttle_value, last_throttle_zone

    while True:
        if not enabled:
            await asyncio.sleep(POLL_INTERVAL)
            continue

        # Get current throttle value
        raw_value = axis_state[AXIS_Z]

        # inversion 
        if throttle_cfg.get("invert", True):  # default True since many throttles are reversed
            current_value = 255 - raw_value
        else:
            current_value = raw_value

        dz = current_value - last_throttle_value

        # Zone detection
        if current_value >= MAX_THRESHOLD:
            zone = "max"
        elif current_value <= MIN_THRESHOLD:
            zone = "min"
        else:
            zone = "middle"

        if zone != last_throttle_zone:
            # Release any keys before changing zone
            ui.write(ecodes.EV_KEY, INCREASE_KEY, 0)
            ui.write(ecodes.EV_KEY, DECREASE_KEY, 0)
            ui.syn()

            if zone == "max":
                print(f"Throttle at MAX ({current_value}) - holding increase key")
                ui.write(ecodes.EV_KEY, INCREASE_KEY, 1)
                ui.syn()
            elif zone == "min":
                print(f"Throttle at MIN ({current_value}) - holding decrease key")
                ui.write(ecodes.EV_KEY, DECREASE_KEY, 1)
                ui.syn()

            last_throttle_zone = zone

        elif zone == "middle":
            # In middle zone tap proportionally if change is big enough
            ui.write(ecodes.EV_KEY, INCREASE_KEY, 0)
            ui.write(ecodes.EV_KEY, DECREASE_KEY, 0) 
            if abs(dz) > THROTTLE_CHANGE_THRESHOLD:
                if dz > 0:
                    duration = dz * PRESS_DURATION_MULTIPLIER
                    print(f"Increasing Throttle ({duration:.2f}s)")
                    ui.write(ecodes.EV_KEY, INCREASE_KEY, 1)
                    ui.syn()
                    await asyncio.sleep(duration)
                    ui.write(ecodes.EV_KEY, INCREASE_KEY, 0)
                    ui.syn()
                else:
                    duration = -dz * PRESS_DURATION_MULTIPLIER
                    print(f"Decreasing Throttle ({duration:.2f}s)")
                    ui.write(ecodes.EV_KEY, DECREASE_KEY, 1)
                    ui.syn()
                    await asyncio.sleep(duration)
                    ui.write(ecodes.EV_KEY, DECREASE_KEY, 0)
                    ui.syn()

        last_throttle_value = current_value
        await asyncio.sleep(POLL_INTERVAL)


last_rudder_value = CENTER  
rudder_active = False

last_rudder_direction = 0  # -1 = left, 0 = center, 1 = right

async def rudder_handler():
    global last_rudder_direction
    while True:
        if not enabled:
            
            await asyncio.sleep(POLL_INTERVAL)
            continue

        val = axis_state.get(AXIS_RUDDER, CENTER)  # Use CENTER if set, else 0
        delta = val - CENTER

        if delta < -RUDDER_DEADZONE:
            # Move left hold Q
            if last_rudder_direction != -1:
                # Release previous if any
                if last_rudder_direction == 1:
                    ui.write(ecodes.EV_KEY, RIGHT_KEY, 0)
                ui.write(ecodes.EV_KEY, LEFT_KEY, 1)
                ui.syn()
                last_rudder_direction = -1
        elif delta > RUDDER_DEADZONE:
            # Move right hold E
            if last_rudder_direction != 1:
                if last_rudder_direction == -1:
                    ui.write(ecodes.EV_KEY, LEFT_KEY, 0)
                ui.write(ecodes.EV_KEY, RIGHT_KEY, 1)
                ui.syn()
                last_rudder_direction = 1
        else:
            # Center release both keys if any held
            if last_rudder_direction != 0:
                ui.write(ecodes.EV_KEY, RIGHT_KEY, 0)
                ui.write(ecodes.EV_KEY, LEFT_KEY, 0)
            ui.syn()
            last_rudder_direction = 0

        await asyncio.sleep(POLL_INTERVAL)

async def main():
    await asyncio.gather(reader(), mover(), throttle_handler(), rudder_handler())

asyncio.run(main())
