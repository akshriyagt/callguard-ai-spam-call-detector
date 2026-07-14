# CallGuard AI — Spam Call Detection & Auto-IVR Response

An AI system that **automatically detects whether an incoming call is spam**
and, if it is, **auto-attends the call using an AI/IVR voice response** instead
of ringing the user's phone.

This repo ships as a **working local demo** (simulate calls in a browser) plus
a **skeleton for real phone integration** using Twilio, so you can extend it
to actually screen live calls later without rewriting the core logic.

---

## How it works (architecture)

```
 Incoming call (simulated in demo / real via Twilio later)
        │
        ▼
 ┌────────────────────┐
 │  spam_detector.py   │   combines:
 │                     │     1) ML model  (TF-IDF transcript + call metadata → RandomForest)
 │                     │     2) Rule engine (blacklist numbers + scam keyword phrases)
 └─────────┬──────────┘
           │  final_score (0-100), is_spam, category
           ▼
 ┌────────────────────┐
 │  ivr_handler.py      │  picks an IVR script based on scam category
 └─────────┬──────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
  SPAM        GENUINE
  AI answers   Call forwarded
  & logs it    to the user
```

**Why ML + rules together?**
- The **ML model** generalizes to new spam callers who reword their script.
- The **rule engine** catches known blacklisted numbers and exact scam phrases
  instantly, even before the ML model has "seen" that wording.
- Final score = `0.6 × ML score + 0.4 × rule score`, flagged as spam at ≥ 50.

---

## Project structure

```
spam_call_ai/
├── app.py                     # Flask server: dashboard UI + /api/simulate_call
├── spam_detector.py            # Combines ML + rule-based scoring
├── ivr_handler.py               # Generates the AI's spoken IVR script per scam type
├── requirements.txt
├── ml/
│   ├── generate_dataset.py      # Builds a synthetic labeled call dataset
│   ├── train_model.py           # Trains + saves the RandomForest model.pkl
│   ├── dataset.csv              # Generated training data (1200 sample calls)
│   └── model.pkl                # Trained model (already included, ready to use)
├── rules/
│   ├── blacklist.json           # Known spam numbers / risky prefixes
│   └── keywords.json            # Scam phrase -> category -> weight
├── templates/index.html         # Call-screening dashboard UI
├── static/style.css, script.js  # Frontend styling + logic
├── twilio_integration/
│   └── webhook.py               # Real-call extension (Twilio webhook, commented setup steps)
└── logs/call_log.jsonl          # Every simulated call gets logged here
```

---

## Running the demo

```bash
cd spam_call_ai
pip install -r requirements.txt

# (Optional — model.pkl is already included, only do this if you want to retrain)
cd ml && python3 generate_dataset.py && python3 train_model.py && cd ..

python3 app.py
```

Open **http://localhost:5000** in your browser.

### Option A — Fully automatic (upload a real call recording)
Drag & drop a call recording (WAV / MP3 / M4A / OGG / FLAC) onto the upload box.
The app **automatically**:
1. Transcribes the audio to text (speech-to-text),
2. Feeds that transcript into the spam detector,
3. Shows the live score gauge + IVR playback — no typing required.

> Needs an internet connection on your machine (uses the free Google Web
> Speech API for transcription). For MP3/M4A files you also need `ffmpeg`
> installed (WAV/FLAC work without it). If ffmpeg isn't installed, just
> export/upload as WAV.

### Option B — Manual simulation
1. Type in a caller number + what the caller is saying (or click a sample chip
   like "Lottery scam" / "Genuine call").
2. Click **Answer with AI**.
3. Watch the live spam-score gauge, the ML vs rule-engine score breakdown,
   and — if it's spam — the AI's IVR conversation play out line by line before
   the call is auto-blocked and logged.

---

## Extending to real phone calls (Twilio)

`twilio_integration/webhook.py` contains a ready-to-adapt Flask route that:
- Receives real incoming-call webhooks from Twilio,
- Runs the **same** `spam_detector.py` used in the demo,
- Speaks the IVR script back to the caller using text-to-speech (`<Say>` in
  TwiML), and either hangs up (spam) or forwards the call (genuine).

Full setup steps are documented as comments at the top of that file — you'll
need a free Twilio trial account, a rented phone number, and `ngrok` (or any
tunnel) to expose your local server to Twilio's webhook. Getting a live
transcript of the caller's speech in real time additionally needs Twilio's
speech-to-text `<Gather>` or a streaming STT service — noted inline in the code.

---

## For your project report / viva

**Problem statement:** Robocalls and scam calls (fake lottery, loan, OTP/bank
fraud, tech-support scams) are hard for users to filter manually. This system
automates detection and response.

**Key components to mention:**
- **Feature engineering:** call transcript (text) + call metadata (frequency,
  duration, international/unknown code) — spam calls are typically short,
  come from numbers that call many people per day, and use money/urgency language.
- **Model:** RandomForestClassifier over TF-IDF (1-2 gram) text features
  combined with scaled numeric features via a scikit-learn `ColumnTransformer`.
- **Hybrid decision system:** ML score blended with an explainable rule score,
  so you can always justify *why* a call was flagged (see the `reasons` list
  returned by the API) — useful to explain in a viva.
- **IVR automation:** category-specific auto-response scripts, mirroring how
  a real telecom-grade system (like Truecaller / Reliance Jio's spam
  filtering) auto-handles suspected spam.

**Possible extensions to mention as "future scope":**
- Real-time speech-to-text integration for live transcripts.
- Crowd-sourced blacklist updates (like Truecaller's community reporting).
- Caller reputation scoring using call graph / frequency across all users.
- Multilingual keyword rules (Tamil/Hindi scam phrases) for wider coverage.

---

## Notes

- The dataset in `ml/dataset.csv` is **synthetically generated** for demo
  purposes (see `ml/generate_dataset.py`) — swap in real anonymized call logs
  for a stronger project if you have access to any.
- `model.pkl` is already trained and committed, so the demo works out of the box.
