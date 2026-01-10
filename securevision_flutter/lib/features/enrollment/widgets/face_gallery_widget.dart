import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:securevision_flutter/design_system/app_colors.dart';

class EnrolledFace {
  EnrolledFace({
    required this.personId,
    required this.thumbnail,
    required this.shotCount,
    required this.enrolledAt,
  });

  final String personId;
  final Uint8List thumbnail;
  final int shotCount;
  final DateTime enrolledAt;
}

class FaceGalleryWidget extends StatelessWidget {
  const FaceGalleryWidget({
    super.key,
    required this.faces,
    required this.onRemove,
  });

  final List<EnrolledFace> faces;
  final ValueChanged<EnrolledFace> onRemove;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.offWhite,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: theme.colorScheme.outlineVariant),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Enrolled Faces',
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w700,
              color: AppColors.jetBlack,
            ),
          ),
          const SizedBox(height: 8),
          if (faces.isEmpty)
            Text(
              'No enrolled faces yet.',
              style: theme.textTheme.bodySmall?.copyWith(
                color: AppColors.darkGrey,
              ),
            )
          else
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                for (final face in faces)
                  _FaceCard(
                    face: face,
                    onRemove: () => onRemove(face),
                  ),
              ],
            ),
        ],
      ),
    );
  }
}

class _FaceCard extends StatelessWidget {
  const _FaceCard({required this.face, required this.onRemove});

  final EnrolledFace face;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return SizedBox(
      width: 150,
      child: Stack(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              borderRadius: BorderRadius.circular(4),
              border: Border.all(color: theme.colorScheme.outlineVariant),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: Image.memory(
                    face.thumbnail,
                    height: 90,
                    width: double.infinity,
                    fit: BoxFit.cover,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  face.personId,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  '${face.shotCount} shots',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.secondary,
                  ),
                ),
              ],
            ),
          ),
          Positioned(
            top: 6,
            right: 6,
            child: Material(
              color: theme.colorScheme.surface.withValues(alpha: 0.9),
              shape: const CircleBorder(),
              child: IconButton(
                icon: const Icon(Icons.close, size: 16),
                onPressed: onRemove,
                tooltip: 'Remove',
              ),
            ),
          ),
        ],
      ),
    );
  }
}
