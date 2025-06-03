async function submitDiagnostic() {
  const input = document.getElementById("inputText").value;

  const payload = {
    text: input,
    age: 60,
    tier: "Shift Session",
    chronic: ["hypertension"],
    lifestyle: ["poor sleep"],
    client_data: {
      symptoms: "",
      goals: "get more energy",
      medications: null,
      emergency_contact: ""
    }
  };

 const response = await fetch("https://purposeful-ai-backend.onrender.com/api/run_diagnostic", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const result = await response.json();

  document.getElementById("results").innerHTML = `
    <strong>🧠 Flags:</strong>\n${JSON.stringify(result.flags, null, 2)}\n\n
    <strong>🔬 Mortality Risk:</strong> ${result.risk}\n
    <strong>🧭 Tier Mismatch:</strong> ${result.tier_mismatch}\n
    <strong>⚠️ Missing Info:</strong> ${JSON.stringify(result.missing_info)}
  `;
}
