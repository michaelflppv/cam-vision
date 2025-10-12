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


def test_plates_settings_defaults():
    """Test PlatesSettings has sensible defaults."""
    from cam_vision.config import PlatesSettings

    settings = PlatesSettings()
    assert settings.enabled is True

    # Detector defaults
    assert settings.detector.model_path == "./weights/yolov8n_plate.pt"
    assert settings.detector.conf_threshold == 0.25
    assert settings.detector.iou_threshold == 0.45
    assert settings.detector.max_det == 10
    assert settings.detector.input_size == 640

    # OCR defaults
    assert settings.ocr.tesseract_lang == "eng"
    assert settings.ocr.psm_mode == 7
    assert settings.ocr.oem_mode == 3
    assert settings.ocr.char_whitelist == "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- "
    assert settings.ocr.enable_grayscale is True
    assert settings.ocr.enable_bilateral is False
    assert settings.ocr.enable_clahe is False

    # Postprocess defaults
    assert settings.postprocess.regex == "[A-Z0-9-]{4,10}"
    assert settings.postprocess.uppercase is True
    assert settings.postprocess.min_length == 4
    assert settings.postprocess.max_length == 10

    # ROI defaults
    assert settings.roi.enabled is False
    assert settings.roi.x1 == 0
    assert settings.roi.y1 == 0
    assert settings.roi.x2 == 0
    assert settings.roi.y2 == 0

    # List paths
    assert settings.whitelist_path == "./data/plates/whitelist.csv"
    assert settings.blacklist_path == "./data/plates/blacklist.csv"


def test_plates_settings_env_override(monkeypatch):
    """Test PlatesSettings can be overridden via environment variables."""
    monkeypatch.setenv("SECUREVISION__PLATES__ENABLED", "false")
    monkeypatch.setenv("SECUREVISION__PLATES__DETECTOR__MODEL_PATH", "/custom/model.pt")
    monkeypatch.setenv("SECUREVISION__PLATES__DETECTOR__CONF_THRESHOLD", "0.35")
    monkeypatch.setenv("SECUREVISION__PLATES__OCR__TESSERACT_LANG", "deu")
    monkeypatch.setenv("SECUREVISION__PLATES__OCR__PSM_MODE", "8")
    monkeypatch.setenv("SECUREVISION__PLATES__OCR__ENABLE_BILATERAL", "true")
    monkeypatch.setenv("SECUREVISION__PLATES__POSTPROCESS__REGEX", "[A-Z]{2}[0-9]{4}")
    monkeypatch.setenv("SECUREVISION__PLATES__ROI__ENABLED", "true")
    monkeypatch.setenv("SECUREVISION__PLATES__ROI__X1", "100")
    monkeypatch.setenv("SECUREVISION__PLATES__ROI__Y1", "50")
    monkeypatch.setenv("SECUREVISION__PLATES__WHITELIST_PATH", "/custom/whitelist.csv")

    settings = load_settings()
    assert settings.plates.enabled is False
    assert settings.plates.detector.model_path == "/custom/model.pt"
    assert settings.plates.detector.conf_threshold == 0.35
    assert settings.plates.ocr.tesseract_lang == "deu"
    assert settings.plates.ocr.psm_mode == 8
    assert settings.plates.ocr.enable_bilateral is True
    assert settings.plates.postprocess.regex == "[A-Z]{2}[0-9]{4}"
    assert settings.plates.roi.enabled is True
    assert settings.plates.roi.x1 == 100
    assert settings.plates.roi.y1 == 50
    assert settings.plates.whitelist_path == "/custom/whitelist.csv"


def test_plates_detector_settings_validation():
    """Test PlateDetectorSettings field validation."""
    from cam_vision.config import PlateDetectorSettings

    # Valid settings
    settings = PlateDetectorSettings(
        model_path="./weights/yolov8s.pt",
        conf_threshold=0.5,
        iou_threshold=0.7,
        max_det=5,
    )
    assert settings.conf_threshold == 0.5
    assert settings.iou_threshold == 0.7
    assert settings.max_det == 5

    # Test threshold bounds
    with pytest.raises(Exception):
        PlateDetectorSettings(conf_threshold=1.5)  # > 1.0

    with pytest.raises(Exception):
        PlateDetectorSettings(conf_threshold=-0.1)  # < 0.0


def test_plates_ocr_settings_validation():
    """Test PlateOCRSettings field validation."""
    from cam_vision.config import PlateOCRSettings

    # Valid custom settings
    settings = PlateOCRSettings(
        tesseract_lang="fra",
        psm_mode=8,
        oem_mode=1,
        char_whitelist="ABC123",
        enable_bilateral=True,
        enable_clahe=True,
    )
    assert settings.tesseract_lang == "fra"
    assert settings.psm_mode == 8
    assert settings.oem_mode == 1
    assert settings.char_whitelist == "ABC123"
    assert settings.enable_bilateral is True
    assert settings.enable_clahe is True

    # Test PSM bounds
    with pytest.raises(Exception):
        PlateOCRSettings(psm_mode=14)  # > 13

    with pytest.raises(Exception):
        PlateOCRSettings(psm_mode=-1)  # < 0


def test_plates_postprocess_settings():
    """Test PlatePostProcessSettings customization."""
    from cam_vision.config import PlatePostProcessSettings

    settings = PlatePostProcessSettings(
        regex="[A-Z]{3}[0-9]{4}",
        uppercase=True,
        min_length=7,
        max_length=7,
    )
    assert settings.regex == "[A-Z]{3}[0-9]{4}"
    assert settings.min_length == 7
    assert settings.max_length == 7


def test_plates_roi_settings():
    """Test PlateROISettings for region-of-interest crop."""
    from cam_vision.config import PlateROISettings

    # Disabled by default
    settings = PlateROISettings()
    assert settings.enabled is False

    # Custom ROI
    settings = PlateROISettings(
        enabled=True,
        x1=100,
        y1=200,
        x2=800,
        y2=600,
    )
    assert settings.enabled is True
    assert settings.x1 == 100
    assert settings.y1 == 200
    assert settings.x2 == 800
    assert settings.y2 == 600


def test_plates_settings_complete_override(monkeypatch):
    """Test complete PlatesSettings configuration via environment."""
    monkeypatch.setenv("SECUREVISION__PLATES__DETECTOR__MODEL_PATH", "weights/custom.pt")
    monkeypatch.setenv("SECUREVISION__PLATES__OCR__TESSERACT_LANG", "spa")
    monkeypatch.setenv(
        "SECUREVISION__PLATES__OCR__CHAR_WHITELIST", "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    )
    monkeypatch.setenv("SECUREVISION__PLATES__POSTPROCESS__UPPERCASE", "false")
    monkeypatch.setenv("SECUREVISION__PLATES__MIN_CONFIDENCE", "0.7")

    settings = load_settings()
    assert settings.plates.detector.model_path == "weights/custom.pt"
    assert settings.plates.ocr.tesseract_lang == "spa"
    assert settings.plates.ocr.char_whitelist == "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    assert settings.plates.postprocess.uppercase is False
    assert settings.plates.min_confidence == 0.7
