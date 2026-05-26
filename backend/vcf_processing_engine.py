import os
import re


def parse_vcf_patient_metadata(vcf_path):
    """
    Reads ##PATIENT_AGE and ##PATIENT_WEIGHT from VCF header lines.
    Returns dict with 'age' and 'weight' (None if not found).
    """
    metadata = {"age": None, "weight": None}
    with open(vcf_path, 'r') as f:
        for line in f:
            if not line.startswith('#'):
                break
            age_match = re.match(r'##PATIENT_AGE=(\d+)', line.strip())
            if age_match:
                metadata["age"] = int(age_match.group(1))
            weight_match = re.match(r'##PATIENT_WEIGHT=(\d+\.?\d*)', line.strip())
            if weight_match:
                metadata["weight"] = float(weight_match.group(1))
    return metadata


def parse_vcf_genomics(vcf_path):
    genomic_profile = {
        "rs1799853_cyp2c9_2": "0/0",
        "rs1057910_cyp2c9_3": "0/0",
        "rs9923231_vkorc1":   "0/0",
        "rs3918290_dpyd":     "0/0",  # DPYD Chemo Feature
        "rs4244285_cyp2c19_2": "0/0",  # NEW: Serotonin Features
        "rs28399504_cyp2c19_3": "0/0",
        "rs25531_slc6a4":      "0/0"
    }

    if not os.path.exists(vcf_path):
        raise FileNotFoundError(f"VCF not found: {vcf_path}")
        
    with open(vcf_path, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            cols = line.strip().split('\t')
            if len(cols) < 10:
                continue
            rsid = cols[2]
            fmt = cols[8].split(':')
            sample = cols[9].split(':')
            
            if 'GT' in fmt:
                gt = sample[fmt.index('GT')]
                if rsid == "rs1799853":
                    genomic_profile["rs1799853_cyp2c9_2"] = gt
                elif rsid == "rs1057910":
                    genomic_profile["rs1057910_cyp2c9_3"] = gt
                elif rsid == "rs9923231":
                    genomic_profile["rs9923231_vkorc1"] = gt
                elif rsid == "rs3918290":                         
                    genomic_profile["rs3918290_dpyd"] = gt        
                elif rsid == "rs4244285":                         # NEW Serotonin Mapping
                    genomic_profile["rs4244285_cyp2c19_2"] = gt
                elif rsid == "rs28399504":                        # NEW Serotonin Mapping
                    genomic_profile["rs28399504_cyp2c19_3"] = gt
                elif rsid == "rs25531":                           # NEW Serotonin Mapping
                    genomic_profile["rs25531_slc6a4"] = gt
                    
    return genomic_profile


def evaluate_clinical_dosage(clinical_data, genomics, drug="warfarin"):
    """
    CPIC-aligned rule-based dosage calculator.
    Supports Warfarin, 5-Fluorouracil, and Sertraline (Serotonin pathway).
    """
    age    = clinical_data['age']
    weight = clinical_data['weight']

    # ─────────────────────────────────────────────────────────────
    # WARFARIN (Cardiovascular anticoagulant)
    # ─────────────────────────────────────────────────────────────
    if drug.lower() == "warfarin":
        base_dose = 5.0

        # Age adjustments
        if age > 65: base_dose -= 0.5
        if age > 75: base_dose -= 0.5

        # Weight adjustment
        if weight < 60: base_dose -= 0.5

        vkorc1   = genomics["rs9923231_vkorc1"]
        cyp2c9_2 = genomics["rs1799853_cyp2c9_2"]
        cyp2c9_3 = genomics["rs1057910_cyp2c9_3"]

        # VKORC1 sensitivity modifiers
        if vkorc1 == "0/1":
            base_dose *= 0.72
        elif vkorc1 == "1/1":
            base_dose *= 0.43

        # CYP2C9 clearance modifiers
        if cyp2c9_2 in ("0/1", "1/1"):
            base_dose *= 0.81
        if cyp2c9_3 == "0/1":
            base_dose *= 0.66
        elif cyp2c9_3 == "1/1":
            base_dose *= 0.34

        final_dosage = round(max(0.5, base_dose), 2)

        # Risk classification for warfarin
        if final_dosage >= 4.0:
            risk_level     = "🟢 Normal Baseline"
            suitability    = "FULLY SUITABLE"
            clinical_notes = "Patient exhibits typical drug clearing. Standard maintenance monitoring required."
        elif 2.0 <= final_dosage < 4.0:
            risk_level     = "🟡 Moderate Toxic Risk"
            suitability    = "SUITABLE WITH PRECAUTIONS"
            clinical_notes = "Elevated bleeding risk due to genetic variants. Monitor INR every 3–5 days initially."
        else:
            risk_level     = "🔴 CRITICAL TOXICITY WARNING"
            suitability    = "HIGH RISK — ALTERNATIVE DOSING REQUIRED"
            clinical_notes = "Extremely narrow therapeutic window. Standard dosing will cause toxic accumulation."

    # ─────────────────────────────────────────────────────────────
    # 5-FLUOROURACIL (Chemotherapy drug)
    # ─────────────────────────────────────────────────────────────
    elif drug.lower() in ("5-fu", "5fu", "fluorouracil"):
        base_dose = 1000.0
        if age > 75: base_dose *= 0.85  
        if weight < 50: base_dose *= 0.8
        elif weight > 100: base_dose *= 1.1
        
        dpyd = genomics["rs3918290_dpyd"]
        if dpyd == "0/1":
            base_dose *= 0.5
            risk_level = "🟡 Moderate Toxicity Risk"
            suitability = "SUITABLE WITH DOSE REDUCTION"
            clinical_notes = "DPYD heterozygous variant detected. 50% dose reduction recommended. Monitor for severe toxicity."
        elif dpyd == "1/1":
            base_dose = 0.0
            risk_level = "🔴 CRITICAL — DO NOT ADMINISTER STANDARD DOSE"
            suitability = "CONTRAINDICATED — GENETIC TESTING REQUIRED"
            clinical_notes = "Homozygous DPYD mutation detected. Standard 5-FU dosing will cause severe toxicity. Alternative chemotherapy agents must be considered. Genetic counseling recommended."
        else:
            risk_level = "🟢 Normal Metabolism"
            suitability = "FULLY SUITABLE"
            clinical_notes = "Normal DPYD metabolism. Standard 5-FU dosing appropriate. Monitor for cumulative toxicity."
        
        final_dosage = round(max(0.0, base_dose), 2)

    # ─────────────────────────────────────────────────────────────
    # SEROTONIN DRUG (Sertraline / Antidepressant) - NEW
    # ─────────────────────────────────────────────────────────────
    elif drug.lower() in ("sertraline", "serotonin"):
        def encode_gt_internal(gt):
            return {"0/0": 0.0, "0/1": 1.0, "1/1": 2.0}.get(gt, 0.0)

        val_cyp2c19_2 = encode_gt_internal(genomics.get("rs4244285_cyp2c19_2", "0/0"))
        val_cyp2c19_3 = encode_gt_internal(genomics.get("rs28399504_cyp2c19_3", "0/0"))
        val_slc6a4 = encode_gt_internal(genomics.get("rs25531_slc6a4", "0/0"))

        base_dose = (
            50.0 
            - (val_cyp2c19_2 * 12.5) 
            - (val_cyp2c19_3 * 15.0) 
            - (val_slc6a4 * 7.5) 
            + (weight * 0.05)
            - (age * 0.08)
        )
        final_dosage = round(max(12.5, min(200.0, base_dose)), 2)

        if val_cyp2c19_2 >= 1.0 or val_cyp2c19_3 >= 1.0:
            risk_level = "🟡 Moderate Metabolic Risk"
            suitability = "SUITABLE WITH PRECAUTIONS"
            clinical_notes = "Reduced CYP2C19 metabolism detected. Monitor for prolonged QT intervals and typical SSRI side effects."
        elif val_slc6a4 >= 1.0:
            risk_level = "🟡 Altered Transporter Sensitivity"
            suitability = "SUITABLE WITH MONITORING"
            clinical_notes = "Altered serotonin transporter expression. Response profile may vary; titrate based on clinical response."
        else:
            risk_level = "🟢 Normal Responder Profile"
            suitability = "FULLY SUITABLE"
            clinical_notes = "Normal serotonin pathway genetics. Standard Sertraline dosing guidelines apply."

    else:
        final_dosage = 0.0
        risk_level = "⚪ Unknown Drug"
        suitability = "DRUG NOT SUPPORTED"
        clinical_notes = f"Drug '{drug}' is not currently supported by GenieDose."

    return {
        "recommended_dosage": f"{final_dosage} mg" if drug.lower() in ("sertraline", "serotonin") else f"{final_dosage} mg/day",
        "dosage_value":        final_dosage,
        "suitability_status":  suitability,
        "toxic_risk_profile":  risk_level,
        "clinical_notes":      clinical_notes,
        "drug":                drug.lower()
    }


def parse_vcf_and_predict(vcf_path, drug="warfarin", fallback_age=50, fallback_weight=70):
    metadata = parse_vcf_patient_metadata(vcf_path)
    clinical_data = {
        "age":    metadata["age"]    if metadata["age"]    is not None else fallback_age,
        "weight": metadata["weight"] if metadata["weight"] is not None else fallback_weight
    }
    genomics     = parse_vcf_genomics(vcf_path)
    dosage_report = evaluate_clinical_dosage(clinical_data, genomics, drug=drug)

    return clinical_data, genomics, dosage_report