#!/usr/bin/env python3
# reads keyboard from evdev, sends to websocket for the browser source.
# input-overlay doesn't work on wayland so this is the workaround.

import asyncio
import json
import sys

try:
    import evdev
    from evdev import ecodes
except ImportError:
    print("install evdev: pip install evdev")
    sys.exit(1)

try:
    import websockets
except ImportError:
    print("install websockets: pip install websockets")
    sys.exit(1)

# libuiohook keycodes, not evdev. arrow keys are 0xE0XX prefixed.
EVDEV_TO_IO = {
    ecodes.KEY_UP:       57416,
    ecodes.KEY_DOWN:     57424,
    ecodes.KEY_LEFT:     57419,
    ecodes.KEY_RIGHT:    57421,
    ecodes.KEY_Z:        44,
    ecodes.KEY_X:        45,
    ecodes.KEY_C:        46,
}

PORT = 16900
connected = set()

async def handler(websocket):
    connected.add(websocket)
    print(f"client connected ({len(connected)} total)", flush=True)
    try:
        async for _ in websocket:
            pass
    finally:
        connected.discard(websocket)
        print(f"client disconnected ({len(connected)} total)", flush=True)

async def broadcast(msg):
    if connected:
        await asyncio.gather(*(ws.send(msg) for ws in connected))

def find_keyboard():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for d in devices:
        name = d.name.lower()
        if 'keyboard' in name and 'consumer' not in name and 'system' not in name and 'mouse' not in name:
            return d
    return None

async def read_events(device):
    loop = asyncio.get_running_loop()
    while True:
        # this blocks the thread but thats fine, run_in_executor handles it
        event = await loop.run_in_executor(None, device.read_one)
        if event is None:
            continue
        if event.type == ecodes.EV_KEY:
            key_event = evdev.categorize(event)
            code = EVDEV_TO_IO.get(key_event.scancode)
            if code is not None:
                is_pressed = key_event.keystate in (key_event.key_down, key_event.key_hold)
                msg = json.dumps({"code": code, "pressed": is_pressed})
                await broadcast(msg)

async def main():
    kbd_path = sys.argv[1] if len(sys.argv) > 1 else None
    if kbd_path:
        device = evdev.InputDevice(kbd_path)
    else:
        device = find_keyboard()

    if not device:
        print("no keyboard found. pass device path:", flush=True)
        print(f"  python3 {sys.argv[0]} /dev/input/event2", flush=True)
        sys.exit(1)

    print(f"reading from: {device.name} ({device.path})", flush=True)
    print(f"websocket: ws://localhost:{PORT}", flush=True)
    print("waiting for connections...", flush=True)

    # run both the ws server and evdev reader at the same time
    ws_server = websockets.serve(handler, "localhost", PORT)
    async with ws_server:
        await read_events(device)

if __name__ == "__main__":
    asyncio.run(main())
