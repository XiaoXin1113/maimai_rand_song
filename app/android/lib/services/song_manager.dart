import 'dart:convert';
import 'dart:math';
import 'package:flutter/services.dart';
import '../models/models.dart';

class SongManager {
  List<Song> _songs = [];
  bool _isLoaded = false;

  List<Song> get songs => _songs;
  bool get isLoaded => _isLoaded;

  Future<void> loadSongs() async {
    try {
      final String jsonString = await rootBundle.loadString(
        'assets/data/songs_database.json',
      );
      final Map<String, dynamic> jsonData = json.decode(jsonString);

      final List<dynamic> songsData = jsonData['songs'] ?? jsonData;
      _songs = songsData.map((s) => Song.fromJson(s)).toList();
      _isLoaded = true;
    } catch (e) {
      print('Error loading songs: $e');
      _songs = [];
      _isLoaded = false;
    }
  }

  List<Song> filterSongs(SelectionCriteria criteria) {
    List<Song> filtered = List.from(_songs);

    if (criteria.songType != null) {
      filtered = filtered.where((s) {
        return s.charts.any((c) => c.type == criteria.songType);
      }).toList();
    }

    if (criteria.genre != null && criteria.genre!.isNotEmpty) {
      filtered = filtered.where((s) => s.genre == criteria.genre).toList();
    }

    if (criteria.minLevel != null || criteria.maxLevel != null) {
      filtered = filtered.where((song) {
        for (final chart in song.charts) {
          if (criteria.difficulty != null &&
              chart.difficulty != criteria.difficulty) {
            continue;
          }
          if (criteria.songType != null && chart.type != criteria.songType) {
            continue;
          }

          double? level = chart.internalLevel;
          if (level == null) {
            final levelStr = chart.level.replaceAll('+', '.7');
            level = double.tryParse(levelStr);
          }

          if (level == null) continue;

          if (criteria.minLevel != null && level < criteria.minLevel!) {
            continue;
          }
          if (criteria.maxLevel != null && level > criteria.maxLevel!) {
            continue;
          }

          return true;
        }
        return false;
      }).toList();
    }

    return filtered;
  }

  SelectionResult selectRandom(SelectionCriteria criteria) {
    final filtered = filterSongs(criteria);

    if (filtered.isEmpty) {
      return SelectionResult(songs: [], totalAvailable: 0);
    }

    final random = Random();
    final selected = <Song>[];

    for (int i = 0; i < criteria.count; i++) {
      selected.add(filtered[random.nextInt(filtered.length)]);
    }

    return SelectionResult(songs: selected, totalAvailable: filtered.length);
  }

  Set<String> getGenres() {
    final genres = <String>{};
    for (final song in _songs) {
      if (song.genre != null && song.genre!.isNotEmpty) {
        genres.add(song.genre!);
      }
    }
    return genres;
  }

  int get totalSongs => _songs.length;

  int get totalCharts => _songs.fold(0, (sum, song) => sum + song.charts.length);
}
