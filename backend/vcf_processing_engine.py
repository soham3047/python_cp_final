import os

def parse_vcf_genomics(vcf_path):
    """
    Parses standard VCF files to identify key Warfarin-altering variants.
    Maps rsIDs directly to genetic mutations.
    """
    genomic_profile = {
        "rs1799853_cyp2c9_2": "0/0",
        "rs1057910_cyp2c9_3": "0/0",
        "rs9923231_vkorc1": "0/0"
    }
    
    # Safety check: Prevent immediate crashing if path is wrong
    if not os.path.exists(vcf_path):
        raise FileNotFoundError(f"⚠️ Could not find VCF file at: {vcf_path}. Check your folder path!")
    
    with open(vcf_path, 'r') as file:
        for line in file:
            # Skip header lines
            if line.startswith('#'):
                continue
            
            columns = line.strip().split('\t')
            if len(columns) < 10:
                continue
                
            rsid = columns[2]
            format_field = columns[8].split(':')
            patient_field = columns[9].split(':')
            
            # Find the index of the Genotype (GT) tag
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


def evaluate_clinical_dosage(clinical_data, genomics):
    """
    Combines parsed genomic metrics with clinical patient data to calculate 
    precise initial dosing benchmarks and toxicity alerts.
    """
    age = clinical_data['age']
    weight = clinical_data['weight']
    
    # Base baseline clinical dosing estimation formula
    base_dose = 5.0
    if age > 65:
        base_dose -= 0.5
    if age > 75:
        base_dose -= 0.5
    if weight < 60:
        base_dose -= 0.5
        
    # Apply Genomic Penalties based on parsed metrics
    vkorc1 = genomics["rs9923231_vkorc1"]
    cyp2c9_2 = genomics["rs1799853_cyp2c9_2"]
    cyp2c9_3 = genomics["rs1057910_cyp2c9_3"]
    
    # 1. VKORC1 Sensitivity Modifiers
    if vkorc1 == "0/1":
        base_dose *= 0.72   # Moderate sensitivity reduction
    elif vkorc1 == "1/1":
        base_dose *= 0.43   # High sensitivity reduction
        
    # 2. CYP2C9 Clearance Modifiers
    if cyp2c9_2 == "0/1" or cyp2c9_2 == "1/1":
        base_dose *= 0.81
    if cyp2c9_3 == "0/1":
        base_dose *= 0.66
    elif cyp2c9_3 == "1/1":
        base_dose *= 0.34   # Critical clearing restriction
        
    final_dosage = round(base_dose, 2)
    
    # Generate Dynamic Risk Warnings and Suitability Outputs for the UI
    suitability = "SUITABLE WITH PRECAUTIONS"
    risk_level = "Low Risk"
    clinical_notes = "Standard maintenance tracking is required."
    
    if final_dosage >= 4.0:
        risk_level = "Normal Baseline"
        suitability = "FULLY SUITABLE"
        clinical_notes = "Patient exhibits typical drug clearing patterns and expected sensitivities."
    elif 2.0 <= final_dosage < 4.0:
        risk_level = "Moderate Toxic Risk"
        clinical_notes = "Patient has an elevated risk of bleeding due to genetic variants. Monitor baseline INR closely."
    elif final_dosage < 2.0:
        risk_level = "CRITICAL TOXICITY WARNING"
        suitability = "HIGH RISK / ALTERNATIVE SUGGESTED"
        clinical_notes = "Extremely narrow therapeutic window! Standard dosing will cause toxic systemic build-up."

    return {
        "recommended_dosage": f"{final_dosage} mg/day",
        "suitability_status": suitability,
        "toxic_risk_profile": risk_level,
        "clinical_notes": clinical_notes
    }

# ==========================================
# SIMULATION WORKFLOWS FOR YOUR 4 PROFILES
# ==========================================

# 🎯 FIXED PATHS: Updated to target your 'mock_data' folder properly!
patients_clinical_inputs = {
    "mock_data/patient_1_normal.vcf": {"age": 45, "weight": 75},
    "mock_data/patient_2_vkorc1_sensitive.vcf": {"age": 68, "weight": 61},
    "mock_data/patient_3_cyp2c9_slow.vcf": {"age": 52, "weight": 80},
    "mock_data/patient_4_critical_combined.vcf": {"age": 79, "weight": 55}
}

print("=== GENIEDOSE INTEGRATED ANALYSIS REPORT ===\n")
for vcf_file, clinical_info in patients_clinical_inputs.items():
    print(f"🔄 Processing File: {vcf_file}")
    
    # 1. Extract entities from DNA sequence
    genomics = parse_vcf_genomics(vcf_file)
    print(f"   ↳ Extracted Genotypes: {genomics}")
    
    # 2. Run clinical math + rule boundaries
    report = evaluate_clinical_dosage(clinical_info, genomics)
    
    print(f"   ↳ Result Dosing: {report['recommended_dosage']}")
    print(f"   ↳ Profile Status: {report['suitability_status']}")
    print(f"   ↳ Threat Evaluation: {report['toxic_risk_profile']}")
    print(f"   ↳ System Instructions: {report['clinical_notes']}\n" + "-"*50 + "\n")