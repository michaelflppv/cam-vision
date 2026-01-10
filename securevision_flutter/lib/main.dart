import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:securevision_flutter/core/services/asset_manager_service.dart';
import 'package:securevision_flutter/design_system/app_theme.dart';
import 'package:securevision_flutter/features/enrollment/screens/enrollment_screen.dart';
import 'package:securevision_flutter/features/events/screens/event_history_screen.dart';
import 'package:securevision_flutter/features/live_view/screens/live_view_screen.dart';
import 'package:securevision_flutter/features/settings/screens/settings_screen.dart';
import 'package:securevision_flutter/features/live_view/controllers/live_view_provider.dart';
import 'package:securevision_flutter/providers/app_state_provider.dart';
import 'package:securevision_flutter/providers/asset_manager_provider.dart';
import 'package:securevision_flutter/providers/desktop_shell_provider.dart';
import 'package:securevision_flutter/providers/event_ingest_provider.dart';
import 'package:securevision_flutter/providers/settings_provider.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize asset manager for mobile platforms
  // This copies bundled Python modules and models to persistent storage
  final assetManager = AssetManagerService();
  await assetManager.initialize();

  runApp(ProviderScope(
    overrides: [
      assetManagerProvider.overrideWithValue(assetManager),
    ],
    child: const SecureVisionApp(),
  ));
}

class SecureVisionApp extends ConsumerWidget {
  const SecureVisionApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);
    ref.watch(desktopShellProvider);
    ref.watch(eventIngestProvider);
    return MaterialApp(
      title: 'SecureVision',
      theme: AppTheme.lightTheme(),
      darkTheme: AppTheme.darkTheme(),
      themeMode: settings.themeMode,
      home: const AppShell(),
    );
  }
}

class AppShell extends ConsumerWidget {
  const AppShell({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedIndex = ref.watch(appTabProvider);
    final screens = const [
      LiveViewScreen(),
      EventHistoryScreen(),
      EnrollmentScreen(),
      SettingsScreen(),
    ];
    final destinations = const [
      NavigationDestination(icon: Icon(Icons.live_tv), label: 'Live'),
      NavigationDestination(icon: Icon(Icons.history), label: 'Events'),
      NavigationDestination(icon: Icon(Icons.person_add_alt_1), label: 'Enroll'),
      NavigationDestination(icon: Icon(Icons.settings), label: 'Settings'),
    ];

    return Shortcuts(
      shortcuts: _desktopShortcuts(),
      child: Actions(
        actions: {
          ChangeTabIntent: CallbackAction<ChangeTabIntent>(
            onInvoke: (intent) {
              ref.read(appTabProvider.notifier).state = intent.index;
              return null;
            },
          ),
          ToggleCaptureIntent: CallbackAction<ToggleCaptureIntent>(
            onInvoke: (intent) {
              if (ref.read(appTabProvider) != 0) {
                return null;
              }
              final settings = ref.read(settingsProvider);
              final controller = ref.read(liveViewControllerProvider.notifier);
              final state = ref.read(liveViewControllerProvider);
              if (state.isRunning) {
                controller.stop();
              } else if (!settings.isLoading) {
                controller.start(
                  source: settings.source,
                  enableFaces: settings.enableFace,
                  enablePlates: settings.enablePlate,
                  targetFps: settings.targetFps,
                );
              }
              return null;
            },
          ),
        },
        child: Focus(
          autofocus: true,
          child: LayoutBuilder(
            builder: (context, constraints) {
              final isWide = constraints.maxWidth >= 900;
              if (isWide) {
                return Scaffold(
                  body: Row(
                    children: [
                      NavigationRail(
                        selectedIndex: selectedIndex,
                        onDestinationSelected: (index) {
                          ref.read(appTabProvider.notifier).state = index;
                        },
                        labelType: NavigationRailLabelType.all,
                        destinations: const [
                          NavigationRailDestination(
                            icon: Icon(Icons.live_tv),
                            label: Text('Live'),
                          ),
                          NavigationRailDestination(
                            icon: Icon(Icons.history),
                            label: Text('Events'),
                          ),
                          NavigationRailDestination(
                            icon: Icon(Icons.person_add_alt_1),
                            label: Text('Enroll'),
                          ),
                          NavigationRailDestination(
                            icon: Icon(Icons.settings),
                            label: Text('Settings'),
                          ),
                        ],
                      ),
                      const VerticalDivider(width: 1),
                      Expanded(child: screens[selectedIndex]),
                    ],
                  ),
                );
              }

              return Scaffold(
                body: screens[selectedIndex],
                bottomNavigationBar: NavigationBar(
                  selectedIndex: selectedIndex,
                  destinations: destinations,
                  onDestinationSelected: (index) {
                    ref.read(appTabProvider.notifier).state = index;
                  },
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}

class ChangeTabIntent extends Intent {
  const ChangeTabIntent(this.index);

  final int index;
}

class ToggleCaptureIntent extends Intent {
  const ToggleCaptureIntent();
}

Map<LogicalKeySet, Intent> _desktopShortcuts() {
  return {
    LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.digit1):
        const ChangeTabIntent(0),
    LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.digit2):
        const ChangeTabIntent(1),
    LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.digit3):
        const ChangeTabIntent(2),
    LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.digit4):
        const ChangeTabIntent(3),
    LogicalKeySet(LogicalKeyboardKey.meta, LogicalKeyboardKey.digit1):
        const ChangeTabIntent(0),
    LogicalKeySet(LogicalKeyboardKey.meta, LogicalKeyboardKey.digit2):
        const ChangeTabIntent(1),
    LogicalKeySet(LogicalKeyboardKey.meta, LogicalKeyboardKey.digit3):
        const ChangeTabIntent(2),
    LogicalKeySet(LogicalKeyboardKey.meta, LogicalKeyboardKey.digit4):
        const ChangeTabIntent(3),
    LogicalKeySet(LogicalKeyboardKey.space): const ToggleCaptureIntent(),
  };
}
