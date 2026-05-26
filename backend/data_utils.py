import os
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader

os.makedirs('backend/mock_data', exist_ok=True)

class GenomicDosageDataset(Dataset):
    def __init__(self, csv_file):
        df = pd.read_csv(csv_file)
        # Drop metadata columns to isolate mathematical features
        self.X = torch.tensor(df.drop(columns=['patient_id', 'target_drug', 'optimal_dosage']).values, dtype=torch.float32)
        self.y = torch.tensor(df['optimal_dosage'].values, dtype=torch.float32).unsqueeze(1)

    def __len__(self): return len(self.y)
    def __getitem__(self, idx): return self.X[idx], self.y[idx]

def generate_synthetic_databases(num_samples=250):
    """Generates clinically relevant local databases for specific drug classes."""
    np.random.seed(42)
    
    # Concrete genetic features mapped to CPIC guidelines
    # 0 = Normal/Wild Type, 1 = Heterozygous Variant, 2 = Homozygous Mutant
    features = [
        'cyp2c9_mutations',   # Warfarin clearance pathway
        'vkorc1_variant',     # Warfarin sensitivity pathway
        'cyp2c19_mutations',  # SSRI Antidepressant pathway
        'cyp2d6_mutations',   # Tricyclic Antidepressant pathway
        'dpyd_mutations',
        'cyp3a5_expresser',   # Tacrolimus pathway
        'age_years',          # Clinical baseline feature 1
        'weight_kg',          # Clinical baseline feature 2
        'liver_function_score',# Clinical baseline feature 3
        'kidney_filtration',  # Clinical baseline feature 4
        'concurrent_nsaids'   # Drug-drug interaction feature
    ]
    
    # --- HOSPITAL ALPHA: WARFARIN COHORT (Cardiovascular Specialty) ---
    alpha_data = np.random.randint(0, 3, size=(num_samples, 5)) # Genetic tokens
    alpha_clinical = np.hstack([
        np.random.randint(45, 85, size=(num_samples, 1)),   # Older age demographic
        np.random.randint(55, 110, size=(num_samples, 1)),  # Weight range
        np.random.uniform(0.6, 1.4, size=(num_samples, 2)), # Liver/Kidney indicators
        np.random.randint(0, 2, size=(num_samples, 1))      # NSAID flags
    ])
    alpha_combined = np.hstack([alpha_data, alpha_clinical])
    alpha_df = pd.DataFrame(alpha_combined, columns=features)
    alpha_df.insert(0, 'patient_id', [f'CARD_WARFARIN_{i}' for i in range(num_samples)])
    alpha_df.insert(1, 'target_drug', 'Warfarin')
    
    # Warfarin Mathematical Dosage Rule: VKORC1 variants drastically suppress required dosage concentrations
    alpha_df['optimal_dosage'] = 5.0 - (alpha_df['vkorc1_variant'] * 1.8) - (alpha_df['cyp2c9_mutations'] * 0.9) + (alpha_df['weight_kg'] * 0.03) + np.random.normal(0, 0.2, num_samples)
    # Clip values to ensure medical realism (minimum dosage threshold)
    alpha_df['optimal_dosage'] = alpha_df['optimal_dosage'].clip(lower=0.5)
    alpha_df.to_csv('backend/mock_data/hospital_alpha.csv', index=False)

    # --- HOSPITAL BETA: ANTIDEPRESSANT COHORT (Psychiatric Care Center) ---
    beta_data = np.random.randint(0, 3, size=(num_samples, 5))
    beta_clinical = np.hstack([
        np.random.randint(18, 60, size=(num_samples, 1)),   # Younger age demographic
        np.random.randint(50, 95, size=(num_samples, 1)),   # Weight range
        np.random.uniform(0.8, 1.2, size=(num_samples, 2)), # Functional indicators
        np.random.randint(0, 2, size=(num_samples, 1))
    ])
    beta_combined = np.hstack([beta_data, beta_clinical])
    beta_df = pd.DataFrame(beta_combined, columns=features)
    beta_df.insert(0, 'patient_id', [f'PSYCH_SERTRAINE_{i}' for i in range(num_samples)])
    beta_df.insert(1, 'target_drug', 'Sertraline')
    
    # Antidepressant Mathematical Dosage Rule: High mutations in cyp2c19 mean poor clearance = accumulate toxically = lower dose
    beta_df['optimal_dosage'] = 50.0 - (beta_df['cyp2c19_mutations'] * 15.0) + (beta_df['age_years'] * 0.2) + np.random.normal(0, 2.0, num_samples)
    beta_df['optimal_dosage'] = beta_df['optimal_dosage'].clip(lower=12.5)
    beta_df.to_csv('backend/mock_data/hospital_beta.csv', index=False)
    
    print("✓ Clinical genomic databases successfully re-populated for Warfarin & Sertraline!")

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