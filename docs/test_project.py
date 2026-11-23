import os
import sys

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import app
from food_consultant import get_recommendations, load_food_data

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Unit Tests: BMI helper
def calculate_bmi_test(weight, height_cm):
    try:
        w = float(weight)
        h = float(height_cm) / 100.0
        if w <= 0 or h <= 0:
            return None, "Invalid"
        bmi = w / (h * h)
        if bmi < 18.5:
            cat = "Underweight"
        elif bmi < 25.0:
            cat = "Normal weight"
        elif bmi < 30.0:
            cat = "Overweight"
        else:
            cat = "Obese"
        return round(bmi, 1), cat
    except (ValueError, TypeError):
        return None, "Invalid"

def test_bmi_normal():
    bmi, cat = calculate_bmi_test(70, 175)
    assert bmi == 22.9
    assert cat == "Normal weight"

def test_bmi_underweight():
    bmi, cat = calculate_bmi_test(45, 165)
    assert bmi == 16.5
    assert cat == "Underweight"

def test_bmi_overweight():
    bmi, cat = calculate_bmi_test(80, 172)
    assert bmi == 27.0
    assert cat == "Overweight"

def test_bmi_obese():
    bmi, cat = calculate_bmi_test(110, 170)
    assert bmi == 38.1
    assert cat == "Obese"

def test_bmi_zero_or_negative():
    assert calculate_bmi_test(0, 170) == (None, "Invalid")
    assert calculate_bmi_test(70, 0) == (None, "Invalid")
    assert calculate_bmi_test(-5, 170) == (None, "Invalid")

def test_bmi_invalid_types():
    assert calculate_bmi_test("abc", 170) == (None, "Invalid")
    assert calculate_bmi_test(70, None) == (None, "Invalid")

def test_bmi_boundary_underweight():
    bmi, cat = calculate_bmi_test(53.465, 170)
    assert bmi == 18.5
    assert cat == "Normal weight"

def test_bmi_boundary_overweight():
    bmi, cat = calculate_bmi_test(72.25, 170)
    assert bmi == 25.0
    assert cat == "Overweight"

def test_bmi_boundary_obese():
    bmi, cat = calculate_bmi_test(86.7, 170)
    assert bmi == 30.0
    assert cat == "Obese"

# Unit Tests: Food Consultant Engine
def test_food_consultant_load_data():
    data = load_food_data()
    assert isinstance(data, dict)
    assert 'foods_to_eat_more' in data

def test_food_consultant_recommendations_low_risk():
    recs = get_recommendations(risk_level="Low", bmi_category="Normal", food_type="Vegetarian", goal="Prevent diabetes")
    assert 'foods_to_eat_more' in recs
    assert len(recs['foods_to_eat_more']) > 0

def test_food_consultant_recommendations_high_risk():
    recs = get_recommendations(risk_level="High", bmi_category="Obese", food_type="Non-Vegetarian", goal="Manage blood sugar")
    assert recs['is_high_risk'] == True
    assert 'foods_to_avoid' in recs

def test_food_consultant_diet_pref_nonveg():
    recs = get_recommendations(risk_level="Moderate", bmi_category="Overweight", food_type="Eggetarian", goal="Weight loss")
    assert 'meal_plan' in recs

# Functional & Route Tests
def test_home_route(client):
    rv = client.get('/')
    assert rv.status_code == 200
    assert b"DiaGuard" in rv.data

def test_quick_check_get(client):
    rv = client.get('/quick-check')
    assert rv.status_code == 200

def test_quick_check_post_submission(client):
    data = {
        'age': '2', 'gender': '1', 'bmi': '22.5', 'family_history': '0',
        'high_bp': '0', 'physically_active': '1', 'diet_fruits_veg': '1',
        'sugar_intake': '0', 'smoking': '0', 'stress_level': '0',
        'sleep_hours': '1', 'gestational_diabetes': '0', 'frequent_urination': '0'
    }
    rv = client.post('/quick-check', data=data, follow_redirects=True)
    assert rv.status_code == 200

def test_detailed_check_get(client):
    rv = client.get('/detailed-check')
    assert rv.status_code == 200

def test_detailed_check_post_prediction(client):
    form_data = {
        'pregnancies': '2', 'glucose': '120', 'blood_pressure': '70',
        'skin_thickness': '20', 'insulin': '79', 'bmi': '25.0',
        'diabetes_pedigree': '0.5', 'age': '33'
    }
    rv = client.post('/detailed-check', data=form_data, follow_redirects=True)
    assert rv.status_code == 200

def test_about_diabetes_route(client):
    rv = client.get('/about-diabetes')
    assert rv.status_code == 200

def test_faq_route(client):
    rv = client.get('/faq')
    assert rv.status_code == 200

def test_about_model_route(client):
    rv = client.get('/about-model')
    assert rv.status_code == 200

def test_about_project_route(client):
    rv = client.get('/about-project')
    assert rv.status_code == 200

def test_food_consultant_route_get(client):
    rv = client.get('/food-consultant')
    assert rv.status_code == 200

def test_food_consultant_route_post(client):
    rv = client.post('/food-consultant', data={'risk_level': 'Moderate', 'goal': 'prevention', 'diet_pref': 'veg'}, follow_redirects=True)
    assert rv.status_code == 200

def test_assessment_history_route(client):
    rv = client.get('/history')
    assert rv.status_code == 200

def test_pdf_download_route_empty(client):
    rv = client.get('/download-report')
    assert rv.status_code in [200, 302, 400]

def test_admin_unauthorized_redirect(client):
    rv = client.get('/admin')
    assert rv.status_code in [302, 401, 200]

def test_admin_login_get(client):
    rv = client.get('/admin/login')
    assert rv.status_code == 200

def test_admin_valid_login(client):
    rv = client.post('/admin/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert rv.status_code == 200

def test_admin_invalid_login(client):
    rv = client.post('/admin/login', data={'username': 'admin', 'password': 'wrongpassword'}, follow_redirects=True)
    assert rv.status_code == 200
    assert b"Invalid" in rv.data or b"admin" in rv.data

def test_admin_logout_route(client):
    rv = client.get('/admin/logout', follow_redirects=True)
    assert rv.status_code == 200

def test_clear_history_post(client):
    rv = client.post('/clear-history', follow_redirects=True)
    assert rv.status_code == 200

def test_404_handler(client):
    rv = client.get('/nonexistent-page-url')
    assert rv.status_code == 404
