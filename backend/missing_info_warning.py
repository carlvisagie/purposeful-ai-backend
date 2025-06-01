REQUIRED_FIELDS = ["symptoms", "goals", "medications", "emergency_contact"]

def check_missing_info(client_data):
    return [field for field in REQUIRED_FIELDS if not client_data.get(field)]
