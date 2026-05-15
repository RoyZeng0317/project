<?php

$conn = new mysqli(
    "localhost",
    "root",
    "password",
    "database_name"
);

$message = $_POST['message'];

$sql = "INSERT INTO messages(message)"
VALUES('$message');

if($conn->query($sql)){
    echo "success";
}else{
    echo "error";
}
?>