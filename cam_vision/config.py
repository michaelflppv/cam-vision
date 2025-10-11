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


class PlatesSettings(BaseModel):
    enabled: bool = True
    whitelist_path: str = "./data/plates/whitelist.csv"
    blacklist_path: str = "./data/plates/blacklist.csv"
    min_confidence: float = 0.55


class EventsSettings(BaseModel):
    db_url: str = "sqlite:///./data/events.db"
    retention_days: int = 30


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
