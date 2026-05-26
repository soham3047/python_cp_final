import argparse
import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import flwr as fl
# FIX: Imported evaluate_clinical_dosage to prevent NameError
from vcf_processing_engine import parse_vcf_genomics, evaluate_clinical_dosage

# 1. Handle command line arguments to segment the hospitals
parser = argparse.ArgumentParser(description="GenieDose Hospital Client Node")
parser.add_argument("--hospital_id", type=int, required=True, help="Must pass 1 or 2")
args = parser.parse_args()

# Clinical matrix mappings corresponding to the mock_data profiles
patients_clinical_inputs = {
    "mock_data/patient_1_normal.vcf": {"age": 45, "weight": 75},
    "mock_data/patient_2_vkorc1_sensitive.vcf": {"age": 68, "weight": 61},
    "mock_data/patient_3_cyp2c9_slow.vcf": {"age": 52, "weight": 80},
    "mock_data/patient_4_critical_combined.vcf": {"age": 79, "weight": 55}
}

# 2. Point to the correct files inside the mock_data directory
if args.hospital_id == 1:
    my_vcf_files = ["mock_data/patient_1_normal.vcf", "mock_data/patient_2_vkorc1_sensitive.vcf"]
    print("🏥 Node Activated: Hospital Client 1 (Training on Patients 1 & 2)")
elif args.hospital_id == 2:
    my_vcf_files = ["mock_data/patient_3_cyp2c9_slow.vcf", "mock_data/patient_4_critical_combined.vcf"]
    print("🏥 Node Activated: Hospital Client 2 (Training on Patients 3 & 4)")
else:
    raise ValueError("Invalid Hospital ID! Use --hospital_id 1 or --hospital_id 2")

# 3. Data encoding utilities
def encode_genotype(gt_string):
    mapping = {"0/0": 0.0, "0/1": 1.0, "1/1": 2.0}
    return mapping.get(gt_string, 0.0)

def prepare_local_data(vcf_files, clinical_profiles):
    X_list, Y_list = [], []
    for vcf_file in vcf_files:
        genomics = parse_vcf_genomics(vcf_file)
        clinical = clinical_profiles[vcf_file]
        report = evaluate_clinical_dosage(clinical, genomics)
        # FIX: Switched from split parsing string to direct numeric float to avoid parsing crashes
        target_dosage = float(report['dosage_value'])
        
        feature_vector = [
            float(clinical['age']),
            float(clinical['weight']),
            encode_genotype(genomics["rs1799853_cyp2c9_2"]),
            encode_genotype(genomics["rs1057910_cyp2c9_3"]),
            encode_genotype(genomics["rs9923231_vkorc1"]),
            encode_genotype(genomics["rs3918290_dpyd"])
        ]
        X_list.append(feature_vector)
        Y_list.append(target_dosage)
    return np.array(X_list, dtype=np.float32), np.array(Y_list, dtype=np.float32)

# Load data into memory
X_train, Y_train = prepare_local_data(my_vcf_files, patients_clinical_inputs)

# 4. Core PyTorch ML Neural Network Model
class ClinicalDosageModel(nn.Module):
    def __init__(self):
        super(ClinicalDosageModel, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(6, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1) # Outputs predicted continuous dosage value
        )
    def forward(self, x):
        return self.network(x)

model = ClinicalDosageModel()
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

# 5. Flower client loop configuration
class HospitalFlowerClient(fl.client.NumPyClient):
    def get_parameters(self, config):
        return [val.cpu().numpy() for _, val in model.state_dict().items()]

    def set_parameters(self, parameters):
        params_dict = zip(model.state_dict().keys(), parameters)
        state_dict = {k: torch.tensor(v) for k, v in params_dict}
        model.load_state_dict(state_dict, strict=True)

    def fit(self, parameters, config):
        self.set_parameters(parameters)
        model.train()
        inputs = torch.tensor(X_train, dtype=torch.float32)
        labels = torch.tensor(Y_train, dtype=torch.float32).unsqueeze(1)
        
        for epoch in range(10):
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
        print(f"✅ Local cycle complete. Training Loss: {loss.item():.4f}")
        return self.get_parameters(config={}), len(X_train), {}

    def evaluate(self, parameters, config):
        self.set_parameters(parameters)
        model.eval()
        inputs = torch.tensor(X_train, dtype=torch.float32)
        labels = torch.tensor(Y_train, dtype=torch.float32).unsqueeze(1)
        with torch.no_grad():
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            
        # Use absolute path to ensure model is saved in backend directory
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        torch.save(model.state_dict(), os.path.join(backend_dir, "global_geniedose_model.pt"))
        
        return float(loss.item()), len(X_train), {}

# Fire up connection pipeline to the running server
fl.client.start_client(server_address="127.0.0.1:8080", client=HospitalFlowerClient().to_client())