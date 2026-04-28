<?php
$msg = $_POST['message'];

$sql = "INSERT INTO messages(message) VALUES ('$msg')";
$conn->query($sql);

echo "ok";
?>