from __future__ import annotations

import json
import signal
import sys
import threading
import time
from typing import Any

from cam_vision.flutter_bridge.cv_bridge import CVBridge


class DesktopBridge:
    def __init__(self) -> None:
        self._bridge = CVBridge()
        self._polling = False
        self._poll_thread: threading.Thread | None = None
        self._running = True

    def run(self) -> None:
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            payload = self._parse_line(line)
            if payload is None:
                continue
            self._handle_message(payload)
            if not self._running:
                break

        self._shutdown()

    def _handle_signal(self, _sig: int, _frame: Any) -> None:
        self._running = False
        self._shutdown()

    def _shutdown(self) -> None:
        self._stop_polling()
        self._bridge.stop_capture()

    def _parse_line(self, line: str) -> dict | None:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            self._write_error("invalid_json")
            return None
        if not isinstance(payload, dict):
            self._write_error("invalid_payload")
            return None
        return payload

    def _handle_message(self, payload: dict) -> None:
        message_type = payload.get("type")
        if message_type == "initialize":
            config = payload.get("config")
            config_json = payload.get("config_json", "")
            response = self._bridge.initialize(_to_json(config, config_json))
            self._handle_control_response(response)
            return
        if message_type == "start_capture":
            source = payload.get("source")
            source_json = payload.get("source_json", "")
            response = self._bridge.start_capture(_to_json(source, source_json))
            self._handle_control_response(response)
            self._start_polling()
            return
        if message_type == "stop_capture":
            self._stop_polling()
            response = self._bridge.stop_capture()
            self._handle_control_response(response)
            return
        if message_type == "enroll_face":
            response = self._bridge.enroll_face(
                payload.get("image_base64", ""),
                payload.get("person_id", ""),
            )
            self._handle_control_response(response)
            return
        if message_type == "update_plate_list":
            response = self._bridge.update_plate_list(
                payload.get("list_type", ""),
                payload.get("plates", []),
            )
            self._handle_control_response(response)
            return
        if message_type == "discover_onvif":
            request_id = payload.get("request_id")
            request = payload.get("request")
            response = self._bridge.discover_onvif(_to_json(request, ""))
            self._send_response(request_id, response)
            return
        if message_type == "shutdown":
            self._running = False
            return

        self._write_error(f"unknown_message:{message_type}")

    def _start_polling(self) -> None:
        if self._poll_thread and self._poll_thread.is_alive():
            return
        self._polling = True
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def _stop_polling(self) -> None:
        self._polling = False
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=1.0)
        self._poll_thread = None

    def _poll_loop(self) -> None:
        while self._polling:
            self._emit_if_ready(self._bridge.get_next_frame())
            self._emit_if_ready(self._bridge.get_next_event())
            time.sleep(0.02)

    def _emit_if_ready(self, payload_json: str) -> None:
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            self._write_error("invalid_response")
            return

        message_type = payload.get("type")
        if message_type in {"frame", "event"}:
            self._send_raw(payload_json)
            return

        if payload.get("status") == "error":
            self._write_error(payload.get("message", "error"))

    def _handle_control_response(self, payload_json: str) -> None:
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            self._write_error("invalid_control_response")
            return
        if payload.get("status") == "error":
            self._write_error(payload.get("message", "error"))

    @staticmethod
    def _send_raw(payload: str) -> None:
        sys.stdout.write(payload + "\n")
        sys.stdout.flush()

    def _send_response(self, request_id: Any, payload_json: str) -> None:
        if request_id is None:
            return
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            payload = {"status": "error", "message": "invalid_response"}
        response = {
            "type": "response",
            "request_id": str(request_id),
            "payload": payload,
        }
        self._send_raw(json.dumps(response))

    @staticmethod
    def _write_error(message: str) -> None:
        sys.stderr.write(f"[flutter_bridge] {message}\n")
        sys.stderr.flush()


def _to_json(payload: Any, fallback: str) -> str:
    if isinstance(payload, dict):
        return json.dumps(payload)
    if isinstance(payload, str):
        return payload
    return fallback or "{}"


def main() -> None:
    DesktopBridge().run()


if __name__ == "__main__":
    main()
