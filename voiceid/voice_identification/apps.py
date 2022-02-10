from django.apps import AppConfig

import torch

pyannote_model = None
vectors = None
names = []

class VoiceIdentificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'voice_identification'

    def ready(self):
        global pyannote_model
        pyannote_model = torch.hub.load('static/models/pyannote-audio-master', 'emb', source='local')
