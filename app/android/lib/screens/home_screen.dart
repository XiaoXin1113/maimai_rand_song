import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/song_manager.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final SongManager _songManager = SongManager();
  bool _isLoading = true;

  final _difficultyController = TextEditingController();
  final _minLevelController = TextEditingController();
  final _maxLevelController = TextEditingController();
  final _countController = TextEditingController(text: '1');

  Difficulty? _selectedDifficulty;
  SongType? _selectedSongType;
  String? _selectedGenre;
  List<Song> _results = [];
  int _totalAvailable = 0;
  bool _hasSearched = false;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    await _songManager.loadSongs();
    setState(() {
      _isLoading = false;
    });
  }

  void _selectRandom() {
    double? minLevel;
    double? maxLevel;

    if (_minLevelController.text.isNotEmpty) {
      final parsed = parseLevelInput(_minLevelController.text);
      minLevel = parsed[0];
    }
    if (_maxLevelController.text.isNotEmpty) {
      final parsed = parseLevelInput(_maxLevelController.text);
      maxLevel = parsed[1];
    }

    final count = int.tryParse(_countController.text) ?? 1;

    final criteria = SelectionCriteria(
      minLevel: minLevel,
      maxLevel: maxLevel,
      difficulty: _selectedDifficulty,
      songType: _selectedSongType,
      genre: _selectedGenre,
      count: count,
    );

    final result = _songManager.selectRandom(criteria);

    setState(() {
      _results = result.songs;
      _totalAvailable = result.totalAvailable;
      _hasSearched = true;
    });
  }

  void _clearCriteria() {
    setState(() {
      _selectedDifficulty = null;
      _selectedSongType = null;
      _selectedGenre = null;
      _minLevelController.clear();
      _maxLevelController.clear();
      _countController.text = '1';
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🎵 maimai随机选歌工具'),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: _showAbout,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildCriteriaCard(),
                  const SizedBox(height: 16),
                  _buildResultsCard(),
                ],
              ),
            ),
    );
  }

  Widget _buildCriteriaCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '选歌条件',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _buildDropdown<Difficulty>(
                    label: '难度',
                    value: _selectedDifficulty,
                    items: Difficulty.values,
                    onChanged: (v) => setState(() => _selectedDifficulty = v),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: _buildDropdown<SongType>(
                    label: '歌曲类型',
                    value: _selectedSongType,
                    items: SongType.values,
                    onChanged: (v) => setState(() => _selectedSongType = v),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            _buildDropdown<String>(
              label: '流派',
              value: _selectedGenre,
              items: _songManager.getGenres().toList()..sort(),
              onChanged: (v) => setState(() => _selectedGenre = v),
              includeAll: true,
            ),
            const SizedBox(height: 16),
            Text(
              '等级范围',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _minLevelController,
                    decoration: const InputDecoration(
                      labelText: '最低等级',
                      hintText: '如: 14, 14+, 14.5',
                      border: OutlineInputBorder(),
                    ),
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: TextField(
                    controller: _maxLevelController,
                    decoration: const InputDecoration(
                      labelText: '最高等级',
                      hintText: '如: 14, 14+, 14.5',
                      border: OutlineInputBorder(),
                    ),
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                const Text('随机次数: '),
                SizedBox(
                  width: 80,
                  child: TextField(
                    controller: _countController,
                    decoration: const InputDecoration(
                      border: OutlineInputBorder(),
                      contentPadding: EdgeInsets.symmetric(horizontal: 12),
                    ),
                    keyboardType: TextInputType.number,
                  ),
                ),
                const SizedBox(width: 8),
                const Text('(可重复)', style: TextStyle(color: Colors.grey)),
              ],
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: FilledButton.icon(
                    onPressed: _selectRandom,
                    icon: const Icon(Icons.casino),
                    label: const Text('随机选歌'),
                    style: FilledButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton(
                    onPressed: _clearCriteria,
                    child: const Text('清空条件'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    '总歌曲: ${_songManager.totalSongs} | 总谱面: ${_songManager.totalCharts}',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDropdown<T>({
    required String label,
    required T? value,
    required List items,
    required void Function(T?) onChanged,
    bool includeAll = false,
  }) {
    return DropdownButtonFormField<T>(
      value: value,
      decoration: InputDecoration(
        labelText: label,
        border: const OutlineInputBorder(),
      ),
      items: [
        if (includeAll)
          DropdownMenuItem(
            value: null,
            child: const Text('全部'),
          ),
        ...items.map((item) {
          String displayText;
          if (item is Difficulty) {
            displayText = item.displayName;
          } else if (item is SongType) {
            displayText = item.displayName;
          } else {
            displayText = item.toString();
          }
          return DropdownMenuItem(
            value: item as T,
            child: Text(displayText),
          );
        }),
      ],
      onChanged: onChanged,
    );
  }

  Widget _buildResultsCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '选歌结果',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 12),
            if (!_hasSearched)
              const Center(
                child: Padding(
                  padding: EdgeInsets.all(32),
                  child: Text(
                    '请设置条件后点击"随机选歌"',
                    style: TextStyle(color: Colors.grey),
                  ),
                ),
              )
            else if (_results.isEmpty)
              const Center(
                child: Padding(
                  padding: EdgeInsets.all(32),
                  child: Text(
                    '没有找到符合条件的歌曲',
                    style: TextStyle(color: Colors.grey),
                  ),
                ),
              )
            else ...[
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text(
                  '共找到 $_totalAvailable 首符合条件的歌曲',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.grey[600],
                      ),
                ),
              ),
              ..._results.asMap().entries.map((entry) {
                final index = entry.key;
                final song = entry.value;
                return _buildSongCard(index + 1, song);
              }),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildSongCard(int index, Song song) {
    final chartsByType = <SongType, List<Chart>>{};
    for (final chart in song.charts) {
      chartsByType.putIfAbsent(chart.type, () => []).add(chart);
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: Image.network(
              song.coverUrl,
              width: 100,
              height: 100,
              fit: BoxFit.cover,
              errorBuilder: (context, error, stackTrace) {
                return Container(
                  width: 100,
                  height: 100,
                  color: Colors.grey[300],
                  child: const Icon(Icons.music_note,
                      size: 40, color: Colors.grey),
                );
              },
              loadingBuilder: (context, child, loadingProgress) {
                if (loadingProgress == null) return child;
                return Container(
                  width: 100,
                  height: 100,
                  color: Colors.grey[200],
                  child: const Center(
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                );
              },
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '【$index】${song.title}',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: Theme.of(context).colorScheme.primary,
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 4),
                Text('艺术家: ${song.artist}'),
                Text('类型: ${song.type.displayName}'),
                if (song.genre != null) Text('流派: ${song.genre}'),
                Text('BPM: ${song.bpm}'),
                const SizedBox(height: 8),
                const Text(
                  '谱面:',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                ...chartsByType.entries.map((entry) {
                  final typeStr = entry.key.displayName;
                  final charts = entry.value;
                  final chartInfo = charts.map((c) {
                    final levelStr = c.internalLevel != null
                        ? '${c.level} (${c.internalLevel})'
                        : c.level;
                    return '${c.difficulty.displayName} $levelStr';
                  }).join(' | ');
                  return Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      '  $typeStr: $chartInfo',
                      style: TextStyle(color: Colors.red[700]),
                    ),
                  );
                }),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _showAbout() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('关于'),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('🎵 maimai随机选歌工具'),
            SizedBox(height: 8),
            Text('Android版 - Alpha-0.0.3'),
            SizedBox(height: 16),
            Text('一款用于maimai游戏的随机选歌工具'),
            Text('支持精确难度筛选、多条件组合查询'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('确定'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _difficultyController.dispose();
    _minLevelController.dispose();
    _maxLevelController.dispose();
    _countController.dispose();
    super.dispose();
  }
}
