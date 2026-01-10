import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import 'package:securevision_flutter/providers/python_bridge_provider.dart';

enum PlateListType { whitelist, blacklist }

class PlateListScreen extends ConsumerStatefulWidget {
  const PlateListScreen({super.key});

  @override
  ConsumerState<PlateListScreen> createState() => _PlateListScreenState();
}

class _PlateListScreenState extends ConsumerState<PlateListScreen> {
  final TextEditingController _plateController = TextEditingController();
  bool _isLoading = true;
  bool _isSyncing = false;
  PlateListType _selected = PlateListType.whitelist;
  List<String> _whitelist = [];
  List<String> _blacklist = [];
  String? _statusMessage;

  @override
  void initState() {
    super.initState();
    _loadLists();
  }

  @override
  void dispose() {
    _plateController.dispose();
    super.dispose();
  }

  Future<File> _listFile() async {
    final directory = await getApplicationDocumentsDirectory();
    return File('${directory.path}/plate_lists.json');
  }

  Future<void> _loadLists() async {
    try {
      final file = await _listFile();
      if (await file.exists()) {
        final contents = await file.readAsString();
        final payload = jsonDecode(contents) as Map<String, dynamic>;
        _whitelist = _decodePlateList(payload['whitelist']);
        _blacklist = _decodePlateList(payload['blacklist']);
      }
    } catch (exc) {
      _statusMessage = 'Failed to load plate lists: $exc';
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  List<String> _decodePlateList(dynamic payload) {
    if (payload is List) {
      return payload.map((value) => value.toString()).toList();
    }
    return [];
  }

  Future<void> _saveLists() async {
    final file = await _listFile();
    final payload = jsonEncode({
      'whitelist': _whitelist,
      'blacklist': _blacklist,
    });
    await file.writeAsString(payload);
  }

  List<String> _activeList() {
    return _selected == PlateListType.whitelist ? _whitelist : _blacklist;
  }

  void _setActiveList(List<String> value) {
    if (_selected == PlateListType.whitelist) {
      _whitelist = value;
    } else {
      _blacklist = value;
    }
  }

  Future<void> _addPlate() async {
    final text = _plateController.text.trim().toUpperCase();
    if (text.isEmpty) {
      return;
    }
    final list = List<String>.from(_activeList());
    if (!list.contains(text)) {
      list.add(text);
      list.sort();
      _setActiveList(list);
      _plateController.clear();
      await _saveLists();
    }
    setState(() {
      _statusMessage = null;
    });
  }

  Future<void> _removePlate(String plate) async {
    final list = List<String>.from(_activeList());
    list.remove(plate);
    _setActiveList(list);
    await _saveLists();
    if (mounted) {
      setState(() {});
    }
  }

  Future<void> _importCsv() async {
    final controller = TextEditingController();
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Import CSV'),
          content: TextField(
            controller: controller,
            maxLines: 8,
            decoration: const InputDecoration(
              hintText: 'Paste CSV content here (one plate per line).',
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: const Text('Import'),
            ),
          ],
        );
      },
    );
    if (accepted != true) {
      controller.dispose();
      return;
    }
    final raw = controller.text.trim();
    controller.dispose();
    if (raw.isEmpty) {
      return;
    }
    final incoming = <String>{};
    for (final line in raw.split(RegExp(r'[\r\n]+'))) {
      final cleaned = line.split(',').first.trim().toUpperCase();
      if (cleaned.isEmpty || cleaned == 'PLATE') {
        continue;
      }
      incoming.add(cleaned);
    }
    if (incoming.isEmpty) {
      return;
    }
    final list = List<String>.from(_activeList())..addAll(incoming);
    list.sort();
    _setActiveList(list.toSet().toList()..sort());
    await _saveLists();
    if (mounted) {
      setState(() {
        _statusMessage = 'Imported ${incoming.length} plates.';
      });
    }
  }

  Future<void> _exportCsv() async {
    final list = _activeList();
    if (list.isEmpty) {
      setState(() {
        _statusMessage = 'No plates to export.';
      });
      return;
    }
    final buffer = StringBuffer('plate\n');
    for (final plate in list) {
      buffer.writeln(plate);
    }
    await Clipboard.setData(ClipboardData(text: buffer.toString()));
    if (mounted) {
      setState(() {
        _statusMessage = 'CSV copied to clipboard.';
      });
    }
  }

  Future<void> _syncList() async {
    final bridge = ref.read(pythonBridgeProvider);
    setState(() {
      _isSyncing = true;
      _statusMessage = null;
    });
    try {
      await bridge.updatePlateList(_selected.name, _activeList());
      setState(() {
        _statusMessage = 'Synced ${_activeList().length} plates.';
      });
    } catch (exc) {
      setState(() {
        _statusMessage = 'Sync failed: $exc';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSyncing = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final activeList = _activeList();

    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SegmentedButton<PlateListType>(
            segments: const [
              ButtonSegment(
                value: PlateListType.whitelist,
                label: Text('Whitelist'),
                icon: Icon(Icons.check_circle_outline),
              ),
              ButtonSegment(
                value: PlateListType.blacklist,
                label: Text('Blacklist'),
                icon: Icon(Icons.block),
              ),
            ],
            selected: {_selected},
            onSelectionChanged: (value) {
              setState(() {
                _selected = value.first;
                _statusMessage = null;
              });
            },
          ),
          const SizedBox(height: 16),
          Text(
            _selected == PlateListType.whitelist
                ? 'Allowed plates'
                : 'Blocked plates',
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w700,
              color: theme.colorScheme.onSurface,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Total: ${activeList.length}',
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.secondary,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _plateController,
                  textCapitalization: TextCapitalization.characters,
                  decoration: const InputDecoration(
                    labelText: 'Plate number',
                    border: OutlineInputBorder(),
                  ),
                  onSubmitted: (_) => _addPlate(),
                ),
              ),
              const SizedBox(width: 12),
              ElevatedButton(
                onPressed: () => _addPlate(),
                child: const Text('Add'),
              ),
            ],
          ),
          const SizedBox(height: 16),
          if (activeList.isEmpty)
            Text(
              'No plates added yet.',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.secondary,
              ),
            )
          else
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final plate in activeList)
                  InputChip(
                    label: Text(plate),
                    onDeleted: () => _removePlate(plate),
                  ),
              ],
            ),
          const SizedBox(height: 20),
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              OutlinedButton.icon(
                onPressed: _importCsv,
                icon: const Icon(Icons.upload_file),
                label: const Text('Import CSV'),
              ),
              OutlinedButton.icon(
                onPressed: _exportCsv,
                icon: const Icon(Icons.copy),
                label: const Text('Export CSV'),
              ),
              FilledButton.icon(
                onPressed: _isSyncing ? null : _syncList,
                icon: const Icon(Icons.sync),
                label: Text(_isSyncing ? 'Syncing...' : 'Sync to Python'),
              ),
            ],
          ),
          if (_statusMessage != null) ...[
            const SizedBox(height: 12),
            Text(
              _statusMessage!,
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
