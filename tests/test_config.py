import pytest

from cam_vision.config import AppSettings, VideoSource, example_env_for_macbook, load_settings


def test_default_settings_compile():
    s = AppSettings()
    assert s.video.fps_target == 15
    assert s.face.enabled is True
    assert s.plates.enabled is True
    # Default source is device index 0
    assert s.video.source.type == "device"


@pytest.mark.parametrize(
    "env_map,expect_type",
    [
        (
            {
                "SECUREVISION__VIDEO__SOURCE__TYPE": "device",
                "SECUREVISION__VIDEO__SOURCE__DEVICE_INDEX": "0",
            },
            "device",
        ),
        (
            {
                "SECUREVISION__VIDEO__SOURCE__TYPE": "rtsp",
                "SECUREVISION__VIDEO__SOURCE__URL": "rtsp://x",
            },
            "rtsp",
        ),
        (
            {
                "SECUREVISION__VIDEO__SOURCE__TYPE": "http_mjpeg",
                "SECUREVISION__VIDEO__SOURCE__URL": "http://x/mjpg",
            },
            "http_mjpeg",
        ),
        (
            {
                "SECUREVISION__VIDEO__SOURCE__TYPE": "file",
                "SECUREVISION__VIDEO__SOURCE__URL": "/tmp/demo.mp4",
            },
            "file",
        ),
    ],
)
def test_env_loading_variants(monkeypatch, env_map, expect_type):
    for k, v in env_map.items():
        monkeypatch.setenv(k, v)
    settings = load_settings()
    assert settings.video.source.type == expect_type


def test_macbook_example_env(monkeypatch):
    for k, v in example_env_for_macbook().items():
        monkeypatch.setenv(k, v)
    s = load_settings()
    assert s.video.source.type == "device"
    assert s.video.source.device_index == 0
    assert s.video.source.backend == "AVFOUNDATION"


def test_video_source_to_concrete_requires_url_for_rtsp():
    vs = VideoSource(type="rtsp")
    with pytest.raises(Exception):
        vs.to_concrete()

    vs_ok = VideoSource(type="rtsp", url="rtsp://user:pass@host/stream")
    concrete = vs_ok.to_concrete()
    assert concrete.type == "rtsp"
    assert "rtsp://" in concrete.url


def test_video_source_to_concrete_device():
    """Device source should use device_index with default 0."""
    vs = VideoSource(type="device")
    concrete = vs.to_concrete()
    assert concrete.type == "device"
    assert concrete.device_index == 0
    assert concrete.backend is None

    vs_with_backend = VideoSource(type="device", device_index=1, backend="AVFOUNDATION")
    concrete = vs_with_backend.to_concrete()
    assert concrete.device_index == 1
    assert concrete.backend == "AVFOUNDATION"


def test_video_source_to_concrete_http_mjpeg():
    """HTTP MJPEG source requires URL."""
    vs = VideoSource(type="http_mjpeg")
    with pytest.raises(Exception):
        vs.to_concrete()

    vs_ok = VideoSource(type="http_mjpeg", url="http://192.168.1.100/mjpeg")
    concrete = vs_ok.to_concrete()
    assert concrete.type == "http_mjpeg"
    assert concrete.url == "http://192.168.1.100/mjpeg"


def test_video_source_to_concrete_file():
    """File source requires URL (path)."""
    vs = VideoSource(type="file")
    with pytest.raises(Exception):
        vs.to_concrete()

    vs_ok = VideoSource(type="file", url="/path/to/video.mp4")
    concrete = vs_ok.to_concrete()
    assert concrete.type == "file"
    assert concrete.url == "/path/to/video.mp4"


def test_video_settings_defaults():
    """Test VideoSettings has sensible defaults."""
    from cam_vision.config import VideoSettings

    settings = VideoSettings()
    assert settings.source.type == "device"
    assert settings.fps_target == 15
    assert settings.frame_resize is None
    assert settings.rotate_180 is False
    assert settings.onvif_discovery_enabled is False
    assert settings.read_timeout_s == 5.0
    assert settings.reconnect_interval_s == 3.0


def test_nested_env_vars(monkeypatch):
    """Test nested environment variable parsing with double underscores."""
    monkeypatch.setenv("SECUREVISION__VIDEO__FPS_TARGET", "30")
    monkeypatch.setenv("SECUREVISION__VIDEO__ROTATE_180", "true")
    monkeypatch.setenv("SECUREVISION__VIDEO__SOURCE__TYPE", "rtsp")
    monkeypatch.setenv("SECUREVISION__VIDEO__SOURCE__URL", "rtsp://cam.local/stream")
    monkeypatch.setenv("SECUREVISION__FACE__SIMILARITY_THRESHOLD", "0.5")

    settings = load_settings()
    assert settings.video.fps_target == 30
    assert settings.video.rotate_180 is True
    assert settings.video.source.type == "rtsp"
    assert settings.video.source.url == "rtsp://cam.local/stream"
    assert settings.face.similarity_threshold == 0.5
