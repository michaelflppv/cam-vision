import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:securevision_flutter/core/models/event.dart';
import 'package:securevision_flutter/features/events/screens/event_detail_screen.dart';
import 'package:securevision_flutter/features/events/widgets/event_card.dart';
import 'package:securevision_flutter/providers/event_ingest_provider.dart';

class EventHistoryScreen extends ConsumerStatefulWidget {
  const EventHistoryScreen({super.key});

  @override
  ConsumerState<EventHistoryScreen> createState() => _EventHistoryScreenState();
}

class _EventHistoryScreenState extends ConsumerState<EventHistoryScreen> {
  static const int _pageSize = 30;

  final ScrollController _scrollController = ScrollController();
  final TextEditingController _searchController = TextEditingController();

  List<Event> _events = [];
  bool _isLoading = false;
  bool _hasMore = true;
  String _selectedType = 'all';
  Timer? _searchDebounce;
  StreamSubscription<Event>? _eventSubscription;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_handleScroll);
    _searchController.addListener(_handleSearchChange);
    _eventSubscription =
        ref.read(eventStoreProvider).eventStream.listen(_handleIncomingEvent);
    _loadEvents(reset: true);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    _searchController.dispose();
    _searchDebounce?.cancel();
    _eventSubscription?.cancel();
    super.dispose();
  }

  void _handleIncomingEvent(Event event) {
    if (!_matchesFilter(event, _selectedType, _searchController.text)) {
      return;
    }
    setState(() {
      _events.insert(0, event);
    });
  }

  void _handleScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      _loadEvents();
    }
  }

  void _handleSearchChange() {
    _searchDebounce?.cancel();
    _searchDebounce = Timer(const Duration(milliseconds: 300), () {
      _loadEvents(reset: true);
    });
  }

  Future<void> _loadEvents({bool reset = false}) async {
    if (_isLoading) {
      return;
    }
    if (!reset && !_hasMore) {
      return;
    }
    setState(() {
      _isLoading = true;
    });
    final store = ref.read(eventStoreProvider);
    final events = await store.fetchEvents(
      limit: _pageSize,
      offset: reset ? 0 : _events.length,
      type: _selectedType == 'all' ? null : _selectedType,
      query: _searchController.text,
    );
    if (!mounted) {
      return;
    }
    setState(() {
      if (reset) {
        _events = events;
      } else {
        _events = [..._events, ...events];
      }
      _hasMore = events.length == _pageSize;
      _isLoading = false;
    });
  }

  bool _matchesFilter(Event event, String type, String query) {
    if (type != 'all' && event.type != type) {
      return false;
    }
    final trimmed = query.trim();
    if (trimmed.isEmpty) {
      return true;
    }
    final lower = trimmed.toLowerCase();
    return event.toJson().toString().toLowerCase().contains(lower);
  }

  @override
  Widget build(BuildContext context) {
    ref.watch(eventIngestProvider);
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Event History')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                TextField(
                  controller: _searchController,
                  decoration: const InputDecoration(
                    labelText: 'Search events',
                    prefixIcon: Icon(Icons.search),
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'all', label: Text('All')),
                    ButtonSegment(value: 'face_match', label: Text('Faces')),
                    ButtonSegment(value: 'plate_read', label: Text('Plates')),
                  ],
                  selected: {_selectedType},
                  onSelectionChanged: (value) {
                    setState(() {
                      _selectedType = value.first;
                    });
                    _loadEvents(reset: true);
                  },
                ),
              ],
            ),
          ),
          Expanded(
            child: RefreshIndicator(
              onRefresh: () => _loadEvents(reset: true),
              child: _events.isEmpty && !_isLoading
                  ? ListView(
                      children: [
                        Padding(
                          padding: const EdgeInsets.all(24),
                          child: Text(
                            'No events recorded yet.',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: theme.colorScheme.secondary,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ),
                      ],
                    )
                  : ListView.separated(
                      controller: _scrollController,
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
                      itemCount: _events.length + (_isLoading ? 1 : 0),
                      separatorBuilder: (_, __) => const SizedBox(height: 12),
                      itemBuilder: (context, index) {
                        if (index >= _events.length) {
                          return const Center(
                            child: Padding(
                              padding: EdgeInsets.all(12),
                              child: CircularProgressIndicator(),
                            ),
                          );
                        }
                        final event = _events[index];
                        return EventCard(
                          event: event,
                          onTap: () {
                            Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => EventDetailScreen(event: event),
                              ),
                            );
                          },
                        );
                      },
                    ),
            ),
          ),
        ],
      ),
    );
  }
}
