import 'dart:io';
import 'dart:typed_data';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:securevision_flutter/design_system/app_colors.dart';

class CameraCaptureWidget extends StatefulWidget {
  const CameraCaptureWidget({
    super.key,
    required this.onCapture,
    this.captureEnabled = true,
  });

  final Future<void> Function(Uint8List bytes) onCapture;
  final bool captureEnabled;

  @override
  State<CameraCaptureWidget> createState() => _CameraCaptureWidgetState();
}

class _CameraCaptureWidgetState extends State<CameraCaptureWidget> {
  CameraController? _controller;
  Future<void>? _initializeFuture;
  String? _error;
  bool _isCapturing = false;
  final ImagePicker _imagePicker = ImagePicker();

  @override
  void initState() {
    super.initState();
    // Only try camera on mobile platforms
    if (Platform.isAndroid || Platform.isIOS) {
      _initializeFuture = _initializeCamera();
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        setState(() {
          _error = 'No cameras available on this device.';
        });
        return;
      }
      final selected = cameras.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );
      final controller = CameraController(
        selected,
        ResolutionPreset.medium,
        enableAudio: false,
      );
      await controller.initialize();
      if (!mounted) {
        return;
      }
      setState(() {
        _controller = controller;
      });
    } catch (exc) {
      if (!mounted) {
        return;
      }
      setState(() {
        _error = 'Camera init failed: $exc';
      });
    }
  }

  Future<void> _capture() async {
    final controller = _controller;
    if (controller == null || !controller.value.isInitialized) {
      return;
    }
    if (_isCapturing || !widget.captureEnabled) {
      return;
    }
    setState(() {
      _isCapturing = true;
    });
    try {
      final file = await controller.takePicture();
      final bytes = await file.readAsBytes();
      await widget.onCapture(bytes);
    } catch (exc) {
      if (mounted) {
        setState(() {
          _error = 'Capture failed: $exc';
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _isCapturing = false;
        });
      }
    }
  }

  Future<void> _pickImage() async {
    if (!widget.captureEnabled) {
      return;
    }

    setState(() {
      _isCapturing = true;
      _error = null;
    });

    try {
      final XFile? pickedFile = await _imagePicker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 1920,
        maxHeight: 1920,
        imageQuality: 85,
      );

      if (pickedFile == null) {
        // User cancelled
        return;
      }

      final bytes = await pickedFile.readAsBytes();
      await widget.onCapture(bytes);
    } catch (exc) {
      if (mounted) {
        setState(() {
          _error = 'Failed to load image: $exc';
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _isCapturing = false;
        });
      }
    }
  }

  void _retry() {
    setState(() {
      _error = null;
      _controller?.dispose();
      _controller = null;
      _initializeFuture = _initializeCamera();
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDesktop = Platform.isMacOS || Platform.isWindows || Platform.isLinux;

    // Desktop: show file picker UI
    if (isDesktop) {
      return _FilePickerCard(
        onPickImage: _pickImage,
        isCapturing: _isCapturing,
        captureEnabled: widget.captureEnabled,
        error: _error,
      );
    }

    // Mobile: show camera UI
    if (_error != null) {
      return _ErrorCard(message: _error!, onRetry: _retry);
    }

    return FutureBuilder<void>(
      future: _initializeFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done ||
            _controller == null) {
          return _LoadingCard();
        }
        final controller = _controller!;
        return Container(
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            borderRadius: BorderRadius.circular(4),
            border: Border.all(color: theme.colorScheme.outlineVariant),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: Stack(
              fit: StackFit.expand,
              children: [
                AspectRatio(
                  aspectRatio: controller.value.aspectRatio,
                  child: CameraPreview(controller),
                ),
                Positioned(
                  bottom: 16,
                  right: 16,
                  child: FloatingActionButton(
                    onPressed: widget.captureEnabled ? _capture : null,
                    backgroundColor: AppColors.jetBlack,
                    child: _isCapturing
                        ? const SizedBox(
                            width: 24,
                            height: 24,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: AppColors.pureWhite,
                            ),
                          )
                        : const Icon(Icons.camera_alt),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _LoadingCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: theme.colorScheme.outlineVariant),
      ),
      child: Row(
        children: [
          const SizedBox(
            width: 24,
            height: 24,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
          const SizedBox(width: 12),
          Text(
            'Starting camera...',
            style: theme.textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }
}

class _ErrorCard extends StatelessWidget {
  const _ErrorCard({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.burntOrange.withValues(alpha:0.15),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: AppColors.burntOrange),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Camera unavailable',
            style: theme.textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.w700,
              color: AppColors.burntOrange,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            message,
            style: theme.textTheme.bodySmall?.copyWith(
              color: AppColors.darkGrey,
            ),
          ),
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: onRetry,
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }
}

class _FilePickerCard extends StatelessWidget {
  const _FilePickerCard({
    required this.onPickImage,
    required this.isCapturing,
    required this.captureEnabled,
    this.error,
  });

  final VoidCallback onPickImage;
  final bool isCapturing;
  final bool captureEnabled;
  final String? error;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: theme.colorScheme.outlineVariant),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.add_photo_alternate_outlined,
            size: 64,
            color: AppColors.mutedSage.withValues(alpha:0.6),
          ),
          const SizedBox(height: 16),
          Text(
            'Select Face Image',
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Choose a clear headshot photo from your files',
            textAlign: TextAlign.center,
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.secondary,
            ),
          ),
          if (error != null) ...[
            const SizedBox(height: 12),
            Text(
              error!,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodySmall?.copyWith(
                color: AppColors.burntOrange,
              ),
            ),
          ],
          const SizedBox(height: 20),
          ElevatedButton.icon(
            onPressed: captureEnabled && !isCapturing ? onPickImage : null,
            icon: isCapturing
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.upload_file),
            label: Text(isCapturing ? 'Loading...' : 'Choose Image'),
          ),
        ],
      ),
    );
  }
}
