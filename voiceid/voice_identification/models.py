from django.db import models

import datetime

# Create your models here.
class Student(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self) -> str:
        return self.name

def get_path(obj, filename):
    ext = filename.split('.')[-1]
    f_name = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    f_name += '.%s'%ext
    return f'voice/{obj.student.name}/{f_name}'

class VoiceData(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    audio = models.FileField(upload_to=get_path, null=True)
    data = models.BinaryField()

    def __str__(self) -> str:
        return self.student.name

class VoiceVector(models.Model):
    student = models.OneToOneField(Student, primary_key=True, on_delete=models.CASCADE)
    vector = models.BinaryField()

    def __str__(self) -> str:
        return self.student.name