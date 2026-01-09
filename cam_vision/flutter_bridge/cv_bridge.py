from __future__ import annotations

import base64
import csv
import json
import re
import time
from pathlib import Path
from typing import Any, Optional

from pydantic import ValidationError

from cam_vision.config import VideoSource, load_settings
from cam_vision.face.gallery import FaceGallery
from cam_vision.face.loader import FaceModels
from cam_vision.ui.capture import CaptureManager

from .json_serializer import events_from_frame, frame_result_to_json
from .thread_manager import EventQueue

try:
    from onvif import ONVIFCamera  # type: ignore[import]
except ImportError:  # pragma: no cover - optional extra
    ONVIFCamera = None  # type: ignore[assignment]

try:
    from ws_discovery import WSDiscovery  # type: ignore[import]
except ImportError:  # pragma: no cover - optional extra
    WSDiscovery = None  # type: ignore[assignment]


class CVBridge:
    def __init__(self) -> None:
        self._manager: Optional[CaptureManager] = None
        self._events = EventQueue()
        self._include_image = True
        self._jpeg_quality = 80
        self._fps_target = 10
        self._frame_resize = None
        self._enable_faces = True
        self._enable_plates = True
        self._enable_tracking = True
        self._face_similarity_threshold = None
        self._tracking_params: dict[str, Any] = {}

    def initialize(self, config_json: str) -> str:
        config = _parse_json(config_json)
        if isinstance(config, dict):
            self._enable_faces = bool(config.get("enable_faces", self._enable_faces))
            self._enable_plates = bool(config.get("enable_plates", self._enable_plates))
            self._enable_tracking = bool(config.get("enable_tracking", self._enable_tracking))
            self._include_image = bool(config.get("include_image", self._include_image))
            self._jpeg_quality = int(config.get("jpeg_quality", self._jpeg_quality))
            self._fps_target = int(config.get("target_fps", self._fps_target))
            self._frame_resize = _normalize_frame_resize(config.get("frame_resize"))
            self._face_similarity_threshold = config.get("face_similarity_threshold")
            self._tracking_params = {
                "frames_required": config.get("tracking_frames"),
                "iou_threshold": config.get("tracking_iou"),
                "max_age_frames": config.get("tracking_max_age"),
                "ocr_agreement_threshold": config.get("ocr_agreement"),
            }
        return _ok()

    def start_capture(self, source_json: str) -> str:
        source_payload = _parse_json(source_json)
        if not isinstance(source_payload, dict):
            return _error("invalid_source_payload")

        source_data = dict(source_payload)
        fps_override = source_data.pop("target_fps", None)
        try:
            source = VideoSource.model_validate(source_data).to_concrete()
        except ValidationError as exc:
            return _error("invalid_source_config", details=str(exc))

        if self._manager is None:
            self._manager = CaptureManager(
                enable_faces=self._enable_faces,
                enable_plates=self._enable_plates,
                enable_tracking=self._enable_tracking,
            )
        elif self._manager.is_running():
            self._manager.stop()

        self._events.clear()
        fps_target = self._fps_target
        if fps_override is not None:
            try:
                fps_target = int(fps_override)
            except (TypeError, ValueError):
                fps_target = self._fps_target

        self._manager.start(
            source_config=source,
            fps_target=fps_target,
            frame_resize=self._frame_resize,
            face_similarity_threshold=self._face_similarity_threshold,
            tracking_enabled=self._enable_tracking,
            frames_required=self._tracking_params.get("frames_required"),
            iou_threshold=self._tracking_params.get("iou_threshold"),
            max_age_frames=self._tracking_params.get("max_age_frames"),
            ocr_agreement_threshold=self._tracking_params.get("ocr_agreement_threshold"),
        )
        return _ok()

    def get_next_frame(self) -> str:
        if self._manager is None or not self._manager.is_running():
            return _error("capture_not_running")

        result = self._manager.get_latest_frame()
        if result is None:
            return _empty("frame")

        payload = frame_result_to_json(
            result,
            include_image=self._include_image,
            jpeg_quality=self._jpeg_quality,
        )
        for event in events_from_frame(result):
            self._events.put(event)
        return json.dumps({"type": "frame", "payload": payload})

    def get_next_event(self) -> str:
        event = self._events.get_nowait()
        if event is None:
            return _empty("event")
        return json.dumps({"type": "event", "payload": event})

    def stop_capture(self) -> str:
        if self._manager is None or not self._manager.is_running():
            return _ok(status="not_running")
        self._manager.stop()
        return _ok(status="stopped")

    def enroll_face(self, image_base64: str, person_id: str) -> str:
        if not image_base64:
            return _error("missing_image")
        if not person_id:
            return _error("missing_person_id")

        safe_person_id = _sanitize_person_id(person_id)
        if not safe_person_id:
            return _error("invalid_person_id")

        image_payload = _strip_data_url(image_base64)
        try:
            image_bytes = base64.b64decode(image_payload)
        except (ValueError, TypeError) as exc:
            return _error("invalid_image_payload", details=str(exc))

        try:
            settings = load_settings()
            gallery_path = Path(settings.faces.gallery_path)
            cache_path = Path(settings.faces.gallery_cache)
            gallery_path.mkdir(parents=True, exist_ok=True)
            person_dir = gallery_path / safe_person_id
            person_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{int(time.time() * 1000)}.jpg"
            image_path = person_dir / filename
            image_path.write_bytes(image_bytes)

            models = FaceModels.get_models()
            gallery = FaceGallery(str(gallery_path), str(cache_path))
            enrolled_count = gallery.build(embedder=models, force_rebuild=True)
        except Exception as exc:
            return _error("enroll_face_failed", details=str(exc))

        return _ok(enrolled_count=enrolled_count, person_id=safe_person_id)

    def update_plate_list(self, list_type: str, plates: list[str]) -> str:
        normalized_type = (list_type or "").strip().lower()
        if normalized_type not in {"whitelist", "blacklist"}:
            return _error("invalid_list_type")

        normalized = _normalize_plates(plates)

        try:
            settings = load_settings()
            target_path = (
                settings.plates.whitelist_path
                if normalized_type == "whitelist"
                else settings.plates.blacklist_path
            )
            path = Path(target_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["plate"])
                writer.writerows([[plate] for plate in normalized])
        except Exception as exc:
            return _error("update_plate_list_failed", details=str(exc))

        return _ok(count=len(normalized), list_type=normalized_type)

    def discover_onvif(self, request_json: str) -> str:
        payload = _parse_json(request_json)
        if payload is None:
            return _error("invalid_request")
        if not _has_onvif_support():
            return _error(
                "onvif_dependencies_missing",
                details="Install optional extras: poetry install --with onvif",
            )

        host = payload.get("host")
        port = _coerce_int(payload.get("port"), 80)
        username = payload.get("username")
        password = payload.get("password")
        timeout = _coerce_int(payload.get("timeout"), 5)
        profiles = payload.get("profiles")
        if isinstance(profiles, str):
            profiles = [item.strip() for item in profiles.split(",") if item.strip()]
        if profiles is not None and not isinstance(profiles, list):
            profiles = None

        devices: list[dict[str, Any]] = []
        warnings: list[str] = []
        hosts: list[str]

        if host:
            hosts = [host]
        else:
            hosts = list(_discover_onvif_hosts(timeout, warnings))

        for candidate in hosts:
            device_payload = _discover_onvif_device(
                candidate,
                port,
                username,
                password,
                profiles,
                warnings,
            )
            if device_payload is not None:
                devices.append(device_payload)

        return _ok(devices=devices, warnings=warnings)


def _parse_json(payload: str) -> Any:
    if not payload:
        return {}
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def _ok(**extras: Any) -> str:
    payload = {"status": "ok"}
    payload.update(extras)
    return json.dumps(payload)


def _error(message: str, **extras: Any) -> str:
    payload = {"status": "error", "message": message}
    payload.update(extras)
    return json.dumps(payload)


def _empty(kind: str) -> str:
    return json.dumps({"status": "empty", "kind": kind})


def _normalize_frame_resize(value: Any) -> Any:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            return int(value[0]), int(value[1])
        except (TypeError, ValueError):
            return None
    return value


def _has_onvif_support() -> bool:
    return WSDiscovery is not None and ONVIFCamera is not None


def _discover_onvif_hosts(timeout: int, warnings: list[str]) -> list[str]:
    if WSDiscovery is None:
        warnings.append("ws_discovery_not_available")
        return []
    ws = WSDiscovery()
    ws.start()
    try:
        services = ws.searchServices(timeout=timeout)
    finally:
        ws.stop()

    hosts: set[str] = set()
    for service in services:
        for xaddr in service.getXAddrs():
            hosts.add(xaddr.split("//")[-1].split("/")[0])

    if not hosts:
        warnings.append("no_onvif_devices_found")
    return sorted(hosts)


def _discover_onvif_device(
    host: str,
    port: int,
    username: Optional[str],
    password: Optional[str],
    profiles: Optional[list[str]],
    warnings: list[str],
) -> Optional[dict[str, Any]]:
    if ONVIFCamera is None:
        warnings.append("onvif_not_available")
        return None
    try:
        camera = ONVIFCamera(host, port, username or "", password or "")  # type: ignore
        camera.update_xaddrs()
    except Exception as exc:
        warnings.append(f"connect_failed:{host}:{exc}")
        return None

    try:
        media_service = camera.create_media_service()
        profile_items = media_service.GetProfiles()
    except Exception as exc:
        warnings.append(f"profiles_failed:{host}:{exc}")
        return None

    device_profiles: list[dict[str, str]] = []
    for profile in profile_items:
        token = getattr(profile, "token", "")
        name = getattr(profile, "Name", token)
        if profiles and token not in profiles and name not in profiles:
            continue
        stream_request = {
            "StreamSetup": {
                "Stream": "RTP-Unicast",
                "Transport": {"Protocol": "RTSP"},
            },
            "ProfileToken": token,
        }
        try:
            uri = media_service.GetStreamUri(stream_request)
        except Exception as exc:
            warnings.append(f"stream_uri_failed:{host}:{token}:{exc}")
            continue
        device_profiles.append(
            {
                "name": name,
                "token": token,
                "uri": getattr(uri, "Uri", ""),
            }
        )

    if not device_profiles:
        warnings.append(f"no_profiles:{host}")
        return None
    return {"host": host, "profiles": device_profiles}


def _coerce_int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _sanitize_person_id(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip())
    return cleaned.strip("_")


def _normalize_plates(plates: list[str]) -> list[str]:
    normalized = []
    for plate in plates or []:
        if plate is None:
            continue
        cleaned = str(plate).strip().upper()
        if cleaned:
            normalized.append(cleaned)
    return sorted(set(normalized))


def _strip_data_url(value: str) -> str:
    if "base64," in value:
        return value.split("base64,", 1)[1]
    return value
