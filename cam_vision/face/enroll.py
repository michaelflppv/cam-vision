"""CLI tool for enrolling trusted faces into gallery."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .gallery import FaceGallery
from .loader import FaceModels

logger = logging.getLogger(__name__)


def enroll_gallery(
    gallery_path: str, cache_path: str, force_rebuild: bool = False, verbose: bool = False
) -> int:
    """
    Enroll faces from gallery_path into cache.

    Args:
        gallery_path: Folder containing person subfolders with images
        cache_path: Path to save precomputed embeddings
        force_rebuild: Rebuild even if cache exists
        verbose: Verbose logging

    Returns:
        Number of persons enrolled, or -1 on error
    """
    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        # Load models (will download on first use)
        logger.info("Loading InsightFace models...")
        models = FaceModels.get_models()

        # Create gallery
        gallery = FaceGallery(gallery_path=gallery_path, cache_path=cache_path)

        # Build gallery
        logger.info(f"Building gallery from {gallery_path}...")
        num_enrolled = gallery.build(embedder=models, force_rebuild=force_rebuild)

        if num_enrolled == 0:
            logger.warning("No persons enrolled (cache may already exist, use --force to rebuild)")
            return 0

        logger.info(f"Successfully enrolled {num_enrolled} persons")
        logger.info(f"Gallery cache saved to: {cache_path}")

        return num_enrolled

    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        return -1
    except ValueError as e:
        logger.error(f"Error: {e}")
        return -1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        return -1


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Enroll trusted faces into gallery for recognition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Enroll faces from default gallery folder
  securevision-face-enroll --gallery ./data/faces/trusted

  # Use custom cache location
  securevision-face-enroll --gallery ./my_faces --cache ./my_gallery.npz

  # Force rebuild of existing cache
  securevision-face-enroll --gallery ./data/faces/trusted --force

Gallery folder structure:
  gallery_path/
    john_doe/
      photo1.jpg
      photo2.jpg
    jane_smith/
      photo1.png
      photo2.png

Each person should have 1-3 clear headshot images for best results.
        """,
    )

    parser.add_argument(
        "--gallery",
        type=str,
        default="./data/faces/trusted",
        help="Path to gallery folder with person subfolders (default: ./data/faces/trusted)",
    )

    parser.add_argument(
        "--cache",
        type=str,
        default="./data/faces/gallery.npz",
        help="Path to save/load gallery cache (default: ./data/faces/gallery.npz)",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rebuild even if cache exists",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose logging",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point for CLI."""
    args = parse_args()

    # Validate gallery path
    gallery_path = Path(args.gallery)
    if not gallery_path.exists():
        print(f"Error: Gallery path not found: {gallery_path}")
        print("Create folder structure: gallery/person_name/*.jpg")
        return 1

    if not gallery_path.is_dir():
        print(f"Error: Gallery path is not a directory: {gallery_path}")
        return 1

    print("=" * 60)
    print("Face Enrollment Tool")
    print("=" * 60)
    print(f"Gallery path:  {gallery_path.absolute()}")
    print(f"Cache path:    {args.cache}")
    print(f"Force rebuild: {args.force}")
    print("=" * 60)
    print()

    # Run enrollment
    num_enrolled = enroll_gallery(
        gallery_path=args.gallery,
        cache_path=args.cache,
        force_rebuild=args.force,
        verbose=args.verbose,
    )

    if num_enrolled < 0:
        print("\nEnrollment failed. Check errors above.")
        return 1

    if num_enrolled == 0:
        print("\nNo persons enrolled.")
        return 0

    print("\n" + "=" * 60)
    print(f"SUCCESS: Enrolled {num_enrolled} persons")
    print("=" * 60)
    print(f"\nGallery cache: {args.cache}")
    print("Use securevision-face-demo to test recognition")

    return 0


if __name__ == "__main__":
    sys.exit(main())
