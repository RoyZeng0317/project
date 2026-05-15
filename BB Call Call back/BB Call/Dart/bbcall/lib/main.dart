import 'dart:async';

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:network_info_plus/network_info_plus.dart';
import 'package:wifi_iot/wifi_iot.dart';
import 'package:permission_handler/permission_handler.dart';
import 'firebase_options.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  runApp(const BbCallApp());
}
// Get the current Wi-Fi information (SSID, BSSID, IP address).
Future<void> getWiFiInfo() async {
  final info = NetworkInfo();
  
  final wifiName = await info.getWifiName();
  final wifiBSSID = await info.getWifiBSSID();
  final wifiIP = await info.getWifiIP();

  print('Wi-Fi Name: $wifiName');
  print('Wi-Fi BSSID: $wifiBSSID');
  print('Wi-Fi IP: $wifiIP');
}

Future<bool> requestWiFiPermissions() async {
  final location = await Permission.location.request();
  final nearbyWifiDevices = await Permission.nearbyWifiDevices.request();

  return location.isGranted || nearbyWifiDevices.isGranted;
}

// Connection for the Wi-Fi.
Future<void> connectToWiFi() async {
  const ssid = 'Your_WiFi_Name';
  const password = 'Your_WiFi_Password';

  final connected = await WiFiForIoTPlugin.connect(
    ssid,
    password: password,
    security: NetworkSecurity.WPA,
    joinOnce: true,
  );

  if(connected) {
    print('Wi-Fi connected');
  } else {
    print('Wi-Fi connection failed');
  }
}
// set up the wifi
Future<void> setupWiFi() async {
  final granted = await requestWiFiPermissions();
  if (!granted) {
    print('Wi-Fi permissions denied');
    return;
  }
  await getWiFiInfo();
  await connectToWiFi();
}

class BbCallApp extends StatelessWidget {
  const BbCallApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'BB Call',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
        useMaterial3: true,
      ),
      home: const BbCallHomePage(),
    );
  }
}
// Settings
void settings(){
  final settings = ["Connections", "Notifications", "Privacy"];
  final connections = ["Wi-Fi", "Bluetooth", "MQTT"];
  final notifications = ["Volume", "Vibration", "LED"];
  final vibrations = ["Couple"];
  final couple = vibrations.contains("Couple");

  int i = 1;
  for(final connection in connections) {
      print("$i. $connection");
    i++;
  }

  if(couple == true){
    print("Vibrate on call: true");
  } else {
    print("Vibrate on call: false");
  }

  const ssid = "";
  const password = "";
  print("SSID: $ssid, password length: ${password.length}");
}

class BbCallHomePage extends StatefulWidget {
  const BbCallHomePage({super.key});

  @override
  State<BbCallHomePage> createState() => _BbCallHomePageState();
}

class _BbCallHomePageState extends State<BbCallHomePage> {
  final ConnectionController _connectionController = ConnectionController();
  int _selectedIndex = 0;

  @override
  void dispose() {
    _connectionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final pages = [
      ChatPage(connectionController: _connectionController),
      ConnectionSettingsPage(controller: _connectionController),
    ];

    return Scaffold(
      body: pages[_selectedIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (index) {
          setState(() => _selectedIndex = index);
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.chat_bubble_outline),
            selectedIcon: Icon(Icons.chat_bubble),
            label: 'Chat',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            selectedIcon: Icon(Icons.settings),
            label: 'Settings',
          ),
        ],
      ),
    );
  }
}

class ChatPage extends StatefulWidget {
  const ChatPage({super.key, required this.connectionController});

  final ConnectionController connectionController;

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final TextEditingController _messageController = TextEditingController();
  final CollectionReference<Map<String, dynamic>> _messages = FirebaseFirestore
      .instance
      .collection('messages');

  @override
  void dispose() {
    _messageController.dispose();
    super.dispose();
  }

  Future<void> _sendMessage() async {
    final text = _messageController.text.trim();
    if (text.isEmpty) return;

    await _messages.add({
      'text': text,
      'transport': widget.connectionController.primaryTransport.name,
      'time': FieldValue.serverTimestamp(),
    });
    _messageController.clear();
  }

  
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('BB Call Chat')),
      body: Column(
        children: [
          ConnectionStatusStrip(controller: widget.connectionController),
          Expanded(
            child: StreamBuilder<QuerySnapshot<Map<String, dynamic>>>(
              stream: _messages.orderBy('time', descending: true).snapshots(),
              builder: (context, snapshot) {
                if (snapshot.hasError) {
                  return Center(child: Text('Error: ${snapshot.error}'));
                }

                if (!snapshot.hasData) {
                  return const Center(child: CircularProgressIndicator());
                }

                final docs = snapshot.data!.docs;
                if (docs.isEmpty) {
                  return const Center(child: Text('No messages yet.'));
                }

                return ListView.separated(
                  reverse: true,
                  padding: const EdgeInsets.all(16),
                  itemCount: docs.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final data = docs[index].data();
                    return MessageTile(
                      text: data['text']?.toString() ?? '',
                      transport: data['transport']?.toString() ?? 'unknown',
                    );
                  },
                );
              },
            ),
          ),
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _messageController,
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _sendMessage(),
                      decoration: const InputDecoration(
                        hintText: 'Message',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    tooltip: 'Send',
                    onPressed: _sendMessage,
                    icon: const Icon(Icons.send),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class MessageTile extends StatelessWidget {
  const MessageTile({super.key, required this.text, required this.transport});

  final String text;
  final String transport;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(text),
              const SizedBox(height: 4),
              Text(transport, style: Theme.of(context).textTheme.labelSmall),
            ],
          ),
        ),
      ),
    );
  }
}

class ConnectionStatusStrip extends StatelessWidget {
  const ConnectionStatusStrip({super.key, required this.controller});

  final ConnectionController controller;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        final theme = Theme.of(context);
        return Material(
          color: theme.colorScheme.surfaceContainerHighest,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(
              children: [
                Icon(
                  controller.isConnected ? Icons.link : Icons.link_off,
                  color: controller.isConnected
                      ? Colors.green
                      : theme.colorScheme.onSurfaceVariant,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    controller.statusLabel,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class ConnectionSettingsPage extends StatefulWidget {
  const ConnectionSettingsPage({super.key, required this.controller});

  final ConnectionController controller;

  @override
  State<ConnectionSettingsPage> createState() => _ConnectionSettingsPageState();
}

class _ConnectionSettingsPageState extends State<ConnectionSettingsPage> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  late final TextEditingController _bluetoothNameController;
  late final TextEditingController _bluetoothServiceController;
  late final TextEditingController _wifiSsidController;
  late final TextEditingController _wifiPasswordController;
  late final TextEditingController _deviceSetupUrlController;
  late final TextEditingController _mqttHostController;
  late final TextEditingController _mqttPortController;
  late final TextEditingController _mqttClientIdController;
  late final TextEditingController _mqttUsernameController;
  late final TextEditingController _mqttPasswordController;
  late final TextEditingController _mqttTopicController;

  @override
  void initState() {
    super.initState();
    final settings = widget.controller.settings;
    _bluetoothNameController = TextEditingController(
      text: settings.bluetooth.deviceName,
    );
    _bluetoothServiceController = TextEditingController(
      text: settings.bluetooth.serviceUuid,
    );
    _wifiSsidController = TextEditingController(text: settings.wifi.ssid);
    _wifiPasswordController = TextEditingController(
      text: settings.wifi.password,
    );
    _deviceSetupUrlController = TextEditingController(
      text: settings.wifi.deviceSetupUrl,
    );
    _mqttHostController = TextEditingController(text: settings.mqtt.host);
    _mqttPortController = TextEditingController(
      text: settings.mqtt.port.toString(),
    );
    _mqttClientIdController = TextEditingController(
      text: settings.mqtt.clientId,
    );
    _mqttUsernameController = TextEditingController(
      text: settings.mqtt.username,
    );
    _mqttPasswordController = TextEditingController(
      text: settings.mqtt.password,
    );
    _mqttTopicController = TextEditingController(text: settings.mqtt.topic);
  }

  @override
  void dispose() {
    _bluetoothNameController.dispose();
    _bluetoothServiceController.dispose();
    _wifiSsidController.dispose();
    _wifiPasswordController.dispose();
    _deviceSetupUrlController.dispose();
    _mqttHostController.dispose();
    _mqttPortController.dispose();
    _mqttClientIdController.dispose();
    _mqttUsernameController.dispose();
    _mqttPasswordController.dispose();
    _mqttTopicController.dispose();
    super.dispose();
  }

  void _saveSettings() {
    if (!_formKey.currentState!.validate()) return;

    widget.controller.updateSettings(
      widget.controller.settings.copyWith(
        bluetooth: BluetoothConnectionSettings(
          deviceName: _bluetoothNameController.text.trim(),
          serviceUuid: _bluetoothServiceController.text.trim(),
        ),
        wifi: WifiConnectionSettings(
          ssid: _wifiSsidController.text.trim(),
          password: _wifiPasswordController.text,
          deviceSetupUrl: _deviceSetupUrlController.text.trim(),
        ),
        mqtt: MqttConnectionSettings(
          host: _mqttHostController.text.trim(),
          port: int.parse(_mqttPortController.text.trim()),
          clientId: _mqttClientIdController.text.trim(),
          username: _mqttUsernameController.text.trim(),
          password: _mqttPasswordController.text,
          topic: _mqttTopicController.text.trim(),
        ),
      ),
    );

    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('Settings saved')));
  }

  Future<void> _connect(ConnectionTransport transport) async {
    _saveSettings();
    await widget.controller.connect(transport);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Connection Settings')),
      body: AnimatedBuilder(
        animation: widget.controller,
        builder: (context, _) {
          return Form(
            key: _formKey,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                ConnectionStatusCard(controller: widget.controller),
                const SizedBox(height: 16),
                SettingsSection(
                  title: 'Bluetooth',
                  icon: Icons.bluetooth,
                  children: [
                    TextFormField(
                      controller: _bluetoothNameController,
                      decoration: const InputDecoration(
                        labelText: 'Device name',
                        border: OutlineInputBorder(),
                      ),
                      validator: _required,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _bluetoothServiceController,
                      decoration: const InputDecoration(
                        labelText: 'Service UUID',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 12),
                    ConnectionButtonRow(
                      isBusy: widget.controller.isBusy,
                      onConnect: () => _connect(ConnectionTransport.bluetooth),
                      onDisconnect: widget.controller.disconnect,
                    ),
                  ],
                ),
                SettingsSection(
                  title: 'WiFi',
                  icon: Icons.wifi,
                  children: [
                    TextFormField(
                      controller: _wifiSsidController,
                      decoration: const InputDecoration(
                        labelText: 'SSID',
                        border: OutlineInputBorder(),
                      ),
                      validator: _required,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _wifiPasswordController,
                      decoration: const InputDecoration(
                        labelText: 'Password',
                        border: OutlineInputBorder(),
                      ),
                      obscureText: true,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _deviceSetupUrlController,
                      decoration: const InputDecoration(
                        labelText: 'Device setup URL',
                        border: OutlineInputBorder(),
                      ),
                      validator: _urlLike,
                    ),
                    const SizedBox(height: 12),
                    ConnectionButtonRow(
                      isBusy: widget.controller.isBusy,
                      onConnect: () => _connect(ConnectionTransport.wifi),
                      onDisconnect: widget.controller.disconnect,
                    ),
                  ],
                ),
                SettingsSection(
                  title: 'MQTT',
                  icon: Icons.hub_outlined,
                  children: [
                    TextFormField(
                      controller: _mqttHostController,
                      decoration: const InputDecoration(
                        labelText: 'Broker host',
                        border: OutlineInputBorder(),
                      ),
                      validator: _required,
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: TextFormField(
                            controller: _mqttPortController,
                            decoration: const InputDecoration(
                              labelText: 'Port',
                              border: OutlineInputBorder(),
                            ),
                            keyboardType: TextInputType.number,
                            validator: _port,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          flex: 2,
                          child: TextFormField(
                            controller: _mqttClientIdController,
                            decoration: const InputDecoration(
                              labelText: 'Client ID',
                              border: OutlineInputBorder(),
                            ),
                            validator: _required,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _mqttTopicController,
                      decoration: const InputDecoration(
                        labelText: 'Topic',
                        border: OutlineInputBorder(),
                      ),
                      validator: _required,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _mqttUsernameController,
                      decoration: const InputDecoration(
                        labelText: 'Username',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _mqttPasswordController,
                      decoration: const InputDecoration(
                        labelText: 'Password',
                        border: OutlineInputBorder(),
                      ),
                      obscureText: true,
                    ),
                    const SizedBox(height: 12),
                    ConnectionButtonRow(
                      isBusy: widget.controller.isBusy,
                      onConnect: () => _connect(ConnectionTransport.mqtt),
                      onDisconnect: widget.controller.disconnect,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                FilledButton.icon(
                  onPressed: _saveSettings,
                  icon: const Icon(Icons.save),
                  label: const Text('Save settings'),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  String? _required(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Required';
    }
    return null;
  }

  String? _port(String? value) {
    final port = int.tryParse(value?.trim() ?? '');
    if (port == null || port <= 0 || port > 65535) {
      return '1-65535';
    }
    return null;
  }

  String? _urlLike(String? value) {
    final uri = Uri.tryParse(value?.trim() ?? '');
    if (uri == null || !uri.hasScheme || uri.host.isEmpty) {
      return 'Enter a valid URL';
    }
    return null;
  }
}

class ConnectionStatusCard extends StatelessWidget {
  const ConnectionStatusCard({super.key, required this.controller});

  final ConnectionController controller;

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            CircleAvatar(
              backgroundColor: controller.isConnected
                  ? Colors.green
                  : Theme.of(context).colorScheme.surfaceContainerHighest,
              child: Icon(
                controller.isConnected ? Icons.check : Icons.link_off,
                color: controller.isConnected
                    ? Colors.white
                    : Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    controller.statusLabel,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 4),
                  Text(controller.detailLabel),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class SettingsSection extends StatelessWidget {
  const SettingsSection({
    super.key,
    required this.title,
    required this.icon,
    required this.children,
  });

  final String title;
  final IconData icon;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon),
                const SizedBox(width: 8),
                Text(title, style: Theme.of(context).textTheme.titleMedium),
              ],
            ),
            const SizedBox(height: 16),
            ...children,
          ],
        ),
      ),
    );
  }
}

class ConnectionButtonRow extends StatelessWidget {
  const ConnectionButtonRow({
    super.key,
    required this.isBusy,
    required this.onConnect,
    required this.onDisconnect,
  });

  final bool isBusy;
  final VoidCallback onConnect;
  final VoidCallback onDisconnect;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: FilledButton.icon(
            onPressed: isBusy ? null : onConnect,
            icon: isBusy
                ? const SizedBox.square(
                    dimension: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.power),
            label: const Text('Connect'),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: OutlinedButton.icon(
            onPressed: isBusy ? null : onDisconnect,
            icon: const Icon(Icons.power_off),
            label: const Text('Disconnect'),
          ),
        ),
      ],
    );
  }
}

enum ConnectionTransport { bluetooth, wifi, mqtt }

enum ConnectionStateStatus { disconnected, connecting, connected, failed }

class ConnectionController extends ChangeNotifier {
  ConnectionSettings settings = ConnectionSettings.defaults();
  ConnectionTransport primaryTransport = ConnectionTransport.wifi;
  ConnectionStateStatus status = ConnectionStateStatus.disconnected;
  String? lastError;

  bool get isBusy => status == ConnectionStateStatus.connecting;

  bool get isConnected => status == ConnectionStateStatus.connected;

  String get statusLabel {
    switch (status) {
      case ConnectionStateStatus.disconnected:
        return 'Disconnected';
      case ConnectionStateStatus.connecting:
        return 'Connecting to ${primaryTransport.name}';
      case ConnectionStateStatus.connected:
        return 'Connected by ${primaryTransport.name}';
      case ConnectionStateStatus.failed:
        return 'Connection failed';
    }
  }

  String get detailLabel {
    if (lastError != null) return lastError!;

    switch (primaryTransport) {
      case ConnectionTransport.bluetooth:
        return settings.bluetooth.deviceName;
      case ConnectionTransport.wifi:
        return '${settings.wifi.ssid} -> ${settings.wifi.deviceSetupUrl}';
      case ConnectionTransport.mqtt:
        return '${settings.mqtt.host}:${settings.mqtt.port} / ${settings.mqtt.topic}';
    }
  }

  void updateSettings(ConnectionSettings value) {
    settings = value;
    notifyListeners();
  }

  Future<void> connect(ConnectionTransport transport) async {
    primaryTransport = transport;
    status = ConnectionStateStatus.connecting;
    lastError = null;
    notifyListeners();

    try {
      await Future<void>.delayed(const Duration(milliseconds: 600));
      _validateSelectedSettings(transport);
      status = ConnectionStateStatus.connected;
    } on Object catch (error) {
      status = ConnectionStateStatus.failed;
      lastError = error.toString();
    }

    notifyListeners();
  }

  void disconnect() {
    status = ConnectionStateStatus.disconnected;
    lastError = null;
    notifyListeners();
  }

  void _validateSelectedSettings(ConnectionTransport transport) {
    switch (transport) {
      case ConnectionTransport.bluetooth:
        if (settings.bluetooth.deviceName.isEmpty) {
          throw 'Bluetooth device name is required.';
        }
      case ConnectionTransport.wifi:
        if (settings.wifi.ssid.isEmpty) {
          throw 'WiFi SSID is required.';
        }
        final uri = Uri.tryParse(settings.wifi.deviceSetupUrl);
        if (uri == null || !uri.hasScheme || uri.host.isEmpty) {
          throw 'Device setup URL is invalid.';
        }
      case ConnectionTransport.mqtt:
        if (settings.mqtt.host.isEmpty || settings.mqtt.topic.isEmpty) {
          throw 'MQTT host and topic are required.';
        }
    }
  }
}

class ConnectionSettings {
  const ConnectionSettings({
    required this.bluetooth,
    required this.wifi,
    required this.mqtt,
  });

  final BluetoothConnectionSettings bluetooth;
  final WifiConnectionSettings wifi;
  final MqttConnectionSettings mqtt;

  factory ConnectionSettings.defaults() {
    return const ConnectionSettings(
      bluetooth: BluetoothConnectionSettings(
        deviceName: 'BB Call',
        serviceUuid: '',
      ),
      wifi: WifiConnectionSettings(
        ssid: 'ESP32_WiFi_Setup',
        password: '12345678',
        deviceSetupUrl: 'http://192.168.4.1/setup',
      ),
      mqtt: MqttConnectionSettings(
        host: 'broker.hivemq.com',
        port: 1883,
        clientId: 'bbcall-mobile',
        username: '',
        password: '',
        topic: 'bbcall/messages',
      ),
    );
  }

  ConnectionSettings copyWith({
    BluetoothConnectionSettings? bluetooth,
    WifiConnectionSettings? wifi,
    MqttConnectionSettings? mqtt,
  }) {
    return ConnectionSettings(
      bluetooth: bluetooth ?? this.bluetooth,
      wifi: wifi ?? this.wifi,
      mqtt: mqtt ?? this.mqtt,
    );
  }
}

class BluetoothConnectionSettings {
  const BluetoothConnectionSettings({
    required this.deviceName,
    required this.serviceUuid,
  });

  final String deviceName;
  final String serviceUuid;
}

class WifiConnectionSettings {
  const WifiConnectionSettings({
    required this.ssid,
    required this.password,
    required this.deviceSetupUrl,
  });

  final String ssid;
  final String password;
  final String deviceSetupUrl;
}

class MqttConnectionSettings {
  const MqttConnectionSettings({
    required this.host,
    required this.port,
    required this.clientId,
    required this.username,
    required this.password,
    required this.topic,
  });

  final String host;
  final int port;
  final String clientId;
  final String username;
  final String password;
  final String topic;
}
