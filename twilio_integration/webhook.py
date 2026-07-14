"""
webhook.py
-----------
FUTURE / REAL-WORLD EXTENSION (not required to run the demo).

This shows how the exact same spam_detector.py + ivr_handler.py from the
demo would be wired to REAL incoming phone calls using Twilio's Programmable
Voice API. Twilio is a telephony provider — when someone calls your Twilio
number, Twilio sends an HTTP webhook to this Flask route, and whatever TwiML
(Twilio Markup XML) you return controls what the caller hears next.

SETUP STEPS (do this later, when ready to go live):
  1. Create a free Twilio account -> https://www.twilio.com/try-twilio
  2. Buy/rent a Twilio phone number (has voice capability).
  3. pip install twilio
  4. Run this file, then expose it publicly (e.g. `ngrok http 5001`) so
     Twilio's servers can reach your machine.
  5. In the Twilio console, set the phone number's "A call comes in"
     webhook to:  https://<your-ngrok-url>/incoming_call  (HTTP POST)
  6. Call your Twilio number from any phone — Twilio will POST call data
     here, and this code will run detection + speak the IVR script back
     using text-to-speech (via <Say>), fully hands-free.

Twilio also gives you real caller metadata (From number, call duration
history via their Lookup API, etc.) which you can feed into the SAME
`SpamDetector.analyze()` used by the demo — no changes needed there.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, Response
from spam_detector import SpamDetector
from ivr_handler import get_ivr_conversation

# from twilio.twiml.voice_response import VoiceResponse, Gather
# ^ uncomment once `pip install twilio` is done

app = Flask(__name__)
detector = SpamDetector()

# In real usage you'd track this in a database keyed by caller number.
CALL_FREQUENCY_CACHE = {}


@app.route("/incoming_call", methods=["POST"])
def incoming_call():
    caller_number = request.values.get("From", "unknown")
    CALL_FREQUENCY_CACHE[caller_number] = CALL_FREQUENCY_CACHE.get(caller_number, 0) + 1

    # NOTE: Getting a live transcript of what the caller says requires
    # Twilio's <Gather input="speech"> (speech-to-text) on a first "listen"
    # leg of the call, or a streaming STT service (e.g. Twilio Media Streams
    # + Deepgram/Google Speech-to-Text). That transcript then gets passed
    # into detector.analyze() below instead of a hardcoded string.
    simulated_transcript = "Congratulations, you have won a lottery prize, share your otp"

    result = detector.analyze(
        phone_number=caller_number,
        transcript=simulated_transcript,
        calls_per_day=CALL_FREQUENCY_CACHE[caller_number],
        avg_call_duration=20,
        is_international=0,
    )

    conversation = get_ivr_conversation(result["is_spam"], result["primary_category"])

    # Build TwiML by hand here (so this file runs even without the twilio
    # package installed). With `twilio` installed, use VoiceResponse instead:
    #
    #   vr = VoiceResponse()
    #   for line in conversation:
    #       vr.say(line, voice="Polly.Aditi")
    #   if not result["is_spam"]:
    #       vr.dial(os.environ.get("FORWARD_TO_NUMBER"))
    #   return Response(str(vr), mimetype="text/xml")

    say_tags = "".join(f"<Say voice='Polly.Aditi'>{line}</Say>" for line in conversation)

    if result["is_spam"]:
        twiml = f"<?xml version='1.0' encoding='UTF-8'?><Response>{say_tags}<Hangup/></Response>"
    else:
        forward_number = os.environ.get("FORWARD_TO_NUMBER", "")
        dial_tag = f"<Dial>{forward_number}</Dial>" if forward_number else ""
        twiml = f"<?xml version='1.0' encoding='UTF-8'?><Response>{say_tags}{dial_tag}</Response>"

    return Response(twiml, mimetype="text/xml")


if __name__ == "__main__":
    app.run(port=5001, debug=True)
