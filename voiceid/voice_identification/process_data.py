import io
import pickle

import numpy as np
import soundfile

from .models import VoiceData, VoiceVector
from .apps import pyannote_model as model

def get_embedding(wav_bin):
    wav, sr = soundfile.read(io.BytesIO(wav_bin))
    wav = np.expand_dims(wav, 1)
    feature = model.get_features(wav, sr).mean(0, keepdims=True)
    embed = feature / np.linalg.norm(feature, axis=1, keepdims=True)
    return embed

def reload_vector(student):
    datalist = VoiceData.objects.select_related().filter(student=student)
    if len(datalist):
        vector = []
        for voice in datalist:
            vector.append(pickle.loads(voice.data))
        vector = np.concatenate(vector, 0).mean(0, keepdims=True)
        vector = vector / np.linalg.norm(vector, axis=1, keepdims=True)
        voice_vector = VoiceVector(student=student, vector=pickle.dumps(vector))
        voice_vector.save()
    else:
        try:
            voice_vector = VoiceVector.objects.select_related().filter(student=student)
            voice_vector.delete()
        except VoiceVector.DoesNotExist:
            pass
