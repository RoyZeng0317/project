<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');

$host = 'localhost';
$user = 'root';
$password = '';
$database = 'nfu_school';

$conn = new mysqli($host, $user, $password, $database);
$conn->set_charset('utf8mb4');

if ($conn->connect_error) {
    die(json_encode(['error' => '資料庫連線失敗: ' . $conn->connect_error]));
}

$sql = "SELECT * FROM parking_lots ORDER BY id";
$result = $conn->query($sql);

if (!$result) {
    die(json_encode(['error' => '查詢失敗: ' . $conn->error]));
}

$data = [];
while ($row = $result->fetch_assoc()) {
    $data[] = $row;
}

echo json_encode($data);
$conn->close();
?>
