import 'dart:convert';
import 'package:http/http.dart' as http;

class B2Service {
  final String baseUrl;

  B2Service({required this.baseUrl});

  Future<List<ParkingLotB2>> fetchParkingLots() async {
    final url = Uri.parse('$baseUrl/parking_lots/data.json');
    final response = await http.get(url);
    if (response.statusCode != 200) {
      throw Exception('B2 讀取失敗: HTTP ${response.statusCode}');
    }
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((json) => ParkingLotB2.fromJson(json)).toList();
  }

  String getImageUrl(int lotId) {
    return '$baseUrl/parking_lots/images/$lotId.jpg';
  }
}

class ParkingLotB2 {
  final int id;
  final String name;
  final String address;
  final double lat;
  final double lng;
  final int? totalSlots;
  final int? availableSlots;
  final int? feePerHour;
  final String? imageUrl;

  const ParkingLotB2({
    required this.id,
    required this.name,
    required this.address,
    required this.lat,
    required this.lng,
    this.totalSlots,
    this.availableSlots,
    this.feePerHour,
    this.imageUrl,
  });

  factory ParkingLotB2.fromJson(Map<String, dynamic> json) {
    return ParkingLotB2(
      id: json['id'] as int,
      name: json['name'] as String,
      address: json['address'] as String,
      lat: (json['lat'] as num).toDouble(),
      lng: (json['lng'] as num).toDouble(),
      totalSlots: json['totalSlots'] as int?,
      availableSlots: json['availableSlots'] as int?,
      feePerHour: json['feePerHour'] as int?,
      imageUrl: json['imageUrl'] as String?,
    );
  }
}
