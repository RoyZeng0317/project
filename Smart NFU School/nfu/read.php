<?php

$conn = new mysqli(
    "localhost",
    "root",
    "password",
    "database_name"
);

$data = [];

while($row = $result->fetch_assoc()){
    $data[] = $row;
}

echo json_encode($data);
?>