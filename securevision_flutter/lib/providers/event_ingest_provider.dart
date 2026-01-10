import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:securevision_flutter/core/models/event.dart';
import 'package:securevision_flutter/core/platform_channels/python_bridge.dart';
import 'package:securevision_flutter/core/services/event_store_service.dart';
import 'package:securevision_flutter/core/services/notification_service.dart';
import 'package:securevision_flutter/providers/python_bridge_provider.dart';

class EventIngestor {
  EventIngestor({
    required this.bridge,
    required this.store,
    required this.notifications,
  });

  final PythonBridge bridge;
  final EventStoreService store;
  final NotificationService notifications;
  StreamSubscription<Event>? _subscription;

  void start() {
    _subscription ??= bridge.getEventStream().listen(_handleEvent);
  }

  Future<void> _handleEvent(Event event) async {
    await store.insertEvent(event);
    await notifications.showEvent(event);
  }

  Future<void> dispose() async {
    await _subscription?.cancel();
    _subscription = null;
  }
}

final eventStoreProvider = Provider<EventStoreService>((ref) {
  final store = EventStoreService();
  ref.onDispose(store.dispose);
  return store;
});

final notificationServiceProvider = Provider<NotificationService>((ref) {
  return NotificationService();
});

final eventIngestProvider = Provider<EventIngestor>((ref) {
  final ingestor = EventIngestor(
    bridge: ref.read(pythonBridgeProvider),
    store: ref.read(eventStoreProvider),
    notifications: ref.read(notificationServiceProvider),
  );
  ingestor.start();
  ref.onDispose(ingestor.dispose);
  return ingestor;
});
