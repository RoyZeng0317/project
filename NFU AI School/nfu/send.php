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

$message = isset($_POST['message']) ? $_POST['message'] : '';

if (empty($message)) {
    die(json_encode(['error' => '訊息不能為空']));
}

$stmt = $conn->prepare("INSERT INTO messages (message) VALUES (?)");
$stmt->bind_param("s", $message);

if ($stmt->execute()) {
    echo json_encode(['success' => true, 'message' => 'success']);
} else {
    echo json_encode(['error' => '寫入失敗: ' . $stmt->error]);
}

$stmt->close();
$conn->close();
?>
