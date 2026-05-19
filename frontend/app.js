document.getElementById('start-btn').addEventListener('click', async () => {
    const btn = document.getElementById('start-btn');
    const logBox = document.getElementById('console-output');

    // Update UI layout states
    btn.disabled = true;
    btn.innerText = "⏳ Running FL Engine...";
    logBox.innerText = "Connecting to Flask container...\nTriggering Flower Simulation Engine...\nCheck your taskbar/desktop for the live Matplotlib Plot window!";

    try {
        const response = await fetch('http://127.0.0.1:5000/run-simulation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.status === "success") {
            logBox.innerText += `\n\n✅ Success: ${data.message}`;
        } else {
            logBox.innerText += `\n\n❌ Error: ${data.message}`;
        }
    } catch (err) {
        logBox.innerText += `\n\n❌ Network failure connecting to server backend: ${err.message}`;
    } finally {
        btn.disabled = false;
        btn.innerText = "🚀 Start Federated Training";
    }
});