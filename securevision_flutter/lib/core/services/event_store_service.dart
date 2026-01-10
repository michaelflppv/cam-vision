import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:sqflite/sqflite.dart';
import 'package:securevision_flutter/core/models/detection.dart';
import 'package:securevision_flutter/core/models/event.dart';

class EventStoreService {
  static const String _dbName = 'securevision_events.db';
  static const String _tableName = 'events';
  static const int _dbVersion = 1;
  static const int _defaultRetentionDays = 30;

  Database? _db;
  final StreamController<Event> _eventStream = StreamController.broadcast();
  DateTime? _lastPrune;

  Stream<Event> get eventStream => _eventStream.stream;

  Future<void> insertEvent(Event event) async {
    final db = await _openDb();
    final values = {
      'id': event.id,
      'type': event.type,
      'timestamp': event.timestamp.toUtc().millisecondsSinceEpoch,
      'detection_json': jsonEncode(event.detection.toJson()),
      'image_path': event.imagePath,
      'metadata_json': event.metadata.isNotEmpty ? jsonEncode(event.metadata) : null,
    };
    final inserted = await db.insert(
      _tableName,
      values,
      conflictAlgorithm: ConflictAlgorithm.ignore,
    );
    if (inserted > 0) {
      _eventStream.add(event);
      await _maybePrune(db);
    }
  }

  Future<List<Event>> fetchEvents({
    int limit = 40,
    int offset = 0,
    String? type,
    String? query,
  }) async {
    final db = await _openDb();
    final whereClauses = <String>[];
    final whereArgs = <Object?>[];

    if (type != null && type.isNotEmpty) {
      whereClauses.add('type = ?');
      whereArgs.add(type);
    }
    final trimmedQuery = query?.trim();
    if (trimmedQuery != null && trimmedQuery.isNotEmpty) {
      whereClauses.add('(detection_json LIKE ? OR metadata_json LIKE ?)');
      final pattern = '%$trimmedQuery%';
      whereArgs.add(pattern);
      whereArgs.add(pattern);
    }

    final rows = await db.query(
      _tableName,
      where: whereClauses.isEmpty ? null : whereClauses.join(' AND '),
      whereArgs: whereArgs.isEmpty ? null : whereArgs,
      orderBy: 'timestamp DESC',
      limit: limit,
      offset: offset,
    );

    return rows.map(_rowToEvent).toList();
  }

  Future<int> deleteOlderThan({int retentionDays = _defaultRetentionDays}) async {
    final db = await _openDb();
    final cutoff = DateTime.now()
        .toUtc()
        .subtract(Duration(days: retentionDays))
        .millisecondsSinceEpoch;
    return db.delete(
      _tableName,
      where: 'timestamp < ?',
      whereArgs: [cutoff],
    );
  }

  Future<void> dispose() async {
    await _db?.close();
    _db = null;
    await _eventStream.close();
  }

  Future<Database> _openDb() async {
    if (_db != null) {
      return _db!;
    }
    final base = await getDatabasesPath();
    final path = base.endsWith(Platform.pathSeparator)
        ? '$base$_dbName'
        : '$base${Platform.pathSeparator}$_dbName';
    _db = await openDatabase(
      path,
      version: _dbVersion,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE $_tableName (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            detection_json TEXT NOT NULL,
            image_path TEXT,
            metadata_json TEXT
          )
        ''');
        await db.execute(
          'CREATE INDEX idx_events_timestamp ON $_tableName(timestamp DESC)',
        );
        await db.execute(
          'CREATE INDEX idx_events_type ON $_tableName(type)',
        );
      },
    );
    return _db!;
  }

  Event _rowToEvent(Map<String, Object?> row) {
    final detectionJson =
        jsonDecode(row['detection_json'] as String) as Map<String, dynamic>;
    final metadataRaw = row['metadata_json'] as String?;
    final metadata = metadataRaw == null || metadataRaw.isEmpty
        ? const <String, dynamic>{}
        : jsonDecode(metadataRaw) as Map<String, dynamic>;
    return Event(
      id: row['id'] as String,
      type: row['type'] as String,
      timestamp: DateTime.fromMillisecondsSinceEpoch(
        (row['timestamp'] as num?)?.toInt() ?? 0,
        isUtc: true,
      ),
      detection: Detection.fromJson(detectionJson),
      imagePath: row['image_path'] as String?,
      metadata: metadata,
    );
  }

  Future<void> _maybePrune(Database db) async {
    final now = DateTime.now();
    if (_lastPrune != null && now.difference(_lastPrune!) < const Duration(hours: 1)) {
      return;
    }
    _lastPrune = now;
    final cutoff = now
        .toUtc()
        .subtract(const Duration(days: _defaultRetentionDays))
        .millisecondsSinceEpoch;
    await db.delete(
      _tableName,
      where: 'timestamp < ?',
      whereArgs: [cutoff],
    );
  }
}
