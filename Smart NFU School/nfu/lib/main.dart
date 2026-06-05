import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'firebase_options.dart';
import 'map.dart';
import 'class.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      debugShowCheckedModeBanner: false,
      home: HomePage(),
    );
  }
}

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('虎科大智慧校園')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Card(
              child: ListTile(
                leading: const Icon(Icons.map, size: 40, color: Colors.blue),
                title: const Text('停車場地圖'),
                subtitle: const Text('查看校園停車位與路線規劃'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const MapPage()),
                ),
              ),
            ),
            const SizedBox(height: 8),
            Card(
              child: ListTile(
                leading: const Icon(
                  Icons.local_parking,
                  size: 40,
                  color: Colors.green,
                ),
                title: const Text('智慧教室牌'),
                subtitle: const Text('查詢未知教室的地理位置'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => _showParkingLots(context),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showParkingLots(BuildContext context) async {
    try {
      final lots = await fetchParkingLotsFromFirestore();
      if (!context.mounted) return;
      showModalBottomSheet(
        context: context,
        builder: (_) => ListView(
          padding: const EdgeInsets.all(16),
          children: lots
              .map(
                (lot) => ListTile(
                  title: Text(lot.name),
                  subtitle: Text(
                    '${lot.address}\n可用: ${lot.availableSlots ?? "?"} / 總共: ${lot.totalSlots ?? "?"}',
                  ),
                ),
              )
              .toList(),
        ),
      );
    } on Object catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('載入失敗: $e')));
      }
    }
  }
}
