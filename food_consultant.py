"""
food_consultant.py
------------------
Rule-based Food Consultant engine for the Diabetes Risk Prediction System.
Provides personalized South Indian dietary guidance based on risk level,
BMI category, food preference (Vegetarian / Non-vegetarian / Eggetarian),
and wellness goal (Prevent diabetes / Control sugar / Lose weight).
"""

import json
import os

DATA_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "food_consultant_data.json")

def load_food_data():
    """Loads nutritional rules and meal plan templates from JSON."""
    if not os.path.exists(DATA_FILE_PATH):
        raise FileNotFoundError(f"Food consultant data file not found at {DATA_FILE_PATH}")
    with open(DATA_FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_recommendations(risk_level="Low", bmi_category="Normal", food_type="Vegetarian", goal="Prevent diabetes"):
    """
    Computes rule-based diet recommendations.

    Parameters:
    - risk_level: str ('Low', 'Medium', 'High')
    - bmi_category: str ('Underweight', 'Normal', 'Overweight', 'Obese')
    - food_type: str ('Vegetarian', 'Non-vegetarian', 'Eggetarian')
    - goal: str ('Prevent diabetes', 'Control sugar', 'Lose weight')

    Returns:
    - dict containing:
        - foods_to_eat_more: list of dicts
        - foods_to_limit: list of dicts
        - foods_to_avoid: list of dicts
        - meal_plan: dict with keys (breakfast, lunch, snack, dinner)
        - tips: list of dicts (title, desc)
        - is_high_risk: bool
        - bmi_note: str (tailored portion guidance)
        - user_summary: dict of parsed parameters
    """
    # 1. Clean & normalize inputs
    risk = (risk_level or "Low").strip().capitalize()
    if risk not in ["Low", "Medium", "High"]:
        risk = "Low"

    bmi_cat = (bmi_category or "Normal").strip().capitalize()
    if bmi_cat not in ["Underweight", "Normal", "Overweight", "Obese"]:
        bmi_cat = "Normal"

    # Food type normalization
    valid_food_types = {
        "vegetarian": "Vegetarian",
        "non-vegetarian": "Non-vegetarian",
        "non vegetarian": "Non-vegetarian",
        "eggetarian": "Eggetarian"
    }
    f_type = valid_food_types.get((food_type or "").strip().lower(), "Vegetarian")

    # Goal normalization
    valid_goals = {
        "prevent diabetes": "Prevent diabetes",
        "control sugar": "Control sugar",
        "lose weight": "Lose weight"
    }
    g_val = valid_goals.get((goal or "").strip().lower(), "Prevent diabetes")

    # 2. Load dataset
    data = load_food_data()

    # 3. Assemble 'Foods to eat more' based on food preference
    eat_more = list(data["foods_to_eat_more"]["base"])
    if f_type == "Non-vegetarian":
        eat_more.extend(data["foods_to_eat_more"].get("non_veg", []))
        eat_more.extend(data["foods_to_eat_more"].get("egg", []))
    elif f_type == "Eggetarian":
        eat_more.extend(data["foods_to_eat_more"].get("egg", []))

    # 4. Tailor Foods to Limit / Avoid
    foods_limit = list(data["foods_to_limit"])
    foods_avoid = list(data["foods_to_avoid"])

    # If BMI is Overweight or Obese, emphasize portion reduction on grains and oils
    bmi_note = ""
    if bmi_cat in ["Overweight", "Obese"]:
        bmi_note = f"Your BMI indicates you are in the {bmi_cat} range. Prioritize half-plate vegetable servings, strictly avoid fried evening snacks, and limit cooking oil to under 3 teaspoons (15ml) daily."
    elif bmi_cat == "Underweight":
        bmi_note = "Your BMI is in the Underweight range. Do not restrict wholesome calories; consume nutrient-dense whole foods like nuts, seeds, dhal, and ragi porridge while still avoiding refined white sugars."
    else:
        bmi_note = "Your BMI is in the Normal range. Maintain caloric balance with fiber-rich complex grains and regular hydration."

    # 5. Extract 1-Day Sample Meal Plan
    plans_by_type = data.get("meal_plans", {}).get(f_type, {})
    meal_plan = plans_by_type.get(g_val, plans_by_type.get("Prevent diabetes", {}))

    # 6. Extract tips
    tips = list(data.get("healthy_eating_tips", []))

    # 7. Check high risk status
    is_high_risk = (risk == "High")

    return {
        "foods_to_eat_more": eat_more,
        "foods_to_limit": foods_limit,
        "foods_to_avoid": foods_avoid,
        "meal_plan": meal_plan,
        "tips": tips,
        "is_high_risk": is_high_risk,
        "bmi_note": bmi_note,
        "user_summary": {
            "risk_level": risk,
            "bmi_category": bmi_cat,
            "food_type": f_type,
            "goal": g_val
        }
    }
