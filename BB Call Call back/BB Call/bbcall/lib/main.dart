import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:firebase_core/firebase_core.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'firebase_options.dart';

Future<void> getMessages() async {
  final response = await http.get(Uri.parse("https://ip/api.php"));

  if (response.statusCode == 200) {
    var data = jsonDecode(response.body);
    print(data);
  }
}

Future<void> sendMessage(String msg) async {
  await http.post(Uri.parse("https://ip/send.php"), body: {"message": msg});
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(title: 'My First App', home: HomePage());
  }
}

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final meessages = FirebaseFirestore.instance.collection('messages');

    return Scaffold(
      appBar: AppBar(title: const Text("BB Call Chat")),
      body: Column(
        children: [
          // messages
          Expanded(
            child: StreamBuilder(
              stream: meessages.orderBy('time').snapshots(),
              builder: (context, snapshot) {
                if (!snapshot.hasData) {
                  return const Center(child: CircularProgressIndicator());
                }

                final docs = snapshot.data!.docs;

                return ListView(
                  children: docs.map((doc) {
                    return ListTile(title: Text(doc['text']));
                  }).toList(),
                );
              },
            ),
          ),
          TextField(
            onSubmitted: (text) {
              meessages.add({
                'text': text,
                'time': FieldValue.serverTimestamp(),
              });
            },
            decoration: const InputDecoration(
              hintText: "Please enter the messages...",
            ),
          ),
        ],
      ),
    );
  }
}
