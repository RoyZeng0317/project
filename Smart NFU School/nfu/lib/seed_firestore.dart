import 'package:firebase_core/firebase_core.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

/// 執行一次將初始資料寫入 Firestore
Future<void> seedParkingLots() async {
  final db = FirebaseFirestore.instance;
  final batch = db.batch();

  final lots = [
    {
      'id': 1,
      'name': '第一停車場',
      'address': '第一校區警衛室大門ATD與ASA旁',
      'lat': 23.70310,
      'lng': 120.43210,
      'totalSlots': 120,
      'availableSlots': 35,
      'feePerHour': 30,
    },
    {
      'id': 2,
      'name': '第二停車場',
      'address': '第一校區ATC與行政大樓後方',
      'lat': 23.70220,
      'lng': 120.43120,
      'totalSlots': 80,
      'availableSlots': 12,
      'feePerHour': 25,
    },
    {
      'id': 3,
      'name': '第三停車場',
      'address': '第一校區ATA後方',
      'lat': 23.70170,
      'lng': 120.43300,
      'totalSlots': 60,
      'availableSlots': 20,
      'feePerHour': 20,
    },
    {
      'id': 4,
      'name': '第四停車場',
      'address': '第一校區AGR後方',
      'lat': 23.70410,
      'lng': 120.43050,
      'totalSlots': 100,
      'availableSlots': 55,
      'feePerHour': 35,
    },
    {
      'id': 5,
      'name': '第五停車場',
      'address': '第三校區CPB與CPG旁',
      'lat': 23.70090,
      'lng': 120.43430,
      'totalSlots': 150,
      'availableSlots': 70,
      'feePerHour': 40,
    },
  ];

  for (final lot in lots) {
    final ref = db.collection('parking_lots').doc();
    batch.set(ref, lot);
  }

  await batch.commit();
  print('✅ 已寫入 ${lots.length} 筆停車場資料到 Firestore');
}
