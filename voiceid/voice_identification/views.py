from django.core.files.uploadedfile import InMemoryUploadedFile
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponse, HttpRequest
from django.http.response import JsonResponse

import pickle

from .models import Student, VoiceData, VoiceVector
from .process_data import get_embedding, reload_vector

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
    return HttpResponse('音声を登録しました。')

def delete(request:HttpRequest):
    try:
        student = Student.objects.get(name=request.POST['name'])
        VoiceData.objects.select_related().filter(student=student).delete()
    except Student.DoesNotExist:
        pass
    return HttpResponse('音声データを削除しました。')

@ensure_csrf_cookie
def analyzer(request:HttpRequest):
    return render(request, 'voice_identification/analyzer.html')

def analyze(request:HttpRequest):
    file = request.FILES['audio']
    embed = get_embedding(file.read())
    results = []
    for vv in VoiceVector.objects.all().order_by('student__name'):
        v = pickle.loads(vv.vector)
        results.append((
            vv.student.name, float((embed*v).sum())
        ))
    return JsonResponse({'result':dict(results)})

def test_analyze(request:HttpRequest):
    return render(request, 'voice_identification/test_analyze.html')