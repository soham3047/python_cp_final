import numpy as np
import matplotlib.pyplot as plt

def calculate_5fu_dosage(age, weight, dpyd):
    """Core CPIC rule-based logic for 5-Fluorouracil (Chemotherapy)."""
    base_dose = 1000.0
    
    # Clinical adjustments
    if age > 75: 
        base_dose *= 0.85  # Elderly deduction
        
    if weight < 50: 
        base_dose *= 0.8   # Low body weight deduction
    elif weight > 100: 
        base_dose *= 1.1   # High body weight increase
        
    # Genetic (DPYD) adjustments
    if dpyd == "0/1":
        base_dose *= 0.5   # 50% reduction for intermediate metabolizers
    elif dpyd == "1/1":
        base_dose = 0.0    # Contraindicated for poor metabolizers
        
    return max(0.0, base_dose)

# Create a grid layout with 1 row and 2 descriptive panels
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# -------------------------------------------------------------------------
# PANEL 1: CONTINUOUS WEIGHT VS DOSAGE CURVE BY GENETIC RISK PROFILE
# -------------------------------------------------------------------------
# Plotting Weight from 40kg to 120kg for a standard 50-year-old patient
weights = np.arange(40, 120, 1)

# Scenario A: Normal DPYD Metabolism (Wild Type 0/0)
doses_normal = [calculate_5fu_dosage(50, w, "0/0") for w in weights]

# Scenario B: Intermediate DPYD Metabolism (Heterozygous 0/1)
doses_high_risk = [calculate_5fu_dosage(50, w, "0/1") for w in weights]

ax1.plot(weights, doses_normal, label="Wild Type (0/0) - Normal Clearance", color="#10b981", linewidth=3, marker='o', markevery=10)
ax1.plot(weights, doses_high_risk, label="DPYD Mutant (0/1) - High Toxicity Risk", color="#f59e0b", linewidth=3, marker='s', markevery=10)

ax1.set_title("Impact of Body Weight & DPYD Genetics on 5-FU Dosage", fontsize=12, fontweight='bold', pad=10)
ax1.set_xlabel("Patient Weight (Kg)", fontsize=11)
ax1.set_ylabel("Recommended Starting Dose (mg)", fontsize=11)
ax1.set_ylim(0, 1250)
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(loc="lower right", frameon=True, shadow=True)

# Annotate the specific step-changes caused by clinical weight thresholds
ax1.annotate('< 50kg Penalty', xy=(49, 800), xytext=(42, 600),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6))
ax1.annotate('> 100kg Bonus', xy=(101, 1100), xytext=(102, 900),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6))

# -------------------------------------------------------------------------
# PANEL 2: BAR CHART OF PURE DPYD GENETIC MUTATION PENALTIES
# -------------------------------------------------------------------------
# Keep clinical factors completely constant (Age 50, Weight 75kg) to isolate genetics
genetic_scenarios = [
    "Normal Baseline\n(DPYD 0/0)",
    "Intermediate Metabolizer\n(DPYD 0/1)",
    "Poor Metabolizer\n(DPYD 1/1 - Fatal Risk)"
]

genetic_doses = [
    calculate_5fu_dosage(50, 75, "0/0"), # Normal
    calculate_5fu_dosage(50, 75, "0/1"), # 50% Reduction
    calculate_5fu_dosage(50, 75, "1/1")  # Contraindicated (0mg)
]

# Using Green (Safe), Yellow (Caution), Red (Danger)
bars = ax2.bar(genetic_scenarios, genetic_doses, color=['#10b981', '#f59e0b', '#ef4444'], edgecolor='black', width=0.45)

# Write precise numeric dosage targets right over each bar
for bar in bars:
    yval = bar.get_height()
    if yval == 0.0:
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 20, "CONTRAINDICATED\n(0 mg)", ha='center', va='bottom', color='#ef4444', fontweight='bold')
    else:
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 20, f"{yval:.2f} mg", ha='center', va='bottom', fontweight='bold')

ax2.set_title("Isolated Effect of DPYD Mutations on 5-FU Dosage", fontsize=12, fontweight='bold', pad=10)
ax2.set_ylabel("Recommended Starting Dose (mg)", fontsize=11)
ax2.set_ylim(0, 1250)
ax2.grid(axis='y', linestyle='--', alpha=0.5)
plt.setp(ax2.get_xticklabels(), rotation=0, ha="center", fontsize=10)

# Final formatting adjustment
plt.suptitle("CPIC Pharmacogenomic Calibration Landscape for 5-Fluorouracil (Chemo)", fontsize=15, fontweight='bold', y=0.98)
plt.tight_layout()

print("📊 Rendering 5-FU Chemo multi-panel descriptive dashboard layout...")
plt.show()