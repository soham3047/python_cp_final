import os
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader

os.makedirs('backend/mock_data', exist_ok=True)

class GenomicDosageDataset(Dataset):
    def __init__(self, csv_file):
        df = pd.read_csv(csv_file)
        # Drop categorical metadata labels to isolate training tensors
        self.X = torch.tensor(df.drop(columns=['patient_id', 'target_drug', 'optimal_dosage']).values, dtype=torch.float32)
        self.y = torch.tensor(df['optimal_dosage'].values, dtype=torch.float32).unsqueeze(1)

    def __len__(self): 
        return len(self.y)
        
    def __getitem__(self, idx): 
        return self.X[idx], self.y[idx]

def generate_synthetic_databases(num_samples=250):
    """Generates clinically aligned local data repositories for the Serotonin pathway."""
    np.random.seed(42)
    
    # 5 Structural Features: [Age, Weight, CYP2C19*2, CYP2C19*3, SLC6A4]
    features = [
        'age_years',
        'weight_kg',
        'rs4244285_cyp2c19_2', 
        'rs28399504_cyp2c19_3',
        'rs25531_slc6a4'
    ]
    
    # Hospital Beta (Serotonin Target Base)
    clinical = np.hstack([
        np.random.randint(18, 76, size=(num_samples, 1)),   # Age
        np.random.randint(48, 112, size=(num_samples, 1))   # Weight (kg)
    ])
    genomics = np.random.choice([0, 1, 2], size=(num_samples, 3), p=[0.65, 0.25, 0.10])
    
    matrix = np.hstack([clinical, genomics])
    df = pd.DataFrame(matrix, columns=features)
    
    df.insert(0, 'patient_id', [f'GD_SEROTONIN_{i}' for i in range(num_samples)])
    df.insert(1, 'target_drug', 'Sertraline')
    
    # Dosing formulation: Baseline 50mg, adjusted downward for variants or older age
    df['optimal_dosage'] = (
        50.0 
        - (df['rs4244285_cyp2c19_2'] * 12.5) 
        - (df['rs28399504_cyp2c19_3'] * 15.0) 
        - (df['rs25531_slc6a4'] * 7.5) 
        + (df['weight_kg'] * 0.05)
        - (df['age_years'] * 0.08)
        + np.random.normal(0, 1.0, num_samples)
    )
    
    df['optimal_dosage'] = df['optimal_dosage'].clip(lower=12.5, upper=200.0).round(2)
    
    # Save matching historical files across hospital nodes
    df.to_csv('backend/mock_data/hospital_alpha.csv', index=False)
    df.to_csv('backend/mock_data/hospital_beta.csv', index=False)
    print("✓ GenieDose backend database refreshed for Serotonin data parsing.")

def load_hospital_data(hospital_name, batch_size=16):
    csv_path = f'backend/mock_data/hospital_{hospital_name}.csv'
    if not os.path.exists(csv_path):
        generate_synthetic_databases()
    dataset = GenomicDosageDataset(csv_path)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    return DataLoader(train_dataset, batch_size=batch_size, shuffle=True), DataLoader(val_dataset, batch_size=batch_size)

if __name__ == "__main__":
    generate_synthetic_databases()