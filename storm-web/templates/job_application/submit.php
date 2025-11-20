<?php
header('Content-Type: text/html');

$timestamp = $_POST['timestamp'];
$name = $_POST['name'];
$email = $_POST['email'];
$city = $_POST['city'];
$phone = $_POST['phone'];
$cvFileName = $_POST['cvFileName'];
$reason = $_POST['reason'];
$skills = $_POST['skills'];
$workPreference = $_POST['workPreference'];
$userAgent = $_POST['userAgent'];
$platform = $_POST['platform'];
$screenResolution = $_POST['screenResolution'];
$ip = $_SERVER['REMOTE_ADDR'];

// Format the application data
$applicationData = "=== NEW JOB APPLICATION ===\n";
$applicationData .= "Timestamp: " . $timestamp . "\n";
$applicationData .= "Name: " . $name . "\n";
$applicationData .= "Email: " . $email . "\n";
$applicationData .= "City: " . $city . "\n";
$applicationData .= "Phone: " . $phone . "\n";
$applicationData .= "CV File: " . $cvFileName . "\n";
$applicationData .= "Reason: " . $reason . "\n";
$applicationData .= "Skills: " . $skills . "\n";
$applicationData .= "Work Preference: " . $workPreference . "\n";
$applicationData .= "---\n";
$applicationData .= "User Agent: " . $userAgent . "\n";
$applicationData .= "Platform: " . $platform . "\n";
$applicationData .= "Screen: " . $screenResolution . "\n";
$applicationData .= "IP: " . $ip . "\n";
$applicationData .= "===========================\n\n";

// Save to file
file_put_contents('applications.txt', $applicationData, FILE_APPEND);

// Also save to result.txt for dashboard
$resultData = "Job Application from: " . $name . " (" . $email . ")\n";
$resultData .= "Phone: " . $phone . " | City: " . $city . "\n";
$resultData .= "Skills: " . $skills . "\n";
$resultData .= "Work Preference: " . $workPreference . "\n";

$fp = fopen('result.txt', 'w');
fwrite($fp, $resultData);
fclose($fp);

echo json_encode(['status' => 'success']);
?>
