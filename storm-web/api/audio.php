<?php
header('Content-Type: application/json');

// Get all audio files from the assets/audio directory
$audioDir = '../assets/audio/';
$audioFiles = [];

if (is_dir($audioDir)) {
    $files = scandir($audioDir);
    
    foreach ($files as $file) {
        if ($file !== '.' && $file !== '..') {
            $filePath = $audioDir . $file;
            
            // Check if it's an audio file
            $ext = strtolower(pathinfo($file, PATHINFO_EXTENSION));
            if (in_array($ext, ['wav', 'mp3', 'ogg', 'webm', 'm4a'])) {
                $audioFiles[] = [
                    'name' => $file,
                    'url' => '/assets/audio/' . $file,
                    'timestamp' => filemtime($filePath),
                    'size' => filesize($filePath)
                ];
            }
        }
    }
    
    // Sort by timestamp (newest first)
    usort($audioFiles, function($a, $b) {
        return $b['timestamp'] - $a['timestamp'];
    });
}

echo json_encode([
    'success' => true,
    'audio' => $audioFiles,
    'count' => count($audioFiles)
]);
