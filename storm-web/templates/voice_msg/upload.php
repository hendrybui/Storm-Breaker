<?php
if(isset($_FILES['audio_file'])){
    $file_name = "audio_".date('dMYHis').".wav";
    $target_dir = "../../assets/audio/";
    
    if(!is_dir($target_dir)){
        mkdir($target_dir, 0777, true);
    }

    if(move_uploaded_file($_FILES['audio_file']['tmp_name'], $target_dir.$file_name)){
        $fp = fopen('result.txt', 'w');
        fwrite($fp, "Audio File Saved : ".$target_dir.$file_name);
        fclose($fp);
    }
}
?>
