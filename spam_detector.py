"""
spam_detector.py
-----------------
Combines:
  1) ML model prediction (probability that the call is spam), trained on
     transcript text + call metadata.
  2) Rule-based scoring (blacklist numbers/prefixes + keyword phrase matches).

Final decision = weighted blend of ML probability and rule score, so the
system still catches spam callers who slightly reword their script (rules)
while remaining accurate on unseen ML edge cases.
"""

import os
import json
import joblib
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ML_MODEL_PATH = os.path.join(BASE_DIR, "ml", "model.pkl")
BLACKLIST_PATH = os.path.join(BASE_DIR, "rules", "blacklist.json")
KEYWORDS_PATH = os.path.join(BASE_DIR, "rules", "keywords.json")

ML_WEIGHT = 0.6
RULE_WEIGHT = 0.4
SPAM_THRESHOLD = 50  # final_score (0-100) >= this => classified as SPAM


def _load_json(path):
    with open(path, "r") as f:
        return json.load(f)


class SpamDetector:
    def __init__(self):
        self.model = joblib.load(ML_MODEL_PATH)
        self.blacklist = _load_json(BLACKLIST_PATH)
        self.keyword_rules = _load_json(KEYWORDS_PATH)

    # ---------- ML SCORE ----------
    def _ml_score(self, transcript, calls_per_day, avg_call_duration, is_international):
        row = pd.DataFrame([{
            "transcript": transcript,
            "calls_per_day": calls_per_day,
            "avg_call_duration": avg_call_duration,
            "is_international": is_international,
        }])
        proba = self.model.predict_proba(row)[0]
        classes = list(self.model.classes_)
        spam_idx = classes.index(1)
        return float(proba[spam_idx]) * 100  # 0-100

    # ---------- RULE SCORE ----------
    def _rule_score(self, phone_number, transcript):
        score = 0
        matched_categories = []
        reasons = []

        if phone_number in self.blacklist.get("blacklisted_numbers", []):
            score += 50
            reasons.append(f"Number {phone_number} is in the reported-spam blacklist")

        for prefix in self.blacklist.get("blacklisted_prefixes", []):
            if phone_number.startswith(prefix):
                score += 25
                reasons.append(f"Number prefix {prefix} is flagged as high-risk")
                break

        text_lower = transcript.lower()
        for category, rule in self.keyword_rules.items():
            if category.startswith("_"):
                continue
            for phrase in rule["keywords"]:
                if phrase in text_lower:
                    score += rule["weight"]
                    matched_categories.append(category)
                    reasons.append(f"Transcript matched '{phrase}' ({category} pattern)")
                    break  # only count each category once

        return min(score, 100), matched_categories, reasons

    # ---------- COMBINED DECISION ----------
    def analyze(self, phone_number, transcript, calls_per_day=1, avg_call_duration=60, is_international=0):
        ml_score = self._ml_score(transcript, calls_per_day, avg_call_duration, is_international)
        rule_score, categories, reasons = self._rule_score(phone_number, transcript)

        final_score = round(ML_WEIGHT * ml_score + RULE_WEIGHT * rule_score, 1)
        is_spam = final_score >= SPAM_THRESHOLD

        primary_category = categories[0] if categories else ("unknown_spam" if is_spam else None)

        return {
            "phone_number": phone_number,
            "transcript": transcript,
            "ml_score": round(ml_score, 1),
            "rule_score": round(rule_score, 1),
            "final_score": final_score,
            "is_spam": is_spam,
            "matched_categories": categories,
            "primary_category": primary_category,
            "reasons": reasons,
        }
