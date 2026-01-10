import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:securevision_flutter/core/models/onvif_discovery.dart';
import 'package:securevision_flutter/core/models/source_config.dart';
import 'package:securevision_flutter/core/services/settings_service.dart';
import 'package:securevision_flutter/design_system/app_spacing.dart';
import 'package:securevision_flutter/design_system/components/app_button.dart';
import 'package:securevision_flutter/design_system/components/app_card.dart';
import 'package:securevision_flutter/design_system/components/app_section.dart';
import 'package:securevision_flutter/providers/python_bridge_provider.dart';
import 'package:securevision_flutter/providers/settings_provider.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  final TextEditingController _uriController = TextEditingController();
  final TextEditingController _deviceIndexController = TextEditingController();
  final TextEditingController _onvifHostController = TextEditingController();
  final TextEditingController _onvifPortController =
      TextEditingController(text: '80');
  final TextEditingController _onvifUserController = TextEditingController();
  final TextEditingController _onvifPassController = TextEditingController();
  final TextEditingController _onvifProfilesController = TextEditingController();
  final TextEditingController _onvifTimeoutController =
      TextEditingController(text: '5');
  SourceType _sourceType = SourceType.device;
  String? _statusMessage;
  bool _onvifLoading = false;
  String? _onvifError;
  List<OnvifDiscoveryResult> _onvifResults = [];

  @override
  void initState() {
    super.initState();
    final settings = ref.read(settingsProvider);
    _applySettings(settings);
  }

  @override
  void dispose() {
    _uriController.dispose();
    _deviceIndexController.dispose();
    _onvifHostController.dispose();
    _onvifPortController.dispose();
    _onvifUserController.dispose();
    _onvifPassController.dispose();
    _onvifProfilesController.dispose();
    _onvifTimeoutController.dispose();
    super.dispose();
  }

  void _applySettings(SettingsState settings) {
    _sourceType = settings.source.sourceType == SourceType.unknown
        ? SourceType.device
        : settings.source.sourceType;
    _uriController.text = settings.source.uri ?? '';
    _deviceIndexController.text =
        (settings.source.deviceIndex ?? 0).toString();
  }

  Future<void> _applySource() async {
    final controller = ref.read(settingsProvider.notifier);
    final uri = _uriController.text.trim();
    final deviceIndex = int.tryParse(_deviceIndexController.text.trim()) ?? 0;

    SourceConfig source;
    switch (_sourceType) {
      case SourceType.device:
        source = SourceConfig.device(deviceIndex: deviceIndex);
        break;
      case SourceType.rtsp:
      case SourceType.httpMjpeg:
      case SourceType.file:
      case SourceType.rtmp:
        if (uri.isEmpty) {
          setState(() {
            _statusMessage = 'Enter a source URI or file path.';
          });
          return;
        }
        source = SourceConfig(sourceType: _sourceType, uri: uri);
        break;
      case SourceType.unknown:
        source = SourceConfig.device(deviceIndex: deviceIndex);
        break;
    }

    await controller.updateSource(source);
    if (mounted) {
      setState(() {
        _statusMessage = 'Source updated. Restart capture to apply.';
      });
    }
  }

  Future<void> _runOnvifDiscovery() async {
    setState(() {
      _onvifLoading = true;
      _onvifError = null;
    });
    final bridge = ref.read(pythonBridgeProvider);
    try {
      final host = _onvifHostController.text.trim();
      final port = int.tryParse(_onvifPortController.text.trim()) ?? 80;
      final timeout = int.tryParse(_onvifTimeoutController.text.trim()) ?? 5;
      final profilesRaw = _onvifProfilesController.text.trim();
      final profiles = profilesRaw.isEmpty
          ? null
          : profilesRaw.split(',').map((value) => value.trim()).toList();
      final request = OnvifDiscoveryRequest(
        host: host.isEmpty ? null : host,
        port: port,
        username: _onvifUserController.text.trim().isEmpty
            ? null
            : _onvifUserController.text.trim(),
        password: _onvifPassController.text,
        timeoutSeconds: timeout,
        profiles: profiles?.where((value) => value.isNotEmpty).toList(),
      );
      final results = await bridge.discoverOnvif(request);
      if (!mounted) {
        return;
      }
      setState(() {
        _onvifResults = results;
        _onvifError = results.isEmpty ? 'No ONVIF devices found.' : null;
      });
    } catch (exc) {
      if (!mounted) {
        return;
      }
      setState(() {
        _onvifError = exc.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _onvifLoading = false;
        });
      }
    }
  }

  void _useOnvifUri(String uri) {
    setState(() {
      _sourceType = SourceType.rtsp;
      _uriController.text = uri;
      _statusMessage = 'RTSP URI loaded. Tap Apply Source to use it.';
    });
  }

  String _sourceHint(SourceType type) {
    switch (type) {
      case SourceType.rtsp:
        return 'rtsp://camera/stream';
      case SourceType.httpMjpeg:
        return 'http://camera/stream.mjpg';
      case SourceType.file:
        return '/storage/emulated/0/Movies/sample.mp4';
      case SourceType.rtmp:
        return 'rtmp://host/app/stream';
      case SourceType.device:
      case SourceType.unknown:
        return '';
    }
  }

  String _sourceLabel(SourceType type) {
    switch (type) {
      case SourceType.device:
        return 'DEVICE';
      case SourceType.rtsp:
        return 'RTSP';
      case SourceType.httpMjpeg:
        return 'HTTP MJPEG';
      case SourceType.file:
        return 'FILE';
      case SourceType.rtmp:
        return 'RTMP';
      case SourceType.unknown:
        return 'UNKNOWN';
    }
  }

  @override
  Widget build(BuildContext context) {
    ref.listen<SettingsState>(settingsProvider, (previous, next) {
      if ((previous?.isLoading ?? true) && !next.isLoading) {
        if (!mounted) {
          return;
        }
        setState(() {
          _applySettings(next);
        });
      }
    });
    final settings = ref.watch(settingsProvider);
    final theme = Theme.of(context);
    final fpsOptions = const [5, 10, 15];
    final selectedFps = fpsOptions.contains(settings.targetFps)
        ? settings.targetFps
        : 10;
    final showOnvif = Platform.isMacOS || Platform.isWindows || Platform.isLinux;

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (settings.isLoading) const LinearProgressIndicator(),
          AppSection(
            title: 'Video Source',
            subtitle: 'Choose device camera or remote stream.',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                DropdownButtonFormField<SourceType>(
                  value: _sourceType,
                  decoration: const InputDecoration(
                    labelText: 'Source type',
                    border: OutlineInputBorder(),
                  ),
                  items: [
                    for (final type in SourceType.values)
                      if (type != SourceType.unknown)
                        DropdownMenuItem(
                          value: type,
                          child: Text(_sourceLabel(type)),
                        ),
                  ],
                  onChanged: (value) {
                    if (value == null) {
                      return;
                    }
                    setState(() {
                      _sourceType = value;
                      _statusMessage = null;
                    });
                  },
                ),
                const SizedBox(height: 12),
                if (_sourceType == SourceType.device)
                  TextField(
                    controller: _deviceIndexController,
                    decoration: const InputDecoration(
                      labelText: 'Device index',
                      border: OutlineInputBorder(),
                    ),
                    keyboardType: TextInputType.number,
                  )
                else
                  TextField(
                    controller: _uriController,
                    decoration: InputDecoration(
                      labelText: 'Source URI',
                      hintText: _sourceHint(_sourceType),
                      border: const OutlineInputBorder(),
                    ),
                  ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: AppButton(
                        label: 'Apply Source',
                        onPressed:
                            settings.isLoading ? null : () => _applySource(),
                        variant: AppButtonVariant.primary,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'Changes apply on next capture start.',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.secondary,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          AppSection(
            title: 'Features',
            subtitle: 'Toggle recognition modules.',
            child: Column(
              children: [
                SwitchListTile(
                  value: settings.enableFace,
                  onChanged: (value) {
                    ref.read(settingsProvider.notifier).updateFeatureToggles(
                          enableFace: value,
                          enablePlate: settings.enablePlate,
                        );
                  },
                  title: const Text('Face recognition'),
                ),
                SwitchListTile(
                  value: settings.enablePlate,
                  onChanged: (value) {
                    ref.read(settingsProvider.notifier).updateFeatureToggles(
                          enableFace: settings.enableFace,
                          enablePlate: value,
                        );
                  },
                  title: const Text('Plate recognition'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          AppSection(
            title: 'Performance',
            subtitle: 'Target FPS for the CV pipeline.',
            child: SegmentedButton<int>(
              segments: const [
                ButtonSegment(value: 5, label: Text('5 FPS')),
                ButtonSegment(value: 10, label: Text('10 FPS')),
                ButtonSegment(value: 15, label: Text('15 FPS')),
              ],
              selected: {selectedFps},
              onSelectionChanged: (value) {
                ref
                    .read(settingsProvider.notifier)
                    .updateTargetFps(value.first);
              },
            ),
          ),
          const SizedBox(height: 16),
          AppSection(
            title: 'Theme',
            subtitle: 'Match system or force light/dark.',
            child: SegmentedButton<ThemePreference>(
              segments: const [
                ButtonSegment(
                  value: ThemePreference.system,
                  label: Text('System'),
                ),
                ButtonSegment(
                  value: ThemePreference.light,
                  label: Text('Light'),
                ),
                ButtonSegment(
                  value: ThemePreference.dark,
                  label: Text('Dark'),
                ),
              ],
              selected: {settings.themePreference},
              onSelectionChanged: (value) {
                ref
                    .read(settingsProvider.notifier)
                    .updateThemePreference(value.first);
              },
            ),
          ),
          const SizedBox(height: 16),
          AppSection(
            title: 'About',
            subtitle: 'SecureVision mobile preview.',
            child: Text(
              'Mobile settings are simplified by design. '
              'Advanced tuning remains available via desktop CLI/env config.',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.secondary,
              ),
            ),
          ),
          if (showOnvif) ...[
            const SizedBox(height: 16),
            AppSection(
              title: 'ONVIF Discovery',
              subtitle: 'Desktop helper to find camera RTSP URLs.',
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  TextField(
                    controller: _onvifHostController,
                    decoration: const InputDecoration(
                      labelText: 'Host (optional)',
                      hintText: '192.168.1.50',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _onvifPortController,
                          decoration: const InputDecoration(
                            labelText: 'Port',
                            border: OutlineInputBorder(),
                          ),
                          keyboardType: TextInputType.number,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: TextField(
                          controller: _onvifTimeoutController,
                          decoration: const InputDecoration(
                            labelText: 'Timeout (s)',
                            border: OutlineInputBorder(),
                          ),
                          keyboardType: TextInputType.number,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _onvifUserController,
                    decoration: const InputDecoration(
                      labelText: 'Username (optional)',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _onvifPassController,
                    decoration: const InputDecoration(
                      labelText: 'Password (optional)',
                      border: OutlineInputBorder(),
                    ),
                    obscureText: true,
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _onvifProfilesController,
                    decoration: const InputDecoration(
                      labelText: 'Profiles (comma separated)',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  AppButton(
                    label: _onvifLoading ? 'Discovering...' : 'Discover Cameras',
                    onPressed: _onvifLoading ? null : _runOnvifDiscovery,
                    variant: AppButtonVariant.primary,
                    icon: Icons.search,
                  ),
                  if (_onvifError != null) ...[
                    const SizedBox(height: 8),
                    Text(
                      _onvifError!,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.secondary,
                      ),
                    ),
                  ],
                  if (_onvifResults.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    for (final device in _onvifResults)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: _OnvifDeviceCard(
                          device: device,
                          onUse: _useOnvifUri,
                        ),
                      ),
                  ],
                ],
              ),
            ),
          ],
          if (settings.errorMessage != null || _statusMessage != null) ...[
            const SizedBox(height: 12),
            Text(
              _statusMessage ?? settings.errorMessage!,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.secondary,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _OnvifDeviceCard extends StatelessWidget {
  const _OnvifDeviceCard({required this.device, required this.onUse});

  final OnvifDiscoveryResult device;
  final ValueChanged<String> onUse;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AppCard(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            device.host,
            style: theme.textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 8),
          for (final profile in device.profiles)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          profile.name,
                          style: theme.textTheme.bodyMedium?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 4),
                        SelectableText(
                          profile.uri,
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.secondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  Column(
                    children: [
                      IconButton(
                        onPressed: () {
                          Clipboard.setData(ClipboardData(text: profile.uri));
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('RTSP URI copied')),
                          );
                        },
                        icon: const Icon(Icons.copy, size: 18),
                        tooltip: 'Copy URI',
                      ),
                      TextButton(
                        onPressed: () => onUse(profile.uri),
                        child: const Text('Use'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
