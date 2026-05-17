import 'dart:async'; // 同步資料的庫
import 'dart:convert'; // 轉換到dart
import 'dart:math' as math; // 數學計算的庫
import 'package:flutter/material.dart';  // Flutter 的 UI 庫
import 'package:flutter/services.dart';  // 與平台通訊的庫
import 'package:geolocator/geolocator.dart';  // 獲取地理位置的庫
import 'package:google_maps_flutter/google_maps_flutter.dart'; // Google 地圖的 Flutter 插件
import 'package:http/http.dart' as http; // 發送 HTTP 請求的庫(主要是連線到 MySQL資料庫)

// 執行程式的開始點
void main() {
  runApp(const MyApp());
}
// google 的地圖 API 金鑰
const String googleMapsApiKey = 'AIzaSyDiHrp7c5hkRWtwXSoWYJ_Vtr6pgSR-z34';

// 執行程式的開始點
class MyApp extends StatelessWidget {
    const MyApp({super.key});

    @override
    Widget build(BuildContext context) {
        return MaterialApp(
            title: '虎科大智慧校園',
            theme: ThemeData(
                primarySwatch: Colors.blue,
            ),
            home: const HomePage(),
        );
    }
}
// 首頁
class HomePage extends StatefulWidget {
    const HomePage({super.key});

    @override
    State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  // Google 地圖控制器
  Completer<GoogleMapController> _mapController = Completer();
  // 使用者目前位置
  Position? _currentPosition;
  // 地圖初始位置，設定在虎尾鎮
  static final CameraPosition _initialCameraPosition = CameraPosition(
    target: LatLng(23.6978, 120.9605), // 以南投最為台灣本島的中心點
    zoom: 7,  // 縮放到 7 倍，顯示整個台灣
    );
}
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