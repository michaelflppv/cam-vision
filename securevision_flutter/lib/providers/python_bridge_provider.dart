import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:securevision_flutter/core/platform_channels/python_bridge.dart';
import 'package:securevision_flutter/core/platform_channels/python_bridge_factory.dart';
import 'package:securevision_flutter/providers/asset_manager_provider.dart';

final pythonBridgeProvider = Provider<PythonBridge>((ref) {
  final assetManager = ref.watch(assetManagerProvider);
  return createPythonBridge(assetManager: assetManager);
});
