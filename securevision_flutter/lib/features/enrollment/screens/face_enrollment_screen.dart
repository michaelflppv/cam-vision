import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:securevision_flutter/design_system/app_colors.dart';
import 'package:securevision_flutter/features/enrollment/widgets/camera_capture_widget.dart';
import 'package:securevision_flutter/features/enrollment/widgets/face_gallery_widget.dart';
import 'package:securevision_flutter/providers/python_bridge_provider.dart';

class FaceEnrollmentScreen extends ConsumerStatefulWidget {
  const FaceEnrollmentScreen({super.key});

  @override
  ConsumerState<FaceEnrollmentScreen> createState() => _FaceEnrollmentScreenState();
}

class _FaceEnrollmentScreenState extends ConsumerState<FaceEnrollmentScreen> {
  static const int _minShots = 3;
  static const int _maxShots = 5;

  final TextEditingController _personController = TextEditingController();
  final List<Uint8List> _captures = [];
  final List<EnrolledFace> _enrolled = [];
  String? _statusMessage;
  bool _isEnrolling = false;

  @override
  void dispose() {
    _personController.dispose();
    super.dispose();
  }

  Future<void> _handleCapture(Uint8List bytes) async {
    if (_captures.length >= _maxShots) {
      return;
    }
    setState(() {
      _captures.add(bytes);
      _statusMessage = null;
    });
  }

  void _clearCaptures() {
    setState(() {
      _captures.clear();
      _statusMessage = null;
    });
  }

  Future<void> _enroll() async {
    final personId = _personController.text.trim();
    if (personId.isEmpty) {
      setState(() {
        _statusMessage = 'Enter a person name or ID before enrolling.';
      });
      return;
    }
    if (_captures.length < _minShots) {
      setState(() {
        _statusMessage = 'Capture at least $_minShots shots to enroll.';
      });
      return;
    }

    setState(() {
      _isEnrolling = true;
      _statusMessage = null;
    });

    final bridge = ref.read(pythonBridgeProvider);
    try {
      for (final capture in _captures) {
        await bridge.enrollFace(capture, personId);
      }
      if (!mounted) {
        return;
      }
      setState(() {
        _enrolled.insert(
          0,
          EnrolledFace(
            personId: personId,
            thumbnail: _captures.first,
            shotCount: _captures.length,
            enrolledAt: DateTime.now(),
          ),
        );
        _captures.clear();
        _statusMessage = 'Enrollment complete for $personId.';
      });
    } catch (exc) {
      if (mounted) {
        setState(() {
          _statusMessage = 'Enrollment failed: $exc';
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _isEnrolling = false;
        });
      }
    }
  }

  void _removeEnrollment(EnrolledFace face) {
    setState(() {
      _enrolled.remove(face);
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final shotProgress = _captures.length / _maxShots;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.offWhite,
              borderRadius: BorderRadius.circular(4),
              border: Border.all(color: theme.colorScheme.outlineVariant),
            ),
            child: Row(
              children: [
                const Icon(Icons.auto_awesome, color: AppColors.jetBlack),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'Capture $_minShots-$_maxShots clear headshots for each person.',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: AppColors.darkGrey,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _personController,
            decoration: const InputDecoration(
              labelText: 'Person ID',
              hintText: 'e.g. alex_johnson',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          CameraCaptureWidget(
            onCapture: _handleCapture,
            captureEnabled: _captures.length < _maxShots && !_isEnrolling,
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Text(
                'Shots: ${_captures.length} / $_maxShots',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.secondary,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: LinearProgressIndicator(
                  value: shotProgress.clamp(0.0, 1.0),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              for (var index = 0; index < _captures.length; index++)
                Stack(
                  children: [
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: Image.memory(
                        _captures[index],
                        width: 72,
                        height: 72,
                        fit: BoxFit.cover,
                      ),
                    ),
                    Positioned(
                      top: 4,
                      right: 4,
                      child: InkWell(
                        onTap: _isEnrolling
                            ? null
                            : () {
                                setState(() {
                                  _captures.removeAt(index);
                                });
                              },
                        child: Container(
                          padding: const EdgeInsets.all(4),
                          decoration: BoxDecoration(
                            color: AppColors.jetBlack.withValues(alpha: 0.6),
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(
                            Icons.close,
                            size: 12,
                            color: AppColors.pureWhite,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              OutlinedButton(
                onPressed: _captures.isEmpty || _isEnrolling ? null : _clearCaptures,
                child: const Text('Clear'),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: _isEnrolling ? null : _enroll,
                  icon: const Icon(Icons.check_circle_outline),
                  label: Text(_isEnrolling ? 'Enrolling...' : 'Enroll'),
                ),
              ),
            ],
          ),
          if (_statusMessage != null) ...[
            const SizedBox(height: 12),
            Text(
              _statusMessage!,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.secondary,
              ),
            ),
          ],
          const SizedBox(height: 24),
          FaceGalleryWidget(
            faces: _enrolled,
            onRemove: _removeEnrollment,
          ),
        ],
      ),
    );
  }
}
