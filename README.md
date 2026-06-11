# wayland-input-overlay

input-overlay but it actually works on wayland.

[input-overlay](https://github.com/univrsal/input-overlay) uses libuiohook for
input capture. libuiohook doesn't work on wayland. the plugin devs know about
this ([#484](https://github.com/univrsal/input-overlay/issues/484)) and have
done nothing about it. so here we are.

this reads keyboard events straight from evdev (`/dev/input/event*`), shoves
them over a local websocket, and renders them in an OBS browser source using the
same sprite sheets the original plugin uses.

## requirements

- python 3.10+
- `pip install evdev websockets`
- obs studio with browser source support
- a keyboard that shows up in `/dev/input/`

## setup

```bash
# install python deps
pip install evdev websockets

# add yourself to the input group (log out and back in after this)
sudo usermod -aG input $USER

# if you dont want to log out, just chmod the device
sudo chmod 666 /dev/input/event2  # adjust for your keyboard
```

## usage

**1. start the bridge server:**

```bash
cd ~/.config/obs-studio/input-overlay-wayland
python3 server.py /dev/input/event2
```

pass your keyboard device path. find it with:
```bash
for d in /dev/input/event*; do echo "$d: $(cat /sys/class/input/$(basename $d)/device/name)"; done
```

**2. add a browser source in obs:**

- sources -> + -> browser
- check "Local File"
- browse to `~/.config/obs-studio/input-overlay-wayland/overlay.html`
- set width/height to `264x264` (for the arrows+zxc preset)
- uncheck "Shutdown source when not visible"
- click OK

**3. press keys. they light up. done.**

## presets

the default preset shows arrow keys + zxc in a compact layout. to change which
keys are shown, edit `arrows-zxc.json`. each element looks like:

```json
{
    "type": 1,
    "pos": [44, 0],
    "id": "up_arrow",
    "z_level": "0",
    "mapping": [912, 348, 44, 44],
    "code": 57416
}
```

- `pos`: where to draw it on the canvas (x, y)
- `mapping`: where to grab it from the sprite sheet (x, y, w, h)
- `code`: input-overlay keycode (not evdev)

### keycodes

| key | input-overlay code |
|-----|-------------------|
| up | 57416 |
| down | 57424 |
| left | 57419 |
| right | 57421 |
| z | 44 |
| x | 45 |
| c | 46 |

the server maps evdev keycodes to these automatically. if you add new keys to
the preset, you need to add the evdev->input-overlay mapping in `server.py`
(`EVDEV_TO_IO` dict).

## sprite sheet

the sprite sheet (`qwerty-pixel-with-keypad.png`) has gray (unpressed) and blue
(pressed) states. the blue state is exactly **47 pixels** below the gray state.
this is hardcoded in `overlay.html` as `PRESSED_OFFSET`. if you use a different
sprite sheet, you'll need to measure this yourself.

## known issues

- no mouse support (could add it, havent needed it)
- only captures keys that are in the `EVDEV_TO_IO` mapping
- server grabs evdev events which may conflict with other input readers
- the debug overlay in the top-left is ugly but useful for troubleshooting

## files

```
server.py            evdev -> websocket bridge (the actual hard part)
overlay.html         browser source that renders the keys
arrows-zxc.json      preset config (which keys, where to draw them)
qwerty-pixel-with-keypad.png   sprite sheet from input-overlay
```
