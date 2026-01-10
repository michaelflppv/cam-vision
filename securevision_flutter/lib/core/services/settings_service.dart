import 'package:shared_preferences/shared_preferences.dart';
import 'package:securevision_flutter/core/models/source_config.dart';

enum ThemePreference { system, light, dark }

ThemePreference themePreferenceFromString(String? value) {
  switch (value) {
    case 'light':
      return ThemePreference.light;
    case 'dark':
      return ThemePreference.dark;
    case 'system':
    default:
      return ThemePreference.system;
  }
}

String themePreferenceToString(ThemePreference value) {
  switch (value) {
    case ThemePreference.light:
      return 'light';
    case ThemePreference.dark:
      return 'dark';
    case ThemePreference.system:
      return 'system';
  }
}

class SettingsSnapshot {
  const SettingsSnapshot({
    required this.source,
    required this.enableFace,
    required this.enablePlate,
    required this.targetFps,
    required this.themePreference,
  });

  final SourceConfig source;
  final bool enableFace;
  final bool enablePlate;
  final int targetFps;
  final ThemePreference themePreference;

  SettingsSnapshot copyWith({
    SourceConfig? source,
    bool? enableFace,
    bool? enablePlate,
    int? targetFps,
    ThemePreference? themePreference,
  }) {
    return SettingsSnapshot(
      source: source ?? this.source,
      enableFace: enableFace ?? this.enableFace,
      enablePlate: enablePlate ?? this.enablePlate,
      targetFps: targetFps ?? this.targetFps,
      themePreference: themePreference ?? this.themePreference,
    );
  }

  factory SettingsSnapshot.defaults() {
    return SettingsSnapshot(
      source: SourceConfig.device(),
      enableFace: true,
      enablePlate: true,
      targetFps: 10,
      themePreference: ThemePreference.system,
    );
  }
}

class SettingsService {
  static const _sourceTypeKey = 'settings.source_type';
  static const _sourceUriKey = 'settings.source_uri';
  static const _deviceIndexKey = 'settings.device_index';
  static const _targetFpsKey = 'settings.target_fps';
  static const _enableFaceKey = 'settings.enable_face';
  static const _enablePlateKey = 'settings.enable_plate';
  static const _themeModeKey = 'settings.theme_mode';

  Future<SettingsSnapshot> load() async {
    final prefs = await SharedPreferences.getInstance();
    var sourceType = sourceTypeFromString(prefs.getString(_sourceTypeKey));
    if (sourceType == SourceType.unknown) {
      sourceType = SourceType.device;
    }
    final sourceUri = prefs.getString(_sourceUriKey);
    final deviceIndex = prefs.getInt(_deviceIndexKey);
    final targetFps = prefs.getInt(_targetFpsKey) ?? 10;
    final enableFace = prefs.getBool(_enableFaceKey) ?? true;
    final enablePlate = prefs.getBool(_enablePlateKey) ?? true;
    final themePreference =
        themePreferenceFromString(prefs.getString(_themeModeKey));

    return SettingsSnapshot(
      source: SourceConfig(
        sourceType: sourceType,
        uri: sourceUri,
        deviceIndex: deviceIndex,
      ),
      enableFace: enableFace,
      enablePlate: enablePlate,
      targetFps: targetFps,
      themePreference: themePreference,
    );
  }

  Future<void> save(SettingsSnapshot snapshot) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _sourceTypeKey,
      sourceTypeToString(snapshot.source.sourceType),
    );
    if (snapshot.source.uri == null) {
      await prefs.remove(_sourceUriKey);
    } else {
      await prefs.setString(_sourceUriKey, snapshot.source.uri!);
    }
    if (snapshot.source.deviceIndex == null) {
      await prefs.remove(_deviceIndexKey);
    } else {
      await prefs.setInt(_deviceIndexKey, snapshot.source.deviceIndex!);
    }
    await prefs.setInt(_targetFpsKey, snapshot.targetFps);
    await prefs.setBool(_enableFaceKey, snapshot.enableFace);
    await prefs.setBool(_enablePlateKey, snapshot.enablePlate);
    await prefs.setString(
      _themeModeKey,
      themePreferenceToString(snapshot.themePreference),
    );
  }
}
