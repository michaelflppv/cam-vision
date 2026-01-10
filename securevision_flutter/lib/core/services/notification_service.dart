import 'dart:io';

import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:securevision_flutter/core/models/detection.dart';
import 'package:securevision_flutter/core/models/event.dart';

class NotificationService {
  static const String _channelId = 'securevision_events';
  static const String _channelName = 'SecureVision Events';

  final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();
  bool _initialized = false;

  Future<void> initialize() async {
    if (_initialized) {
      return;
    }

    const android = AndroidInitializationSettings('@mipmap/ic_launcher');
    const ios = DarwinInitializationSettings();
    const macos = DarwinInitializationSettings();
    const settings = InitializationSettings(
      android: android,
      iOS: ios,
      macOS: macos,
    );

    await _plugin.initialize(settings);

    if (Platform.isAndroid) {
      await _plugin
          .resolvePlatformSpecificImplementation<
              AndroidFlutterLocalNotificationsPlugin>()
          ?.requestNotificationsPermission();
    }
    if (Platform.isIOS) {
      await _plugin
          .resolvePlatformSpecificImplementation<
              IOSFlutterLocalNotificationsPlugin>()
          ?.requestPermissions(
            alert: true,
            badge: true,
            sound: true,
          );
    }
    if (Platform.isMacOS) {
      await _plugin
          .resolvePlatformSpecificImplementation<
              MacOSFlutterLocalNotificationsPlugin>()
          ?.requestPermissions(
            alert: true,
            badge: true,
            sound: true,
          );
    }

    _initialized = true;
  }

  Future<void> showEvent(Event event) async {
    if (!(Platform.isAndroid || Platform.isIOS)) {
      return;
    }
    await initialize();

    const details = NotificationDetails(
      android: AndroidNotificationDetails(
        _channelId,
        _channelName,
        channelDescription: 'SecureVision detection alerts',
        importance: Importance.defaultImportance,
        priority: Priority.defaultPriority,
      ),
      iOS: DarwinNotificationDetails(),
    );

    await _plugin.show(
      event.id.hashCode & 0x7fffffff,
      _titleFor(event),
      _bodyFor(event),
      details,
      payload: event.id,
    );
  }

  String _titleFor(Event event) {
    switch (event.detection.type) {
      case DetectionType.face:
        return event.detection.faceMatch?.label ?? 'Unknown face detected';
      case DetectionType.plate:
        return event.detection.plateRead?.plate ?? 'Plate detected';
      case DetectionType.unknown:
        return 'Detection event';
    }
  }

  String _bodyFor(Event event) {
    switch (event.detection.type) {
      case DetectionType.face:
        final similarity = event.detection.faceMatch?.similarity;
        if (similarity != null) {
          return 'Similarity ${(similarity * 100).toStringAsFixed(1)}%';
        }
        return 'Face match event';
      case DetectionType.plate:
        final listType = event.detection.plateRead?.listType;
        if (listType != null && listType.isNotEmpty) {
          return 'Listed on $listType';
        }
        return 'Plate read event';
      case DetectionType.unknown:
        return event.type;
    }
  }
}
