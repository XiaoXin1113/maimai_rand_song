class Song {
  final String id;
  final String title;
  final String artist;
  final String type;
  final Map<String, double> difficulties;
  final String? genre;
  final String? version;
  final int? bpm;

  Song({
    required this.id,
    required this.title,
    required this.artist,
    required this.type,
    required this.difficulties,
    this.genre,
    this.version,
    this.bpm,
  });

  factory Song.fromJson(Map<String, dynamic> json) {
    return Song(
      id: json['id'],
      title: json['title'],
      artist: json['artist'],
      type: json['type'],
      difficulties: Map<String, double>.from(json['difficulties']),
      genre: json['genre'],
      version: json['version'],
      bpm: json['bpm'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'artist': artist,
      'type': type,
      'difficulties': difficulties,
      'genre': genre,
      'version': version,
      'bpm': bpm,
    };
  }
}
