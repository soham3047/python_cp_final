import torch
import torch.nn as nn
import os

# Define the updated 6-feature architecture matching your new app.py
class ClinicalDosageModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(6, 16), nn.ReLU(),
            nn.Linear(16, 8), nn.ReLU(),
            nn.Linear(8, 1)
        )
    def forward(self, x):
        return self.network(x)

def transplant_weights():
    model_path = "global_geniedose_model.pt"
    
    if not os.path.exists(model_path):
        print(f"❌ Error: Could not find '{model_path}'!")
        return

    # 1. Load your trained 5-feature weights safely
    print("🧠 Extracting your trained Warfarin & Antidepressant weights...")
    old_state = torch.load(model_path, weights_only=True)
    
    # 2. Instantiate the new 6-feature template
    new_model = ClinicalDosageModel()
    new_state = new_model.state_dict()
    
    # 3. SURGERY: Extract old weights
    old_input_weights = old_state["network.0.weight"]  # Shape: (16, 5)
    old_input_bias = old_state["network.0.bias"]      # Shape: (16,)
    
    # Copy old 5-feature weights into the first 5 slots of the new 6-slot matrix
    new_state["network.0.weight"][:, :5] = old_input_weights
    # Set the 6th slot (5-FU/DPYD) to 0.0 so it doesn't alter current outputs
    new_state["network.0.weight"][:, 5] = 0.0
    # Keep the original trained bias completely intact
    new_state["network.0.bias"] = old_input_bias
    
    # 4. Copy all deeper trained hidden layers perfectly (shapes match)
    new_state["network.2.weight"] = old_state["network.2.weight"]
    new_state["network.2.bias"] = old_state["network.2.bias"]
    new_state["network.4.weight"] = old_state["network.4.weight"]
    new_state["network.4.bias"] = old_state["network.4.bias"]
    
    # 5. Overwrite the file with the upgraded version
    torch.save(new_state, model_path)
    print("✅ Model Surgery Successful!")
    print("🎯 Warfarin & Antidepressant memory preserved. 6th slot added for Chemo (5-FU).")

if __name__ == "__main__":
    transplant_weights()