# 🎓 Viva & Technical Interview Notes - Diabetes Risk Prediction System

This document is prepared specifically for students to easily understand, explain, and defend the project during a viva, lab assessment, or project evaluation.

---

## 1. Project Overview & Architecture

### What is this project?
The **Diabetes Risk Prediction System** is a preventive health-informatics application that provides early diabetes risk screening through two complementary tracks:
1. **Quick Check (Questionnaire Screener)**: A 12-question non-invasive screener based on lifestyle habits, common osmotic symptoms, and family history (ideal for individuals who don't have recent lab tests).
2. **Detailed Check (Clinical Machine Learning Mode)**: Evaluates laboratory biomarkers (Glucose, Diastolic Blood Pressure, Insulin, BMI, Pedigree function, Age) using machine learning.

### Tech Stack
- **Backend**: Python 3, Flask
- **Data & ML**: Scikit-Learn, Pandas, NumPy, Joblib
- **Database**: SQLite (`assessments.db`)
- **PDF Generation**: ReportLab
- **Frontend**: HTML5, Vanilla JavaScript, CSS3, Bootstrap 5, Chart.js, Bootstrap Icons

---

## 2. Machine Learning Models & Selection ("About Model" Page)

### Dataset Used
- **Pima Indians Diabetes Database** (National Institute of Diabetes and Digestive and Kidney Diseases).
- **Instances**: 768 patient records with 8 biological feature columns and a binary outcome (0 = Non-diabetic, 1 = Diabetic).
- **Features**:
  1. `Pregnancies`: Number of times pregnant
  2. `Glucose`: Fasting plasma glucose concentration (mg/dL)
  3. `BloodPressure`: Diastolic blood pressure (mm Hg)
  4. `SkinThickness`: Triceps skin fold thickness (mm)
  5. `Insulin`: 2-Hour serum insulin (mu U/ml)
  6. `BMI`: Body mass index ($kg/m^2$)
  7. `DiabetesPedigreeFunction`: Genetic risk score based on family history
  8. `Age`: Age in years

### Handling Biological Zeros (Missing Data)
In attributes like Glucose, Blood Pressure, Skin Thickness, Insulin, and BMI, a recorded value of `0` is physiologically impossible for a living human.
- **Handling**: These `0`s represent missing data. We replace them with `NaN` and impute them with the **column median**, which prevents outlier skewness compared to the mean.
- **Feature Scaling**: Numerical features are standardized using `StandardScaler` ($z = \frac{x - \mu}{\sigma}$) so features with large scales (e.g., Insulin) do not dominate those with smaller scales (e.g., Pedigree).

### The Three Compared Models
We train and compare three distinct algorithmic families:
1. **Logistic Regression**: Linear boundary model mapping weighted inputs to a sigmoid probability curve. Quick and interpretable baseline.
2. **Decision Tree**: Non-linear tree model that recursively splits features based on information gain (Gini impurity). Easily readable rule paths.
3. **Random Forest Classifier**: Ensemble of multiple decision trees trained with bootstrap bagging and feature subsampling.

### Performance Comparison & Metrics
- **Accuracy**: $\frac{TP + TN}{TP + TN + FP + FN}$ (Overall correctness)
- **Precision**: $\frac{TP}{TP + FP}$ (Out of all predicted positive, how many are truly diabetic)
- **Recall (Sensitivity)**: $\frac{TP}{TP + FN}$ (Out of all actual diabetic cases, how many did the model catch)
- **Confusion Matrix**:
  - $TN$: True Negatives (Healthy predicted as Healthy)
  - $FP$: False Positives (Healthy predicted as Diabetic)
  - $FN$: False Negatives (Diabetic predicted as Healthy - *clinically most dangerous*)
  - $TP$: True Positives (Diabetic predicted as Diabetic)

### Why the Best Model is Auto-Selected
The system evaluates all three models on the same stratified test split (20% test size). The model that balances top overall accuracy while maximizing **Recall** (to minimize false negatives in a medical screening context) is automatically chosen and saved as `model/model.pkl`. A plain-English explanation is generated and displayed on the `/about-model` page.

---

## 3. How BMI is Calculated and Categorized

### Formula
$$BMI = \frac{\text{Weight in kg}}{(\text{Height in meters})^2}$$
In the questionnaire, users enter height in centimeters and weight in kilograms:
$$\text{Height in meters} = \frac{\text{Height in cm}}{100}$$

### WHO Clinical Categories
- **Underweight**: $BMI < 18.5$
- **Normal / Healthy**: $18.5 \le BMI \le 24.9$
- **Overweight**: $25.0 \le BMI \le 29.9$
- **Obese**: $BMI \ge 30.0$

### Implementation
- Both frontend (`script.js`) and backend (`app.py`) dynamically calculate this and display color-coded category badges (Underweight: grey, Normal: green, Overweight: yellow, Obese: red).

---

## 4. How Top 3 Risk Factors are Identified and Explained

### Questionnaire Mode
Each risk factor is assigned an evidence-based clinical weight (inspired by FINDRISC and ADA risk scoring):
- Severe Obesity ($BMI \ge 35$): 20 pts
- Age $\ge 65$: 15 pts | Obesity ($BMI \ge 30$): 15 pts
- Family History: 12 pts
- Fasting Glucose $\ge 126$ mg/dL (in ML check): 35 pts
- Frequent Thirst / Urination / Weight loss: 8 pts each
- Slow healing wounds: 7 pts
- Blurry vision / Fatigue: 6 pts each
- Lack of physical exercise: 5 pts
- High BP: 5 pts

**Ranking**: The system tracks all triggered factors, sorts them by their point contribution in descending order, selects the top 3, and pairs each with a plain-English explanation:
- *Example*: **BMI is 31 (Obese)** &rarr; *"High body fat mass directly drives systemic insulin resistance and elevated blood glucose."*
- *Example*: **Family history of diabetes** &rarr; *"First-degree genetic predisposition significantly increases the biological susceptibility to diabetes."*
- *Example*: **No regular daily exercise (< 30 mins)** &rarr; *"Physical inactivity reduces muscle glucose uptake independent of insulin levels."*

---

## 5. Overview of New Upgrades

1. **Top 3 Risk Factor Explanation**: Shown as distinct cards with rationale on `result.html`.
2. **Model Comparison Page (`/about-model`)**: Interactive comparison table showing Accuracy, Precision, Recall, Confusion Matrix ($TN, FP, FN, TP$), and plain-English justification for the chosen model.
3. **PDF Clinical Report Download (`/download-report`)**: Generates professional PDF reports with ReportLab containing patient vitals, BMI category, risk gauge, top 3 factors, customized tips, and the medical disclaimer.
4. **Chart.js Visualizations**:
   - Risk Percentage Semi-Doughnut Gauge on `result.html`.
   - Horizontal BMI Benchmark Chart on `result.html`.
   - Chronological Risk Score Trend Line Chart on `history.html`.
   - Risk Level Distribution Doughnut Chart on `/admin`.
5. **SQLite History with Trend Analysis (`/history`)**: Automatically logs every assessment; displays past records and visual risk trends over time.
6. **7-Day Diet & Exercise Plan with English / Tamil Toggle**:
   - Customized based on risk tier (Low / Medium / High).
   - Instant language toggle switch using `plans_data.py` dictionary.
7. **Nearby Diabetologist / Hospital Link**:
   - Automatically displayed for Medium and High risk users.
   - Plain URL: `https://www.google.com/maps/search/diabetologist+near+me` (no API key needed).
8. **Admin Dashboard (`/admin`)**:
   - Protected with session login (`/admin/login`).
   - Default credentials: `admin` / `admin123` (configurable via environment variables).
   - Displays total tests, count of Low/Medium/High, average BMI, average risk score, and audit logs.
9. **Universal Medical Disclaimer**:
   - *"This is not a medical diagnosis. Please consult a doctor."* placed prominently on every result page, footer, and in the PDF report.

---

## 6. Sample Viva Questions & Quick Answers

**Q1: Why did you not just use deep learning / neural networks?**
*Answer*: The Pima Indians Diabetes dataset has only 768 samples. Deep learning models require thousands of samples and easily overfit on small tabular datasets. Classical algorithms like Random Forest, Decision Tree, and Logistic Regression are more sample-efficient and interpretable for clinical decision support.

**Q2: What is the clinical difference between Precision and Recall here?**
*Answer*: In medical screening, **Recall** is critical because False Negatives mean telling a patient with early diabetes that they are healthy, which delays life-saving interventions. Precision matters to prevent unnecessary anxiety and lab costs, but Recall takes precedence in initial risk screening.

**Q3: How does the PDF download work without saving files on the server?**
*Answer*: The PDF is compiled dynamically in-memory using an `io.BytesIO` buffer via ReportLab and sent directly to the client with `Content-Type: application/pdf` and `Content-Disposition: attachment`.

**Q4: How does session-based history work without requiring user login?**
*Answer*: Every submission is safely committed to the local SQLite database `assessments.db` with a timestamp and user name. The active test data is kept in the Flask signed encrypted cookie `session['last_assessment']` for instant PDF generation.

---

## 7. New Pages and UI Improvements (Viva Reference)

1. **About Diabetes (`/about-diabetes`)**:
   - Provides patient health literacy on glucose metabolism, Type 1 (autoimmune lack of insulin) vs. Type 2 (insulin resistance), classical osmotic symptoms (polyuria, polydipsia), and lifestyle prevention tips.
2. **FAQ Page (`/faq`)**:
   - Addresses 6 common patient questions in an accordion format (explaining prediction accuracy, data privacy, non-replacement of clinical diagnosis, BMI relevance, high risk action, and Pima dataset training).
3. **About Project Page (`/about-project`)**:
   - Outlines the project title, core objective, problem statement on why early risk screening is useful, technology stack (Python, Flask, scikit-learn, SQLite, Bootstrap, Chart.js), Pima Indians dataset overview, 4-step prediction workflow, and key features list.
4. **"Check Again" Button**:
   - Located on `result.html` to allow instant reset and re-assessment without browser back-button caching.
5. **Interactive Question Tooltips**:
   - Provides hover and mobile-tap explanation popovers on `(i)` icons next to BMI, Family History, Hypertension, and Physical Exercise questions.
6. **Custom 404 & 500 Error Handlers**:
   - Branded error pages that gracefully handle broken URLs or unexpected server exceptions with a "Back to Home" recovery path.
7. **"Fill Sample Data" Demo Button**:
   - Accelerates live viva and examiner demos by populating representative clinical inputs in a single click while maintaining full user editability.

---

## 8. South Indian Food Consultant Module (Viva Reference)

### Q1: How does the Food Consultant work without an external API?
*Answer*: It is an entirely deterministic, **rule-based expert system**. Nutrition rules and meal profiles are decoupled into a dedicated JSON file (`food_consultant_data.json`). The Python engine `food_consultant.py` evaluates 4 input vectors:
1. **Risk Level** (`Low`, `Medium`, `High`)
2. **BMI Category** (`Underweight`, `Normal`, `Overweight`, `Obese`)
3. **Food Preference** (`Vegetarian`, `Non-vegetarian`, `Eggetarian`)
4. **Primary Goal** (`Prevent diabetes`, `Control sugar`, `Lose weight`)

### Q2: How are the food recommendations organized?
*Answer*:
1. **Foods to Eat More**: Whole grains and millets (ragi mudde, kodo/foxtail millets, brown rice), high-fiber pulses (toor dhal sambar, moong dhal, sprouted sundal), green vegetables (keerai, drumstick leaves, bitter gourd), and lean protein sources (boiled eggs, country chicken, steamed fish).
2. **Foods to Limit**: High-glycemic carbs (polished white rice, large portions of idli/dosa), coconut chutney, and sweetened filter coffee/tea.
3. **Foods to Avoid**: Saturated ghee sweets (Mysore pak, laddu, halwa, payasam), deep-fried snacks (medu vada, bajji, samosa), maida bakery goods, and sugary sodas.
4. **1-Day Meal Plan**: Distinct menus for Breakfast, Lunch, Evening Snack, and Dinner tailored specifically to the user's food type and goal.
5. **Healthy Eating Tips**: Practical guidance on portion sizing (50% vegetables, 25% protein, 25% carbs), 15-minute post-meal walks, and carbohydrate sequencing (eating fiber/protein before carbs).

### Q3: What safety mechanisms are implemented?
*Answer*:
- A prominent medical disclaimer is rendered on every request: *"This is general diet guidance, not a medical prescription. Please consult a doctor or dietitian."*
- If the risk level is **High**, a red critical alert instructs the user to consult a doctor or clinical dietitian before altering their diet.

---

## 9. Site-Wide Dark / Light Mode Toggle (Viva Reference)

### Q1: How is the theme toggle implemented across the entire application?
*Answer*:
1. **Bootstrap 5.3 Color Modes**: Uses the standard `data-bs-theme="light"` or `data-bs-theme="dark"` attribute on the `<html>` root element.
2. **CSS Custom Properties (Variables)**: Rather than hard-coding hex values, UI elements consume semantic variables (`--bg-page`, `--bg-surface`, `--text-primary`, `--border-color`, `--primary-color`). Switching `data-bs-theme` automatically updates every variable simultaneously with a smooth 0.2s transition.
3. **Flash Prevention (Anti-Flash)**: An inline script placed at the top of `<head>` immediately inspects `localStorage` or `window.matchMedia('(prefers-color-scheme: dark)')` and sets `data-bs-theme` before CSS rendering, preventing any white flashes on page loads.
4. **Dynamic Chart.js Re-rendering**: When the toggle is clicked, an event handler updates `Chart.defaults.color`, grid lines, axes, and active chart instances on-the-fly without requiring a full page refresh.
5. **Print & PDF Isolation**: Print media queries (`@media print`) and the ReportLab Python PDF generator enforce clean light backgrounds, ensuring printed documentation and downloaded PDF reports are unaffected by dark mode.




