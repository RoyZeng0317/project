import 'dart:async';
import 'dart:convert';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:geolocator/geolocator.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:http/http.dart' as http;
import 'package:firebase_core/firebase_core.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'firebase_options.dart';
import 'b2_service.dart';
// import 'seed_firestore.dart';
const String googleMapsApiKey = 'AIzaSyDiHrp7c5hkRWtwXSoWYJ_Vtr6pgSR-z34';

const String b2BaseUrl = 'https://f002.backblazeb2.com/file/YOUR_BUCKET_NAME';
final b2Service = B2Service(baseUrl: b2BaseUrl);

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  // await seedParkingLots();
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

class MapPage extends StatefulWidget {
  const MapPage({super.key});

  @override
  State<MapPage> createState() => _MapPageState();
}

class _MapPageState extends State<MapPage> {
  static const MethodChannel _navigationChannel = MethodChannel('nfu/navigation');

  static const CameraPosition _initialCameraPosition = CameraPosition(
    target: LatLng(23.6978, 120.9605),
    zoom: 8,
  );

  GoogleMapController? _mapController;
  Position? _currentPosition;
  Set<Polyline> _polylines = {};
  bool _isLoadingRoute = false;
  bool _isLoadingLots = true;

  List<ParkingLot> _parkingLots = [];
  ParkingLot? _selectedParkingLot;

  LatLng? get _destination {
    if (_selectedParkingLot == null) return null;
    return LatLng(_selectedParkingLot!.lat, _selectedParkingLot!.lng);
  }

  @override
  void initState() {
    super.initState();
    unawaited(_initMap());
  }

  @override
  void dispose() {
    _mapController?.dispose();
    super.dispose();
  }

  Future<void> _initMap() async {
    await Future.wait([
      _loadCurrentLocation(),
      _loadParkingLots(),
    ]);
  }

  Future<void> _loadParkingLots() async {
    try {
      List<ParkingLot> lots;
      try {
        final b2Lots = await b2Service.fetchParkingLots();
        lots = b2Lots.map((b) => ParkingLot.fromB2Json(b)).toList();
      } on Object catch (_) {
        lots = await fetchParkingLotsFromFirestore();
      }
      if (!mounted) return;
      setState(() {
        _parkingLots = lots;
        _isLoadingLots = false;
        if (lots.isNotEmpty) {
          _selectedParkingLot = lots.first;
        }
      });
    } on Object catch (e) {
      if (!mounted) return;
      setState(() => _isLoadingLots = false);
      _showMessage('無法載入停車場資料: $e');
    }
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
    if (!serviceEnabled) throw '請先開啟定位服務';
    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied) throw '需要定位權限才能規劃路線';
    if (permission == LocationPermission.deniedForever) {
      throw '定位權限已被永久拒絕，請到系統設定中開啟';
    }
    return Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
    );
  }

  void _onMarkerTapped(ParkingLot lot) {
    setState(() => _selectedParkingLot = lot);
    _mapController?.animateCamera(
      CameraUpdate.newLatLngZoom(LatLng(lot.lat, lot.lng), 16),
    );
  }

  Future<void> _drawRoute() async {
    if (_destination == null) return;
    setState(() => _isLoadingRoute = true);
    try {
      final origin = _currentPosition ?? await _determinePosition();
      final originLatLng = LatLng(origin.latitude, origin.longitude);
      final points = await _fetchDirections(originLatLng, _destination!);
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
      await _fitMapToRoute([originLatLng, _destination!, ...points]);
    } on Object catch (error) {
      if (!mounted) return;
      _showMessage(error.toString());
    } finally {
      if (mounted) setState(() => _isLoadingRoute = false);
    }
  }

  Future<List<LatLng>> _fetchDirections(LatLng origin, LatLng destination) async {
    final uri = Uri.https('maps.googleapis.com', '/maps/api/directions/json', {
      'origin': '${origin.latitude},${origin.longitude}',
      'destination': '${destination.latitude},${destination.longitude}',
      'mode': 'driving',
      'language': 'zh-TW',
      'key': googleMapsApiKey,
    });
    final response = await http.get(uri);
    if (response.statusCode != 200) {
      throw '路線請求失敗: HTTP ${response.statusCode}';
    }
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final status = data['status'] as String?;
    if (status != 'OK') {
      throw data['error_message'] as String? ?? 'Google Directions API 回傳: $status';
    }
    final routes = data['routes'] as List<dynamic>;
    if (routes.isEmpty) throw '找不到可用路線';
    final route = routes.first as Map<String, dynamic>;
    final polyline = route['overview_polyline'] as Map<String, dynamic>;
    final encoded = polyline['points'] as String?;
    if (encoded == null || encoded.isEmpty) throw '路線回應缺少 polyline';
    return _decodePolyline(encoded);
  }

  Future<void> _openGoogleMapsNavigation() async {
    if (_destination == null) return;
    try {
      await _navigationChannel.invokeMethod<void>('openNavigation', {
        'latitude': _destination!.latitude,
        'longitude': _destination!.longitude,
      });
    } on PlatformException catch (error) {
      _showMessage(error.message ?? '無法開啟 Google Maps 導航');
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
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  Set<Marker> _buildMarkers() {
    return _parkingLots.map((lot) {
      final isSelected = _selectedParkingLot?.id == lot.id;
      return Marker(
        markerId: MarkerId(lot.id.toString()),
        position: LatLng(lot.lat, lot.lng),
        icon: isSelected
            ? BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueAzure)
            : BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueRed),
        infoWindow: InfoWindow(
          title: lot.name,
          snippet: '可用: ${lot.availableSlots ?? "?"} / 總共: ${lot.totalSlots ?? "?"}',
        ),
        onTap: () => _onMarkerTapped(lot),
      );
    }).toSet();
  }

  @override
  Widget build(BuildContext context) {
    final markers = _buildMarkers();

    return Scaffold(
      appBar: AppBar(title: const Text('虎科大智慧校園 - 停車場')),
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
                unawaited(controller.animateCamera(
                  CameraUpdate.newLatLngZoom(
                    LatLng(currentPosition.latitude, currentPosition.longitude),
                    15,
                  ),
                ));
              }
            },
          ),
          if (_isLoadingLots)
            const Center(child: CircularProgressIndicator()),
          if (_selectedParkingLot != null && !_isLoadingLots)
            Positioned(
              left: 16,
              right: 16,
              bottom: 24,
              child: _ParkingLotPanel(
                parkingLot: _selectedParkingLot!,
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
            Text(parkingLot.name, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 4),
            Text(parkingLot.address),
            const SizedBox(height: 8),
            Wrap(
              spacing: 12,
              runSpacing: 4,
              children: [
                if (parkingLot.availableSlots != null)
                  Text('可用: ${parkingLot.availableSlots}'),
                if (parkingLot.totalSlots != null)
                  Text('總共: ${parkingLot.totalSlots}'),
                if (parkingLot.feePerHour != null)
                  Text('每小時: \$${parkingLot.feePerHour}'),
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
                    label: const Text('顯示路線'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: onNavigate,
                    icon: const Icon(Icons.navigation),
                    label: const Text('導航'),
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

  factory ParkingLot.fromB2Json(ParkingLotB2 b2) {
    return ParkingLot(
      id: b2.id,
      name: b2.name,
      address: b2.address,
      lat: b2.lat,
      lng: b2.lng,
      totalSlots: b2.totalSlots,
      availableSlots: b2.availableSlots,
      feePerHour: b2.feePerHour,
    );
  }

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
