import 'package:flutter/material.dart';
import 'package:securevision_flutter/core/models/detection.dart';
import 'package:securevision_flutter/core/models/frame.dart';
import 'package:securevision_flutter/design_system/app_colors.dart';

class DetectionOverlay extends StatelessWidget {
  const DetectionOverlay({super.key, required this.frame});

  final Frame frame;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      painter: DetectionOverlayPainter(frame: frame),
    );
  }
}

class DetectionOverlayPainter extends CustomPainter {
  DetectionOverlayPainter({required this.frame});

  final Frame frame;

  @override
  void paint(Canvas canvas, Size size) {
    if (frame.width <= 0 || frame.height <= 0) {
      return;
    }

    final imageSize = Size(frame.width.toDouble(), frame.height.toDouble());
    final fitted = _fittedRect(size, imageSize);

    for (final detection in frame.detections) {
      final rect = Rect.fromLTWH(
        fitted.left + detection.boundingBox.x * fitted.scaleX,
        fitted.top + detection.boundingBox.y * fitted.scaleY,
        detection.boundingBox.width * fitted.scaleX,
        detection.boundingBox.height * fitted.scaleY,
      );

      final color = _colorForDetection(detection);
      final paint = Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2;

      canvas.drawRect(rect, paint);

      final label = _labelForDetection(detection);
      if (label.isEmpty) {
        continue;
      }

      final textPainter = TextPainter(
        text: TextSpan(
          text: label,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 12,
            fontWeight: FontWeight.w600,
            shadows: [
              Shadow(
                color: Colors.black54,
                offset: Offset(0, 1),
                blurRadius: 2,
              ),
            ],
          ),
        ),
        textDirection: TextDirection.ltr,
      )..layout(maxWidth: rect.width);

      final textOffset = Offset(
        rect.left + 4,
        rect.top - textPainter.height - 4,
      );
      final backgroundRect = Rect.fromLTWH(
        textOffset.dx - 4,
        textOffset.dy - 2,
        textPainter.width + 8,
        textPainter.height + 4,
      );

      final backgroundPaint = Paint()
        ..color = color.withValues(alpha: 0.65)
        ..style = PaintingStyle.fill;

      canvas.drawRRect(
        RRect.fromRectAndRadius(backgroundRect, const Radius.circular(6)),
        backgroundPaint,
      );
      textPainter.paint(canvas, textOffset);
    }
  }

  @override
  bool shouldRepaint(covariant DetectionOverlayPainter oldDelegate) {
    return oldDelegate.frame != frame;
  }

  String _labelForDetection(Detection detection) {
    switch (detection.type) {
      case DetectionType.face:
        final match = detection.faceMatch;
        final label = match?.label ?? match?.personId ?? 'Unknown';
        final confidence = _formatConfidence(detection.confidence);
        return confidence.isNotEmpty ? '$label $confidence' : label;
      case DetectionType.plate:
        final plate = detection.plateRead?.plate ?? 'Plate';
        final confidence = _formatConfidence(detection.confidence);
        return confidence.isNotEmpty ? '$plate $confidence' : plate;
      case DetectionType.unknown:
        return '';
    }
  }

  String _formatConfidence(double value) {
    if (value <= 0) {
      return '';
    }
    final percent = value <= 1 ? value * 100 : value;
    return '${percent.toStringAsFixed(0)}%';
  }

  Color _colorForDetection(Detection detection) {
    switch (detection.type) {
      case DetectionType.face:
        return detection.faceMatch == null
            ? AppColors.mediumGrey
            : AppColors.mutedSage;
      case DetectionType.plate:
        if (detection.plateRead?.listType == 'blacklist') {
          return AppColors.burntOrange;
        }
        if (detection.plateRead?.listType == 'whitelist') {
          return AppColors.mutedSage;
        }
        return AppColors.darkGrey;
      case DetectionType.unknown:
        return AppColors.mediumGrey;
    }
  }
}

class _FittedRect {
  const _FittedRect({
    required this.left,
    required this.top,
    required this.scaleX,
    required this.scaleY,
  });

  final double left;
  final double top;
  final double scaleX;
  final double scaleY;
}

_FittedRect _fittedRect(Size container, Size image) {
  final containerRatio = container.width / container.height;
  final imageRatio = image.width / image.height;
  if (containerRatio > imageRatio) {
    final renderHeight = container.height;
    final renderWidth = renderHeight * imageRatio;
    final left = (container.width - renderWidth) / 2;
    return _FittedRect(
      left: left,
      top: 0,
      scaleX: renderWidth / image.width,
      scaleY: renderHeight / image.height,
    );
  }

  final renderWidth = container.width;
  final renderHeight = renderWidth / imageRatio;
  final top = (container.height - renderHeight) / 2;
  return _FittedRect(
    left: 0,
    top: top,
    scaleX: renderWidth / image.width,
    scaleY: renderHeight / image.height,
  );
}
