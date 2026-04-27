#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import time

import cv2


class Camera:
    def __init__(self, index: int, width: int, height: int, fourcc: str) -> None:
        self.capture = cv2.VideoCapture(index, cv2.CAP_V4L2)
        if fourcc:
            self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc))
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not self.capture.isOpened():
            raise RuntimeError(f"Could not open camera {index}")

        actual_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fourcc = int(self.capture.get(cv2.CAP_PROP_FOURCC))
        self.actual_fourcc_text = "".join(chr((actual_fourcc >> 8 * i) & 0xFF) for i in range(4))
        self.description = f"{actual_width}x{actual_height} {self.actual_fourcc_text}"

        self.lock = threading.Lock()
        self.latest = None
        self.running = True
        self.thread = threading.Thread(target=self._reader, daemon=True)
        self.thread.start()

    def _reader(self) -> None:
        while self.running:
            ok, frame = self.capture.read()
            if ok:
                with self.lock:
                    self.latest = frame
            else:
                time.sleep(0.05)

    def jpeg(self, quality: int) -> bytes | None:
        with self.lock:
            frame = None if self.latest is None else self.latest.copy()
        if frame is None:
            return None
        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if not ok:
            return None
        return encoded.tobytes()

    def save(self, output_dir: Path) -> Path | None:
        with self.lock:
            frame = None if self.latest is None else self.latest.copy()
        if frame is None:
            return None
        output_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = output_dir / f"capture_{stamp}.png"
        cv2.imwrite(str(output), frame)
        return output

    def close(self) -> None:
        self.running = False
        self.thread.join(timeout=1)
        self.capture.release()


def make_handler(camera: Camera, jpeg_quality: int, output_dir: Path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:
            return

        def do_GET(self) -> None:
            if self.path == "/":
                html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>grblHAL Bedmapping Camera Preview</title>
  <style>
    body {{ margin: 0; background: #111; color: #eee; font-family: Arial, sans-serif; }}
    header {{ padding: 10px 14px; display: flex; gap: 14px; align-items: center; background: #202020; }}
    button {{ font-size: 14px; padding: 7px 10px; }}
    img {{ display: block; max-width: 100vw; max-height: calc(100vh - 48px); margin: 0 auto; }}
    .muted {{ color: #aaa; }}
  </style>
</head>
<body>
  <header>
    <strong>Camera Preview</strong>
    <span class="muted">{camera.description}</span>
    <button onclick="fetch('/capture').then(r => r.text()).then(alert)">Save frame</button>
  </header>
  <img src="/stream" alt="camera stream">
</body>
</html>
"""
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html.encode("utf-8"))))
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
                return

            if self.path == "/capture":
                output = camera.save(output_dir)
                message = "No frame available yet" if output is None else f"Saved {output}"
                body = message.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if self.path != "/stream":
                self.send_error(404)
                return

            self.send_response(200)
            self.send_header("Age", "0")
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()

            while True:
                jpeg = camera.jpeg(jpeg_quality)
                if jpeg is None:
                    time.sleep(0.05)
                    continue
                try:
                    self.wfile.write(b"--frame\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n")
                    self.wfile.write(f"Content-Length: {len(jpeg)}\r\n\r\n".encode("ascii"))
                    self.wfile.write(jpeg)
                    self.wfile.write(b"\r\n")
                    time.sleep(0.03)
                except (BrokenPipeError, ConnectionResetError):
                    break

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve a live camera preview in a web browser.")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fourcc", default="MJPG")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--quality", type=int, default=85)
    parser.add_argument("--output-dir", default="data/captures")
    args = parser.parse_args()

    camera = Camera(args.camera, args.width, args.height, args.fourcc)
    server = ThreadingHTTPServer(
        (args.host, args.port),
        make_handler(camera, args.quality, Path(args.output_dir)),
    )

    url = f"http://{args.host}:{args.port}"
    print(f"Camera open: {camera.description}")
    print(f"Live preview: {url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping preview.")
    finally:
        server.server_close()
        camera.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
