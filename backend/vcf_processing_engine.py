import os
import re

def parse_vcf_patient_metadata(vcf_path):
    """
    NEW: Reads ##PATIENT_ header lines from VCF to extract age and weight.
    Your VCF files must have these two lines in their headers:
        ##PATIENT_AGE=62
        ##PATIENT_WEIGHT=78
    Returns a dict with 'age' and 'weight' (or None if not found).
    """
    metadata = {"age": None, "weight": None}

    with open(vcf_path, 'r') as f:
        for line in f:
            if not line.startswith('#'):
                break  # Stop once we leave the header block

            # Match ##PATIENT_AGE=<number>
            age_match = re.match(r'##PATIENT_AGE=(\d+)', line.strip())
            if age_match:
                metadata["age"] = int(age_match.group(1))

            # Match ##PATIENT_WEIGHT=<number>
            weight_match = re.match(r'##PATIENT_WEIGHT=(\d+\.?\d*)', line.strip())
            if weight_match:
                metadata["weight"] = float(weight_match.group(1))

    return metadata


def parse_vcf_genomics(vcf_path):
    """
    Parses standard VCF files to identify key Warfarin-altering variants.
    Maps rsIDs directly to genetic mutations.
    """
    genomic_profile = {
        "rs1799853_cyp2c9_2": "0/0",
        "rs1057910_cyp2c9_3": "0/0",
        "rs9923231_vkorc1":   "0/0"
    }

    if not os.path.exists(vcf_path):
        raise FileNotFoundError(f"⚠️ Could not find VCF file at: {vcf_path}. Check your folder path!")

    with open(vcf_path, 'r') as file:
        for line in file:
            if line.startswith('#'):
                continue

            columns = line.strip().split('\t')
            if len(columns) < 10:
                continue

            rsid         = columns[2]
            format_field = columns[8].split(':')
            patient_field = columns[9].split(':')

            if 'GT' in format_field:
                gt_index = format_field.index('GT')
                genotype = patient_field[gt_index]

                if rsid == "rs1799853":
                    genomic_profile["rs1799853_cyp2c9_2"] = genotype
                elif rsid == "rs1057910":
                    genomic_profile["rs1057910_cyp2c9_3"] = genotype
                elif rsid == "rs9923231":
                    genomic_profile["rs9923231_vkorc1"] = genotype

    return genomic_profile


def parse_vcf_and_predict(vcf_path, fallback_age=50, fallback_weight=70):
    """
    NEW MASTER FUNCTION: Combines metadata + genomics parsing into one call.
    Used by app.py's /api/predict-vcf-upload endpoint.
    Returns: (clinical_data_dict, genomics_dict)
    """
    # 1. Try to pull age/weight from the VCF header
    metadata = parse_vcf_patient_metadata(vcf_path)

    clinical_data = {
        "age":    metadata["age"]    if metadata["age"]    is not None else fallback_age,
        "weight": metadata["weight"] if metadata["weight"] is not None else fallback_weight
    }

    # 2. Pull the three pharmacogenomic SNPs
    genomics = parse_vcf_genomics(vcf_path)

    return clinical_data, genomics


def evaluate_clinical_dosage(clinical_data, genomics):
    """
    Combines parsed genomic metrics with clinical patient data to calculate
    precise initial dosing benchmarks and toxicity alerts.
    """
    age    = clinical_data['age']
    weight = clinical_data['weight']

    base_dose = 5.0
    if age > 65:
        base_dose -= 0.5
    if age > 75:
        base_dose -= 0.5
    if weight < 60:
        base_dose -= 0.5

    vkorc1   = genomics["rs9923231_vkorc1"]
    cyp2c9_2 = genomics["rs1799853_cyp2c9_2"]
    cyp2c9_3 = genomics["rs1057910_cyp2c9_3"]

    if vkorc1 == "0/1":
        base_dose *= 0.72
    elif vkorc1 == "1/1":
        base_dose *= 0.43

    if cyp2c9_2 in ("0/1", "1/1"):
        base_dose *= 0.81
    if cyp2c9_3 == "0/1":
        base_dose *= 0.66
    elif cyp2c9_3 == "1/1":
        base_dose *= 0.34

    final_dosage = round(base_dose, 2)

    suitability    = "SUITABLE WITH PRECAUTIONS"
    risk_level     = "Low Risk"
    clinical_notes = "Standard maintenance tracking is required."

    if final_dosage >= 4.0:
        risk_level     = "Normal Baseline"
        suitability    = "FULLY SUITABLE"
        clinical_notes = "Patient exhibits typical drug clearing patterns and expected sensitivities."
    elif 2.0 <= final_dosage < 4.0:
        risk_level     = "Moderate Toxic Risk"
        clinical_notes = "Patient has elevated bleeding risk due to genetic variants. Monitor INR closely."
    elif final_dosage < 2.0:
        risk_level     = "CRITICAL TOXICITY WARNING"
        suitability    = "HIGH RISK / ALTERNATIVE SUGGESTED"
        clinical_notes = "Extremely narrow therapeutic window! Standard dosing will cause toxic build-up."

    return {
        "recommended_dosage": f"{final_dosage} mg/day",
        "suitability_status": suitability,
        "toxic_risk_profile": risk_level,
        "clinical_notes":     clinical_notes
    }
