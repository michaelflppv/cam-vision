import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:securevision_flutter/core/models/frame.dart';
import 'package:securevision_flutter/features/live_view/widgets/detection_overlay.dart';

class VideoPreview extends StatefulWidget {
  const VideoPreview({super.key, required this.imageBytes, required this.frame});

  final Uint8List? imageBytes;
  final Frame? frame;

  @override
  State<VideoPreview> createState() => _VideoPreviewState();
}

class _VideoPreviewState extends State<VideoPreview> {
  final TransformationController _transformController =
      TransformationController();

  @override
  void dispose() {
    _transformController.dispose();
    super.dispose();
  }

  void _resetZoom() {
    _transformController.value = Matrix4.identity();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (widget.imageBytes == null) {
      return Container(
        color: theme.colorScheme.surface,
        alignment: Alignment.center,
        child: Text(
          'Waiting for video stream',
          style: theme.textTheme.titleMedium,
        ),
      );
    }

    final preview = Stack(
      fit: StackFit.expand,
      children: [
        Container(
          color: Colors.black,
          alignment: Alignment.center,
          child: Image.memory(
            widget.imageBytes!,
            fit: BoxFit.contain,
            gaplessPlayback: true,
            filterQuality: FilterQuality.low,
          ),
        ),
        if (widget.frame != null)
          Positioned.fill(
            child: RepaintBoundary(child: DetectionOverlay(frame: widget.frame!)),
          ),
      ],
    );

    return LayoutBuilder(
      builder: (context, constraints) {
        return GestureDetector(
          onDoubleTap: _resetZoom,
          child: InteractiveViewer(
            transformationController: _transformController,
            minScale: 1.0,
            maxScale: 4.0,
            boundaryMargin: const EdgeInsets.all(80),
            child: SizedBox(
              width: constraints.maxWidth,
              height: constraints.maxHeight,
              child: preview,
            ),
          ),
        );
      },
    );
  }
}
