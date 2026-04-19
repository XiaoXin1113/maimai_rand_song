import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const MaimaiApp());
}

class MaimaiApp extends StatelessWidget {
  const MaimaiApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'maimai随机选歌工具',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF667eea),
          brightness: Brightness.light,
        ),
        useMaterial3: true,
        fontFamily: 'PingFang SC',
      ),
      home: const HomeScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}
