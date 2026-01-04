#!/usr/bin/env python3
"""Optional ONVIF discovery helper for SecureVision."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

try:
    from onvif import ONVIFCamera  # type: ignore[import]
except ImportError:  # pragma: no cover - optional extra
    ONVIFCamera = None  # type: ignore[assignment]

try:
    from ws_discovery import WSDiscovery  # type: ignore[import]
except ImportError:  # pragma: no cover - optional extra
    WSDiscovery = None  # type: ignore[assignment]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover ONVIF cameras and generate RTSP URLs (optional extra).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--host", help="Camera hostname/IP (skip to trigger WS-Discovery)")
    parser.add_argument("--port", type=int, default=80, help="Camera management port")
    parser.add_argument("--username", help="Camera admin username (ONVIF)")
    parser.add_argument("--password", help="Camera admin password (ONVIF)")
    parser.add_argument(
        "--rtsp-username",
        help="RTSP username (defaults to --username when omitted)",
    )
    parser.add_argument(
        "--rtsp-password",
        help="RTSP password (defaults to --password when omitted)",
    )
    parser.add_argument("--timeout", type=int, default=5, help="Discovery timeout seconds")
    parser.add_argument(
        "--profiles",
        nargs="*",
        help="Optional list of profile names/tokens to target (defaults to all)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging verbosity",
    )

    return parser.parse_args()


def ensure_optional_dependency(name: str, module) -> None:
    if module is None:
        print(
            f"This command requires the optional '{name}' extra.\n"
            "Install with: poetry install --with onvif",
            file=sys.stderr,
        )
        sys.exit(1)


def discover_hosts(timeout: int) -> Iterable[str]:
    ensure_optional_dependency("onvif", WSDiscovery)
    logger.info("Starting WS-Discovery broadcast (timeout=%ss)...", timeout)

    ws = WSDiscovery()
    ws.start()
    try:
        services = ws.searchServices(timeout=timeout)
    finally:
        ws.stop()

    hosts: set[str] = set()
    for svc in services:
        for xaddr in svc.getXAddrs():
            hosts.add(xaddr.split("//")[-1].split("/")[0])

    if not hosts:
        logger.warning(
            "No ONVIF devices discovered. Ensure the camera and host share the same LAN."
        )
    else:
        logger.info("Discovered %d candidate device(s): %s", len(hosts), ", ".join(hosts))
    return hosts


def connect_camera(
    host: str, port: int, username: Optional[str], password: Optional[str]
) -> Optional["ONVIFCamera"]:
    ensure_optional_dependency("onvif", ONVIFCamera)

    try:
        camera = ONVIFCamera(host, port, username or "", password or "")  # type: ignore[call-arg]
        camera.update_xaddrs()
        return camera
    except Exception as exc:  # pragma: no cover - network
        logger.error("Failed to connect to %s:%s - %s", host, port, exc)
        return None


def enumerate_profiles(camera: "ONVIFCamera", target_profiles: Optional[list[str]] = None):
    media_service = camera.create_media_service()
    profiles = media_service.GetProfiles()

    for profile in profiles:
        token = profile.token
        name = getattr(profile, "Name", token)

        if target_profiles and token not in target_profiles and name not in target_profiles:
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
            logger.error("Unable to fetch stream URI for profile %s: %s", token, exc)
            continue

        yield name, token, uri.Uri  # type: ignore[attr-defined]


def format_rtsp_hint(
    host: str, rtsp_user: Optional[str], rtsp_pass: Optional[str], stream: str
) -> str:
    creds = ""
    if rtsp_user and rtsp_pass:
        creds = f"{rtsp_user}:{rtsp_pass}@"
    elif rtsp_user:
        creds = f"{rtsp_user}@"
    return f"rtsp://{creds}{host}:554/{stream}"


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    hosts: Iterable[str]
    if args.host:
        hosts = [args.host]
    else:
        hosts = discover_hosts(args.timeout)
        if not hosts:
            return 1

    rtsp_user = args.rtsp_username or args.username
    rtsp_pass = args.rtsp_password or args.password

    for host in hosts:
        logger.info("Querying ONVIF device at %s:%s", host, args.port)

        camera = connect_camera(host, args.port, args.username, args.password)
        if camera is None:
            continue

        found = False
        for name, token, uri in enumerate_profiles(camera, args.profiles or None):
            found = True
            print("\nProfile:", name)
            print("  Token:    ", token)
            print("  RTSP URI: ", uri)
            if rtsp_user:
                print(
                    "  Tapo Hint:",
                    format_rtsp_hint(host, rtsp_user, rtsp_pass, "stream1 or stream2"),
                )
        if not found:
            logger.warning("No media profiles returned for %s. Check credentials.", host)

    print(
        "\nTip: Validate the RTSP URL in VLC first. If playback fails, re-check RTSP enablement in the "
        "Tapo app, credentials, IP, that port 554 is open, and try /stream2 for the lower-bandwidth feed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
