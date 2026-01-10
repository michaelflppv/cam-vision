import 'dart:io';

import 'package:securevision_flutter/core/services/system_tray_service.dart';
import 'package:securevision_flutter/core/services/window_state_service.dart';

class DesktopShellService {
  DesktopShellService({
    WindowStateService? windowStateService,
    SystemTrayService? systemTrayService,
  })  : _windowStateService = windowStateService ?? WindowStateService(),
        _systemTrayService = systemTrayService ?? SystemTrayService();

  final WindowStateService _windowStateService;
  final SystemTrayService _systemTrayService;

  Future<void> initialize() async {
    if (!(Platform.isMacOS || Platform.isWindows || Platform.isLinux)) {
      return;
    }
    await _windowStateService.initialize();
    await _systemTrayService.initialize();
  }

  Future<void> dispose() async {
    await _systemTrayService.dispose();
    await _windowStateService.dispose();
  }
}
