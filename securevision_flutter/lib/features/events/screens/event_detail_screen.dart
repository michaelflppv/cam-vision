import 'package:flutter/material.dart';
import 'package:securevision_flutter/core/models/detection.dart';
import 'package:securevision_flutter/core/models/event.dart';
import 'package:securevision_flutter/design_system/components/app_section.dart';

class EventDetailScreen extends StatelessWidget {
  const EventDetailScreen({super.key, required this.event});

  final Event event;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Event Detail'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          AppSection(
            title: 'Summary',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _titleFor(event),
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  _formatTimestamp(event.timestamp),
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.secondary,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          AppSection(
            title: 'Detection',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: _buildDetectionDetails(theme, event.detection),
            ),
          ),
          const SizedBox(height: 16),
          AppSection(
            title: 'Metadata',
            child: event.metadata.isEmpty
                ? Text(
                    'No metadata recorded.',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.secondary,
                    ),
                  )
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: event.metadata.entries
                        .map(
                          (entry) => Padding(
                            padding: const EdgeInsets.only(bottom: 6),
                            child: Text(
                              '${entry.key}: ${entry.value}',
                              style: theme.textTheme.bodySmall,
                            ),
                          ),
                        )
                        .toList(),
                  ),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildDetectionDetails(ThemeData theme, Detection detection) {
    final rows = <Widget>[
      Text(
        'Type: ${detectionTypeToString(detection.type)}',
        style: theme.textTheme.bodyMedium,
      ),
      const SizedBox(height: 6),
      Text(
        'Confidence: ${(detection.confidence * 100).toStringAsFixed(1)}%',
        style: theme.textTheme.bodyMedium,
      ),
      const SizedBox(height: 6),
      Text(
        'Bounding box: '
        '${detection.boundingBox.width.toStringAsFixed(1)}x'
        '${detection.boundingBox.height.toStringAsFixed(1)}',
        style: theme.textTheme.bodyMedium,
      ),
    ];

    if (detection.trackId != null) {
      rows.add(const SizedBox(height: 6));
      rows.add(
        Text(
          'Track ID: ${detection.trackId}',
          style: theme.textTheme.bodyMedium,
        ),
      );
    }

    if (detection.faceMatch != null) {
      rows.add(const SizedBox(height: 6));
      rows.add(
        Text(
          'Match: ${detection.faceMatch!.label}',
          style: theme.textTheme.bodyMedium,
        ),
      );
    }

    if (detection.plateRead != null) {
      rows.add(const SizedBox(height: 6));
      rows.add(
        Text(
          'Plate: ${detection.plateRead!.plate}',
          style: theme.textTheme.bodyMedium,
        ),
      );
      final listType = detection.plateRead!.listType;
      if (listType != null && listType.isNotEmpty) {
        rows.add(const SizedBox(height: 6));
        rows.add(
          Text(
            'List: $listType',
            style: theme.textTheme.bodyMedium,
          ),
        );
      }
    }

    return rows;
  }

  String _titleFor(Event event) {
    switch (event.detection.type) {
      case DetectionType.face:
        return event.detection.faceMatch?.label ?? 'Unknown face';
      case DetectionType.plate:
        return event.detection.plateRead?.plate ?? 'Plate read';
      case DetectionType.unknown:
        return event.type;
    }
  }

  String _formatTimestamp(DateTime value) {
    final local = value.toLocal();
    final month = local.month.toString().padLeft(2, '0');
    final day = local.day.toString().padLeft(2, '0');
    final hour = local.hour.toString().padLeft(2, '0');
    final minute = local.minute.toString().padLeft(2, '0');
    final second = local.second.toString().padLeft(2, '0');
    return '$month/$day $hour:$minute:$second';
  }
}
