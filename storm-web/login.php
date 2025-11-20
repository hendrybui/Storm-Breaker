<?php
session_start();
include "config.php";
include "./assets/components/login-arc.php";

if(isset($_COOKIE['logindata']) && $_COOKIE['logindata'] == $key['token'] && $key['expired'] == "no"){
    $_SESSION['IAm-logined'] = 'yes';
    header("location: panel.php");
}
elseif(isset($_SESSION['IAm-logined'])){
    header('location: panel.php');
    exit;
}
else{ 
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Storm Breaker | Login</title>
    <link rel="stylesheet" href="./assets/css/modern-theme.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <!-- Animated Background -->
    <div class="bg-shape shape-1"></div>
    <div class="bg-shape shape-2"></div>

    <div class="login-wrapper">
        <div class="login-card">
            <div class="login-header">
                <h2>Welcome Back</h2>
                <p>Enter your credentials to access the control panel.</p>
            </div>
            
            <form action="" method="POST">       
                <div class="form-group">
                    <input type="text" class="form-control" name="username" placeholder="Username" required autofocus />
                </div>
                <div class="form-group">
                    <input type="password" class="form-control" name="password" placeholder="Password" required />     
                </div>
                <button class="btn-login" type="submit">Sign In</button> 

                <?php
                if($_SERVER['REQUEST_METHOD'] == 'POST'){
                    if(isset($_POST['username']) && isset($_POST['password'])){
                        $username = $_POST['username'];
                        $password = $_POST['password'];

                        if(isset($CONFIG[$username]) && $CONFIG[$username]['password'] == $password){
                            $_SESSION['IAm-logined'] = $username;
                            echo '<script>location.href="panel.php"</script>';
                        } else {
                            echo '<div class="error-msg">Invalid username or password</div>';
                        }
                    }
                }
                ?>
            </form>
        </div>
    </div>
</body>
</html>
<?php
}
?>