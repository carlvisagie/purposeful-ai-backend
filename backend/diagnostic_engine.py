from flag_matrix import FLAG_MATRIX

def diagnose_client_responses(text_input):
    profile = {k: [] for k in FLAG_MATRIX}
    for category, flags in FLAG_MATRIX.items():
        for flag in flags:
            if flag.lower() in text_input.lower():
                profile[category].append(flag)
    return profile
