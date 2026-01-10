import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:securevision_flutter/core/models/detection.dart';
import 'package:securevision_flutter/core/models/frame.dart';
import 'package:securevision_flutter/design_system/app_borders.dart';
import 'package:securevision_flutter/design_system/app_colors.dart';
import 'package:securevision_flutter/design_system/app_spacing.dart';
import 'package:securevision_flutter/features/live_view/controllers/live_view_controller.dart';
import 'package:securevision_flutter/features/live_view/controllers/live_view_provider.dart';
import 'package:securevision_flutter/features/live_view/widgets/face_matches_panel.dart';
import 'package:securevision_flutter/features/live_view/widgets/plate_detections_panel.dart';
import 'package:securevision_flutter/features/live_view/widgets/stats_overlay.dart';
import 'package:securevision_flutter/features/live_view/widgets/video_preview.dart';
import 'package:securevision_flutter/providers/settings_provider.dart';

class LiveViewScreen extends ConsumerStatefulWidget {
  const LiveViewScreen({super.key});

  @override
  ConsumerState<LiveViewScreen> createState() => _LiveViewScreenState();
}

class _LiveViewScreenState extends ConsumerState<LiveViewScreen> {
  bool _started = false;

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(liveViewControllerProvider);
    final settings = ref.watch(settingsProvider);
    if (!_started && !settings.isLoading) {
      _started = true;
      Future.microtask(() {
        ref.read(liveViewControllerProvider.notifier).start(
              source: settings.source,
              enableFaces: settings.enableFace,
              enablePlates: settings.enablePlate,
              targetFps: settings.targetFps,
            );
      });
    }
    final frame = state.latestFrame;
    final detections = frame?.detections ?? <Detection>[];
    final faceDetections = detections
        .where((detection) => detection.type == DetectionType.face)
        .toList();
    final plateDetections = detections
        .where((detection) => detection.type == DetectionType.plate)
        .toList();
    final detectionCount = detections.length;
    final frameId = frame?.id ?? '—';
    final frameLabel = _shortenFrameId(frameId);

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text('Live View'),
        actions: [
          IconButton(
            onPressed: state.isRunning
                ? () => ref.read(liveViewControllerProvider.notifier).stop()
                : () => ref
                    .read(liveViewControllerProvider.notifier)
                    .start(
                      source: settings.source,
                      enableFaces: settings.enableFace,
                      enablePlates: settings.enablePlate,
                      targetFps: settings.targetFps,
                    ),
            icon: Icon(state.isRunning ? Icons.stop : Icons.play_arrow),
            tooltip: state.isRunning ? 'Stop capture' : 'Start capture',
          ),
        ],
      ),
      body: LayoutBuilder(
          builder: (context, constraints) {
            final isWide = constraints.maxWidth >= 960;
            final preview =
                _buildPreview(context, state, frameLabel, detectionCount, frame);
            final panels = _buildPanels(context, faceDetections, plateDetections);
            if (isWide) {
              return Row(
                children: [
                  Expanded(child: preview),
                  const SizedBox(width: 16),
                  SizedBox(width: 360, child: panels),
                ],
              );
            }
            return Column(
              children: [
                Expanded(child: preview),
                const SizedBox(height: 16),
                Expanded(child: panels),
              ],
            );
          },
        ),
    );
  }

  Widget _buildPreview(
    BuildContext context,
    LiveViewState state,
    String frameId,
    int detectionCount,
    Frame? frame,
  ) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: ClipRRect(
        borderRadius: AppBorders.minimalRadius,
        child: Stack(
          fit: StackFit.expand,
          children: [
            VideoPreview(
              imageBytes: state.latestImage,
              frame: frame,
            ),
            Positioned(
              top: 16,
              left: 16,
              child: StatsOverlay(
                isRunning: state.isRunning,
                fps: state.fps,
                detectionCount: detectionCount,
              ),
            ),
            if (state.isStarting)
              const Positioned(
                bottom: 16,
                left: 16,
                child: _StatusBadge(label: 'Starting capture...'),
              ),
            if (state.errorMessage != null)
              Positioned(
                bottom: 16,
                right: 16,
                child: _StatusBadge(
                  label: state.errorMessage!,
                  isError: true,
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildPanels(
    BuildContext context,
    List<Detection> faceDetections,
    List<Detection> plateDetections,
  ) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
      child: Column(
        children: [
          FaceMatchesPanel(detections: faceDetections),
          const SizedBox(height: 16),
          PlateDetectionsPanel(detections: plateDetections),
        ],
      ),
    );
  }

  String _shortenFrameId(String value) {
    if (value == '—') {
      return value;
    }
    final parts = value.split('-');
    if (parts.length > 1) {
      return parts.last;
    }
    if (value.length > 10) {
      return value.substring(value.length - 10);
    }
    return value;
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.label, this.isError = false});

  final String label;
  final bool isError;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = isError ? AppColors.burntOrange : AppColors.mutedSage;
    final bgColor = theme.colorScheme.surfaceContainerHighest;
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.md,
        vertical: AppSpacing.sm,
      ),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: AppBorders.minimalRadius,
        border: Border.all(
          color: theme.colorScheme.outline,
          width: AppBorders.thin,
        ),
      ),
      child: Text(
        label,
        style: theme.textTheme.labelMedium?.copyWith(
          color: color,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
