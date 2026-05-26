import os
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader

# 1. MATCH YOUR ARCHITECTURE (From model.py / app.py)
class DosagePredictionModel(nn.Module):
    def __init__(self, input_dim=11):
        super(DosagePredictionModel, self).__init__()
        self.fc1 = nn.Linear(input_dim, 32)
        self.fc2 = nn.Linear(32, 16)
        self.fc3 = nn.Linear(16, 1)

    def forward(self, x):
        import torch.nn.functional as F
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)

# 2. MATCH YOUR DATA LAYOUT (From data_utils.py)
class LocalHospitalDataset(Dataset):
    def __init__(self, df):
        # Drop columns matching your data_utils.py structure
        X_raw = df.drop(columns=['patient_id', 'target_drug', 'optimal_dosage'], errors='ignore').values
        self.X = torch.tensor(X_raw, dtype=torch.float32)
        self.y = torch.tensor(df['optimal_dosage'].values, dtype=torch.float32).unsqueeze(1)

    def __len__(self): 
        return len(self.y)
        
    def __getitem__(self, idx): 
        return self.X[idx], self.y[idx]

# 3. GENERATE MOCK HOSPITALS DATA (Python 3.14 Compatible)
def create_mock_hospital_data():
    np.random.seed(42)
    num_samples = 200
    features = ['age_years', 'weight_kg', 'rs4244285_cyp2c19_2', 'rs28399504_cyp2c19_3', 'rs25531_slc6a4']
    
    hospitals = {}
    for name in ['Hospital_Alpha', 'Hospital_Beta', 'Hospital_Gamma']:
        clinical = np.hstack([
            np.random.randint(18, 76, size=(num_samples, 1)),   # Age
            np.random.randint(48, 112, size=(num_samples, 1))   # Weight
        ])
        genomics = np.random.choice([0, 1, 2], size=(num_samples, 3), p=[0.65, 0.25, 0.10])
        matrix = np.hstack([clinical, genomics])
        
        # Expand columns to match 11-dim architecture expectations if needed
        # padded to 11 columns to match DosagePredictionModel(input_dim=11)
        padding = np.zeros((num_samples, 6)) 
        full_matrix = np.hstack([matrix, padding])
        
        df = pd.DataFrame(full_matrix, columns=[f'f_{i}' for i in range(11)])
        df.insert(0, 'patient_id', f'GD_{name}_')
        df.insert(1, 'target_drug', 'Sertraline')
        
        # Semi-deterministic targets matching your rule bounds
        df['optimal_dosage'] = 50.0 + (df['f_1'] * 0.05) - (df['f_0'] * 0.08)
        hospitals[name] = df
        
    return hospitals

# 4. FEDERATED AGGREGATION ENGINE (FedAvg Algorithm)
def federated_average(global_model, client_models):
    """Averages parameters across client models directly into the global model."""
    global_dict = global_model.state_dict()
    for key in global_dict.keys():
        if global_dict[key].data.dtype == torch.float32:
            client_weights = [client.state_dict()[key].data for client in client_models]
            global_dict[key].data.copy_(torch.stack(client_weights).mean(dim=0))
    global_model.load_state_dict(global_dict)

# 5. SIMULATION EXECUTION LOOP WITH GRAPH METRICS
def run_federated_simulation(num_rounds=5, local_epochs=3):
    print("🚀 Initializing Ray-less Python 3.14 Federated Engine...")
    
    hospital_data = create_mock_hospital_data()
    global_model = DosagePredictionModel(input_dim=11)
    criterion = nn.MSELoss()
    
    # Track metrics for real-time validation visual plots
    history = {name: [] for name in hospital_data.keys()}
    history['Global_Loss'] = []

    for round_idx in range(1, num_rounds + 1):
        print(f"\n--- 🔄 Federated Round {round_idx}/{num_rounds} ---")
        client_models = []
        round_losses = []

        for name, df in hospital_data.items():
            # Clone global parameters down to the node client
            local_model = DosagePredictionModel(input_dim=11)
            local_model.load_state_dict(global_model.state_dict())
            local_model.train()
            
            optimizer = optim.Adam(local_model.parameters(), lr=0.01)
            loader = DataLoader(LocalHospitalDataset(df), batch_size=16, shuffle=True)
            
            # Local Hospital Site Training
            epoch_loss = 0.0
            for epoch in range(local_epochs):
                for X_batch, y_batch in loader:
                    optimizer.zero_grad()
                    loss = criterion(local_model(X_batch), y_batch)
                    loss.backward()
                    optimizer.step()
                    epoch_loss += loss.item()
            
            avg_loss = epoch_loss / len(loader)
            history[name].append(avg_loss)
            round_losses.append(avg_loss)
            print(f"   🏥 {name} completed local updates. Final Loss: {avg_loss:.4f}")
            client_models.append(local_model)
            
        # Perform server-side weight aggregation (FedAvg)
        federated_average(global_model, client_models)
        history['Global_Loss'].append(sum(round_losses) / len(round_losses))
        print(f"  🧠 Server consolidated global weights. Aggregated Loss: {history['Global_Loss'][-1]:.4f}")

    # 6. GENERATE TRAINING SIMULATION METRICS GRAPH
    print("\n📊 Training complete. Rendering Federated Metrics Chart...")
    plt.figure(figsize=(10, 6))
    rounds = list(range(1, num_rounds + 1))
    
    for name in hospital_data.keys():
        plt.plot(rounds, history[name], marker='o', linestyle='--', label=f'{name} (Local)')
        
    plt.plot(rounds, history['Global_Loss'], marker='s', color='black', linewidth=2.5, label='Consolidated Global Model')
    
    plt.title('GenieDose Federated Learning Convergence Simulation', fontsize=14, fontweight='bold')
    plt.xlabel('Federated Communication Rounds', fontsize=12)
    plt.ylabel('Mean Squared Error (Loss)', fontsize=12)
    plt.xticks(rounds)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(fontsize=11)
    
    # Save chart cleanly to file directory matching your assets
    output_graph_path = "federated_training_graph.png"
    plt.savefig(output_graph_path, dpi=300, bbox_inches='tight')
    print(f"✅ Simulation metrics chart written successfully: '{output_graph_path}'")
    plt.show()

    # Save the consolidated parameters to disk matching your app.py lookup 
    torch.save(global_model.state_dict(), "federated_geniedose_model.pt")
    print("💾 Saved system state matrix checkpoint -> 'federated_geniedose_model.pt'")

if __name__ == "__main__":
    run_federated_simulation(num_rounds=5, local_epochs=3)