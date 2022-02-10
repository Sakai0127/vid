from django.contrib import admin
from django.utils.safestring import mark_safe

import pickle
import numpy as np

from .models import Student, VoiceData, VoiceVector
from .process_data import get_embedding, reload_vector

# Register your models here.
class VoiceDataAdmin(admin.ModelAdmin):
    fields = ('student', 'wave', 'audio', 'vector')
    readonly_fields = ('wave', 'vector')
    exclude = ('wave', 'vector')
    def wave(self, obj):
        return mark_safe(
            '''
            <div id="wave"></div>
            <a id="btnStartPause">start/pause</a>
            <script>
                var wavesurfer = WaveSurfer.create({
                    container: '#wave',
                    waveColor: 'violet',
                    progressColor: 'blue'
                });
                wavesurfer.load("%s");
                var button = document.getElementById("btnStartPause");
                play = function () {
                    wavesurfer.playPause();
                }
                button.href = "javascript:play();"
            </script>
            '''%obj.audio.url
        )

    def vector(self, obj):
        v = obj.data
        try:
            v = pickle.loads(v)[0]
            html = '<div style="display: flex;flex-wrap: wrap;">%s</div>'
            format = '<span style="width:3rem;padding:0 1px;text-align: center;">%.04f</span>'*512
            html = html%(format%(tuple(v)))
            return mark_safe(html)
        except:
            return mark_safe('-')

    def save_model(self, request, obj:VoiceData, form, change):
        file = request.FILES['audio']
        print(file, type(file))
        embed = get_embedding(file.read())
        obj.data=pickle.dumps(embed)
        super().save_model(request, obj, form, change)
        reload_vector(obj.student)
    
    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        reload_vector(obj.student)
    
    def delete_queryset(self, request, queryset):
        super().delete_queryset(request, queryset)
        for obj in queryset:
            reload_vector(obj.student)

class VoiceVectorAdmin(admin.ModelAdmin):
    fields = ('student', 'student_vector')
    readonly_fields = ('student', 'student_vector')

    def has_add_permission(self, request):
        return False

    def student_vector(self, obj):
        v = obj.vector
        v = pickle.loads(v)[0]
        html = '<div style="display: flex;flex-wrap: wrap;">%s</div>'
        format = '<span style="width:3rem;padding:0 1px;text-align: center;">%.04f</span>'*512
        html = html%(format%(tuple(v)))
        return mark_safe(html)

admin.site.register(Student)
admin.site.register(VoiceData, VoiceDataAdmin)
admin.site.register(VoiceVector, VoiceVectorAdmin)