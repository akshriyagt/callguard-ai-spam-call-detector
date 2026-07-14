"""
ivr_handler.py
---------------
When a call is flagged as SPAM, the AI auto-attends it and plays back an
IVR (Interactive Voice Response) script instead of ringing the user's phone.

Each category gets a tailored script. This simulates what would be sent to
a real telephony API (e.g. Twilio <Say>/<Gather> TwiML) as the AI's spoken
response -- see twilio_integration/webhook.py for the real-call version.
"""

IVR_SCRIPTS = {
    "loan_scam": [
        "Namaste. Thank you for calling. This number is registered on the National "
        "Do-Not-Disturb list and does not accept loan or credit offers.",
        "This call is being logged and reported as a suspected loan-scam call.",
        "Press 9 if you are a genuine bank representative, otherwise this call will now end.",
        "No response received. Ending call and adding number to the spam report queue.",
    ],
    "lottery_scam": [
        "Hello. You have reached an automated screening assistant.",
        "Genuine lotteries never ask winners to call them or share personal details "
        "over the phone, so this call has been flagged as a scam attempt.",
        "This interaction has been recorded for consumer protection reporting.",
        "Ending call now.",
    ],
    "otp_bank_fraud": [
        "This is an automated security assistant.",
        "Your bank will never call you asking for an OTP, PIN or CVV. This call has "
        "been identified as a likely fraud attempt and will not be connected.",
        "This number has been reported to the fraud detection team.",
        "Ending call now.",
    ],
    "tech_support_scam": [
        "Hello, automated screening assistant here.",
        "No legitimate tech company calls customers unprompted about virus alerts. "
        "This call has been flagged as a tech-support scam.",
        "Call is being logged and will now be ended.",
    ],
    "telemarketing": [
        "Hello, thank you for calling.",
        "This number has opted out of promotional and telemarketing calls.",
        "Please remove this number from your calling list. Ending call now.",
    ],
    "unknown_spam": [
        "Hello, this is an automated call-screening assistant.",
        "This call matched patterns commonly seen in spam or robocall traffic.",
        "Press 9 to speak to a human, or stay on the line to be disconnected.",
        "No valid response received. Ending call and logging this number.",
    ],
}

DEFAULT_HAM_SCRIPT = [
    "This call looks genuine based on the caller's history and speech pattern.",
    "Forwarding the call to the user's phone now — ringing...",
]


def get_ivr_conversation(is_spam: bool, category: str | None):
    """Return a list of dialogue lines the AI 'speaks' during the call."""
    if not is_spam:
        return DEFAULT_HAM_SCRIPT
    script = IVR_SCRIPTS.get(category, IVR_SCRIPTS["unknown_spam"])
    return script


def get_final_action(is_spam: bool) -> str:
    if is_spam:
        return "CALL_BLOCKED_AND_LOGGED"
    return "CALL_FORWARDED_TO_USER"
