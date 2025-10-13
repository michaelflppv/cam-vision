from __future__ import annotations

from typing import Literal, Optional, Tuple

from pydantic import BaseModel, Field, PositiveInt, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SourceType = Literal["device", "rtsp", "http_mjpeg", "file"]


class DeviceSource(BaseModel):
    type: Literal["device"] = "device"
    device_index: int = Field(0, description="Camera index (0 is MacBook/first USB camera)")
    backend: Optional[str] = Field(
        default=None,
        description="Optional OpenCV backend hint (e.g., 'AVFOUNDATION' on macOS)",
    )


class RTSPSource(BaseModel):
    type: Literal["rtsp"] = "rtsp"
    url: str = Field(..., description="rtsp://user:pass@host:port/stream")


class HTTPMjpegSource(BaseModel):
    type: Literal["http_mjpeg"] = "http_mjpeg"
    url: str = Field(..., description="http(s)://host:port/path to MJPEG stream")


class FileSource(BaseModel):
    type: Literal["file"] = "file"
    url: str = Field(..., description="Local path to video file")


class VideoSource(BaseModel):
    """
    Discriminated union-ish model holding one of the four source configs.
    Use `type` to choose. Remaining fields are ignored.
    """

    type: SourceType = "device"
    device_index: Optional[int] = None
    backend: Optional[str] = None
    url: Optional[str] = None

    @field_validator("url")
    @classmethod
    def _strip_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() == "":
            return None
        return v

    def to_concrete(self) -> DeviceSource | RTSPSource | HTTPMjpegSource | FileSource:
        if self.type == "device":
            return DeviceSource(
                type="device", device_index=self.device_index or 0, backend=self.backend
            )
        if self.type == "rtsp":
            if not self.url:
                raise ValidationError(
                    [{"loc": ("url",), "msg": "RTSP url required", "type": "value_error"}],
                    VideoSource,
                )
            return RTSPSource(type="rtsp", url=self.url)
        if self.type == "http_mjpeg":
            if not self.url:
                raise ValidationError(
                    [{"loc": ("url",), "msg": "HTTP MJPEG url required", "type": "value_error"}],
                    VideoSource,
                )
            return HTTPMjpegSource(type="http_mjpeg", url=self.url)
        if self.type == "file":
            if not self.url:
                raise ValidationError(
                    [{"loc": ("url",), "msg": "file path required", "type": "value_error"}],
                    VideoSource,
                )
            return FileSource(type="file", url=self.url)
        raise ValueError(f"Unknown type: {self.type}")


class VideoSettings(BaseModel):
    source: VideoSource = Field(default_factory=VideoSource)
    fps_target: PositiveInt = Field(15, description="Target processing FPS via frame dropping")
    frame_resize: Optional[Tuple[int, int]] = Field(
        default=None, description="(width,height) to resize frames before processing"
    )
    rotate_180: bool = Field(
        False, description="Rotate frame 180 degrees (some cams are upside-down)"
    )
    onvif_discovery_enabled: bool = Field(
        False, description="Enable ONVIF discovery helpers (separate optional extras)"
    )
    read_timeout_s: float = Field(5.0, description="Per-frame read timeout for network sources")
    reconnect_interval_s: float = Field(3.0, description="Reconnect delay for network sources")


class FaceSettings(BaseModel):
    enabled: bool = True
    gallery_path: str = "./data/faces/trusted"
    gallery_cache: str = "./data/faces/gallery.npz"
    similarity_threshold: float = 0.35
    min_face_size: int = 40  # px


class PlateDetectorSettings(BaseModel):
    """YOLOv8 detector configuration."""

    model_path: str = Field(
        "./weights/yolov8n_plate.pt", description="Path to YOLOv8 plate detection model"
    )
    conf_threshold: float = Field(
        0.25, ge=0.0, le=1.0, description="Detection confidence threshold"
    )
    iou_threshold: float = Field(0.45, ge=0.0, le=1.0, description="NMS IoU threshold")
    max_det: int = Field(10, ge=1, description="Maximum detections per frame")
    input_size: int = Field(640, description="Model input size (square)")


class PlateOCRSettings(BaseModel):
    """Tesseract OCR configuration with preprocessing pipeline."""

    # Tesseract configuration
    tesseract_lang: str = Field(
        "eng+rus",
        description="Tesseract language (multi-language allowed, e.g., 'eng+rus' for EU/Cyrillic plates)",
    )
    psm_mode: int = Field(
        7,
        ge=0,
        le=13,
        description="Page segmentation mode (7=line, optimal for single-line plates)",
    )
    oem_mode: int = Field(3, ge=0, le=3, description="OCR Engine mode (3=default, 1=LSTM)")
    char_whitelist: str = Field(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- ",
        description="Allowed characters for OCR (includes space and hyphen)",
    )

    # Preprocessing pipeline (applied in order)
    crop_margin_px: int = Field(8, ge=0, description="Padding around detected plate bbox")
    enable_grayscale: bool = Field(True, description="Convert to grayscale (recommended)")
    enable_bilateral: bool = Field(
        False, description="Apply bilateral filter (good for noise, adds overhead)"
    )
    bilateral_d: int = Field(9, description="Bilateral filter diameter")
    bilateral_sigma_color: int = Field(75, description="Bilateral sigma color")
    bilateral_sigma_space: int = Field(75, description="Bilateral sigma space")
    enable_adaptive_threshold: bool = Field(
        False, description="Apply adaptive thresholding (good for uneven lighting)"
    )
    adaptive_block_size: int = Field(11, description="Adaptive threshold block size (must be odd)")
    adaptive_c: int = Field(2, description="Adaptive threshold constant")
    enable_clahe: bool = Field(
        False, description="Apply CLAHE (research shows minimal benefit, adds overhead)"
    )
    clahe_clip_limit: float = Field(2.0, description="CLAHE clip limit")
    clahe_tile_size: int = Field(8, description="CLAHE grid size")

    # Post-processing (deprecated - use PlatePostProcessSettings instead)
    to_uppercase: bool = Field(True, description="Convert text to uppercase")
    strip_whitespace: bool = Field(True, description="Remove whitespace from text")
    min_text_length: int = Field(3, ge=1, description="Minimum valid text length")
    substitute_o_to_0: bool = Field(False, description="Replace letter O with digit 0")
    substitute_i_to_1: bool = Field(False, description="Replace letter I with digit 1")


class PlatePostProcessSettings(BaseModel):
    """Post-processing and validation for recognized plate text."""

    regex: str = Field(
        "[A-Z0-9\\u0410-\\u042F\\u0401-]{4,10}",
        description="Regex pattern for valid plate format (supports Latin + Cyrillic uppercase, applied after cleaning)",
    )
    uppercase: bool = Field(True, description="Convert text to uppercase before regex")
    min_length: int = Field(4, ge=1, description="Minimum plate text length")
    max_length: int = Field(10, ge=1, description="Maximum plate text length")


class PlateROISettings(BaseModel):
    """Region of Interest (ROI) crop to speed up detection."""

    enabled: bool = Field(False, description="Enable ROI cropping before detection")
    x1: int = Field(0, ge=0, description="ROI top-left x coordinate (pixels)")
    y1: int = Field(0, ge=0, description="ROI top-left y coordinate (pixels)")
    x2: int = Field(0, ge=0, description="ROI bottom-right x coordinate (0=full width)")
    y2: int = Field(0, ge=0, description="ROI bottom-right y coordinate (0=full height)")


class PlatesSettings(BaseModel):
    """License plate recognition configuration."""

    enabled: bool = True
    detector: PlateDetectorSettings = Field(default_factory=PlateDetectorSettings)
    ocr: PlateOCRSettings = Field(default_factory=PlateOCRSettings)
    postprocess: PlatePostProcessSettings = Field(default_factory=PlatePostProcessSettings)
    roi: PlateROISettings = Field(default_factory=PlateROISettings)
    whitelist_path: str = "./data/plates/whitelist.csv"
    blacklist_path: str = "./data/plates/blacklist.csv"
    min_confidence: float = Field(
        0.55, ge=0.0, le=1.0, description="Overall event confidence threshold"
    )
    min_aspect_ratio: float = Field(1.2, description="Minimum plate aspect ratio (width/height)")
    max_aspect_ratio: float = Field(8.5, description="Maximum plate aspect ratio")
    min_width_px: int = Field(60, description="Minimum plate width in pixels")
    min_height_px: int = Field(18, description="Minimum plate height in pixels")


class EventsSettings(BaseModel):
    db_url: str = "sqlite:///./data/events.db"
    retention_days: int = 30


class TrackingSettings(BaseModel):
    """
    Multi-frame tracking and confirmation settings (PR8).

    These settings control the tracking-based confirmation logic that reduces
    false positives by requiring multiple consecutive frame detections before
    emitting events.

    Environment examples:
      SECUREVISION__TRACKING__ENABLED=true
      SECUREVISION__TRACKING__FRAMES_REQUIRED=3
      SECUREVISION__TRACKING__IOU_THRESHOLD=0.5
      SECUREVISION__TRACKING__COOLDOWN_SECONDS=30
    """

    enabled: bool = Field(
        True,
        description="Enable tracking and multi-frame confirmation",
    )
    frames_required: int = Field(
        3,
        ge=1,
        le=10,
        description="Consecutive frames required for track confirmation (K)",
    )
    frames_window: int = Field(
        5,
        ge=1,
        description="Frame window for tracking (M frames to look back)",
    )
    iou_threshold: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Minimum IoU for bbox matching across frames",
    )
    max_age_frames: int = Field(
        30,
        ge=1,
        description="Maximum frames without match before track removal",
    )
    ocr_agreement_threshold: float = Field(
        0.6,
        ge=0.0,
        le=1.0,
        description="Minimum OCR text agreement ratio for plate confirmation",
    )
    cooldown_seconds: float = Field(
        30.0,
        ge=0.0,
        description="Cooldown period between duplicate events (same person/plate)",
    )


class APISettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    ws_enabled: bool = True
    auth_token: Optional[str] = None


class AppSettings(BaseSettings):
    """
    Application settings. Supports environment variables with nested keys.

    Environment examples (env_nested_delimiter='__'):
      SECUREVISION__VIDEO__SOURCE__TYPE=rtsp
      SECUREVISION__VIDEO__SOURCE__URL=rtsp://user:pass@10.0.0.5:554/stream
      SECUREVISION__VIDEO__FPS_TARGET=10
      SECUREVISION__VIDEO__SOURCE__BACKEND=AVFOUNDATION
    """

    model_config = SettingsConfigDict(
        env_prefix="SECUREVISION__",
        env_nested_delimiter="__",
        extra="ignore",
    )

    video: VideoSettings = Field(default_factory=VideoSettings)
    face: FaceSettings = Field(default_factory=FaceSettings)
    plates: PlatesSettings = Field(default_factory=PlatesSettings)
    events: EventsSettings = Field(default_factory=EventsSettings)
    tracking: TrackingSettings = Field(default_factory=TrackingSettings)
    api: APISettings = Field(default_factory=APISettings)


def load_settings() -> AppSettings:
    """
    Load settings from environment variables.
    We intentionally avoid YAML/JSON config dependencies in PR2 to stay lean.
    A file loader can be added later if needed.
    """
    return AppSettings()  # pydantic-settings reads from env automatically


def example_env_for_macbook() -> dict[str, str]:
    """
    Helper for docs/tests: returns a minimal env mapping for MacBook camera (device index 0).
    """
    return {
        "SECUREVISION__VIDEO__SOURCE__TYPE": "device",
        "SECUREVISION__VIDEO__SOURCE__DEVICE_INDEX": "0",
        "SECUREVISION__VIDEO__SOURCE__BACKEND": "AVFOUNDATION",  # hint for macOS; used in PR3
        "SECUREVISION__VIDEO__FPS_TARGET": "15",
    }
