import os
import torch
import torch.nn as nn
import torch.optim as optim
import random

# ─────────────────────────────────────────────────────────────
# 1. CARBAMAZEPINE NEURAL ARCHITECTURE
# ─────────────────────────────────────────────────────────────
class CarbamazepineDosageModel(nn.Module):
    """
    Accepts 3 clear continuous/discrete input features:
    - Feature 0: Age (Years)
    - Feature 1: Weight (Kg)
    - Feature 2: HLA-B*15:02 Variant genotype status mapped to 0.0, 1.0, or 2.0
    """
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(3, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1)
        )
    def forward(self, x):
        return self.network(x)

# ─────────────────────────────────────────────────────────────
# 2. SEEDED SYNTHETIC CLINICAL DATA RUNTIME TRAINER
# ─────────────────────────────────────────────────────────────
def run_carbamazepine_training():
    """
    Generates a highly localized cohort modeling Indian demographic sets,
    trains the neural network architecture, and generates a solid state dict binary.
    """
    print("🧬 [GenieDose ML] Initializing Carbamazepine Cohort Simulation Training...")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    weights_save_path = os.path.join(BASE_DIR, "carbamazepine_geniedose_model.pt")
    
    # Generate balanced synthetic healthcare instances
    inputs = []
    targets = []
    
    for _ in range(1200):
        age = random.uniform(18, 75)
        weight = random.uniform(45, 95)
        # Model higher distribution of HLA-B*15:02 variants common in specific South Asian sets
        hla_status = random.choice([0.0, 0.0, 0.0, 1.0, 2.0]) 
        
        if hla_status > 0:
            # Contraindicated cases target a safety default baseline zero ceiling value
            ideal_dosage = 0.0
        else:
            # Baseline algorithmic titration: dose increases with weight, decreases with age
            ideal_dosage = 400.0 + (weight * 2.1) - (age * 0.65) + random.uniform(-25, 25)
            ideal_dosage = max(200.0, min(1200.0, ideal_dosage))
            
        inputs.append([age, weight, hla_status])
        targets.append([ideal_dosage])

    # Convert to standard PyTorch tensors
    X_train = torch.tensor(inputs, dtype=torch.float32)
    y_train = torch.tensor(targets, dtype=torch.float32)

    # Initialize model, loss criteria, and Adam optimizer
    model = CarbamazepineDosageModel()
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.01)

    # Train loop execution until stability convergence boundaries are met
    model.train()
    epochs = 150
    for epoch in range(epochs):
        optimizer.zero_grad()
        predictions = model(X_train)
        loss = criterion(predictions, y_train)
        loss.backward()
        optimizer.step()
        
        if (epoch + 1) % 50 == 0:
            print(f"   ↳ Epoch {epoch+1}/{epochs} - Convergence Loss Matrix: {round(loss.item(), 4)}")

    # Save finalized model binary
    torch.save(model.state_dict(), weights_save_path)
    print(f"✅ [GenieDose ML] Training complete. Optimized weights saved to: {weights_save_path}")

if __name__ == "__main__":
    run_carbamazepine_training()