<?php
include "db.php";

$sql = "SELECT * FROM messages ORDER BY id DESC LIMIT 10";
$result = $conn->query($sql);

$data = [];

while($row = $result->fetch_assoc()){
    $datap[] = $row;
}

echo json_encode($data);
?>