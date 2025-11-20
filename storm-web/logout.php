<?php
session_start();
session_unset();
session_destroy();

// Also clear the cookie
if (isset($_COOKIE['logindata'])) {
    unset($_COOKIE['logindata']); 
    setcookie('logindata', '', -1, '/'); 
}

header("location: login.php");
exit;
?>
