import 'dart:io';

import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';

/// Manages copying bundled assets to persistent storage for mobile devices.
///
/// On mobile (iOS/Android), bundled assets are read-only. This service:
/// - Copies Python backend code to app documents directory
/// - Copies YOLO model weights to app support directory
/// - Creates writable directories for face gallery and data
class AssetManagerService {
  bool _initialized = false;
  String? _appSupportDir;
  String? _appDocumentsDir;

  /// Paths after initialization
  String get pythonModulePath => '$_appSupportDir/cam_vision';
  String get weightsPath => '$_appSupportDir/weights';
  String get dataPath => '$_appDocumentsDir/data';
  String get faceGalleryPath => '$dataPath/faces/trusted';
  String get faceGalleryCachePath => '$dataPath/faces/gallery.npz';

  Future<void> initialize() async {
    if (_initialized) {
      return;
    }

    // Desktop platforms don't need asset copying
    if (Platform.isMacOS || Platform.isWindows || Platform.isLinux) {
      _initialized = true;
      return;
    }

    // Get persistent directories
    _appSupportDir = (await getApplicationSupportDirectory()).path;
    _appDocumentsDir = (await getApplicationDocumentsDirectory()).path;

    // Copy Python backend modules (read-only, bundled with app)
    await _copyPythonModules();

    // Copy YOLO model weights (read-only, bundled with app)
    await _copyWeights();

    // Create writable data directories
    await _createDataDirectories();

    _initialized = true;
  }

  Future<void> _copyPythonModules() async {
    final targetDir = Directory(pythonModulePath);
    if (targetDir.existsSync()) {
      // Already copied, skip
      return;
    }

    targetDir.createSync(recursive: true);

    // List of Python modules to copy
    final modules = [
      'cam_vision/config.py',
      'cam_vision/__init__.py',
      'cam_vision/face/',
      'cam_vision/plates/',
      'cam_vision/pipeline/',
      'cam_vision/io/',
      'cam_vision/ui/',
      'cam_vision/flutter_bridge/',
    ];

    for (final module in modules) {
      try {
        await _copyAssetRecursively(module, pythonModulePath);
      } catch (e) {
        print('Warning: Failed to copy Python module $module: $e');
      }
    }
  }

  Future<void> _copyWeights() async {
    final targetDir = Directory(weightsPath);
    targetDir.createSync(recursive: true);

    final weightsFile = File('$weightsPath/yolov8n_plate.pt');
    if (weightsFile.existsSync()) {
      // Already copied
      return;
    }

    try {
      final data = await rootBundle.load('weights/yolov8n_plate.pt');
      await weightsFile.writeAsBytes(
        data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes),
      );
    } catch (e) {
      print('Warning: Failed to copy YOLO weights: $e');
    }
  }

  Future<void> _createDataDirectories() async {
    // Create face gallery directories
    Directory(faceGalleryPath).createSync(recursive: true);

    // Create other data directories as needed
    Directory('$dataPath/plates').createSync(recursive: true);
    Directory('$dataPath/events').createSync(recursive: true);
  }

  Future<void> _copyAssetRecursively(
    String assetPath,
    String targetBasePath,
  ) async {
    try {
      // This is a simplified approach - in production, parse AssetManifest.json properly
      // For now, try to copy individual known files

      if (assetPath.endsWith('/')) {
        // Directory - try known file patterns
        await _copyDirectoryContents(assetPath, targetBasePath);
      } else {
        // Single file
        await _copySingleAsset(assetPath, targetBasePath);
      }
    } catch (e) {
      print('Error copying asset $assetPath: $e');
    }
  }

  Future<void> _copyDirectoryContents(
    String assetDir,
    String targetBasePath,
  ) async {
    // Known file patterns for each module
    final patterns = {
      'cam_vision/face/': [
        '__init__.py',
        'gallery.py',
        'loader.py',
        'recognizer.py',
      ],
      'cam_vision/plates/': [
        '__init__.py',
        'detector.py',
        'lists.py',
        'ocr.py',
        'pipeline.py',
      ],
      'cam_vision/pipeline/': [
        '__init__.py',
        'base.py',
        'confirm.py',
        'graph.py',
      ],
      'cam_vision/io/': [
        '__init__.py',
        'capture.py',
      ],
      'cam_vision/ui/': [
        '__init__.py',
        'capture.py',
      ],
      'cam_vision/flutter_bridge/': [
        '__init__.py',
        'cv_bridge.py',
        'desktop_bridge.py',
        'json_serializer.py',
        'thread_manager.py',
      ],
    };

    final files = patterns[assetDir];
    if (files == null) {
      return;
    }

    for (final file in files) {
      try {
        await _copySingleAsset('$assetDir$file', targetBasePath);
      } catch (e) {
        print('Warning: Could not copy $assetDir$file: $e');
      }
    }
  }

  Future<void> _copySingleAsset(String assetPath, String targetBasePath) async {
    try {
      final data = await rootBundle.load(assetPath);
      final targetPath = '$targetBasePath/${assetPath.replaceFirst('../', '')}';
      final targetFile = File(targetPath);

      targetFile.parent.createSync(recursive: true);
      await targetFile.writeAsBytes(
        data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes),
      );
    } catch (e) {
      throw Exception('Failed to copy $assetPath: $e');
    }
  }

  /// Get configuration for Python bridge based on platform
  Map<String, dynamic> getPythonConfig() {
    if (Platform.isMacOS || Platform.isWindows || Platform.isLinux) {
      // Desktop: use relative paths from project root
      return {
        'working_dir': null, // Use default (project root)
        'gallery_path': './data/faces/trusted',
        'gallery_cache': './data/faces/gallery.npz',
        'weights_path': './weights/yolov8n_plate.pt',
      };
    } else {
      // Mobile: use copied paths
      return {
        'working_dir': _appSupportDir,
        'gallery_path': faceGalleryPath,
        'gallery_cache': faceGalleryCachePath,
        'weights_path': '$weightsPath/yolov8n_plate.pt',
      };
    }
  }
}
