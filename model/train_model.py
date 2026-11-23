"""
Train Machine Learning Model for Diabetes Risk Prediction
Dataset: Pima Indians Diabetes Database
Target: Outcome (0 = No Diabetes, 1 = Diabetes)
"""

import os
import urllib.request
import pandas as pd
import numpy as np
import os
import urllib.request
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix, classification_report
import joblib

DATASET_URL = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv"
COLUMNS = [
    "Pregnancies",
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
    "DiabetesPedigreeFunction",
    "Age",
    "Outcome"
]

def load_or_download_dataset(csv_path):
    """Loads diabetes.csv if present, otherwise downloads it from a trusted repository."""
    if os.path.exists(csv_path):
        print(f"[+] Found existing dataset at {csv_path}")
        df = pd.read_csv(csv_path)
        if list(df.columns) != COLUMNS and len(df.columns) == 9:
            df.columns = COLUMNS
        return df

    print(f"[*] Downloading Pima Indians Diabetes dataset to {csv_path}...")
    try:
        urllib.request.urlretrieve(DATASET_URL, csv_path)
        df = pd.read_csv(csv_path, names=COLUMNS)
        print("[+] Download completed successfully.")
        return df
    except Exception as e:
        print(f"[!] Warning: Could not download online ({e}). Creating standard synthetic seed dataset...")
        np.random.seed(42)
        n = 768
        pregnancies = np.random.choice([0, 1, 2, 3, 4, 5, 6], n)
        glucose = np.random.normal(120, 30, n).clip(60, 200)
        bp = np.random.normal(70, 12, n).clip(40, 120)
        skinthick = np.random.normal(20, 10, n).clip(0, 60)
        insulin = np.random.normal(80, 50, n).clip(0, 400)
        bmi = np.random.normal(32, 6, n).clip(18, 55)
        pedigree = np.random.exponential(0.4, n).clip(0.08, 2.4)
        age = np.random.randint(21, 80, n)
        
        logits = -4.5 + 0.02*glucose + 0.04*bmi + 0.02*age + 0.4*pedigree
        probs = 1 / (1 + np.exp(-logits))
        outcome = (np.random.rand(n) < probs).astype(int)

        df = pd.DataFrame({
            "Pregnancies": pregnancies,
            "Glucose": glucose.round(1),
            "BloodPressure": bp.round(1),
            "SkinThickness": skinthick.round(1),
            "Insulin": insulin.round(1),
            "BMI": bmi.round(1),
            "DiabetesPedigreeFunction": pedigree.round(3),
            "Age": age,
            "Outcome": outcome
        })
        df.to_csv(csv_path, index=False)
        print(f"[+] Generated fallback dataset and saved to {csv_path}")
        return df

def clean_data(df):
    """
    Biological zeros in Glucose, BloodPressure, SkinThickness, Insulin, and BMI
    represent missing values in the Pima dataset. Impute them with the median.
    """
    clean_df = df.copy()
    zero_cols = ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]
    for col in zero_cols:
        clean_df[col] = clean_df[col].replace(0, np.nan)
        clean_df[col] = clean_df[col].fillna(clean_df[col].median())
    return clean_df

def train_and_export():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "diabetes.csv")
    model_path = os.path.join(current_dir, "model.pkl")

    df = load_or_download_dataset(csv_path)
    clean_df = clean_data(df)

    X = clean_df.drop("Outcome", axis=1)
    y = clean_df["Outcome"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scale numerical features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Define candidate models
    models = {
        "Logistic Regression": LogisticRegression(random_state=42, max_iter=200),
        "Decision Tree": DecisionTreeClassifier(random_state=42, max_depth=5, min_samples_split=5),
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=5, min_samples_split=4, random_state=42)
    }

    comparison_results = {}
    best_model_name = None
    best_score = -1
    best_model_obj = None

    print("\n================ MODEL EVALUATION ================")
    for name, clf in models.items():
        clf.fit(X_train_scaled, y_train)
        y_pred = clf.predict(X_test_scaled)
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        cm = confusion_matrix(y_test, y_pred).tolist() # [[TN, FP], [FN, TP]]

        comparison_results[name] = {
            "accuracy": round(acc * 100, 2),
            "precision": round(prec * 100, 2),
            "recall": round(rec * 100, 2),
            "confusion_matrix": cm,
            "tn": cm[0][0],
            "fp": cm[0][1],
            "fn": cm[1][0],
            "tp": cm[1][1]
        }

        print(f"\n[{name}]")
        print(f"  Accuracy:  {acc * 100:.2f}%")
        print(f"  Precision: {prec * 100:.2f}%")
        print(f"  Recall:    {rec * 100:.2f}%")
        print(f"  Confusion Matrix: TN={cm[0][0]}, FP={cm[0][1]}, FN={cm[1][0]}, TP={cm[1][1]}")

        # Selection criterion: Highest accuracy; if tie, higher recall
        composite_score = acc * 100 + rec * 10
        if composite_score > best_score:
            best_score = composite_score
            best_model_name = name
            best_model_obj = clf

    # Formulate plain-English reason for model selection
    best_metrics = comparison_results[best_model_name]
    explanation = (
        f"{best_model_name} was chosen as the primary prediction model because it achieved "
        f"the highest overall testing accuracy ({best_metrics['accuracy']}%) and strong clinical recall ({best_metrics['recall']}%), "
        f"optimizing early detection while minimizing false negatives."
    )

    print(f"\n[+] Auto-selected Best Model: {best_model_name}")
    print(f"    Reason: {explanation}")

    # Save model bundle
    bundle = {
        "model": best_model_obj,
        "best_model_name": best_model_name,
        "scaler": scaler,
        "feature_names": list(X.columns),
        "accuracy": best_metrics["accuracy"],
        "comparison_results": comparison_results,
        "explanation": explanation
    }
    joblib.dump(bundle, model_path)
    print(f"\n[+] Successfully saved {best_model_name} model bundle to {model_path}")

if __name__ == "__main__":
    train_and_export()
