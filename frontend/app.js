// 1. VCF FILE HANDLER MECHANICS
document.getElementById('vcfFile').addEventListener('change', function () {
    const groups   = ['manual-mutation-group', 'age-input-group', 'weight-input-group'];
    const helpText = document.getElementById('vcf-help-text');

    if (this.files.length > 0) {
        groups.forEach(id => {
            const el = document.getElementById(id);
            if (el) { el.style.opacity = "0.3"; el.style.pointerEvents = "none"; }
        });
        helpText.innerHTML   = `⚡ <strong>Armed:</strong> '${this.files[0].name}' ready to parse.`;
        helpText.style.color = "#60a5fa";
    } else {
        groups.forEach(id => {
            const el = document.getElementById(id);
            if (el) { el.style.opacity = "1"; el.style.pointerEvents = "auto"; }
        });
        helpText.innerHTML   = `💡 Uploading a VCF overrides all manual fields.`;
        helpText.style.color = "#94a3b8";
    }
});

// 2. MATPLOTLIB POP-UP ENGINE CONTROLS
const modal      = document.getElementById('graph-modal');
const graphImg   = document.getElementById('displayed-graph-img');
const loader     = document.getElementById('graph-loader');
const closeBtn   = document.getElementById('close-modal-btn');
const graphTitle = document.getElementById('modal-graph-title');

document.getElementById('show-graph-btn').addEventListener('click', async () => {
    const targetDrug = document.getElementById('drug-select').value;
    const drugTitles = {
        "warfarin": "Warfarin Calibration Matrix Profile",
        "sertraline": "Sertraline / SSRI Staging Profile",
        "5-fu": "5-Fluorouracil Toxicity Landscape Profile",
        "carbamazepine": "Carbamazepine SJS Safety Landscape Profile"
    };

    graphTitle.innerText = `📊 ${drugTitles[targetDrug] || "Calibration Profile"}`;
    modal.style.display  = "flex";
    loader.style.display = "block";
    graphImg.style.display = "none";

    try {
        const response = await fetch(`/api/generate-plot?drug=${targetDrug}`);
        if (!response.ok) throw new Error("Failed to capture binary stream.");
        
        const imageBlob = await response.blob();
        graphImg.src = URL.createObjectURL(imageBlob);
        
        loader.style.display = "none";
        graphImg.style.display = "block";
    } catch (err) {
        loader.innerHTML = `<span style="color:#ef4444">❌ Error rendering chart: Server endpoint unreachable or file mapping broken.</span>`;
    }
});

closeBtn.addEventListener('click', () => { modal.style.display = "none"; });
window.addEventListener('click', (e) => { if (e.target === modal) modal.style.display = "none"; });

// 3. RUN PREDICTION SUBMISSIONS
document.getElementById('predict-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const resultBox  = document.getElementById('prediction-result');
    const predictBtn = document.getElementById('predict-btn');
    const fileInput  = document.getElementById('vcfFile');

    predictBtn.disabled  = true;
    predictBtn.innerText = "⏳ Analysing...";

    try {
        if (fileInput && fileInput.files.length > 0) {
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('drug', document.getElementById('drug-select').value);

            const res  = await fetch('/api/predict-vcf-upload', { method: 'POST', body: formData });
            const data = await res.json();

            if (data.status === 'success') {
                document.getElementById('patient-age').value    = data.auto_parsed_age;
                document.getElementById('patient-weight').value = data.auto_parsed_weight;

                const riskColor = data.risk_level.includes("CRITICAL") ? "#ef4444" : data.risk_level.includes("Moderate") ? "#f59e0b" : "#4ade80";

                resultBox.innerHTML = `
<div style="margin-bottom:12px;">
    <span style="color:#64748b; font-size:11px; text-transform:uppercase;">📋 CPIC Pharmacogenomic Rule Engine</span><br>
    <span style="color:#4ade80; font-size:1.25rem; font-weight:bold;">🎯 ${data.rule_dosage}</span>
</div>
<div style="margin-bottom:10px; display:flex; gap:10px;">
    <span style="border:1px solid ${riskColor}; color:${riskColor}; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:bold;">${data.risk_level}</span>
    <span style="border:1px solid #475569; color:#94a3b8; padding:2px 8px; border-radius:12px; font-size:11px;">${data.suitability}</span>
</div>
<div style="color:#cbd5e1; font-size:12px; margin-bottom:8px; border-left:3px solid ${riskColor}; padding-left:8px;">🩺 ${data.clinical_notes}</div>
<div style="color:#94a3b8; font-size:11px; background:#1e293b; padding:6px; border-radius:4px; margin-bottom:6px;">🧬 <strong>Variants:</strong> ${data.detected_mutations}</div>
<div style="color:#64748b; font-size:11px; margin-bottom:8px;">📋 VCF Meta Info: Age: ${data.auto_parsed_age} | Weight: ${data.auto_parsed_weight}kg</div>
<div style="color:#94a3b8; font-size:11px; border-top:1px dashed #334155; padding-top:6px;">🤖 <strong>ML Stack Target Output Estimation:</strong> <span style="color:#a78bfa">${data.ml_dosage}</span></div>`;
            } else {
                resultBox.innerHTML = `❌ Engine Error: ${data.message}`;
            }
        } else {
            const drug     = document.getElementById('drug-select').value;
            const mutation = document.getElementById('gene-mutation').value;
            const age      = document.getElementById('patient-age').value;
            const weight   = document.getElementById('patient-weight').value;

            const res  = await fetch('/predict-dosage', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ drug, mutation, age, weight })
            });
            const data = await res.json();
            resultBox.innerHTML = data.status === "success" ? data.result : `❌ ${data.message}`;
        }
    } catch (err) {
        resultBox.innerHTML = `❌ Network Error: Server unreachable.`;
    } finally {
        predictBtn.disabled  = false;
        predictBtn.innerText = "Calculate Optimal Dosage";
    }
});