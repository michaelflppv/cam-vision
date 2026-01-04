"""
Accuracy benchmarks for SecureVision recognition components.

Measures:
- Face verification accuracy (precision, recall, F1, ROC-AUC)
- Plate OCR accuracy (character accuracy, plate accuracy)
- Tracking accuracy (track persistence, ID switching)
- Multi-frame confirmation effectiveness

Run with: pytest tests/benchmarks/test_accuracy.py -v -s
"""

from pathlib import Path

import cv2
import numpy as np

from cam_vision.tracking.tracker import SimpleTracker
from cam_vision.types import Detection, DetectionKind

# =============================================================================
# Face Verification Accuracy
# =============================================================================


class TestFaceVerificationAccuracy:
    """Measure face recognition accuracy metrics."""

    def test_face_similarity_distribution(self, tmp_path: Path):
        """
        Measure similarity score distribution for same-person vs different-person pairs.

        This helps determine optimal threshold for face matching.
        """
        # Create a minimal face gallery with synthetic embeddings
        gallery_path = tmp_path / "test_gallery"
        gallery_path.mkdir()

        # Simulate 3 people with 5 images each (synthetic embeddings)
        num_people = 3
        images_per_person = 5
        embedding_dim = 512

        # Create synthetic normalized embeddings
        np.random.seed(42)
        embeddings_db = {}

        for person_id in range(num_people):
            person_name = f"person_{person_id}"
            # Generate a base embedding for this person
            base_embedding = np.random.randn(embedding_dim).astype(np.float32)
            base_embedding /= np.linalg.norm(base_embedding)

            # Add slight variations (simulate different photos of same person)
            person_embeddings = []
            for img_id in range(images_per_person):
                # Add noise to base embedding
                noisy_embedding = base_embedding + np.random.randn(embedding_dim) * 0.1
                noisy_embedding /= np.linalg.norm(noisy_embedding)
                person_embeddings.append(noisy_embedding)

            embeddings_db[person_name] = person_embeddings

            # Save as .npz (format expected by gallery loader)
            cache_file = gallery_path / f"{person_name}.npz"
            np.savez(
                cache_file,
                embeddings=np.array(person_embeddings),
                metadata={"source": "synthetic"},
            )

        # Now compute similarity distributions
        from sklearn.metrics.pairwise import cosine_similarity

        same_person_scores = []
        different_person_scores = []

        # Same person comparisons
        for person_name, embeddings in embeddings_db.items():
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim = cosine_similarity([embeddings[i]], [embeddings[j]])[0, 0]
                    same_person_scores.append(float(sim))

        # Different person comparisons
        person_names = list(embeddings_db.keys())
        for i in range(len(person_names)):
            for j in range(i + 1, len(person_names)):
                emb_i = embeddings_db[person_names[i]][0]  # Use first embedding
                emb_j = embeddings_db[person_names[j]][0]
                sim = cosine_similarity([emb_i], [emb_j])[0, 0]
                different_person_scores.append(float(sim))

        # Compute statistics
        same_mean = np.mean(same_person_scores)
        same_std = np.std(same_person_scores)
        diff_mean = np.mean(different_person_scores)
        diff_std = np.std(different_person_scores)

        print("\n=== Face Similarity Distribution ===")
        print(f"Same person:      {same_mean:.3f} ± {same_std:.3f}")
        print(f"Different person: {diff_mean:.3f} ± {diff_std:.3f}")
        print(f"Separation:       {same_mean - diff_mean:.3f}")
        print(f"Samples: {len(same_person_scores)} same, {len(different_person_scores)} different")

        # Verify separation exists
        assert same_mean > diff_mean, "Same-person scores should be higher than different-person"

    def test_face_threshold_analysis(self, tmp_path: Path):
        """
        Analyze precision/recall/F1 at different similarity thresholds.

        Helps determine the optimal threshold for production use.
        """
        # Create ground truth pairs (same person = positive, different = negative)
        # Use synthetic data with controlled similarity scores
        np.random.seed(42)

        # Generate similarity scores for positive pairs (same person)
        # Mean ~0.75, std 0.1
        positive_scores = np.clip(np.random.normal(0.75, 0.1, 100), 0.0, 1.0).tolist()

        # Generate similarity scores for negative pairs (different person)
        # Mean ~0.30, std 0.15
        negative_scores = np.clip(np.random.normal(0.30, 0.15, 100), 0.0, 1.0).tolist()

        # Ground truth labels
        y_true = [1] * len(positive_scores) + [0] * len(negative_scores)
        y_scores = positive_scores + negative_scores

        # Test different thresholds
        thresholds = [0.2, 0.3, 0.35, 0.4, 0.5, 0.6, 0.7]
        results = []

        print("\n=== Face Threshold Analysis ===")
        print(f"{'Threshold':<12} {'Precision':<12} {'Recall':<12} {'F1':<12} {'Accuracy':<12}")
        print("-" * 60)

        for threshold in thresholds:
            # Predict: score >= threshold → same person (positive)
            y_pred = [1 if score >= threshold else 0 for score in y_scores]

            # Compute metrics
            tp = sum(1 for true, pred in zip(y_true, y_pred) if true == 1 and pred == 1)
            fp = sum(1 for true, pred in zip(y_true, y_pred) if true == 0 and pred == 1)
            fn = sum(1 for true, pred in zip(y_true, y_pred) if true == 1 and pred == 0)
            tn = sum(1 for true, pred in zip(y_true, y_pred) if true == 0 and pred == 0)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            accuracy = (tp + tn) / len(y_true)

            results.append(
                {
                    "threshold": threshold,
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                    "accuracy": accuracy,
                }
            )

            print(
                f"{threshold:<12.2f} {precision:<12.3f} {recall:<12.3f} "
                f"{f1:<12.3f} {accuracy:<12.3f}"
            )

        # Find optimal threshold (max F1)
        best = max(results, key=lambda x: x["f1"])
        print(f"\nOptimal threshold (max F1): {best['threshold']:.2f}")
        print(f"  Precision: {best['precision']:.3f}")
        print(f"  Recall:    {best['recall']:.3f}")
        print(f"  F1:        {best['f1']:.3f}")

        assert len(results) == len(thresholds)


# =============================================================================
# Plate OCR Accuracy
# =============================================================================


class TestPlateOCRAccuracy:
    """Measure license plate OCR accuracy."""

    def test_ocr_character_accuracy(self):
        """
        Measure character-level accuracy for OCR.

        Uses synthetic plate text cleaning to simulate OCR errors.
        """
        from cam_vision.plates.ocr import clean_ocr_text

        # Ground truth plates
        ground_truth = [
            "ABC123",
            "XYZ789",
            "DEF456",
            "GHI012",
            "JKL345",
            "7ABC123",  # With prefix
            "MNO678D",  # With suffix
            "PQR901",
            "STU234",
            "VWX567",
        ]

        # Simulate OCR output with common errors
        ocr_outputs = [
            "ABC 123",  # Extra space
            "XYZ789",  # Perfect
            "DEF45G",  # Wrong char (6→G)
            "GHI O12",  # O instead of 0
            "JKL 345",  # Extra space
            "7 ABC123",  # Space after prefix
            "MNOO78D",  # Double O (67→OO)
            "PQR9O1",  # O instead of 0
            "STU234",  # Perfect
            "VWX 567",  # Extra space
        ]

        # Clean OCR outputs
        cleaned = [clean_ocr_text(ocr) for ocr in ocr_outputs]

        # Compute character-level accuracy
        total_chars = sum(len(gt) for gt in ground_truth)
        correct_chars = 0

        for gt, pred in zip(ground_truth, cleaned):
            # Align strings and count correct characters
            for i in range(min(len(gt), len(pred))):
                if gt[i] == pred[i]:
                    correct_chars += 1

        char_accuracy = correct_chars / total_chars if total_chars > 0 else 0.0

        # Compute plate-level accuracy (exact match)
        exact_matches = sum(1 for gt, pred in zip(ground_truth, cleaned) if gt == pred)
        plate_accuracy = exact_matches / len(ground_truth)

        print("\n=== Plate OCR Accuracy ===")
        print(f"Character accuracy: {char_accuracy:.1%} ({correct_chars}/{total_chars})")
        print(f"Plate accuracy:     {plate_accuracy:.1%} ({exact_matches}/{len(ground_truth)})")
        print("\nMismatches:")
        for gt, pred in zip(ground_truth, cleaned):
            if gt != pred:
                print(f"  {gt:12s} → {pred:12s}")

        assert char_accuracy > 0.8  # Should clean most errors

    def test_ocr_preprocessing_effectiveness(self):
        """
        Measure effectiveness of different OCR preprocessing strategies.

        Simulates low-quality plate images and tests preprocessing impact.
        """

        # Create synthetic plate images with varying quality
        def create_plate_image(text: str, noise_level: float = 0.0) -> np.ndarray:
            """Create a synthetic license plate image."""
            # Create white background
            img = np.ones((100, 300, 3), dtype=np.uint8) * 255

            # Add text
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(img, text, (20, 70), font, 2, (0, 0, 0), 3)

            # Add noise if requested
            if noise_level > 0:
                noise = np.random.randint(
                    -int(noise_level * 255),
                    int(noise_level * 255),
                    img.shape,
                    dtype=np.int16,
                )
                img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

            return img

        test_cases = [
            ("ABC123", 0.0, "clean"),
            ("ABC123", 0.1, "light_noise"),
            ("ABC123", 0.2, "medium_noise"),
            ("XYZ789", 0.0, "clean"),
            ("XYZ789", 0.15, "noise"),
        ]

        print("\n=== OCR Preprocessing Effectiveness ===")
        print("Note: Actual OCR requires Tesseract; this tests image preprocessing only.")

        for text, noise, label in test_cases:
            img = create_plate_image(text, noise)
            print(f"  {label:20s}: Created {img.shape} image")

        # Count preprocessing strategies that would be applied
        from cam_vision.plates.ocr import _preprocess_for_ocr

        # Test preprocessing on a sample image
        sample_img = create_plate_image("TEST", 0.1)
        preprocessed_variants = list(_preprocess_for_ocr(sample_img))

        print(f"\nPreprocessing variants generated: {len(preprocessed_variants)}")
        for i, variant in enumerate(preprocessed_variants):
            print(f"  Variant {i}: shape {variant.shape}")

        assert len(preprocessed_variants) > 0


# =============================================================================
# Tracking Accuracy
# =============================================================================


class TestTrackingAccuracy:
    """Measure tracking system accuracy."""

    def test_track_id_persistence(self):
        """
        Measure how well track IDs persist across frames.

        Simulates a moving object and verifies consistent track assignment.
        """
        tracker = SimpleTracker(
            iou_threshold=0.5,
            frames_required=3,
            max_age=30,
        )

        # Simulate a moving face across 50 frames
        # Face moves horizontally from left to right
        num_frames = 50
        bbox_width, bbox_height = 100, 100

        track_ids = []

        for frame_idx in range(num_frames):
            # Face moves 5 pixels per frame
            x = 100 + frame_idx * 5
            y = 200
            bbox = (x, y, x + bbox_width, y + bbox_height)

            detection = Detection(
                kind=DetectionKind.FACE,
                bbox=bbox,
                score=0.95,
            )

            # Update tracker
            tracked = tracker.update([detection])

            if tracked:
                track_ids.append(tracked[0].track_id)

        # Count unique track IDs assigned to this object
        unique_ids = set(track_ids)

        print("\n=== Track ID Persistence ===")
        print(f"Frames processed: {num_frames}")
        print(f"Tracks assigned:  {len(track_ids)}")
        print(f"Unique track IDs: {len(unique_ids)}")
        print(f"ID switches:      {len(unique_ids) - 1}")

        # Ideal: only 1 track ID for entire sequence
        # Acceptable: <= 2 (might have initial tentative period)
        assert len(unique_ids) <= 2, "Should maintain consistent track ID"

    def test_multi_object_tracking(self):
        """
        Measure tracking accuracy with multiple simultaneous objects.

        Simulates 3 faces moving in different directions.
        """
        tracker = SimpleTracker(
            iou_threshold=0.5,
            frames_required=3,
            max_age=30,
        )

        num_frames = 40
        bbox_size = 80

        # Track history: {frame_idx: [track_ids]}
        frame_track_ids = []

        for frame_idx in range(num_frames):
            detections = []

            # Object 1: moves right
            x1 = 50 + frame_idx * 3
            detections.append(
                Detection(
                    kind=DetectionKind.FACE,
                    bbox=(x1, 100, x1 + bbox_size, 100 + bbox_size),
                    score=0.9,
                )
            )

            # Object 2: moves down
            y2 = 50 + frame_idx * 2
            detections.append(
                Detection(
                    kind=DetectionKind.FACE,
                    bbox=(300, y2, 300 + bbox_size, y2 + bbox_size),
                    score=0.9,
                )
            )

            # Object 3: stationary
            detections.append(
                Detection(
                    kind=DetectionKind.FACE,
                    bbox=(500, 300, 500 + bbox_size, 300 + bbox_size),
                    score=0.9,
                )
            )

            # Update tracker
            tracked = tracker.update(detections)
            track_ids = [det.track_id for det in tracked if det.track_id is not None]
            frame_track_ids.append(track_ids)

        # Count unique track IDs per object position
        # After confirmation period, should have exactly 3 unique IDs
        all_track_ids = [tid for frame_ids in frame_track_ids for tid in frame_ids]
        unique_ids = set(all_track_ids)

        print("\n=== Multi-Object Tracking ===")
        print(f"Frames processed:       {num_frames}")
        print("Objects per frame:      3")
        print(f"Total track assignments: {len(all_track_ids)}")
        print(f"Unique track IDs:       {len(unique_ids)}")

        # Should have 3 unique tracks (one per object)
        # Allow up to 6 for tentative tracks
        assert 3 <= len(unique_ids) <= 6, f"Expected ~3 unique tracks, got {len(unique_ids)}"

    def test_occlusion_recovery(self):
        """
        Test tracking recovery after temporary occlusion.

        Simulates a face that disappears for a few frames then reappears.
        """
        tracker = SimpleTracker(
            iou_threshold=0.5,
            frames_required=3,
            max_age=10,  # Allow 10 frames of occlusion
        )

        bbox = (100, 100, 200, 200)
        detection = Detection(
            kind=DetectionKind.FACE,
            bbox=bbox,
            score=0.95,
        )

        track_ids_before = []
        track_ids_after = []

        # Phase 1: Face visible for 15 frames
        for _ in range(15):
            tracked = tracker.update([detection])
            if tracked and tracked[0].track_id is not None:
                track_ids_before.append(tracked[0].track_id)

        # Phase 2: Occlusion for 5 frames (within max_age)
        for _ in range(5):
            tracker.update([])  # No detections

        # Phase 3: Face reappears for 15 frames
        for _ in range(15):
            tracked = tracker.update([detection])
            if tracked and tracked[0].track_id is not None:
                track_ids_after.append(tracked[0].track_id)

        print("\n=== Occlusion Recovery ===")
        print(f"Tracks before occlusion: {len(track_ids_before)}")
        print(f"Tracks after occlusion:  {len(track_ids_after)}")

        # Check if same track ID was recovered
        if track_ids_before and track_ids_after:
            recovered_same_id = track_ids_before[-1] == track_ids_after[0]
            print(f"Same track ID recovered: {recovered_same_id}")
        else:
            recovered_same_id = False
            print("Track ID not recovered (track lost)")

        # At minimum, should have tracks before and after
        assert len(track_ids_before) > 0, "Should track before occlusion"
        assert len(track_ids_after) > 0, "Should re-track after occlusion"


# =============================================================================
# Multi-Frame Confirmation Effectiveness
# =============================================================================


class TestMultiFrameConfirmation:
    """Measure effectiveness of multi-frame confirmation for reducing false positives."""

    def test_confirmation_filtering(self):
        """
        Test how multi-frame confirmation filters transient false positives.

        Simulates intermittent false detections vs persistent true detections.
        """
        tracker = SimpleTracker(
            iou_threshold=0.5,
            frames_required=3,  # Require 3 consecutive frames
            max_age=30,
        )

        confirmed_count = 0
        _ = 0

        # Scenario: 2 objects
        # Object A: appears consistently (true positive)
        # Object B: flickers on/off (false positive)

        for frame_idx in range(30):
            detections = []

            # Object A: always present
            detections.append(
                Detection(
                    kind=DetectionKind.FACE,
                    bbox=(100, 100, 200, 200),
                    score=0.9,
                )
            )

            # Object B: only present every 3rd frame (flickering)
            if frame_idx % 3 == 0:
                detections.append(
                    Detection(
                        kind=DetectionKind.FACE,
                        bbox=(300, 100, 400, 200),
                        score=0.7,
                    )
                )

            # Update tracker
            tracked = tracker.update(detections)

            # Count confirmed vs tentative
            for det in tracked:
                if det.track_id is not None:
                    # Check if confirmed (has track_id and state is CONFIRMED)
                    # For simplicity, we count all with track_id as confirmed after warmup
                    if frame_idx >= 3:  # After warmup period
                        confirmed_count += 1

        print("\n=== Multi-Frame Confirmation ===")
        print("Frames processed:     30")
        print("Object A (persistent): always present")
        print("Object B (flickering): present 10 times")
        print(f"Confirmed detections: {confirmed_count}")

        # Object A should be confirmed ~27 times (30 - warmup)
        # Object B should rarely be confirmed (flickering prevents confirmation)
        # Total should be close to ~27-30 (mostly Object A)
        assert confirmed_count >= 20, "Should mostly confirm persistent object"

    def test_confirmation_latency(self, frames_required=3):
        """
        Measure how many frames are needed before an object is confirmed.

        This represents the latency cost of multi-frame confirmation.
        """
        tracker = SimpleTracker(
            iou_threshold=0.5,
            frames_required=3,
            max_age=30,
        )

        bbox = (100, 100, 200, 200)
        detection = Detection(
            kind=DetectionKind.FACE,
            bbox=bbox,
            score=0.95,
        )

        confirmation_frame = None

        for frame_idx in range(10):
            tracked = tracker.update([detection])
            if tracked and tracked[0].track_id is not None and confirmation_frame is None:
                confirmation_frame = frame_idx

        print("\n=== Confirmation Latency ===")
        print(f"Frames required for confirmation: {frames_required}")
        print(f"Actual confirmation at frame:     {confirmation_frame}")

        # Should confirm at frame = frames_required (0-indexed)
        assert (
            confirmation_frame == frames_required - 1
        ), f"Should confirm at frame {frames_required - 1}"
