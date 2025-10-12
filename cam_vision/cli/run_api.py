#!/usr/bin/env python3
"""CLI to run the SecureVision Events API server."""

import argparse
import logging
import sys

import uvicorn

from ..api.app import create_app
from ..config import load_settings

logger = logging.getLogger(__name__)


def main():
    """Run the FastAPI server."""
    parser = argparse.ArgumentParser(description="SecureVision Events API Server")

    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host to bind to (overrides SECUREVISION__API__HOST)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind to (overrides SECUREVISION__API__PORT)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (development only)",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Load settings
    try:
        settings = load_settings()
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        sys.exit(1)

    # Override with CLI args
    host = args.host if args.host else settings.api.host
    port = args.port if args.port else settings.api.port

    # Create app
    logger.info("Creating FastAPI application...")
    app = create_app(settings)

    # Log configuration
    logger.info(f"API server starting on {host}:{port}")
    logger.info(f"Database: {settings.events.db_url}")
    logger.info(f"WebSocket: {'enabled' if settings.api.ws_enabled else 'disabled'}")
    logger.info(f"Authentication: {'enabled' if settings.api.auth_token else 'disabled'}")
    logger.info(f"Event retention: {settings.events.retention_days} days")

    # Run server
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=args.log_level.lower(),
            reload=args.reload,
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
