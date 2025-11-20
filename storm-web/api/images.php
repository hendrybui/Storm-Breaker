<?php
header('Content-Type: application/json');

// Get all images from the images directory
$imagesDir = '../images/';
$images = [];

if (is_dir($imagesDir)) {
    $files = scandir($imagesDir);
    
    foreach ($files as $file) {
        if ($file !== '.' && $file !== '..') {
            $filePath = $imagesDir . $file;
            
            // Check if it's an image file
            $ext = strtolower(pathinfo($file, PATHINFO_EXTENSION));
            if (in_array($ext, ['jpg', 'jpeg', 'png', 'gif', 'webp'])) {
                $images[] = [
                    'name' => $file,
                    'url' => '/images/' . $file,
                    'timestamp' => filemtime($filePath),
                    'size' => filesize($filePath)
                ];
            }
        }
    }
    
    // Sort by timestamp (newest first)
    usort($images, function($a, $b) {
        return $b['timestamp'] - $a['timestamp'];
    });
}

echo json_encode([
    'success' => true,
    'images' => $images,
    'count' => count($images)
]);
