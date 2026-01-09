from __future__ import annotations

import base64
from typing import Any, Iterable, List, Optional

import cv2
import numpy as np

from cam_vision.types import (
    BBox,
    Detection,
    FaceMatch,
    FaceObservation,
    PlateObservation,
    PlateRead,
)
from cam_vision.ui.capture import FrameResult


def to_native_type(value: Any) -> Any:
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(value, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(value)
    if isinstance(value, (np.floating, np.float64, np.float32, np.float16)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    return value


def bbox_to_json(bbox: BBox) -> dict:
    return {
        "x": to_native_type(bbox.x1),
        "y": to_native_type(bbox.y1),
        "width": to_native_type(bbox.width()),
        "height": to_native_type(bbox.height()),
    }


def detection_base_to_json(detection: Detection) -> dict:
    payload = {
        "type": detection.kind,
        "confidence": to_native_type(detection.score),
        "bounding_box": bbox_to_json(detection.bbox),
    }
    if detection.track_id is not None:
        payload["track_id"] = to_native_type(detection.track_id)
    return payload


def face_match_to_json(match: FaceMatch) -> dict:
    return {
        "person_id": match.person_id,
        "similarity": to_native_type(match.similarity),
        "label": match.person_id,
    }


def plate_read_to_json(read: PlateRead) -> dict:
    payload = {
        "plate": read.text_clean or read.text_raw,
        "confidence": to_native_type(read.confidence),
    }
    if read.matched_list is not None:
        payload["list_type"] = read.matched_list
    return payload


def face_observation_to_detection(observation: FaceObservation) -> dict:
    payload = detection_base_to_json(observation.detection)
    if observation.matched and observation.person_id:
        payload["face_match"] = {
            "person_id": observation.person_id,
            "similarity": to_native_type(observation.similarity or 0.0),
            "label": observation.label,
        }
    return payload


def plate_observation_to_detection(observation: PlateObservation) -> dict:
    payload = detection_base_to_json(observation.detection)
    if observation.text_clean or observation.text_raw:
        payload["plate_read"] = {
            "plate": observation.text_clean or observation.text_raw,
            "confidence": to_native_type(observation.confidence),
        }
        if observation.matched_list is not None:
            payload["plate_read"]["list_type"] = observation.matched_list
    return payload


def encode_preview_image(preview_image, jpeg_quality: int = 80) -> Optional[str]:
    if preview_image is None:
        return None
    success, buffer = cv2.imencode(
        ".jpg",
        preview_image,
        [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)],
    )
    if not success:
        return None
    return base64.b64encode(buffer).decode("ascii")


def frame_result_to_json(
    result: FrameResult,
    include_image: bool = True,
    jpeg_quality: int = 80,
) -> dict:
    preview_image = result.preview_image
    height, width = preview_image.shape[:2]

    detections: List[dict] = []
    if result.face_observations:
        detections.extend(face_observation_to_detection(obs) for obs in result.face_observations)
    else:
        detections.extend(face_match_to_detection(match) for match in result.face_matches)

    if result.plate_observations:
        detections.extend(
            plate_observation_to_detection(obs)
            for obs in result.plate_observations
            if obs.is_displayable()
        )
    else:
        detections.extend(plate_read_to_detection(read) for read in result.plate_reads)

    payload = {
        "id": f"{result.frame.source_id}-{to_native_type(result.frame.ts_ms)}",
        "timestamp": to_native_type(result.frame.ts_ms),
        "width": to_native_type(width),
        "height": to_native_type(height),
        "detections": detections,
        "source_id": result.frame.source_id,
    }

    if include_image:
        encoded = encode_preview_image(preview_image, jpeg_quality)
        if encoded is not None:
            payload["image_base64"] = encoded

    return payload


def events_from_frame(result: FrameResult) -> List[dict]:
    events: List[dict] = []
    source_id = result.frame.source_id
    timestamp = to_native_type(result.frame.ts_ms)

    for index, match in enumerate(result.face_matches):
        detection_payload = face_match_to_detection(match)
        events.append(
            {
                "id": f"{source_id}-{timestamp}-face-{index}",
                "type": "face_match",
                "timestamp": timestamp,
                "detection": detection_payload,
            }
        )

    for index, read in enumerate(result.plate_reads):
        detection_payload = plate_read_to_detection(read)
        events.append(
            {
                "id": f"{source_id}-{timestamp}-plate-{index}",
                "type": "plate_read",
                "timestamp": timestamp,
                "detection": detection_payload,
            }
        )

    return events


def face_match_to_detection(match: FaceMatch) -> dict:
    payload = detection_base_to_json(match.detection)
    payload["face_match"] = face_match_to_json(match)
    return payload


def plate_read_to_detection(read: PlateRead) -> dict:
    payload = detection_base_to_json(read.detection)
    payload["plate_read"] = plate_read_to_json(read)
    return payload


def extend_events(queue, events: Iterable[dict]) -> None:
    for event in events:
        try:
            queue.put_nowait(event)
        except Exception:
            break
