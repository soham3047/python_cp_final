import numpy as np

def encode_genotype(gt_string):
    """Converts VCF string genotypes into ML-friendly numerical features."""
    mapping = {"0/0": 0.0, "0/1": 1.0, "1/1": 2.0}
    return mapping.get(gt_string, 0.0)

def get_hospital_dataset(vcf_files, clinical_profiles):
    """Generates X (features) and Y (labels) for the PyTorch model."""
    from vcf_processing_engine import parse_vcf_genomics, evaluate_clinical_dosage
    
    X_list = []
    Y_list = []
    
    for vcf_file in vcf_files:
        # 1. Parse genomic entities from the VCF
        genomics = parse_vcf_genomics(vcf_file)
        clinical = clinical_profiles[vcf_file]
        
        # 2. Get the target dosage calculation (to act as our ground truth label)
        report = evaluate_clinical_dosage(clinical, genomics)
        target_dosage = float(report['recommended_dosage'].split()[0])
        
        # 3. Build Feature Vector: [Age, Weight, rs1799853, rs1057910, rs9923231]
        feature_vector = [
            float(clinical['age']),
            float(clinical['weight']),
            encode_genotype(genomics["rs1799853_cyp2c9_2"]),
            encode_genotype(genomics["rs1057910_cyp2c9_3"]),
            encode_genotype(genomics["rs9923231_vkorc1"])
        ]
        
        X_list.append(feature_vector)
        Y_list.append(target_dosage)
        
    return np.array(X_list, dtype=np.float32), np.array(Y_list, dtype=np.float32)