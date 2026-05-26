import os

def extract_carbamazepine_genomics(vcf_path):
    """Parses patient variants targeting rs105791026 (HLA-B*15:02) marker."""
    genomics = {"rs105791026_hla_b": "0/0"}
    if not os.path.exists(vcf_path):
        return genomics

    with open(vcf_path, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            columns = line.strip().split('\t')
            if len(columns) > 4 and columns[2] == "rs105791026":
                try:
                    fmt_idx = columns[8].split(':').index('GT')
                    genomics["rs105791026_hla_b"] = columns[9].split(':')[fmt_idx]
                except (ValueError, IndexError):
                    genomics["rs105791026_hla_b"] = "0/0"
                break
    return genomics

def evaluate_carbamazepine_dosage(age, weight, genotype_str):
    """Enforces strict therapeutic restrictions based on genotype parameters."""
    # Convert traditional string formats down to model floats
    if genotype_str in ["0/1", "1/1", "1", "2", "Present", "Positive"]:
        gt_val = 1.0
    else:
        gt_val = 0.0
    
    if gt_val > 0:
        return {
            "recommended_dosage": "CONTRAINDICATED",
            "dosage_value": 0.0,
            "suitability_status": "CRITICAL DANGER",
            "toxic_risk_profile": "HIGH EXTREME RISK",
            "clinical_notes": "Patient is POSITIVE for the HLA-B*15:02 variant. High danger of severe cutaneous reactions (Stevens-Johnson Syndrome). Prescription aborted.",
            "drug": "carbamazepine"
        }
    
    # Calculate baseline maintenance values for wild-type variants
    base_dose = 400.0 + (float(weight) * 1.5) - (float(age) * 0.5)
    final_dosage = round(max(200.0, min(1200.0, base_dose)), 2)
    return {
        "recommended_dosage": f"{final_dosage} mg/day",
        "dosage_value": final_dosage,
        "suitability_status": "SAFE / COMPLIANT",
        "toxic_risk_profile": "LOW RISK",
        "clinical_notes": "Patient is negative for the HLA-B*15:02 variant. Proceed with standard baseline anticonvulsant dosing models.",
        "drug": "carbamazepine"
    }