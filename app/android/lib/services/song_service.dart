import 'dart:convert';
import 'dart:io';
import 'package:flutter/services.dart';
import '../models/song.dart';

class SongService {
  List<Song> _songs = [];
  bool _initialized = false;

  Future<void> _initialize() async {
    if (_initialized) return;
    
    try {
      final String data = await rootBundle.loadString('../../../data/songs.json');
      final List<dynamic> jsonList = json.decode(data);
      _songs = jsonList.map((json) => Song.fromJson(json)).toList();
      _initialized = true;
    } catch (e) {
      _songs = [];
      _initialized = true;
    }
  }

  Future<List<String>> getGenres() async {
    await _initialize();
    final genres = <String>{};
    for (final song in _songs) {
      if (song.genre != null) {
        genres.add(song.genre!);
      }
    }
    return genres.toList()..sort();
  }

  Future<Map<String, dynamic>> selectRandom({
    String? difficulty,
    double? minLevel,
    double? maxLevel,
    String? songType,
    String? genre,
    int count = 1,
  }) async {
    await _initialize();
    
    var filtered = List<Song>.from(_songs);
    
    if (songType != null) {
      filtered = filtered.where((s) => s.type == songType).toList();
    }
    
    if (genre != null) {
      filtered = filtered.where((s) => s.genre == genre).toList();
    }
    
    if (difficulty != null && minLevel != null) {
      filtered = filtered.where((s) {
        final level = s.difficulties[difficulty] ?? 0;
        return level >= minLevel;
      }).toList();
    }
    
    if (difficulty != null && maxLevel != null) {
      filtered = filtered.where((s) {
        final level = s.difficulties[difficulty] ?? 15;
        return level <= maxLevel;
      }).toList();
    }
    
    final totalAvailable = filtered.length;
    final actualCount = count > filtered.length ? filtered.length : count;
    
    filtered.shuffle();
    final selected = filtered.take(actualCount).toList();
    
    return {
      'songs': selected,
      'total_available': totalAvailable,
    };
  }

  Future<List<Song>> getAllSongs() async {
    await _initialize();
    return List.from(_songs);
  }
}
