import 'dart:async';
import 'dart:io';
import 'dart:ui';

import 'package:shared_preferences/shared_preferences.dart';
import 'package:window_manager/window_manager.dart';

class WindowStateService with WindowListener {
  static const _widthKey = 'window.width';
  static const _heightKey = 'window.height';
  static const _leftKey = 'window.left';
  static const _topKey = 'window.top';
  static const _maximizedKey = 'window.maximized';
  static const _fullscreenKey = 'window.fullscreen';

  bool _initialized = false;
  Timer? _debounce;

  Future<void> initialize() async {
    if (_initialized) {
      return;
    }
    if (!(Platform.isMacOS || Platform.isWindows || Platform.isLinux)) {
      return;
    }

    await windowManager.ensureInitialized();
    windowManager.addListener(this);

    final prefs = await SharedPreferences.getInstance();
    final width = prefs.getDouble(_widthKey);
    final height = prefs.getDouble(_heightKey);
    final left = prefs.getDouble(_leftKey);
    final top = prefs.getDouble(_topKey);
    final isMaximized = prefs.getBool(_maximizedKey) ?? false;
    final isFullscreen = prefs.getBool(_fullscreenKey) ?? false;

    const windowOptions = WindowOptions(
      size: Size(1280, 800),
      minimumSize: Size(960, 600),
      center: true,
      title: 'SecureVision',
    );

    windowManager.waitUntilReadyToShow(windowOptions, () async {
      if (width != null && height != null) {
        await windowManager.setSize(Size(width, height));
      }
      if (left != null && top != null) {
        await windowManager.setPosition(Offset(left, top));
      }
      if (isFullscreen) {
        await windowManager.setFullScreen(true);
      } else if (isMaximized) {
        await windowManager.maximize();
      }
      await windowManager.show();
      await windowManager.focus();
    });

    _initialized = true;
  }

  Future<void> dispose() async {
    _debounce?.cancel();
    _debounce = null;
    if (_initialized) {
      windowManager.removeListener(this);
    }
  }

  @override
  void onWindowResized() {
    _scheduleSave();
  }

  @override
  void onWindowMoved() {
    _scheduleSave();
  }

  @override
  void onWindowClose() async {
    await _persistBounds();
  }

  void _scheduleSave() {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 400), _persistBounds);
  }

  Future<void> _persistBounds() async {
    if (!await windowManager.isVisible()) {
      return;
    }
    final prefs = await SharedPreferences.getInstance();
    final bounds = await windowManager.getBounds();
    final isMaximized = await windowManager.isMaximized();
    final isFullscreen = await windowManager.isFullScreen();

    await prefs.setDouble(_widthKey, bounds.width);
    await prefs.setDouble(_heightKey, bounds.height);
    await prefs.setDouble(_leftKey, bounds.left);
    await prefs.setDouble(_topKey, bounds.top);
    await prefs.setBool(_maximizedKey, isMaximized);
    await prefs.setBool(_fullscreenKey, isFullscreen);
  }
}
