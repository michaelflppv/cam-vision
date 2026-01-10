import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:securevision_flutter/core/services/desktop_shell_service.dart';

final desktopShellProvider = Provider<DesktopShellService>((ref) {
  final service = DesktopShellService();
  service.initialize();
  ref.onDispose(service.dispose);
  return service;
});
