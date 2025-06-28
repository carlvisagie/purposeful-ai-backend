FLAG_MATRIX = {
    "mental_health": ["anxiety", "burnout", "overthinking", "depression", "negative self-talk", "panic attacks", "intrusive thoughts", "racing thoughts"],
    "emotional": ["grief", "emotional regulation", "low self-esteem", "loneliness", "anger issues", "mood swings", "emotional numbness"],
    "spiritual": ["lack of purpose", "faith struggles", "existential crisis", "meaninglessness", "spiritual emptiness"],
    "physical": ["chronic pain", "poor sleep", "fatigue", "weight issues", "headaches", "digestive issues", "chronic illness"],
    "financial": ["debt", "instability", "financial anxiety", "income issues", "unemployment", "bankruptcy", "foreclosure"],
    "late_night_logins": {"severity": 2, "message": "Possible stress behavior"},
    "missed_sessions": {"severity": 3, "message": "Client disengagement"},
    "high_sentiment_swing": {"severity": 4, "message": "Emotional instability"}
}

CRISIS_FLAGS = {
    "suicide_keywords": [
        "kill myself", "end it all", "not worth living", "suicide", "suicidal",
        "want to die", "better off dead", "no point in living", "harm myself",
        "end my life", "take my own life", "don't want to be here"
    ],
    "self_harm_keywords": [
        "cut myself", "hurt myself", "self harm", "self-harm", "cutting",
        "burning myself", "hitting myself", "punish myself"
    ],
    "severe_depression_keywords": [
        "hopeless", "worthless", "nothing matters", "empty inside",
        "can't go on", "too much pain", "unbearable", "no way out",
        "trapped", "can't escape", "overwhelming darkness"
    ],
    "substance_abuse_keywords": [
        "drinking too much", "can't stop drinking", "drug problem", "addiction",
        "overdose", "pills", "substance abuse", "getting high"
    ]
}
