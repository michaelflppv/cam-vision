import 'dart:io' show Platform;

import 'package:securevision_flutter/core/platform_channels/python_bridge.dart';
import 'package:securevision_flutter/core/platform_channels/python_bridge_android.dart';
import 'package:securevision_flutter/core/platform_channels/python_bridge_desktop.dart';
import 'package:securevision_flutter/core/platform_channels/python_bridge_ios.dart';
import 'package:securevision_flutter/core/services/asset_manager_service.dart';

PythonBridge createPythonBridge({AssetManagerService? assetManager}) {
  // Get asset paths for mobile platforms
  final assetPaths = assetManager?.getPythonConfig();

  if (Platform.isAndroid) {
    return PythonBridgeAndroid(
      assetPaths: assetPaths != null
          ? {
              'gallery_path': assetPaths['gallery_path'] as String? ?? '',
              'gallery_cache': assetPaths['gallery_cache'] as String? ?? '',
              'weights_path': assetPaths['weights_path'] as String? ?? '',
            }
          : null,
    );
  }
  if (Platform.isIOS) {
    return PythonBridgeIOS(
      assetPaths: assetPaths != null
          ? {
              'gallery_path': assetPaths['gallery_path'] as String? ?? '',
              'gallery_cache': assetPaths['gallery_cache'] as String? ?? '',
              'weights_path': assetPaths['weights_path'] as String? ?? '',
            }
          : null,
    );
  }
  return PythonBridgeDesktop();
}
