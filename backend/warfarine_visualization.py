import numpy as np
import matplotlib.pyplot as plt

def calculate_dosage(age, weight, vkorc1, cyp2c9_2, cyp2c9_3):
    """Core CPIC rule-based logic from the system script."""
    base_dose = 5.0
    if age > 65: base_dose -= 0.5
    if age > 75: base_dose -= 0.5
    if weight < 60: base_dose -= 0.5

    # VKORC1 modifier
    if vkorc1 == "0/1":     base_dose *= 0.72
    elif vkorc1 == "1/1":   base_dose *= 0.43

    # CYP2C9 modifiers
    if cyp2c9_2 in ("0/1", "1/1"): base_dose *= 0.81
    if cyp2c9_3 == "0/1":          base_dose *= 0.66
    elif cyp2c9_3 == "1/1":        base_dose *= 0.34

    return max(0.5, base_dose)

# Create a grid layout with 1 row and 2 descriptive panels
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# -------------------------------------------------------------------------
# PANEL 1: CONTINUOUS AGE VS DOSAGE CURVE BY GENETIC RISK PROFILE
# -------------------------------------------------------------------------
ages = np.arange(20, 90, 1)

# Scenario A: Low Risk Patient (Normal Weight 75kg, No Mutations)
doses_low_risk = [calculate_dosage(a, 75, "0/0", "0/0", "0/0") for a in ages]

# Scenario B: High Genetic Sensitivity (Normal Weight 75kg, Mutant VKORC1 & CYP2C9)
doses_high_risk = [calculate_dosage(a, 75, "1/1", "0/1", "0/0") for a in ages]

ax1.plot(ages, doses_low_risk, label="Wild Type (0/0) - Normal Metabolism", color="#10b981", linewidth=3, marker='o', markevery=5)
ax1.plot(ages, doses_high_risk, label="Mutant Profile - High Sensitivity", color="#ef4444", linewidth=3, marker='s', markevery=5)

ax1.set_title("Impact of Age & Genetics on Warfarin Dosage", fontsize=12, fontweight='bold', pad=10)
ax1.set_xlabel("Patient Age (Years)", fontsize=11)
ax1.set_ylabel("Recommended Dosing Threshold (mg/day)", fontsize=11)
ax1.set_ylim(0, 6.0)
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(loc="upper right", frameon=True, shadow=True)

# Annotate the specific drops caused by age clinical thresholds
ax1.annotate('Age > 65 Threshold Drop', xy=(66, 4.5), xytext=(40, 3.8),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6))
ax1.annotate('Age > 75 Threshold Drop', xy=(76, 4.0), xytext=(50, 2.8),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6))

# -------------------------------------------------------------------------
# PANEL 2: BAR CHART OF PURE GENETIC MUTATION PENALTIES
# -------------------------------------------------------------------------
# Keep clinical factors completely constant (Age 50, Weight 70kg) to isolate genetics
genetic_scenarios = [
    "Baseline\n(No Mutations)",
    "CYP2C9*2 Heterozygous\n(Slower Clearance)",
    "VKORC1 Heterozygous\n(Moderate Sensitivity)",
    "VKORC1 Homozygous\n(Extreme Sensitivity)"
]

genetic_doses = [
    calculate_dosage(50, 70, "0/0", "0/0", "0/0"), # Baseline
    calculate_dosage(50, 70, "0/0", "0/1", "0/0"), # CYP2C9*2 0/1
    calculate_dosage(50, 70, "0/1", "0/0", "0/0"), # VKORC1 0/1
    calculate_dosage(50, 70, "1/1", "0/0", "0/0")  # VKORC1 1/1
]

bars = ax2.bar(genetic_scenarios, genetic_doses, color=['#10b981', '#60a5fa', '#f59e0b', '#ef4444'], edgecolor='black', width=0.45)

# Write precise numeric dosage targets right over each bar
for bar in bars:
    yval = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, f"{yval:.2f} mg", ha='center', va='bottom', fontweight='bold')

ax2.set_title("Isolated Effect of Genetic Mutations on Dose", fontsize=12, fontweight='bold', pad=10)
ax2.set_ylabel("Recommended Starting Dosage (mg/day)", fontsize=11)
ax2.set_ylim(0, 6.0)
ax2.grid(axis='y', linestyle='--', alpha=0.5)
plt.setp(ax2.get_xticklabels(), rotation=15, ha="right", fontsize=9)

# Final formatting adjustment
plt.suptitle("CPIC Pharmacogenomic Calibration Landscape for Warfarin", fontsize=15, fontweight='bold', y=0.98)
plt.tight_layout()

print("📊 Rendering multi-panel descriptive dashboard layout...")
plt.show()