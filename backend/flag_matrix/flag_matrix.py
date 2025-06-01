
FLAG_MATRIX = {
 # backend/flag_matrix/mental.py
mental_flags = [
    "anxiety",
    "burnout",
    "overthinking",
    "depression",
    "negative self-talk"
]

# backend/flag_matrix/emotional.py
emotional_flags = [
    "grief",
    "emotional regulation",
    "low self-esteem",
    "loneliness"
]

# backend/flag_matrix/spiritual.py
spiritual_flags = [
    "lack of purpose",
    "faith struggles",
    "existential crisis"
]

# backend/flag_matrix/physical.py
physical_flags = [
    "chronic pain",
    "poor sleep",
    "fatigue",
    "weight issues"
]

# backend/flag_matrix/financial.py
financial_flags = [
    "debt",
    "instability",
    "financial anxiety",
    "income issues"
]

# backend/flag_matrix/combined.py
from backend.flag_matrix.mental import mental_flags
from backend.flag_matrix.emotional import emotional_flags
from backend.flag_matrix.spiritual import spiritual_flags
from backend.flag_matrix.physical import physical_flags
from backend.flag_matrix.financial import financial_flags

FLAG_MATRIX = {
    "mental_health": mental_flags,
    "emotional": emotional_flags,
    "spiritual": spiritual_flags,
    "physical": physical_flags,
    "financial": financial_flags
}

# backend/flag_matrix/__init__.py
from backend.flag_matrix.combined import FLAG_MATRIX

