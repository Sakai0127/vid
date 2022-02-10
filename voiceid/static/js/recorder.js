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

function record(rec_button){
    navigator.mediaDevices.getUserMedia({audio:true}).then(
        function(stream){
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
                data.append('audio', exportWAV(chunks, sampleRate), f_name);
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
                scriptProcessor.disconnect();
                rec_button.checked = false;
                console.log('stop');
                send();
            }
            rec_button.onchange = function(){
                if(rec_button.checked){
                    chunks.splice(0);
                    scriptProcessor.connect(context.destination);
                    setTimeout(onstop, record_ms);
                } else {
                    onstop();
                }
            };

            document.getElementById("RET").onclick=send;

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
    var start = document.getElementById('rokuon2');
    var stop = document.getElementById('stop');
    record(start);
}