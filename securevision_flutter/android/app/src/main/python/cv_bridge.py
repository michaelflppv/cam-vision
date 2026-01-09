from __future__ import annotations

import json
from typing import Any

try:
    from cam_vision.flutter_bridge.cv_bridge import CVBridge
except Exception:  # pragma: no cover - Android runtime resolves this at build time
    CVBridge = None  # type: ignore


_bridge = CVBridge() if CVBridge is not None else None


def initialize(config_json: str) -> str:
    if _bridge is None:
        return _error("cv_bridge_not_available")
    return _bridge.initialize(config_json or "{}")


def start_capture(source_json: str) -> str:
    if _bridge is None:
        return _error("cv_bridge_not_available")
    return _bridge.start_capture(source_json or "{}")


def get_next_frame() -> str:
    if _bridge is None:
        return _error("cv_bridge_not_available")
    return _bridge.get_next_frame()


def get_next_event() -> str:
    if _bridge is None:
        return _error("cv_bridge_not_available")
    return _bridge.get_next_event()


def stop_capture() -> str:
    if _bridge is None:
        return _error("cv_bridge_not_available")
    return _bridge.stop_capture()


def enroll_face(image_base64: str, person_id: str) -> str:
    if _bridge is None:
        return _error("cv_bridge_not_available")
    return _bridge.enroll_face(image_base64, person_id)


def update_plate_list(list_type: str, plates: Any) -> str:
    if _bridge is None:
        return _error("cv_bridge_not_available")
    if isinstance(plates, str):
        try:
            plates = json.loads(plates)
        except json.JSONDecodeError:
            plates = []
    if plates is None:
        plates = []
    return _bridge.update_plate_list(list_type, list(plates))


def discover_onvif(request_json: str) -> str:
    if _bridge is None:
        return _error("cv_bridge_not_available")
    return _error("onvif_not_supported")


def _error(message: str) -> str:
    return json.dumps({"status": "error", "message": message})
