from array import array
import collections
import io
import pickle
import wave

import librosa
import numpy as np
import soundfile
import webrtcvad

from .models import VoiceData, VoiceVector
from .apps import pyannote_model as model

class Frame(object):
    """Represents a "frame" of audio data."""
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration


def frame_generator(frame_duration_ms, audio, sample_rate):
    """Generates audio frames from PCM audio data.
    Takes the desired frame duration in milliseconds, the PCM data, and
    the sample rate.
    Yields Frames of the requested duration.
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n

def vad_collector(sample_rate, frame_duration_ms, padding_duration_ms, vad, frames):
    """Filters out non-voiced audio frames.
    Given a webrtcvad.Vad and a source of audio frames, yields only
    the voiced audio.
    Uses a padded, sliding window algorithm over the audio frames.
    When more than 90% of the frames in the window are voiced (as
    reported by the VAD), the collector triggers and begins yielding
    audio frames. Then the collector waits until 90% of the frames in
    the window are unvoiced to detrigger.
    The window is padded at the front and back to provide a small
    amount of silence or the beginnings/endings of speech around the
    voiced frames.
    Arguments:
    sample_rate - The audio sample rate, in Hz.
    frame_duration_ms - The frame duration in milliseconds.
    padding_duration_ms - The amount to pad the window, in milliseconds.
    vad - An instance of webrtcvad.Vad.
    frames - a source of audio frames (sequence or generator).
    Returns: A generator that yields PCM audio data.
    """
    num_padding_frames = int(padding_duration_ms / frame_duration_ms)
    # We use a deque for our sliding window/ring buffer.
    ring_buffer = collections.deque(maxlen=num_padding_frames)
    # We have two states: TRIGGERED and NOTTRIGGERED. We start in the
    # NOTTRIGGERED state.
    triggered = False

    voiced_frames = []
    for frame in frames:
        is_speech = vad.is_speech(frame.bytes, sample_rate)

        # sys.stdout.write('1' if is_speech else '0')
        if not triggered:
            ring_buffer.append((frame, is_speech))
            num_voiced = len([f for f, speech in ring_buffer if speech])
            # If we're NOTTRIGGERED and more than 90% of the frames in
            # the ring buffer are voiced frames, then enter the
            # TRIGGERED state.
            if num_voiced > 0.9 * ring_buffer.maxlen:
                triggered = True
                # sys.stdout.write('+(%s)' % (ring_buffer[0][0].timestamp,))
                # We want to yield all the audio we see from now until
                # we are NOTTRIGGERED, but we have to start with the
                # audio that's already in the ring buffer.
                for f, s in ring_buffer:
                    voiced_frames.append(f)
                ring_buffer.clear()
        else:
            # We're in the TRIGGERED state, so collect the audio data
            # and add it to the ring buffer.
            voiced_frames.append(frame)
            ring_buffer.append((frame, is_speech))
            num_unvoiced = len([f for f, speech in ring_buffer if not speech])
            # If more than 90% of the frames in the ring buffer are
            # unvoiced, then enter NOTTRIGGERED and yield whatever
            # audio we've collected.
            if num_unvoiced > 0.9 * ring_buffer.maxlen:
                # sys.stdout.write('-(%s)' % (frame.timestamp + frame.duration))
                triggered = False
                yield b''.join([f.bytes for f in voiced_frames])
                ring_buffer.clear()
                voiced_frames = []
    # if triggered:
    #     sys.stdout.write('-(%s)' % (frame.timestamp + frame.duration))
    # sys.stdout.write('\n')
    # If we have any leftover voiced audio when we run out of input,
    # yield it.
    if voiced_frames:
        yield b''.join([f.bytes for f in voiced_frames])

def get_embedding(wav_bin, return_file=False, normalize=False):
    vad = webrtcvad.Vad(0)
    wav = wave.open(io.BytesIO(wav_bin), 'rb')
    sr = wav.getframerate()
    frames = list(frame_generator(30, wav.readframes(wav.getnframes()), sr))
    frame = list(vad_collector(sr, 30, 300, vad, frames))
    if not frame:
        if return_file:
            return None, None
        return None
    wav = np.array(array('h', frame[0])) / (2**(8*wav.getsampwidth())/2)
    wav = np.expand_dims(wav, 1)
    embed = model.get_features(wav, sr).mean(0, keepdims=True)
    if normalize:
        embed = embed / np.linalg.norm(embed, axis=1, keepdims=True)
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
