import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:securevision_flutter/features/live_view/controllers/live_view_controller.dart';
import 'package:securevision_flutter/providers/python_bridge_provider.dart';

final liveViewControllerProvider =
    StateNotifierProvider<LiveViewController, LiveViewState>((ref) {
  final bridge = ref.watch(pythonBridgeProvider);
  final controller = LiveViewController(bridge);
  ref.onDispose(controller.dispose);
  return controller;
});
