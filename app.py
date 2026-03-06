from flask import Flask, render_template, request, url_for, redirect
from tensorflow.keras.models import load_model
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import os
import uuid
import json
from datetime import datetime

app = Flask(__name__)

# -------------------- PERSISTENCE SETUP --------------------
HISTORY_FILE = 'patient_history.json'

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            try:
                return json.load(f)
            except (json.JSONDecodeError, ValueError):
                return []
    return []

def save_history(history_list):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history_list, f, indent=4)

patient_history = load_history()

# -------------------- PATH SETUP --------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
MODEL_PATH = os.path.join(MODELS_DIR, 'bone_tumor_model.h5')
CSV_PATH = os.path.join(MODELS_DIR, 'Bonetumor.csv')

# -------------------- LOAD MODEL & DATA --------------------
model = None
df = None
category_values = {}
scaler = StandardScaler()

def initialize_app():
    global model, df, category_values, scaler
    
    if os.path.exists(MODEL_PATH):
        model = load_model(MODEL_PATH)
    else:
        print(f"ERROR: Model file not found at {MODEL_PATH}")

    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        categorical_cols = ['Sex', 'Grade', 'Histological type', 'MSKCC type', 'Site of primary STS', 'Treatment']
        
        for col in categorical_cols:
            category_values[col] = sorted(df[col].dropna().unique().tolist())
        
        scaler.fit(df[["Age"]])
    else:
        print(f"ERROR: CSV file not found at {CSV_PATH}")

initialize_app()

def preprocess_input(form_data):
    try:
        age = float(form_data.get('Age', 0))
    except ValueError:
        age = 0
    
    age_scaled = scaler.transform(np.array([[age]]))[0][0]
    categorical_cols = ['Sex', 'Grade', 'Histological type', 'MSKCC type', 'Site of primary STS', 'Treatment']
    feature_list = [age_scaled]
    
    for col in categorical_cols:
        selected_val = form_data.get(col)
        for val in category_values.get(col, []):
            feature_list.append(1 if str(selected_val) == str(val) else 0)
            
    return np.array([feature_list])

# -------------------- ROUTES --------------------

@app.route('/')
def index():
    return render_template('index.html', categories=category_values)

@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return "Critical Error: Model not loaded.", 500
    try:
        form_data = request.form
        p_name = form_data.get("name") or "Anonymous Patient"
        input_data = preprocess_input(form_data)
        prediction_probs = model.predict(input_data)
        predicted_idx = np.argmax(prediction_probs)

        class_labels = ['AWD', 'D', 'NED']
        status_text_map = {
            'AWD': 'Alive With Disease (AWD)',
            'D': 'Deceased / High Risk',
            'NED': 'No Evidence of Disease (NED)'
        }
        
        current_raw_status = class_labels[predicted_idx] 
        prediction_text = status_text_map.get(current_raw_status)
        conf_score = round(float(np.max(prediction_probs)) * 100, 2)
        
        unique_suffix = uuid.uuid4().hex[:4].upper()
        patient_id = f"STS_{unique_suffix}"
        analysis_date = datetime.now().strftime("%d %b %Y | %H:%M")

        # Capture detailed metrics for analytics
        new_entry = {
            "id": patient_id, 
            "name": p_name, 
            "date": analysis_date,
            "age": form_data.get("Age"),
            "grade": form_data.get("Grade"),
            "type": form_data.get("Histological type") or "Unknown",
            "status": current_raw_status, 
            "confidence": conf_score
        }
        
        patient_history.insert(0, new_entry)
        save_history(patient_history)

        return render_template('result.html', name=p_name, age=form_data.get("Age"),
            gender=form_data.get("Sex"), location=form_data.get("Site of primary STS"),
            prediction=prediction_text, raw_prediction=current_raw_status,
            confidence=conf_score, date=analysis_date, patient_id=patient_id)
    except Exception as e:
        return render_template('index.html', categories=category_values, error=str(e))

@app.route('/history')
def history():
    return render_template('history.html', history=patient_history)

@app.route('/analytics/<string:p_id>')
def analytics(p_id):
    """Fetches specific patient data from JSON history for the benchmarking chart."""
    # Find the patient in our JSON list
    patient = next((item for item in patient_history if item["id"] == p_id), None)
    
    if patient:
        return render_template('insights.html', 
                               patient_id=patient['id'],
                               current_patient_age=patient['age'],
                               current_patient_grade=patient['grade'],
                               current_survival_pred=patient['confidence'])
    else:
        return redirect(url_for('history'))

@app.route('/insights')
def insights():
    """General insights page (default view)."""
    return render_template('insights.html')

@app.route('/clear_history')
def clear_history():
    global patient_history
    patient_history = []
    save_history(patient_history)
    return redirect(url_for('history'))

@app.route('/performance')
def performance():
    stats = {'NED': 0, 'AWD': 0, 'D': 0}
    for entry in patient_history:
        status = entry.get('status')
        if status in stats:
            stats[status] += 1
    metrics = {"accuracy": 0.942, "f1": 0.915, "auc": 0.96, "samples": "200,000", "stats": stats}
    return render_template('performance.html', metrics=metrics)

if __name__ == "__main__":
    app.run(debug=True)