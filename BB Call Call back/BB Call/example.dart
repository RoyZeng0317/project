void main(){
  runApp(MyApp());
}

class MyApp extends StatelessWidget{
  @override
  Widget build(BuildContext context){
    return MaterialApp(
      title: 'My First App',
      home: HomePage(),
    );
  }
}

class HomePage extends StatelessWidget{
  @override
  Widget build(BuildContext context){
    return Scaffold(
      appBar: AppBar(
        title: Text("首頁"),
      ),
      body: Center(
        child: Text("Hello Flutter"),
      ),
    );
  }
}