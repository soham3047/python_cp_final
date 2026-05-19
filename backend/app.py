import os
import sys

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

if __name__ == "__main__":
    print("🌍 GenieDose Flask Server launching on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)