import 'dart:async'; // 同步資料的庫
import 'dart:convert';
import 'dart:math' as math; // 數學計算的庫
import 'package:flutter/material.dart';  // Flutter 的 UI 庫
import 'package:flutter/services.dart';  // 與平台通訊的庫
import 'package:geolocator/geolocator.dart';  // 獲取地理位置的庫
import 'package:google_maps_flutter/google_maps_flutter.dart'; // Google 地圖的 Flutter 插件
import 'package:http/http.dart' as http; // 發送 HTTP 請求的庫
// 執行程式的開始點
void main() {
  runApp(const MyApp());
}
// google 的地圖 API 金鑰
const String googleMapsApiKey = 'AIzaSyDiHrp7c5hkRWtwXSoWYJ_Vtr6pgSR-z34';

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

class MapPage extends StatefulWidget {
  const MapPage({super.key});

  @override
  State<MapPage> createState() => _MapPageState();
}

class _MapPageState extends State<MapPage> {
  static const MethodChannel _navigationChannel = MethodChannel(
    'nfu/navigation',
  );

  static const CameraPosition _initialCameraPosition = CameraPosition(
    target: LatLng(23.6978, 120.9605),
    zoom: 7,
  );
  // 目標停車場資訊，這裡使用了 ATC 第三教學大樓電子工程系旁停車場的資訊作為範例
  static const ParkingLot _targetParkingLot = ParkingLot(
    id: 1,
    name: 'ATC 第三教學大樓電子工程系旁停車場',
    address: '632雲林縣虎尾鎮文化路64號',
    lat: 23.7030,
    lng: 120.4294,
    totalSlots: 120,
    availableSlots: 35,
    feePerHour: 20,
  );

  GoogleMapController? _mapController;
  Position? _currentPosition;
  Set<Polyline> _polylines = {};
  bool _isLoadingRoute = false;

  LatLng get _destination =>
      LatLng(_targetParkingLot.lat, _targetParkingLot.lng);

  @override
  void initState() {
    super.initState();
    unawaited(_loadCurrentLocation());
  }

  @override
  void dispose() {
    _mapController?.dispose();
    super.dispose();
  }

  Future<void> _loadCurrentLocation() async {
    try {
      final position = await _determinePosition();
      if (!mounted) return;

      setState(() => _currentPosition = position);
      await _mapController?.animateCamera(
        CameraUpdate.newLatLngZoom(
          LatLng(position.latitude, position.longitude),
          15,
        ),
      );
    } on Object catch (error) {
      if (!mounted) return;
      _showMessage(error.toString());
    }
  }

  Future<Position> _determinePosition() async {
    final serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      throw 'Please enable location services first.';
    }

    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }

    if (permission == LocationPermission.denied) {
      throw 'Location permission is required to plan a route.';
    }

    if (permission == LocationPermission.deniedForever) {
      throw 'Location permission is permanently denied. Enable it in system settings.';
    }

    return Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
    );
  }

  Future<List<ParkingLocation>> fetchParkingLocations() async {
    final response = await http.get(Uri.parse('http://localhost:3000/parking-locations'));

    if (response.statusCode == 200) {
      List jsonResponse = json.decode(response.body);
      return jsonResponse.map((location) => ParkingLocation.fromJson(location)).toList();
    } else {
      throw Exception('無法加載停車場位置');
    }
  }

  Future<void> _drawRoute() async {
    setState(() => _isLoadingRoute = true);

    try {
      final origin = _currentPosition ?? await _determinePosition();
      final originLatLng = LatLng(origin.latitude, origin.longitude);
      final points = await _fetchDirections(originLatLng, _destination);

      if (!mounted) return;
      setState(() {
        _currentPosition = origin;
        _polylines = {
          Polyline(
            polylineId: const PolylineId('route_to_parking_lot'),
            points: points,
            color: Colors.blue,
            width: 6,
          ),
        };
      });

      await _fitMapToRoute([originLatLng, _destination, ...points]);
    } on Object catch (error) {
      if (!mounted) return;
      _showMessage(error.toString());
    } finally {
      if (mounted) {
        setState(() => _isLoadingRoute = false);
      }
    }
  }

  Future<List<LatLng>> _fetchDirections(
    LatLng origin,
    LatLng destination,
  ) async {
    final uri = Uri.https('maps.googleapis.com', '/maps/api/directions/json', {
      'origin': '${origin.latitude},${origin.longitude}',
      'destination': '${destination.latitude},${destination.longitude}',
      'mode': 'driving',
      'language': 'zh-TW',
      'key': googleMapsApiKey,
    });

    final response = await http.get(uri);
    if (response.statusCode != 200) {
      throw 'Route request failed: HTTP ${response.statusCode}';
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final status = data['status'] as String?;
    if (status != 'OK') {
      final message = data['error_message'] as String?;
      throw message ?? 'Google Directions API returned: $status';
    }

    final routes = data['routes'] as List<dynamic>;
    if (routes.isEmpty) {
      throw 'No available route was found.';
    }

    final route = routes.first as Map<String, dynamic>;
    final polyline = route['overview_polyline'] as Map<String, dynamic>;
    final encoded = polyline['points'] as String?;
    if (encoded == null || encoded.isEmpty) {
      throw 'Route response does not contain a polyline.';
    }

    return _decodePolyline(encoded);
  }

  Future<void> _openGoogleMapsNavigation() async {
    try {
      await _navigationChannel.invokeMethod<void>('openNavigation', {
        'latitude': _destination.latitude,
        'longitude': _destination.longitude,
      });
    } on PlatformException catch (error) {
      _showMessage(error.message ?? 'Unable to open Google Maps navigation.');
    }
  }

  Future<void> _fitMapToRoute(List<LatLng> points) async {
    if (points.isEmpty) return;

    var minLat = points.first.latitude;
    var maxLat = points.first.latitude;
    var minLng = points.first.longitude;
    var maxLng = points.first.longitude;

    for (final point in points.skip(1)) {
      minLat = math.min(minLat, point.latitude);
      maxLat = math.max(maxLat, point.latitude);
      minLng = math.min(minLng, point.longitude);
      maxLng = math.max(maxLng, point.longitude);
    }

    await _mapController?.animateCamera(
      CameraUpdate.newLatLngBounds(
        LatLngBounds(
          southwest: LatLng(minLat, minLng),
          northeast: LatLng(maxLat, maxLng),
        ),
        72,
      ),
    );
  }

  List<LatLng> _decodePolyline(String encoded) {
    final points = <LatLng>[];
    var index = 0;
    var lat = 0;
    var lng = 0;

    while (index < encoded.length) {
      final latResult = _decodePolylineValue(encoded, index);
      index = latResult.nextIndex;
      lat += latResult.value;

      final lngResult = _decodePolylineValue(encoded, index);
      index = lngResult.nextIndex;
      lng += lngResult.value;

      points.add(LatLng(lat / 1E5, lng / 1E5));
    }

    return points;
  }

  _DecodedPolylineValue _decodePolylineValue(String encoded, int startIndex) {
    var index = startIndex;
    var result = 0;
    var shift = 0;
    int byte;

    do {
      byte = encoded.codeUnitAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);

    final value = (result & 1) != 0 ? ~(result >> 1) : result >> 1;
    return _DecodedPolylineValue(value, index);
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final markers = {
      Marker(
        markerId: const MarkerId('parking_lot'),
        position: _destination,
        infoWindow: InfoWindow(
          title: _targetParkingLot.name,
          snippet: _targetParkingLot.address,
        ),
      ),
    };

    return Scaffold(
      appBar: AppBar(title: const Text('School Parking lot')),
      body: Stack(
        children: [
          GoogleMap(
            initialCameraPosition: _initialCameraPosition,
            myLocationEnabled: _currentPosition != null,
            myLocationButtonEnabled: true,
            markers: markers,
            polylines: _polylines,
            onMapCreated: (controller) {
              _mapController = controller;
              final currentPosition = _currentPosition;
              if (currentPosition != null) {
                unawaited(
                  controller.animateCamera(
                    CameraUpdate.newLatLngZoom(
                      LatLng(
                        currentPosition.latitude,
                        currentPosition.longitude,
                      ),
                      15,
                    ),
                  ),
                );
              }
            },
          ),
          Positioned(
            left: 16,
            right: 16,
            bottom: 24,
            child: _ParkingLotPanel(
              parkingLot: _targetParkingLot,
              isLoadingRoute: _isLoadingRoute,
              onDrawRoute: _drawRoute,
              onNavigate: _openGoogleMapsNavigation,
            ),
          ),
        ],
      ),
    );
  }
}

class _DecodedPolylineValue {
  const _DecodedPolylineValue(this.value, this.nextIndex);

  final int value;
  final int nextIndex;
}

class _ParkingLotPanel extends StatelessWidget {
  const _ParkingLotPanel({
    required this.parkingLot,
    required this.isLoadingRoute,
    required this.onDrawRoute,
    required this.onNavigate,
  });

  final ParkingLot parkingLot;
  final bool isLoadingRoute;
  final VoidCallback onDrawRoute;
  final VoidCallback onNavigate;

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 8,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              parkingLot.name,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 4),
            Text(parkingLot.address),
            const SizedBox(height: 8),
            Wrap(
              spacing: 12,
              runSpacing: 4,
              children: [
                if (parkingLot.availableSlots != null)
                  Text('Available: ${parkingLot.availableSlots}'),
                if (parkingLot.totalSlots != null)
                  Text('Total: ${parkingLot.totalSlots}'),
                if (parkingLot.feePerHour != null)
                  Text('Hourly: \$${parkingLot.feePerHour}'),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: isLoadingRoute ? null : onDrawRoute,
                    icon: isLoadingRoute
                        ? const SizedBox.square(
                            dimension: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.alt_route),
                    label: const Text('Show route'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: onNavigate,
                    icon: const Icon(Icons.navigation),
                    label: const Text('Navigate'),
                  ),
                ),
              ],
            ),
          ],
        ),
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
class ParkingLocation {
  final int id;
  final String name;
  final double latitude;
  final double longitude;

  ParkingLocation({required this.id, required this.name, required this.latitude, required this.longitude});

  factory ParkingLocation.fromJson(Map<String, dynamic> json) {
    return ParkingLocation(
      id: json['id'],
      name: json['name'],
      latitude: json['latitude'],
      longitude: json['longitude'],
    );
  }
}

// 連線到 MySQL資料庫
Future<void> sendMessage(String msg) async{
    final response = await http.post(

        Uri.parse("https://mydomain.com/send.php"),

        body:{
            "message": msg
        },
    );
    print(response.body);
}

Future<void> getMessages() async{
    final response = await http.get(
        Uri.parse("https://mydomain.com/api.php"),
    );

    var data = jsonDecode(response.body);

    print(data);
}