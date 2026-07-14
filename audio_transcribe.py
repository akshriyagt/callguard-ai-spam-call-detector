"""
audio_transcribe.py
---------------------
Takes an uploaded call-recording audio file and converts it to a text
transcript, which then gets fed straight into spam_detector.analyze() —
no manual typing needed.

Uses SpeechRecognition (Google Web Speech API - free, needs internet on the
user's machine at runtime). Works directly with WAV/AIFF/FLAC. For MP3/M4A/OGG
etc, install ffmpeg + pydub (see requirements.txt comment) for automatic
conversion; otherwise ask the user to upload WAV.

For a fully-offline/private alternative (no internet call per recording),
swap this out for `faster-whisper` — see the commented block at the bottom.
"""

import os
import speech_recognition as sr

SUPPORTED_NATIVE = (".wav", ".aiff", ".aif", ".flac")


def _maybe_convert_to_wav(filepath: str) -> str:
    """If the file isn't natively supported, try converting with pydub+ffmpeg."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in SUPPORTED_NATIVE:
        return filepath
    try:
        from pydub import AudioSegment
        wav_path = filepath + ".converted.wav"
        AudioSegment.from_file(filepath).export(wav_path, format="wav")
        return wav_path
    except Exception as e:
        raise RuntimeError(
            f"Can't read '{ext}' files without ffmpeg+pydub installed. "
            f"Please upload a .wav file instead, or run: pip install pydub "
            f"and install ffmpeg. (Original error: {e})"
        )


def transcribe_audio(filepath: str) -> str:
    """Returns the transcribed text for the given audio file path."""
    wav_path = _maybe_convert_to_wav(filepath)
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
        # Free Google Web Speech API — good enough for demo/short clips.
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return ""  # audio unclear / silence — caller will see "couldn't transcribe"
    except sr.RequestError as e:
        raise RuntimeError(f"Speech recognition service error (check internet connection): {e}")
    finally:
        if wav_path != filepath and os.path.exists(wav_path):
            os.remove(wav_path)


# ---------------------------------------------------------------------------
# OFFLINE / PRIVACY-FOCUSED ALTERNATIVE (optional, heavier setup):
#
#   pip install faster-whisper
#
#   from faster_whisper import WhisperModel
#   _model = WhisperModel("base", device="cpu", compute_type="int8")
#
#   def transcribe_audio(filepath: str) -> str:
#       segments, _ = _model.transcribe(filepath)
#       return " ".join(seg.text for seg in segments)
#
# This runs fully locally (no data leaves the machine) but needs ffmpeg and
# downloads a ~150MB model on first run.
# ---------------------------------------------------------------------------
