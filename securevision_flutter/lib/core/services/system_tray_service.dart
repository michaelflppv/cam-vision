import 'dart:io';

import 'package:tray_manager/tray_manager.dart';
import 'package:window_manager/window_manager.dart';

class SystemTrayService with TrayListener {
  bool _initialized = false;

  Future<void> initialize() async {
    if (_initialized) {
      return;
    }
    if (!(Platform.isMacOS || Platform.isWindows || Platform.isLinux)) {
      return;
    }

    final iconPath = _resolveTrayIconPath();
    if (iconPath == null) {
      return;
    }

    try {
      await trayManager.setIcon(iconPath);
    } catch (e) {
      // Icon loading failed, continue without tray icon
      // This is non-critical - the app can function without a tray icon
      print('Warning: Failed to set tray icon: $e');
      return;
    }

    await trayManager.setContextMenu(
      Menu(items: [
        MenuItem(key: 'show', label: 'Show SecureVision'),
        MenuItem(key: 'hide', label: 'Hide SecureVision'),
        MenuItem.separator(),
        MenuItem(key: 'quit', label: 'Quit'),
      ]),
    );
    trayManager.addListener(this);
    _initialized = true;
  }

  Future<void> dispose() async {
    if (_initialized) {
      trayManager.removeListener(this);
      _initialized = false;
    }
  }

  @override
  void onTrayIconMouseDown() {
    _toggleWindow();
  }

  @override
  void onTrayIconRightMouseDown() {
    trayManager.popUpContextMenu();
  }

  @override
  void onTrayMenuItemClick(MenuItem menuItem) {
    switch (menuItem.key) {
      case 'show':
        _showWindow();
        break;
      case 'hide':
        _hideWindow();
        break;
      case 'quit':
        windowManager.destroy();
        break;
    }
  }

  Future<void> _toggleWindow() async {
    final isVisible = await windowManager.isVisible();
    if (isVisible) {
      await _hideWindow();
    } else {
      await _showWindow();
    }
  }

  Future<void> _showWindow() async {
    await windowManager.show();
    await windowManager.focus();
  }

  Future<void> _hideWindow() async {
    await windowManager.hide();
  }

  String? _resolveTrayIconPath() {
    if (Platform.isWindows) {
      final icon = File('windows/runner/resources/app_icon.ico');
      if (icon.existsSync()) {
        return icon.path;
      }
    }
    if (Platform.isMacOS) {
      final icon = File(
        'macos/Runner/Assets.xcassets/AppIcon.appiconset/app_icon_32.png',
      );
      if (icon.existsSync()) {
        return icon.path;
      }
    }
    if (Platform.isLinux) {
      final icon = File('linux/runner/resources/app_icon.png');
      if (icon.existsSync()) {
        return icon.path;
      }
    }
    return null;
  }
}
