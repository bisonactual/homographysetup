# grblHAL Bed Mapping Vision POC

Single-camera proof of concept for mapping camera pixels to real-world X/Y
coordinates on a flat CNC bed plane.

The first milestone is deliberately bench-only:

1. Generate or print a ChArUco board.
2. Prove OpenCV can detect the board.
3. Compute a homography from image pixels to millimetres.
4. Detect ArUco markers and report their X/Y position on the plane.

No CNC motion is involved at this stage.

## Install

From WSL:

```bash
cd ~/git/grblhal-bedmapping
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you are installing on the Raspberry Pi later, use the same commands first.
If OpenCV install is slow on the Pi, we can switch to Debian packages for that
target.

## Test Before The Camera Arrives

Run the synthetic self-test:

```bash
source .venv/bin/activate
python scripts/self_test_synthetic.py
```

Expected result:

```text
PASS synthetic ChArUco homography test
```

It also writes debug images into `generated/`.

## Test A Still Image

You can test detection with any image file containing the generated board:

```bash
source .venv/bin/activate
python scripts/detect_charuco_image.py path/to/photo.png
```

The script prints the detected corner count, a point-fit error, and the board
outer corners in image pixels. It also writes a debug image with detected corners
and a green outline:

```text
generated/detected_charuco_image.png
```

## Generate A Printable Board

```bash
source .venv/bin/activate
python scripts/make_charuco_board.py \
  --preset default-140 \
  --output generated/charuco_140mm.png
```

The default board is 7 x 7 squares, 20 mm per square, with 14 mm markers. That
makes the active board area 140 x 140 mm.

For a single A4 copy-stand test, use the balanced A4 board:

```text
printables/charuco_a4_balanced_266x190.svg
```

To regenerate it:

```bash
python scripts/make_charuco_board.py \
  --preset a4-balanced \
  --output generated/charuco_a4_balanced_266x190.png
```

That produces a 7 x 5 board with 38 mm squares and 27 mm markers. The active
board area is 266 x 190 mm.

For a more robust but sparser A4 board:

```text
printables/charuco_a4_robust_270x180.svg
```

To regenerate it:

```bash
python scripts/make_charuco_board.py \
  --preset a4-robust \
  --output generated/charuco_a4_robust_270x180.png
```

That produces a 6 x 4 board with 45 mm squares and 32 mm markers. The active
board area is 270 x 180 mm.

For a full copy-stand bed homography board:

```text
printables/charuco_full_bed_500x350.svg
```

To regenerate it:

```bash
python scripts/make_charuco_board.py \
  --preset full-bed-500x350 \
  --output generated/charuco_full_bed_500x350.png
```

That produces a 10 x 7 board with 50 mm squares and 35 mm markers. The active
board area is 500 x 350 mm.

The generator writes both a PNG and a same-name SVG wrapper. Prefer printing the
SVG at 100% scale with no "fit to page". The SVG references the same-name PNG,
so keep both files together. Measure the actual square size after printing and
use the measured value for calibration.

## Preparing A Tiled Full-Bed Board

The tiled pages should behave like one continuous printed board. They do not
need microscopic perfection, but page-to-page offsets, skew, gaps, or overlap
become real geometry errors.

Recommended prep:

1. Print the SVG/PNG at 100% scale using poster/tile printing.
2. Include tile overlap or crop marks if your print tool supports it.
3. Trim only one side of each overlap so the printed pattern can meet cleanly.
4. Tape the sheets face-up to a flat backing board before putting it on the bed.
5. Align grid lines and marker edges across page joins as carefully as possible.
6. Avoid stretching the paper while taping; work from the center outward.
7. Check several 50 mm squares and the total board size with a ruler/calipers.
8. If a join crosses a marker badly, reprint or place the join somewhere less
   harmful.

For quick tests, small gaps are better than overlaps that hide marker edges. For
accuracy tests, a single large-format print or a carefully mounted tiled board is
much better than loose pages.

## Camera Tramming Sheet

Print this at 100% scale before using the camera:

```text
printables/camera_tram_sheet_a4.svg
```

It contains a 200 x 200 mm grid, centerlines, diagonals, a 100 mm scale check,
and a short setup procedure. It is for mechanical alignment only; ChArUco
calibration still provides the actual image-to-mm mapping.

## Camera Smoke Test

Once the USB camera arrives:

```bash
source .venv/bin/activate
python scripts/camera_preview.py --camera 0
```

Press `s` to save a frame into `data/captures/`. Press `q` or Escape to exit.

If WSL cannot open GUI windows, capture one frame without a preview:

```bash
source .venv/bin/activate
python scripts/capture_frame.py --camera 0 --width 1280 --height 720 --fourcc MJPG
```

Or use the browser-based live preview, which avoids OpenCV's WSL GUI window:

```bash
source .venv/bin/activate
python scripts/camera_web_preview.py --camera 0 --width 1280 --height 720 --fourcc MJPG
```

Then open:

```text
http://127.0.0.1:8080
```

## Lock Camera Controls

The Arducam 16MP exposes manual focus, exposure, and white balance through
`v4l2-ctl`. Before calibration, lock the controls:

```bash
bash scripts/lock_camera_controls.sh /dev/video0
```

Defaults are based on the first detected camera values:

```text
FOCUS=144
EXPOSURE=157
WHITE_BALANCE=4600
POWER_LINE=1
```

`POWER_LINE=1` is 50 Hz, which is appropriate for UK lighting. Override values
like this:

```bash
FOCUS=180 EXPOSURE=220 WHITE_BALANCE=5000 bash scripts/lock_camera_controls.sh /dev/video0
```

Use manual focus/exposure for calibration and measurement. If focus, exposure,
resolution, or camera position changes, rerun calibration.

## Project Shape

- `src/bedmapping/charuco.py` - ChArUco board creation and detection helpers.
- `src/bedmapping/geometry.py` - homography and pixel-to-mm transforms.
- `scripts/self_test_synthetic.py` - no-camera proof that the maths works.
- `scripts/make_charuco_board.py` - printable board generator.
- `scripts/lock_camera_controls.sh` - lock UVC focus/exposure/white balance.
- `scripts/camera_preview.py` - simple live camera capture utility.
- `scripts/capture_frame.py` - headless one-frame camera capture utility.
- `scripts/camera_web_preview.py` - browser-based live preview for WSL.
