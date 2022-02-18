from django.core.files.uploadedfile import InMemoryUploadedFile
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.http import HttpResponse, HttpRequest
from django.http.response import JsonResponse

import pickle

from .models import Student, VoiceData, VoiceVector
from .process_data import get_embedding, reload_vector

THRESHOLD = 0.70

@ensure_csrf_cookie
def record(request:HttpRequest):
    return render(request, 'voice_identification/recorder.html')

def upload(request:HttpRequest):
    file = request.FILES['audio']
    embed, wav_file = get_embedding(file.read(), return_file=True)
    wav_file = InMemoryUploadedFile(wav_file, None, file.name, file.content_type, wav_file.tell(), None)
    try:
        student = Student.objects.get(name=request.POST['name'])
    except Student.DoesNotExist:
        student = Student(name=request.POST['name'])
        student.save()
    voice_data = VoiceData(student=student, audio=wav_file, data=pickle.dumps(embed))
    voice_data.save()
    reload_vector(student)
    return HttpResponse('%sの音声を登録しました。'%(request.POST['name']))

def delete(request:HttpRequest):
    n = 0
    try:
        student = Student.objects.get(name=request.POST['name'])
        voice_data = VoiceData.objects.select_related().filter(student=student)
        n = len(voice_data)
        voice_data.delete()
        reload_vector(student)
    except Student.DoesNotExist:
        pass
    return HttpResponse('%sの音声データを削除しました。(%d件)'%(request.POST['name'], n))

@ensure_csrf_cookie
def analyzer(request:HttpRequest):
    return render(request, 'voice_identification/analyzer.html')

@csrf_exempt
def analyze(request:HttpRequest):
    file = request.FILES['audio']
    embed = get_embedding(file.read(), normalize=True)
    scores = []
    for vv in VoiceVector.objects.all().order_by('student__name'):
        v = pickle.loads(vv.vector)
        scores.append((
            vv.student.name, float((embed*v).sum())
        ))
    max_score = max(scores, key=lambda x : x[1])
    if max_score[1] > THRESHOLD:
        result = max_score[0]
    else:
        result = None
    return JsonResponse({
        'result':result ,
        'max_id':max_score[0],
        'max_score':max_score[1],
        'scores':dict(scores)
        })

def test_analyze(request:HttpRequest):
    return render(request, 'voice_identification/test_analyze.html')