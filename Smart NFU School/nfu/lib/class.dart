import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:cloud_firestore/cloud_firestore.dart';

class ParkingLot {
  final int id;
  final String name;
  final String address;
  final double lat;
  final double lng;
  final int? totalSlots;
  final int? availableSlots;
  final int? feePerHour;

  const ParkingLot({
    required this.id,
    required this.name,
    required this.address,
    required this.lat,
    required this.lng,
    this.totalSlots,
    this.availableSlots,
    this.feePerHour,
  });

  factory ParkingLot.fromFirestore(DocumentSnapshot doc) {
    final d = doc.data() as Map<String, dynamic>;
    return ParkingLot(
      id: d['id'] ?? doc.id.hashCode,
      name: d['name'] ?? '',
      address: d['address'] ?? '',
      lat: (d['lat'] as num?)?.toDouble() ?? 0,
      lng: (d['lng'] as num?)?.toDouble() ?? 0,
      totalSlots: d['totalSlots'] as int?,
      availableSlots: d['availableSlots'] as int?,
      feePerHour: d['feePerHour'] as int?,
    );
  }

  Map<String, dynamic> toFirestore() => {
    'name': name,
    'address': address,
    'lat': lat,
    'lng': lng,
    'totalSlots': totalSlots,
    'availableSlots': availableSlots,
    'feePerHour': feePerHour,
  };
}

Future<List<ParkingLot>> fetchParkingLotsFromFirestore() async {
  final snapshot = await FirebaseFirestore.instance
      .collection('parking_lots')
      .get();
  return snapshot.docs.map((doc) => ParkingLot.fromFirestore(doc)).toList();
}

Future<void> sendMessageToFirestore(String msg) async {
  await FirebaseFirestore.instance.collection('messages').add({
    'message': msg,
    'createdAt': FieldValue.serverTimestamp(),
  });
}

Future<List<Map<String, dynamic>>> getMessagesFromFirestore() async {
  final snapshot = await FirebaseFirestore.instance
      .collection('messages')
      .orderBy('createdAt', descending: true)
      .get();
  return snapshot.docs.map((doc) {
    final d = doc.data();
    d['id'] = doc.id;
    return d;
  }).toList();
}

class Esp32Data {
  final int carCount;
  final double latitude;
  final double longitude;
  final int satellites;

  const Esp32Data({
    this.carCount = 0,
    this.latitude = 0,
    this.longitude = 0,
    this.satellites = 0,
  });

  factory Esp32Data.fromJson(Map<String, dynamic> json) {
    return Esp32Data(
      carCount: json['carCount'] as int? ?? 0,
      latitude: (json['latitude'] as num?)?.toDouble() ?? 0,
      longitude: (json['longitude'] as num?)?.toDouble() ?? 0,
      satellites: json['satellites'] as int? ?? 0,
    );
  }
}

Future<Esp32Data> fetchEsp32Data(String ip) async {
  final response = await http
      .get(Uri.parse('http://$ip/data'))
      .timeout(const Duration(seconds: 5));
  if (response.statusCode != 200) {
    throw 'ESP32 回應錯誤: HTTP ${response.statusCode}';
  }
  return Esp32Data.fromJson(jsonDecode(response.body));
}
