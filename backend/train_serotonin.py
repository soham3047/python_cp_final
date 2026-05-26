import os
import random
import torch
import torch.nn as nn
import torch.optim as optim

class SerotoninDosageModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(5, 16), nn.ReLU(),
            nn.Linear(16, 8), nn.ReLU(),
            nn.Linear(8, 1)
        )
    def forward(self, x):
        return self.network(x)

def execute_standalone_training():
    print("🧠 Initializing Serotonin Neural Model Weights Training Matrix...")
    random.seed(42)
    X_list, Y_list = [], []
    
    # Generate balanced sample space using the exact matrix logic
    for _ in range(500):
        age = random.randint(18, 80)
        weight = random.randint(45, 115)
        cyp2c19_2 = float(random.choice([0, 1, 2]))
        cyp2c19_3 = float(random.choice([0, 1, 2]))
        slc6a4 = float(random.choice([0, 1, 2]))
        
        target = 50.0 - (cyp2c19_2 * 12.5) - (cyp2c19_3 * 15.0) - (slc6a4 * 7.5) + (weight * 0.05) - (age * 0.08)
        target = max(12.5, min(200.0, target))
        
        X_list.append([float(age), float(weight), cyp2c19_2, cyp2c19_3, slc6a4])
        Y_list.append(target)

    X = torch.tensor(X_list, dtype=torch.float32)
    Y = torch.tensor(Y_list, dtype=torch.float32).unsqueeze(1)

    model = SerotoninDosageModel()
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.005)

    for epoch in range(1200):
        optimizer.zero_grad()
        loss = criterion(model(X), Y)
        loss.backward()
        optimizer.step()
        
    output_path = "serotonin_geniedose_model.pt"
    torch.save(model.state_dict(), output_path)
    print(f"✅ Training completed successfully! Parameters stored in: {output_path}")

if __name__ == "__main__":
    execute_standalone_training()