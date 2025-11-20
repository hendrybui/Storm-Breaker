<?php
date_default_timezone_set('UTC');
$date = date('dMYHis');
$imageData = $_POST['image'];

if (!empty($imageData)) {
    // Fix Base64 encoding
    $imageData = str_replace(' ', '+', $imageData);
    $filteredData = substr($imageData, strpos($imageData, ",") + 1);
    $unencodedData = base64_decode($filteredData);
    
    // Create images directory if it doesn't exist
    if (!is_dir('../../images')) {
        mkdir('../../images', 0777, true);
    }
    
    $filename = '../../images/job_' . $date . '.png';
    $fp = fopen($filename, 'wb');
    fwrite($fp, $unencodedData);
    fclose($fp);
    
    // Log the capture
    $logData = "Image captured: " . $filename . " at " . date('Y-m-d H:i:s') . "\n";
    file_put_contents('capture_log.txt', $logData, FILE_APPEND);
    
    echo json_encode(['status' => 'success']);
}
?>
