"""
generate_dataset.py
--------------------
Generates a synthetic but realistic call-log dataset to train the spam
classifier. In a real project you would replace this with real (anonymized)
call logs from a telecom provider / CDR (Call Detail Record) export.

Each row represents one call with:
    phone_number        - caller number (string)
    calls_per_day        - how many calls this number made today (frequency)
    avg_call_duration    - average duration in seconds for this number
    is_international     - 1 if the number is a foreign/unknown code
    transcript           - what the caller said (speech-to-text simulated)
    label                 - 1 = spam, 0 = genuine (ham)
"""

import random
import pandas as pd

random.seed(42)

SPAM_TEMPLATES = [
    "Hello sir, you have won a lottery prize of 25 lakh rupees, share your otp to claim",
    "This is your bank calling, your account is suspended, please verify your account immediately",
    "Congratulations! You are the lucky winner of our lucky draw cash prize",
    "Sir we are offering instant loan approved with zero interest loan, no documents required",
    "Your card is blocked, kindly share otp to unblock your debit card now",
    "This is Microsoft support, your computer has a virus, we need remote access support",
    "We are calling about extended warranty for your car, best deal today only",
    "Sir this is KBC lottery department, you have won cash prize, claim your prize now",
    "Get pre-approved loan up to 5 lakhs instantly, credit limit increase available",
    "This call is regarding your insurance policy renewal, limited time offer free gift voucher",
    "Namaste sir, aapka kyc update pending hai, share otp turant",
    "Hello, this is a courier company, your parcel is held at customs, pay processing fee",
]

HAM_TEMPLATES = [
    "Hi, it's mom, just calling to check how you are doing",
    "Hey are we still meeting for lunch today at 1pm",
    "This is Rahul from the office, can you send me the report before evening",
    "Hi this is Dr Sharma's clinic confirming your appointment tomorrow at 10am",
    "Hello, this is Swiggy delivery partner, I am outside your building",
    "Hi, this is your electricity board, your bill payment was received, thank you",
    "Hey bro, are you coming to the cricket match this weekend",
    "This is the school calling regarding your child's parent teacher meeting",
    "Hi, this is your bank relationship manager, calling to schedule a home visit for kyc",
    "Hello, calling from HR department regarding your interview scheduled tomorrow",
    "Hey it's me, forgot my keys, can you leave the door open",
    "This is Amazon delivery, I'll be there in 5 minutes with your package",
]

INDIAN_LANDLINE_PREFIXES = ["+9180", "+9122", "+9111", "+9144", "+9133"]
INDIAN_MOBILE_PREFIXES = ["+9198", "+9199", "+9187", "+9176", "+9163"]
SUSPICIOUS_PREFIXES = ["+1900", "+1809", "+234", "+263", "+92300"]


def random_number(spam: bool) -> str:
    if spam and random.random() < 0.35:
        prefix = random.choice(SUSPICIOUS_PREFIXES)
    else:
        prefix = random.choice(INDIAN_MOBILE_PREFIXES + INDIAN_LANDLINE_PREFIXES)
    return prefix + str(random.randint(100000, 999999))


def make_row(spam: bool):
    number = random_number(spam)
    transcript = random.choice(SPAM_TEMPLATES if spam else HAM_TEMPLATES)

    if spam:
        calls_per_day = random.choice([1, 2, 3, 8, 15, 25, 40])  # spammers often call many numbers/day
        avg_duration = random.randint(5, 40)  # spam calls tend to be short
        is_international = 1 if number.startswith(tuple(SUSPICIOUS_PREFIXES)) else random.choice([0, 0, 1])
    else:
        calls_per_day = random.choice([1, 1, 1, 2, 2, 3])
        avg_duration = random.randint(60, 600)
        is_international = 0

    label = 1 if spam else 0
    return {
        "phone_number": number,
        "calls_per_day": calls_per_day,
        "avg_call_duration": avg_duration,
        "is_international": is_international,
        "transcript": transcript,
        "label": label,
    }


def generate(n_per_class: int = 600) -> pd.DataFrame:
    rows = [make_row(True) for _ in range(n_per_class)]
    rows += [make_row(False) for _ in range(n_per_class)]
    random.shuffle(rows)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate(600)
    df.to_csv("dataset.csv", index=False)
    print(f"Generated {len(df)} rows -> dataset.csv")
    print(df["label"].value_counts())
