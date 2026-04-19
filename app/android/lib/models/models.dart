import 'dart:convert';

enum Difficulty {
  easy('easy', 'Easy'),
  basic('basic', 'Basic'),
  advanced('advanced', 'Advanced'),
  expert('expert', 'Expert'),
  master('master', 'Master'),
  remaster('remaster', 'Re:Master'),
  utage('utage', 'Utage');

  final String value;
  final String displayName;
  const Difficulty(this.value, this.displayName);
}

enum SongType {
  std('std', '标准'),
  dx('dx', 'DX'),
  utage('utage', 'Utage');

  final String value;
  final String displayName;
  const SongType(this.value, this.displayName);
}

class NoteCounts {
  final int tap;
  final int hold;
  final int slide;
  final int touch;
  final int breakNote;
  final int total;

  NoteCounts({
    this.tap = 0,
    this.hold = 0,
    this.slide = 0,
    this.touch = 0,
    this.breakNote = 0,
    this.total = 0,
  });

  factory NoteCounts.fromJson(Map<String, dynamic> json) {
    return NoteCounts(
      tap: json['tap'] ?? 0,
      hold: json['hold'] ?? 0,
      slide: json['slide'] ?? 0,
      touch: json['touch'] ?? 0,
      breakNote: json['break_note'] ?? json['break'] ?? 0,
      total: json['total'] ?? 0,
    );
  }
}

class Chart {
  final SongType type;
  final Difficulty difficulty;
  final String level;
  final double? internalLevel;
  final String? noteDesigner;
  final NoteCounts? noteCounts;

  Chart({
    required this.type,
    required this.difficulty,
    required this.level,
    this.internalLevel,
    this.noteDesigner,
    this.noteCounts,
  });

  factory Chart.fromJson(Map<String, dynamic> json) {
    return Chart(
      type: SongType.values.firstWhere(
        (t) => t.value == json['type'],
        orElse: () => SongType.std,
      ),
      difficulty: Difficulty.values.firstWhere(
        (d) => d.value == json['difficulty'],
        orElse: () => Difficulty.master,
      ),
      level: json['level'] ?? '',
      internalLevel: json['internal_level']?.toDouble(),
      noteDesigner: json['note_designer'],
      noteCounts: json['note_counts'] != null
          ? NoteCounts.fromJson(json['note_counts'])
          : null,
    );
  }
}

class Song {
  final int id;
  final String title;
  final String artist;
  final int bpm;
  final String? genre;
  final SongType type;
  final List<Chart> charts;
  final List<String> alias;

  static const String coverBaseUrl =
      'https://raw.githubusercontent.com/realtvop/maimai_music_metadata/main/covers';

  Song({
    required this.id,
    required this.title,
    required this.artist,
    required this.bpm,
    this.genre,
    required this.type,
    required this.charts,
    this.alias = const [],
  });

  String get coverUrl {
    return '$coverBaseUrl/${id.toString().padLeft(6, '0')}.png';
  }

  factory Song.fromJson(Map<String, dynamic> json) {
    return Song(
      id: json['id'] ?? 0,
      title: json['title'] ?? '',
      artist: json['artist'] ?? '',
      bpm: json['bpm'] ?? 0,
      genre: json['genre'],
      type: SongType.values.firstWhere(
        (t) => t.value == json['type'],
        orElse: () => SongType.std,
      ),
      charts: (json['charts'] as List<dynamic>?)
              ?.map((c) => Chart.fromJson(c))
              .toList() ??
          [],
      alias: (json['alias'] as List<dynamic>?)
              ?.map((a) => a.toString())
              .toList() ??
          [],
    );
  }
}

class SelectionCriteria {
  final double? minLevel;
  final double? maxLevel;
  final Difficulty? difficulty;
  final SongType? songType;
  final String? genre;
  final int count;

  SelectionCriteria({
    this.minLevel,
    this.maxLevel,
    this.difficulty,
    this.songType,
    this.genre,
    this.count = 1,
  });
}

class SelectionResult {
  final List<Song> songs;
  final int totalAvailable;

  SelectionResult({
    required this.songs,
    required this.totalAvailable,
  });
}

List<double> parseLevelInput(String levelStr) {
  if (levelStr.isEmpty)
    return [null as dynamic, null as dynamic] as List<double>;

  final hasPlus = levelStr.contains('+');
  final cleanStr = levelStr.replaceAll('+', '').trim();
  final hasDecimal = cleanStr.contains('.');

  final level = double.tryParse(cleanStr);
  if (level == null) return [null as dynamic, null as dynamic] as List<double>;

  if (hasPlus) {
    final levelInt = level.toInt();
    return [(levelInt + 0.6).toDouble(), (levelInt + 0.9).toDouble()];
  } else if (!hasDecimal && level == level.toInt()) {
    final levelInt = level.toInt();
    return [levelInt.toDouble(), (levelInt + 0.5).toDouble()];
  } else {
    return [(level - 0.05).toDouble(), (level + 0.05).toDouble()];
  }
}
