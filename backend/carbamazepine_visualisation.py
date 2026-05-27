import numpy as np
import matplotlib.pyplot as plt

def calculate_carbamazepine_dosage(age, weight, hla_b_1502):
    """
    Core CPIC rule-based logic for Carbamazepine (Antiepileptic/Neurology).
    Baseline maintenance therapeutic window ranges between 200mg and 1200mg per day.
    """
    base_dose = 400.0 + (float(weight) * 2.5) - (float(age) * 0.75)
    if age > 65:
        base_dose *= 0.80
    if weight < 50:
        base_dose *= 0.85
    elif weight > 95:
        base_dose *= 1.15
    if hla_b_1502 in ["0/1", "1/1", "Present", "Positive"]:
        base_dose = 0.0
    if base_dose == 0.0:
        return 0.0
    return max(200.0, min(1200.0, base_dose))


def create_plot():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    weights = np.arange(40, 120, 1)
    doses_normal = [calculate_carbamazepine_dosage(45, w, "0/0") for w in weights]
    doses_high_risk = [calculate_carbamazepine_dosage(45, w, "0/1") for w in weights]
    ax1.plot(weights, doses_normal, label="HLA-B*15:02 Negative (0/0) - Safe to Optimize", color="#10b981", linewidth=3, marker='o', markevery=10)
    ax1.plot(weights, doses_high_risk, label="HLA-B*15:02 Positive (0/1) - SJS Fatal Toxicity Risk", color="#ef4444", linewidth=3, marker='s', markevery=10)
    ax1.set_title("Impact of Body Weight & HLA-B Genetics on Carbamazepine", fontsize=11, fontweight='bold', pad=10)
    ax1.set_xlabel("Patient Weight (Kg)", fontsize=11)
    ax1.set_ylabel("Recommended Maintenance Dose (mg/day)", fontsize=11)
    ax1.set_ylim(-50, 1400)
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(loc="upper left", frameon=True, shadow=True)
    ax1.annotate('< 50kg Base Deduction', xy=(49, 410), xytext=(38, 250), arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6))
    ax1.annotate('> 95kg Volume Surge', xy=(96, 680), xytext=(100, 500), arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6))

    genetic_scenarios = [
        "Normal Baseline\n(HLA-B*15:02 Negative)",
        "Heterozygous Carrier\n(HLA-B*15:02 0/1)",
        "Homozygous Variant\n(HLA-B*15:02 1/1)"
    ]
    genetic_doses = [
        calculate_carbamazepine_dosage(45, 70, "0/0"),
        calculate_carbamazepine_dosage(45, 70, "0/1"),
        calculate_carbamazepine_dosage(45, 70, "1/1")
    ]
    bars = ax2.bar(genetic_scenarios, genetic_doses, color=['#10b981', '#ef4444', '#b91c1c'], edgecolor='black', width=0.45)
    for bar in bars:
        yval = bar.get_height()
        if yval == 0.0:
            ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 30, "CONTRAINDICATED\n(ABORT / 0 mg)", ha='center', va='bottom', color='#ef4444', fontweight='bold', fontsize=9)
        else:
            ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 30, f"{yval:.2f} mg", ha='center', va='bottom', fontweight='bold')
    ax2.set_title("Isolated Effect of HLA-B*15:02 Variant on Neuro-Dosing", fontsize=11, fontweight='bold', pad=10)
    ax2.set_ylabel("Recommended Maintenance Dose (mg/day)", fontsize=11)
    ax2.set_ylim(-50, 1400)
    ax2.grid(axis='y', linestyle='--', alpha=0.5)
    plt.setp(ax2.get_xticklabels(), rotation=0, ha="center", fontsize=9)
    plt.suptitle("CPIC Pharmacogenomic Calibration Landscape for Carbamazepine", fontsize=15, fontweight='bold', y=0.98)
    plt.tight_layout()
    return fig
