"""
app.py
-------
Flask web app that simulates an incoming call, runs it through the
spam detector, and — if flagged spam — plays out an AI/IVR conversation
instead of ringing the phone.

Run:
    python3 app.py
Then open http://localhost:5000
"""

import os
import json
import uuid
import datetime
from flask import Flask, render_template, request, jsonify

from spam_detector import SpamDetector
from ivr_handler import get_ivr_conversation, get_final_action
from audio_transcribe import transcribe_audio

app = Flask(__name__)
detector = SpamDetector()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "logs", "call_log.jsonl")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aiff", ".aif"}


def log_call(record: dict):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    record["timestamp"] = datetime.datetime.now().isoformat()
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/simulate_call", methods=["POST"])
def simulate_call():
    data = request.get_json(force=True)

    phone_number = data.get("phone_number", "").strip()
    transcript = data.get("transcript", "").strip()
    calls_per_day = int(data.get("calls_per_day", 1) or 1)
    avg_call_duration = int(data.get("avg_call_duration", 60) or 60)
    is_international = 1 if data.get("is_international") else 0

    if not phone_number or not transcript:
        return jsonify({"error": "phone_number and transcript are required"}), 400

    result = detector.analyze(
        phone_number=phone_number,
        transcript=transcript,
        calls_per_day=calls_per_day,
        avg_call_duration=avg_call_duration,
        is_international=is_international,
    )

    conversation = get_ivr_conversation(result["is_spam"], result["primary_category"])
    action = get_final_action(result["is_spam"])

    response_payload = {**result, "ivr_conversation": conversation, "final_action": action}
    log_call(response_payload)

    return jsonify(response_payload)


@app.route("/api/analyze_audio", methods=["POST"])
def analyze_audio():
    """Upload a call recording -> auto-transcribe -> auto-run spam detection.
    No manual transcript typing needed."""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    audio_file = request.files["audio"]
    if audio_file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    ext = os.path.splitext(audio_file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Unsupported file type '{ext}'. Try WAV, MP3, M4A, OGG, or FLAC."}), 400

    phone_number = request.form.get("phone_number", "Unknown").strip() or "Unknown"
    calls_per_day = int(request.form.get("calls_per_day", 1) or 1)
    avg_call_duration = int(request.form.get("avg_call_duration", 60) or 60)
    is_international = 1 if request.form.get("is_international") == "true" else 0

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    temp_name = f"{uuid.uuid4().hex}{ext}"
    temp_path = os.path.join(UPLOAD_DIR, temp_name)
    audio_file.save(temp_path)

    try:
        transcript = transcribe_audio(temp_path)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    if not transcript:
        return jsonify({"error": "Couldn't make out any speech in that recording. Try a clearer clip."}), 422

    result = detector.analyze(
        phone_number=phone_number,
        transcript=transcript,
        calls_per_day=calls_per_day,
        avg_call_duration=avg_call_duration,
        is_international=is_international,
    )

    conversation = get_ivr_conversation(result["is_spam"], result["primary_category"])
    action = get_final_action(result["is_spam"])

    response_payload = {**result, "ivr_conversation": conversation, "final_action": action, "source": "audio_upload"}
    log_call(response_payload)

    return jsonify(response_payload)


@app.route("/api/call_log", methods=["GET"])
def call_log():
    if not os.path.exists(LOG_PATH):
        return jsonify([])
    with open(LOG_PATH) as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return jsonify(list(reversed(rows))[:50])


@app.route("/api/call_log", methods=["DELETE"])
def clear_call_log():
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
    return jsonify({"cleared": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
