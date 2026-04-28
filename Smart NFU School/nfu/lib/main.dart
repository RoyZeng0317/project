import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      debugShowCheckedModeBanner: false,
      home: MapPage(),
    );
  }
}

class MapPage extends StatelessWidget {
  const MapPage({super.key});

  static const CameraPosition _initialCameraPosition = CameraPosition(
    target: LatLng(23.6978, 120.9605),
    zoom: 7,
  );
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('School Parking lot')),
      body: const GoogleMap(
        initialCameraPosition: _initialCameraPosition,
        myLocationEnabled: true,
        myLocationButtonEnabled: true,
      ),
    );
  }
}

class ParkingLot {
  final int id;
  final String name;
  final String address;
  final double lat;
  final double lng;
  final int? totalSlots;
  final int? availableSlots;
  final int? feePerHour;

  ParkingLot({
    required this.id,
    required this.name,
    required this.address,
    required this.lat,
    required this.lng,
    this.totalSlots,
    this.availableSlots,
    this.feePerHour,
  });

  factory ParkingLot.fromMap(Map<String, dynamic> m) => ParkingLot(
    id: m['id'],
    name: m['name'],
    address: m['address'],
    lat: m['lat'],
    lng: m['lng'],
    totalSlots: m['totalSlots'],
    availableSlots: m['availableSlots'],
    feePerHour: m['feePerHour'],
  );
}
