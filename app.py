import os
import sqlite3
import json
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, make_response, Response
)
import joblib
import numpy as np
import pandas as pd

from plans_data import PLANS
from report_generator import generate_pdf_report
from food_consultant import get_recommendations

app = Flask(__name__)
app.secret_key = (
    os.environ.get("SECRET_KEY")
    or os.environ.get("FLASK_SECRET_KEY")
    or "diabetes-risk-assessment-secret-key-2026"
)

# Admin credentials
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assessments.db")
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model", "model.pkl")

# Load trained model bundle if available
ml_bundle = None
if os.path.exists(MODEL_PATH):
    try:
        ml_bundle = joblib.load(MODEL_PATH)
        print(f"[+] ML Model bundle loaded: {ml_bundle.get('best_model_name', 'Model')}")
    except Exception as e:
        print(f"[!] Warning: Could not load model ({e})")

def init_db():
    """Initializes SQLite database table for storing assessment history."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            assessment_type TEXT NOT NULL,
            user_name TEXT,
            age INTEGER,
            gender TEXT,
            bmi REAL,
            risk_score REAL NOT NULL,
            risk_level TEXT NOT NULL,
            details TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_bmi_category(bmi):
    """
    Categorizes BMI according to clinical standards:
    Underweight (<18.5), Normal (18.5-24.9), Overweight (25-29.9), Obese (30+)
    Returns (category_name, badge_class, color_hex)
    """
    if bmi is None:
        return "Normal", "success", "#198754"
    try:
        val = float(bmi)
        if val < 18.5:
            return "Underweight", "secondary", "#6c757d"
        elif val <= 24.9:
            return "Normal", "success", "#198754"
        elif val <= 29.9:
            return "Overweight", "warning", "#ffc107"
        else:
            return "Obese", "danger", "#dc3545"
    except (ValueError, TypeError):
        return "Normal", "success", "#198754"

def calculate_bmi(height_cm, weight_kg):
    """Calculates BMI from height (cm) and weight (kg)."""
    try:
        h_m = float(height_cm) / 100.0
        w_kg = float(weight_kg)
        if h_m > 0 and w_kg > 0:
            return round(w_kg / (h_m ** 2), 1)
    except (ValueError, TypeError):
        pass
    return None

def compute_questionnaire_score(data):
    """
    Computes a risk score based on the 12 plain-language lifestyle & symptom questions.
    Returns: score, risk_level, badge_class, color, factors, top_factors (top 3 with one-line explanations), tips
    """
    score = 0
    scored_factors = []

    # 1. Age
    age = int(data.get("age", 25))
    if age >= 65:
        score += 15
        scored_factors.append((15, f"Age is {age} (Senior)", "Metabolic rate slows and pancreatic beta-cell sensitivity decreases naturally with age."))
    elif age >= 55:
        score += 12
        scored_factors.append((12, f"Age is {age} (55-64 yrs)", "Insulin secretion efficiency declines progressively after age 50."))
    elif age >= 45:
        score += 8
        scored_factors.append((8, f"Age is {age} (45-54 yrs)", "Middle age marks a physiological turning point where prediabetes risk rises."))
    elif age >= 35:
        score += 4
        scored_factors.append((4, f"Age is {age} (35-44 yrs)", "Early middle age carries moderate cumulative metabolic risk."))

    # 2. BMI
    bmi = float(data.get("bmi", 22.0))
    if bmi >= 35:
        score += 20
        scored_factors.append((20, f"Severe Obesity (BMI: {bmi})", "Excess adipose tissue releases free fatty acids that impair cellular insulin receptors."))
    elif bmi >= 30:
        score += 15
        scored_factors.append((15, f"Obesity (BMI: {bmi})", "High body fat mass directly drives systemic insulin resistance and elevated blood glucose."))
    elif bmi >= 25:
        score += 8
        scored_factors.append((8, f"Overweight (BMI: {bmi})", "Carrying excess weight places elevated continuous demand on pancreatic insulin output."))

    # 3. Family History
    if data.get("family_history") == "yes":
        score += 12
        scored_factors.append((12, "Family history of diabetes", "First-degree genetic predisposition significantly increases the biological susceptibility to diabetes."))

    # 4. Excessive Thirst
    if data.get("frequent_thirst") == "yes":
        score += 8
        scored_factors.append((8, "Frequent excessive thirst (Polydipsia)", "High circulating blood glucose draws fluid from tissues, triggering intense systemic thirst."))

    # 5. Frequent Urination
    if data.get("frequent_urination") == "yes":
        score += 8
        scored_factors.append((8, "Frequent or nighttime urination (Polyuria)", "Kidneys work overtime to expel surplus blood glucose, causing frequent fluid excretion."))

    # 6. Fatigue
    if data.get("fatigue") == "yes":
        score += 6
        scored_factors.append((6, "Persistent fatigue or weakness", "Cells are deprived of cellular energy when glucose cannot properly cross from blood into cells."))

    # 7. Unexplained Weight Loss
    if data.get("unexplained_weight_loss") == "yes":
        score += 8
        scored_factors.append((8, "Unexplained weight loss", "Body breaks down muscle and fat reserves for energy when insulin cannot transport glucose into cells."))

    # 8. Slow Healing
    if data.get("slow_healing") == "yes":
        score += 7
        scored_factors.append((7, "Slow-healing cuts or wounds", "High glucose levels narrow blood vessels and impair white blood cell repair mechanisms."))

    # 9. Blurry Vision
    if data.get("blurry_vision") == "yes":
        score += 6
        scored_factors.append((6, "Occasional blurry vision", "Osmotic shifts cause lens swelling in the eyes, interfering with focal clarity."))

    # 10. Physical Inactivity
    if data.get("exercise_daily") == "no":
        score += 5
        scored_factors.append((5, "No regular daily exercise (< 30 mins)", "Physical inactivity reduces muscle glucose uptake independent of insulin levels."))

    # 11. High Blood Pressure
    if data.get("high_bp") == "yes":
        score += 5
        scored_factors.append((5, "History of high blood pressure", "Hypertension often co-exists with metabolic syndrome and damages vascular beds."))

    # Sort scored factors descending by weight to pick top 3
    scored_factors.sort(key=lambda x: x[0], reverse=True)
    top_3_factors = [
        {"name": item[1], "explanation": item[2], "weight": item[0]}
        for item in scored_factors[:3]
    ]

    all_factor_names = [item[1] for item in scored_factors]

    # Cap score at 100%
    score_percentage = min(score, 100)

    # Classify Risk Level
    if score_percentage < 25:
        risk_level = "Low"
        badge_class = "success"
        color = "#198754"
    elif score_percentage < 55:
        risk_level = "Medium"
        badge_class = "warning"
        color = "#ffc107"
    else:
        risk_level = "High"
        badge_class = "danger"
        color = "#dc3545"

    tips = generate_tips(risk_level, bmi, data.get("exercise_daily") == "no", all_factor_names)

    return {
        "score": score_percentage,
        "risk_level": risk_level,
        "badge_class": badge_class,
        "color": color,
        "factors": all_factor_names,
        "top_factors": top_3_factors,
        "tips": tips
    }

def generate_tips(risk_level, bmi, lacks_exercise, factors):
    """Generates 3-5 personalized lifestyle and clinical recommendations."""
    tips = []

    if risk_level in ["Medium", "High"] or (bmi and bmi >= 25):
        tips.append("Adopt a balanced low-glycemic diet: minimize refined carbohydrates, white sugars, and sweetened sodas. Focus on fiber-rich whole grains, legumes, and green vegetables.")
    else:
        tips.append("Maintain clean nutrition: prioritize whole foods, healthy fats, and keep processed sugary snacks to a minimum.")

    if lacks_exercise:
        tips.append("Establish a 30-minute daily routine of brisk walking, cycling, or light aerobic activity to improve muscle glucose uptake.")
    else:
        tips.append("Keep up your active habit! Try incorporating 2 days of moderate resistance or strength training to enhance insulin sensitivity.")

    if any("thirst" in f.lower() or "urination" in f.lower() for f in factors):
        tips.append("Stay well-hydrated with pure water instead of fruit juices or energy drinks, and keep a log of daily fluid consumption.")
    else:
        tips.append("Maintain quality sleep (7-8 hours per night), as chronic sleep disruption directly elevates cortisol and blood sugar levels.")

    if risk_level == "High":
        tips.append("Schedule a medical checkup promptly: request a Fasting Blood Glucose (FBG) test and an HbA1c screening from your doctor.")
    elif risk_level == "Medium":
        tips.append("Consider consulting a healthcare provider during your next routine health check for a preventative fasting sugar test.")
    else:
        tips.append("Undergo routine annual wellness checkups to monitor blood pressure and metabolic markers.")

    return tips[:5]

def admin_required(f):
    """Decorator to require login for admin pages."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function

# ==================== ROUTES ====================

@app.route("/")
def index():
    model_acc = ml_bundle.get("accuracy", 70.1) if ml_bundle else 70.0
    best_name = ml_bundle.get("best_model_name", "Machine Learning Model") if ml_bundle else "Random Forest"
    return render_template("index.html", model_accuracy=model_acc, best_model_name=best_name)

@app.route("/quick-check", methods=["GET", "POST"])
def quick_check():
    if request.method == "POST":
        try:
            name = request.form.get("name", "Guest").strip() or "Guest"
            age = int(request.form.get("age", 25))
            gender = request.form.get("gender", "Other")
            height = float(request.form.get("height", 170))
            weight = float(request.form.get("weight", 65))

            bmi = calculate_bmi(height, weight)
            if not bmi:
                bmi = 22.5

            bmi_cat, bmi_badge, bmi_badge_color = get_bmi_category(bmi)

            data = {
                "age": age,
                "gender": gender,
                "bmi": bmi,
                "family_history": request.form.get("family_history", "no"),
                "frequent_thirst": request.form.get("frequent_thirst", "no"),
                "frequent_urination": request.form.get("frequent_urination", "no"),
                "fatigue": request.form.get("fatigue", "no"),
                "unexplained_weight_loss": request.form.get("unexplained_weight_loss", "no"),
                "slow_healing": request.form.get("slow_healing", "no"),
                "blurry_vision": request.form.get("blurry_vision", "no"),
                "exercise_daily": request.form.get("exercise_daily", "yes"),
                "high_bp": request.form.get("high_bp", "no")
            }

            result = compute_questionnaire_score(data)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

            # Store in SQLite
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("""
                    INSERT INTO assessments 
                    (timestamp, assessment_type, user_name, age, gender, bmi, risk_score, risk_level, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    now_str,
                    "Quick Check (Questionnaire)",
                    name,
                    age,
                    gender,
                    bmi,
                    result["score"],
                    result["risk_level"],
                    ", ".join(result["factors"]) if result["factors"] else "None reported"
                ))
                conn.commit()
                conn.close()
            except Exception as db_err:
                print(f"[!] Database log error: {db_err}")

            # Store current assessment in session for PDF download
            session["last_assessment"] = {
                "name": name,
                "age": age,
                "gender": gender,
                "bmi": bmi,
                "bmi_category": bmi_cat,
                "score": result["score"],
                "risk_level": result["risk_level"],
                "factors": result["factors"],
                "top_factors": result["top_factors"],
                "tips": result["tips"],
                "timestamp": now_str,
                "assessment_type": "Quick Lifestyle Check"
            }

            # Retrieve Diet & Exercise plan for this risk level
            plan_data = PLANS.get(result["risk_level"], PLANS["Low"])

            return render_template(
                "result.html",
                name=name,
                mode="Quick Lifestyle & Symptom Check",
                age=age,
                gender=gender,
                bmi=bmi,
                bmi_cat=bmi_cat,
                bmi_badge=bmi_badge,
                bmi_badge_color=bmi_badge_color,
                score=result["score"],
                risk_level=result["risk_level"],
                badge_class=result["badge_class"],
                color=result["color"],
                factors=result["factors"],
                top_factors=result["top_factors"],
                tips=result["tips"],
                plan_data=plan_data
            )
        except Exception as e:
            flash(f"Error processing questionnaire: {str(e)}", "danger")
            return redirect(url_for("quick_check"))

    return render_template("questionnaire.html")

@app.route("/detailed-check", methods=["GET", "POST"])
def detailed_check():
    if request.method == "POST":
        try:
            name = request.form.get("name", "Guest").strip() or "Guest"
            age = int(request.form.get("age", 30))
            gender = request.form.get("gender", "Female")
            height = float(request.form.get("height", 165))
            weight = float(request.form.get("weight", 65))
            bmi = calculate_bmi(height, weight) or 24.0
            bmi_cat, bmi_badge, bmi_badge_color = get_bmi_category(bmi)

            pregnancies = int(request.form.get("pregnancies", 0))
            if gender == "Male":
                pregnancies = 0

            glucose = float(request.form.get("glucose", 100))
            bp = float(request.form.get("bp", 70))
            skin = float(request.form.get("skin_thickness", 20))
            insulin = float(request.form.get("insulin", 80))
            pedigree = float(request.form.get("pedigree", 0.35))

            if ml_bundle is not None:
                model = ml_bundle["model"]
                scaler = ml_bundle["scaler"]
                feature_names = ml_bundle.get("feature_names", [
                    "Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"
                ])
                features_df = pd.DataFrame([[pregnancies, glucose, bp, skin, insulin, bmi, pedigree, age]], columns=feature_names)
                features_scaled = scaler.transform(features_df)
                prob = model.predict_proba(features_scaled)[0][1]
                score = round(prob * 100, 1)
            else:
                score = min(max(int((glucose - 70) * 0.7 + (bmi - 20) * 1.5), 5), 95)

            if score < 30:
                risk_level = "Low"
                badge_class = "success"
                color = "#198754"
            elif score < 65:
                risk_level = "Medium"
                badge_class = "warning"
                color = "#ffc107"
            else:
                risk_level = "High"
                badge_class = "danger"
                color = "#dc3545"

            # Derive contributing factors with weights and explanations
            scored_factors = []
            if glucose >= 126:
                scored_factors.append((35, f"Fasting Blood Glucose is {glucose} mg/dL (Diabetic Threshold)", "Plasma glucose above 126 mg/dL directly signals clinical hyperglycemia."))
            elif glucose >= 100:
                scored_factors.append((20, f"Fasting Blood Glucose is {glucose} mg/dL (Impaired Glucose)", "Glucose between 100-125 mg/dL indicates prediabetes state."))

            if bmi >= 30:
                scored_factors.append((25, f"BMI is {bmi} (Obese)", "Elevated BMI creates adipose insulin resistance, hindering cellular sugar uptake."))
            elif bmi >= 25:
                scored_factors.append((12, f"BMI is {bmi} (Overweight)", "Higher body fat stresses insulin regulation."))

            if pedigree >= 0.7:
                scored_factors.append((15, f"Genetic Pedigree Score is {pedigree}", "High pedigree function reflects strong multi-generational family inheritance."))
            elif pedigree >= 0.45:
                scored_factors.append((8, f"Genetic Pedigree Score is {pedigree}", "Moderate genetic marker indicates elevated diabetic vulnerability."))

            if bp >= 85:
                scored_factors.append((10, f"Diastolic Blood Pressure is {bp} mm Hg", "High blood pressure accelerates vascular endothelial strain common in diabetes."))

            if age >= 50:
                scored_factors.append((8, f"Age is {age} years", "Ageing reduces pancreatic beta cell replenishment."))

            scored_factors.sort(key=lambda x: x[0], reverse=True)
            top_3_factors = [
                {"name": item[1], "explanation": item[2], "weight": item[0]}
                for item in scored_factors[:3]
            ]
            all_factors = [item[1] for item in scored_factors]

            tips = generate_tips(risk_level, bmi, False, all_factors)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

            # Store in SQLite
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("""
                    INSERT INTO assessments 
                    (timestamp, assessment_type, user_name, age, gender, bmi, risk_score, risk_level, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    now_str,
                    "Detailed Lab Check (ML Model)",
                    name,
                    age,
                    gender,
                    bmi,
                    score,
                    risk_level,
                    f"Glucose: {glucose}, BP: {bp}, Insulin: {insulin}"
                ))
                conn.commit()
                conn.close()
            except Exception as db_err:
                print(f"[!] Database log error: {db_err}")

            # Store current assessment in session for PDF download
            session["last_assessment"] = {
                "name": name,
                "age": age,
                "gender": gender,
                "bmi": bmi,
                "bmi_category": bmi_cat,
                "score": score,
                "risk_level": risk_level,
                "factors": all_factors,
                "top_factors": top_3_factors,
                "tips": tips,
                "timestamp": now_str,
                "assessment_type": "Detailed Clinical Check (ML)"
            }

            plan_data = PLANS.get(risk_level, PLANS["Low"])

            return render_template(
                "result.html",
                name=name,
                mode="Detailed Clinical (Machine Learning) Check",
                age=age,
                gender=gender,
                bmi=bmi,
                bmi_cat=bmi_cat,
                bmi_badge=bmi_badge,
                bmi_badge_color=bmi_badge_color,
                score=score,
                risk_level=risk_level,
                badge_class=badge_class,
                color=color,
                factors=all_factors,
                top_factors=top_3_factors,
                tips=tips,
                plan_data=plan_data,
                is_ml=True
            )
        except Exception as e:
            flash(f"Error evaluating clinical parameters: {str(e)}", "danger")
            return redirect(url_for("detailed_check"))

    return render_template("detailed_check.html")

@app.route("/about-model")
def about_model():
    """Shows comparison between Logistic Regression, Decision Tree, and Random Forest."""
    comparison = ml_bundle.get("comparison_results", {}) if ml_bundle else {}
    best_name = ml_bundle.get("best_model_name", "Random Forest") if ml_bundle else "Random Forest"
    explanation = ml_bundle.get("explanation", "The model with highest testing accuracy and best recall balance was selected.") if ml_bundle else "Evaluated on testing split with cross-validation."
    return render_template("about_model.html", comparison=comparison, best_model_name=best_name, explanation=explanation)

@app.route("/download-report")
def download_report():
    """Generates and serves downloadable PDF report."""
    assessment = session.get("last_assessment")
    if not assessment:
        flash("No active assessment found to generate a report. Please take a test first.", "warning")
        return redirect(url_for("quick_check"))

    try:
        pdf_bytes = generate_pdf_report(assessment)
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        safe_name = assessment.get("name", "User").replace(" ", "_")
        response.headers['Content-Disposition'] = f'attachment; filename=DiaGuard_Assessment_{safe_name}.pdf'
        return response
    except Exception as e:
        flash(f"Error generating PDF report: {str(e)}", "danger")
        return redirect(url_for("quick_check"))

@app.route("/history")
def history():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM assessments ORDER BY id DESC LIMIT 50")
    records = c.fetchall()

    # Prepare timeline data for Chart.js trend line
    c.execute("SELECT id, timestamp, risk_score, user_name, risk_level FROM assessments ORDER BY id ASC LIMIT 50")
    chronological = c.fetchall()
    conn.close()

    trend_labels = [f"#{r['id']} ({r['timestamp'].split(' ')[0]})" for r in chronological]
    trend_scores = [r['risk_score'] for r in chronological]

    return render_template(
        "history.html",
        records=records,
        trend_labels=trend_labels,
        trend_scores=trend_scores
    )

@app.route("/clear-history", methods=["POST"])
def clear_history():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM assessments")
    conn.commit()
    conn.close()
    flash("Assessment history has been cleared.", "info")
    return redirect(url_for("history"))

# ==================== ADMIN DASHBOARD ====================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            flash("Welcome to the Admin Dashboard.", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid administrator credentials.", "danger")

    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("Logged out successfully.", "info")
    return redirect(url_for("admin_login"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT COUNT(*) as total FROM assessments")
    total_assessments = c.fetchone()["total"]

    c.execute("SELECT COUNT(*) as count FROM assessments WHERE risk_level = 'Low'")
    low_count = c.fetchone()["count"]

    c.execute("SELECT COUNT(*) as count FROM assessments WHERE risk_level = 'Medium'")
    med_count = c.fetchone()["count"]

    c.execute("SELECT COUNT(*) as count FROM assessments WHERE risk_level = 'High'")
    high_count = c.fetchone()["count"]

    c.execute("SELECT AVG(bmi) as avg_bmi FROM assessments WHERE bmi IS NOT NULL")
    avg_bmi_row = c.fetchone()["avg_bmi"]
    avg_bmi = round(avg_bmi_row, 1) if avg_bmi_row else 0.0

    c.execute("SELECT AVG(risk_score) as avg_score FROM assessments")
    avg_score_row = c.fetchone()["avg_score"]
    avg_score = round(avg_score_row, 1) if avg_score_row else 0.0

    c.execute("SELECT * FROM assessments ORDER BY id DESC LIMIT 20")
    recent_assessments = c.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        total=total_assessments,
        low_count=low_count,
        med_count=med_count,
        high_count=high_count,
        avg_bmi=avg_bmi,
        avg_score=avg_score,
        recent=recent_assessments
    )

# ==========================================
# INFORMATIONAL & EDUCATIONAL ROUTES
# ==========================================
@app.route("/about-diabetes")
def about_diabetes():
    """Renders the About Diabetes educational page."""
    return render_template("about_diabetes.html")

@app.route("/faq")
def faq():
    """Renders the Frequently Asked Questions (FAQ) page."""
    return render_template("faq.html")

@app.route("/about-project")
def about_project():
    """Renders the About Project details page with academic attribution."""
    return render_template("about_project.html")

@app.route("/food-consultant", methods=["GET", "POST"])
def food_consultant():
    """
    South Indian Food Consultant module.
    Recommends foods to eat more, limit, avoid, 1-day meal plans, and lifestyle tips
    based on risk level, BMI category, food type, and wellness goal.
    Auto-fills risk level and BMI category from query params or last assessment session.
    """
    last_assessment = session.get("last_assessment", {})

    # Auto-fill values priority: Form POST -> URL query args -> session last_assessment -> defaults
    selected_risk = request.args.get("risk", last_assessment.get("risk_level", "Low"))
    selected_bmi_cat = request.args.get("bmi_cat", last_assessment.get("bmi_category", "Normal"))
    selected_food_type = "Vegetarian"
    selected_goal = "Prevent diabetes"

    recommendations = None

    if request.method == "POST":
        selected_risk = request.form.get("risk_level", selected_risk)
        selected_bmi_cat = request.form.get("bmi_category", selected_bmi_cat)
        selected_food_type = request.form.get("food_type", selected_food_type)
        selected_goal = request.form.get("goal", selected_goal)

        recommendations = get_recommendations(
            risk_level=selected_risk,
            bmi_category=selected_bmi_cat,
            food_type=selected_food_type,
            goal=selected_goal
        )
    else:
        # On initial GET, if user comes directly or with auto-fill, generate initial recommendation
        recommendations = get_recommendations(
            risk_level=selected_risk,
            bmi_category=selected_bmi_cat,
            food_type=selected_food_type,
            goal=selected_goal
        )

    return render_template(
        "food_consultant.html",
        selected_risk=selected_risk,
        selected_bmi_cat=selected_bmi_cat,
        selected_food_type=selected_food_type,
        selected_goal=selected_goal,
        recommendations=recommendations
    )

# ==========================================
# CUSTOM ERROR HANDLERS (404 & 500)
# ==========================================
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)



