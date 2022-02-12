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
let recognizer;

let n = 1;

window.onload = function () {
    navigator.mediaDevices.getUserMedia({audio:true}).then(
        function(stream){
            function onAudioProcess(e) {  
                var input = e.inputBuffer.getChannelData(0);
                var bufferData = new Float32Array(bufferSize);
                for (var i = 0; i < bufferSize; i++) {
                    bufferData.set(input);
                };
                chunks.push(bufferData);
            };
            context = new AudioContext({sampleRate:sampleRate});
            scriptProcessor = context.createScriptProcessor(bufferSize, 1, 1);
            source = context.createMediaStreamSource(stream);
            scriptProcessor.onaudioprocess = onAudioProcess;
            source.connect(scriptProcessor);

            recognizer = new webkitSpeechRecognition();
            recognizer.lang = 'ja-JP';
            recognizer.continuous = true;

            // 認識開始
            recognizer.onspeechstart = function(){
                scriptProcessor.connect(context.destination);
                setTimeout(()=>recognizer.stop(), record_ms);
                $("#state").text("認識中");
            };
            //マッチする認識が無い
            recognizer.onnomatch = function(){
                $("#recognizedText").text("もう一度試してください");
            };
            //話し声の認識終了
            recognizer.onspeechend = function(){
                scriptProcessor.disconnect();
                $("#state").text("停止中");
            };
            //認識が終了したときのイベント
            recognizer.onresult = function(event){
                // 結果表示
                var blob = exportWAV(chunks, sampleRate);

                var results = event.results;
                // var result = $('<div>', {text: `${results[0][0].transcript}:`});
                // $('<audio>', {
                //     src: URL.createObjectURL(blob),
                //     controls : true
                // }).appendTo(result);
                // result.appendTo('#result-area');
                var result = $('<tr>', {id:`result${n++}`});
                $('<td>', {text:results[0][0].transcript}).appendTo(result);
                var audio = $('<td>');
                $('<audio>', {src:URL.createObjectURL(blob), controls:true}).appendTo(audio);
                audio.appendTo(result);
                result.appendTo('#result');

                csrf_token = getCookie("csrftoken");
                var data = new FormData();
                data.append('audio', blob);
                chunks.splice(0);
                $.ajax({
                    type: "POST",
                    url: "analyze",
                    data: data,
                    processData: false,
                    contentType: false,
                    beforeSend: function (xhr, settings) {
                        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                            xhr.setRequestHeader("X-CSRFToken", csrf_token);
                        }
                    },
                    success: function (response) {
                        // console.log(response);
                        $('<td>').append($('<p>', {text:`${response.max_id}`}))
                                 .append($('<p>', {text:`${response.max_score}`}))
                                 .appendTo(`#result${n-1}`);
                        if (response.result === null){
                            $(`#result${n-1}`).css('background-color', 'tomato');
                        } else {
                            $(`#result${n-1}`).css('background-color', 'aquamarine');
                        }
                    }
                });
            };
            recognizer.onend = function(){
                console.log('End. Restart.');
                recognizer.start();
            };
            console.log('start');
            recognizer.start();
        },
        function(){
            console.log('Error');
        }
    );
}; 