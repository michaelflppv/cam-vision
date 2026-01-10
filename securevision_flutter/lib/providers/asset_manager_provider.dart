import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:securevision_flutter/core/services/asset_manager_service.dart';

final assetManagerProvider = Provider<AssetManagerService>((ref) {
  return AssetManagerService();
});
