import io
import pickle

import librosa
import numpy as np
import soundfile

from .models import VoiceData, VoiceVector
from .apps import pyannote_model as model

def get_embedding(wav_bin, return_file=False):
    wav, sr = soundfile.read(io.BytesIO(wav_bin))
    wav, _ = librosa.effects.trim(wav)
    wav = np.expand_dims(wav, 1)
    embed = model.get_features(wav, sr).mean(0, keepdims=True)
    # embed = embed / np.linalg.norm(embed, axis=1, keepdims=True)
    if return_file:
        wav_file = io.BytesIO()
        soundfile.write(wav_file, wav[:,0], sr, subtype=soundfile.default_subtype('WAV'), format='WAV')
        return embed, wav_file
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
