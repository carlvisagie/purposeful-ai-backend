def calculate_mortality_risk(age, chronic_conditions, habits):
    risk = 0

    if age > 55:
        risk += 1

    if len(chronic_conditions) > 0:
        risk += 2

    risky_habits = ["smoking", "poor sleep", "alcohol", "sedentary", "junk food", "overweight"]
    if any(h in habits for h in risky_habits):
        risk += 1

    if risk >= 3:
        return "critical"
    elif risk == 2:
        return "elevated"
    return "low"
