import os
import sys

import torch
from flask import request

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS



# Dynamic path injection to fix the 'No module named backend' error
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Prevent global tensorflow/tensorboard imports from throwing compatibility errors
sys.modules['tensorflow'] = None
sys.modules['tensorboard'] = None

# Initialize Flask app pointing to the frontend folder for static assets
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
CORS(app) # Allow cross-origin requests

@app.route('/')
def serve_index():
    """Serves the main dashboard page."""
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/run-simulation', methods=['POST'])
def trigger_simulation():
    """API endpoint that triggers the federated learning engine process."""
    try:
        # Import internally to prevent matplotlib thread blocking issues
        from backend.federated_engine import run_fl_simulation
        
        print("\n🌐 Web Dashboard requested a simulation run...")
        # Run 5 rounds of the simulation
        run_fl_simulation(num_rounds=5)
        
        return jsonify({"status": "success", "message": "Federated Learning simulation completed successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    


@app.route('/predict-dosage', methods=['POST'])
def predict_dosage():
    """Takes clinical attributes from frontend and uses the local model to predict dosage."""
    try:
        data = request.json
        drug = data.get('drug')
        mutation = float(data.get('mutation', 0))
        age = float(data.get('age', 50))
        weight = float(data.get('weight', 70))

        # Reconstruct the 10-feature array expected by model.py
        # [cyp2c9, vkorc1, cyp2c19, cyp2d6, cyp3a5, age, weight, liver, kidney, nsaids]
        feature_vector = [0.0] * 10
        
        if drug == 'warfarin':
            feature_vector[0] = mutation  # cyp2c9
            feature_vector[1] = mutation  # vkorc1
            feature_vector[5] = age
            feature_vector[6] = weight
            feature_vector[7] = 1.0       # Normal baseline liver function
            feature_vector[8] = 1.0       # Normal baseline kidney function
        else: # sertraline
            feature_vector[2] = mutation  # cyp2c19
            feature_vector[3] = mutation  # cyp2d6
            feature_vector[5] = age
            feature_vector[6] = weight
            feature_vector[7] = 1.0
            feature_vector[8] = 1.0

        # Import model blueprint dynamically
        from backend.model import DosagePredictionModel
        model = DosagePredictionModel(input_dim=10)
        
        # Pass features through network (eval mode)
        model.eval()
        with torch.no_grad():
            input_tensor = torch.tensor([feature_vector], dtype=torch.float32)
            predicted_tensor = model(input_tensor)
            calculated_dosage = float(predicted_tensor.item())

        # Format clean display units based on drug guidelines
        unit = "mg/day" if drug == 'warfarin' else "mg"
        formatted_result = f"🎯 Recommended Initial {drug.capitalize()} Dosage: {calculated_dosage:.2f} {unit}"
        
        return jsonify({"status": "success", "result": formatted_result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    print("🌍 GenieDose Flask Server launching on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)