import numpy as np
import matplotlib.pyplot as plt

def calculate_sertraline_dosage(age, weight, cyp2c19):
    """
    Core CPIC & FDA rule-based clinical staging logic for Sertraline (SSRI Antidepressant).
    Returns the recommended daily starting target threshold based on metabolic stages.
    """
    base_dose = 50.0
    if age > 65:
        base_dose = 25.0
    if cyp2c19 == "1/1" or cyp2c19 in ["Poor", "PM"]:
        base_dose *= 0.50
    elif cyp2c19 == "0/1" or cyp2c19 in ["Intermediate", "IM"]:
        base_dose *= 0.75
    return max(0.0, base_dose)


def create_plot():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    weights = np.arange(40, 120, 1)
    doses_normal = [calculate_sertraline_dosage(40, w, "0/0") for w in weights]
    doses_intermediate = [calculate_sertraline_dosage(40, w, "0/1") for w in weights]
    doses_poor = [calculate_sertraline_dosage(40, w, "1/1") for w in weights]
    ax1.plot(weights, doses_normal, label="Normal Metabolizer (0/0) - Standard Tier", color="#10b981", linewidth=3)
    ax1.plot(weights, doses_intermediate, label="Intermediate Carrier (0/1) - Caution Tier", color="#f59e0b", linewidth=3, linestyle="--")
    ax1.plot(weights, doses_poor, label="Poor Metabolizer (1/1) - Critical Risk Tier", color="#ef4444", linewidth=3, linestyle=":")
    ax1.set_title("Sertraline Calibration: Flat Metabolic Phenotypic Tiers", fontsize=11, fontweight='bold', pad=10)
    ax1.set_xlabel("Patient Weight (Kg)", fontsize=11)
    ax1.set_ylabel("Recommended Onboarding Starting Target (mg/day)", fontsize=11)
    ax1.set_ylim(0, 80)
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(loc="lower right", frameon=True, shadow=True)
    ax1.text(60, 53, "Standard Tier (50 mg/day Base Onboarding)", color="#10b981", fontweight="bold", fontsize=9)
    ax1.text(60, 39, "Adjusted Titration Tier (25% - 50% Reduction Caution)", color="#f59e0b", fontweight="bold", fontsize=9)
    ax1.text(60, 12, "Alternative Therapy Staging Recommended", color="#ef4444", fontweight="bold", fontsize=9)

    genetic_scenarios = [
        "Normal Clearance\n(CYP2C19 0/0)",
        "Intermediate Clearance\n(CYP2C19 0/1)",
        "Poor Clearance Status\n(CYP2C19 1/1)"
    ]
    genetic_doses = [
        calculate_sertraline_dosage(40, 70, "0/0"),
        calculate_sertraline_dosage(40, 70, "0/1"),
        calculate_sertraline_dosage(40, 70, "1/1")
    ]
    bars = ax2.bar(genetic_scenarios, genetic_doses, color=['#10b981', '#f59e0b', '#ef4444'], edgecolor='black', width=0.45)
    for bar in bars:
        yval = bar.get_height()
        if yval == 25.0:
            ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 2, f"{yval:.1f} mg\n(Alternative/Reduce)", ha='center', va='bottom', color='#ef4444', fontweight='bold', fontsize=9)
        elif yval == 37.5:
            ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 2, f"{yval:.1f} mg\n(Step-Down)", ha='center', va='bottom', color='#d97706', fontweight='bold', fontsize=9)
        else:
            ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 2, f"{yval:.1f} mg\n(Standard Base)", ha='center', va='bottom', color='#047857', fontweight='bold', fontsize=9)
    ax2.set_title("Isolated Effect of CYP2C19 Biomarkers on SSRI Targets", fontsize=11, fontweight='bold', pad=10)
    ax2.set_ylabel("Recommended Onboarding Starting Target (mg/day)", fontsize=11)
    ax2.set_ylim(0, 80)
    ax2.grid(axis='y', linestyle='--', alpha=0.5)
    plt.setp(ax2.get_xticklabels(), rotation=0, ha="center", fontsize=9)
    plt.suptitle("CPIC Pharmacogenomic Calibration Landscape for Sertraline / SSRIs", fontsize=15, fontweight='bold', y=0.98)
    plt.tight_layout()
    return fig
