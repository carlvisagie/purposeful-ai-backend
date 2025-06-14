from flag_matrix import FLAG_MATRIX

def diagnose_client_responses(text_input):
    profile = {k: [] for k in FLAG_MATRIX}
    lowered = text_input.lower()
    for category, flags in FLAG_MATRIX.items():
        for flag in flags:
            words = flag.lower().split()
            if any(word in lowered for word in words):
                profile[category].append(flag)
    return profile
