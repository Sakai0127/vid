import {exportWAV} from './export_wav.js';
import {getCookie, csrfSafeMethod} from './django_csrf.js';

let csrf_token;
let record_ms = 3000;
let sampleRate = 16000;
let bufferSize = 1024;
let context;
let source;
let scriptProcessor;
let chunks = [];

function record(){
    navigator.mediaDevices.getUserMedia({audio:true}).then(
        function(stream){
            var sent = false;
            let rec_button = document.getElementById('rokuon2');
            let del_button = document.getElementById('delete-btn');
            function onAudioProcess(e) {  
                var input = e.inputBuffer.getChannelData(0);
                var bufferData = new Float32Array(bufferSize);
                for (var i = 0; i < bufferSize; i++) {
                    bufferData.set(input);
                }
                chunks.push(bufferData);
            };

            function send() {
                csrf_token = getCookie("csrftoken");
                var data = new FormData();
                var f_name = new Date().toLocaleString('js-JP').replaceAll(/:|\/|\s/g, '_') + '.wav';
                var audio_data = exportWAV(chunks, sampleRate);
                document.getElementsByTagName('audio')[0].src = URL.createObjectURL(audio_data);
                data.append('audio', audio_data, f_name);
                data.append('name', document.getElementById('num').value);
                $.ajax({
                    type: "POST",
                    url: "upload",
                    data: data,
                    processData: false,
                    contentType: false,
                    beforeSend: function(xhr, settings) {
                        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                            xhr.setRequestHeader("X-CSRFToken", csrf_token);
                        }
                    },
                    success: function (response) {
                        console.log(response);
                    }
                });
            };
            function onstop() {
                if(sent == false){
                    scriptProcessor.disconnect();
                    rec_button.checked = false;
                    console.log('stop');
                    console.log(chunks.length)
                    if(chunks.length == 0) return;
                    sent = true;
                    send();
                }
            }
            rec_button.onchange = function(){
                if(document.getElementById('num').value.length != 9){
                    alert('学籍番号を入力してください。');
                    rec_button.checked = false;
                    return;
                };
                if(rec_button.checked){
                    chunks.splice(0);
                    sent = false;
                    scriptProcessor.connect(context.destination);
                    setTimeout(onstop, record_ms);
                } else {
                    onstop();
                };
            };

            del_button.onclick = function () {
                if(document.getElementById('num').value.length != 9){
                    alert('学籍番号を入力してください。');
                    rec_button.checked = false;
                    return;
                };
                csrf_token = getCookie("csrftoken");
                var data = new FormData();
                data.append('name', document.getElementById('num').value);
                $.ajax({
                    type: "POST",
                    url: "delete",
                    data: data,
                    processData: false,
                    contentType: false,
                    beforeSend: function(xhr, settings) {
                        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                            xhr.setRequestHeader("X-CSRFToken", csrf_token);
                        }
                    },
                    success: function (response) {
                        console.log(response);
                    }
                });
            };

            context = new AudioContext({sampleRate:sampleRate});
            scriptProcessor = context.createScriptProcessor(bufferSize, 1, 1);
            source = context.createMediaStreamSource(stream);
            scriptProcessor.onaudioprocess = onAudioProcess;
            source.connect(scriptProcessor);
        },
        function(){
            console.log('Error');
        }
    )
}

window.onload = function () {
    record();
}