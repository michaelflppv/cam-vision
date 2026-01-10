import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:securevision_flutter/core/models/source_config.dart';
import 'package:securevision_flutter/core/services/settings_service.dart';

class SettingsState {
  const SettingsState({
    required this.source,
    required this.enableFace,
    required this.enablePlate,
    required this.targetFps,
    required this.themePreference,
    required this.isLoading,
    this.errorMessage,
  });

  final SourceConfig source;
  final bool enableFace;
  final bool enablePlate;
  final int targetFps;
  final ThemePreference themePreference;
  final bool isLoading;
  final String? errorMessage;

  ThemeMode get themeMode {
    switch (themePreference) {
      case ThemePreference.light:
        return ThemeMode.light;
      case ThemePreference.dark:
        return ThemeMode.dark;
      case ThemePreference.system:
        return ThemeMode.system;
    }
  }

  SettingsState copyWith({
    SourceConfig? source,
    bool? enableFace,
    bool? enablePlate,
    int? targetFps,
    ThemePreference? themePreference,
    bool? isLoading,
    String? errorMessage,
  }) {
    return SettingsState(
      source: source ?? this.source,
      enableFace: enableFace ?? this.enableFace,
      enablePlate: enablePlate ?? this.enablePlate,
      targetFps: targetFps ?? this.targetFps,
      themePreference: themePreference ?? this.themePreference,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: errorMessage,
    );
  }

  SettingsSnapshot toSnapshot() {
    return SettingsSnapshot(
      source: source,
      enableFace: enableFace,
      enablePlate: enablePlate,
      targetFps: targetFps,
      themePreference: themePreference,
    );
  }

  factory SettingsState.initial() {
    final defaults = SettingsSnapshot.defaults();
    return SettingsState(
      source: defaults.source,
      enableFace: defaults.enableFace,
      enablePlate: defaults.enablePlate,
      targetFps: defaults.targetFps,
      themePreference: defaults.themePreference,
      isLoading: true,
    );
  }
}

class SettingsController extends StateNotifier<SettingsState> {
  SettingsController(this._service) : super(SettingsState.initial()) {
    _load();
  }

  final SettingsService _service;

  Future<void> _load() async {
    try {
      final snapshot = await _service.load();
      state = state.copyWith(
        source: snapshot.source,
        enableFace: snapshot.enableFace,
        enablePlate: snapshot.enablePlate,
        targetFps: snapshot.targetFps,
        themePreference: snapshot.themePreference,
        isLoading: false,
        errorMessage: null,
      );
    } catch (exc) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: exc.toString(),
      );
    }
  }

  Future<void> updateSource(SourceConfig source) async {
    state = state.copyWith(source: source, errorMessage: null);
    await _persist();
  }

  Future<void> updateFeatureToggles({
    required bool enableFace,
    required bool enablePlate,
  }) async {
    state = state.copyWith(
      enableFace: enableFace,
      enablePlate: enablePlate,
      errorMessage: null,
    );
    await _persist();
  }

  Future<void> updateTargetFps(int targetFps) async {
    state = state.copyWith(targetFps: targetFps, errorMessage: null);
    await _persist();
  }

  Future<void> updateThemePreference(ThemePreference preference) async {
    state = state.copyWith(themePreference: preference, errorMessage: null);
    await _persist();
  }

  Future<void> _persist() async {
    try {
      await _service.save(state.toSnapshot());
    } catch (exc) {
      state = state.copyWith(errorMessage: exc.toString());
    }
  }
}

final settingsServiceProvider = Provider<SettingsService>((ref) {
  return SettingsService();
});

final settingsProvider =
    StateNotifierProvider<SettingsController, SettingsState>((ref) {
  final controller = SettingsController(ref.read(settingsServiceProvider));
  ref.onDispose(controller.dispose);
  return controller;
});
