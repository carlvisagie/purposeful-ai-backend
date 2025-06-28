
const API_BASE_URL = 'http://localhost:5000';

async function submitDiagnostic() {
    const inputText = document.getElementById('inputText').value;
    const resultsDiv = document.getElementById('results');
    
    if (!inputText.trim()) {
        alert('Please enter some text before submitting.');
        return;
    }
    
    try {
        resultsDiv.innerHTML = '<p>Analyzing your input...</p>';
        
        const response = await fetch(`${API_BASE_URL}/api/run_diagnostic`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: inputText,
                age: 0,
                chronic: [],
                habits: [],
                tier: ""
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayResults(data);
        
    } catch (error) {
        console.error('Error:', error);
        resultsDiv.innerHTML = '<p style="color: red;">Error processing your request. Please try again.</p>';
    }
}

function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    
    let html = '<div class="results-container">';
    html += '<h2>Diagnostic Results</h2>';
    
    if (data.diagnostic_profile) {
        html += '<h3>Identified Areas:</h3>';
        for (const [category, flags] of Object.entries(data.diagnostic_profile)) {
            if (flags && flags.length > 0) {
                html += `<div class="category">`;
                html += `<strong>${category.replace('_', ' ').toUpperCase()}:</strong> `;
                html += flags.join(', ');
                html += `</div>`;
            }
        }
    }
    
    if (data.mortality_risk) {
        html += `<div class="risk-level risk-${data.mortality_risk}">`;
        html += `<strong>Risk Level:</strong> ${data.mortality_risk.toUpperCase()}`;
        html += `</div>`;
    }
    
    if (data.crisis_analysis && data.crisis_analysis.requires_immediate_attention) {
        html += '<div class="crisis-alert">';
        html += '<strong>⚠️ CRISIS ALERT:</strong> Immediate attention required. Please contact emergency services or a crisis hotline.';
        html += '</div>';
    }
    
    if (data.tier_mismatch) {
        html += '<div class="tier-mismatch">';
        html += '<strong>Recommendation:</strong> Consider upgrading your session tier for better support.';
        html += '</div>';
    }
    
    if (data.missing_info && data.missing_info.length > 0) {
        html += '<div class="missing-info">';
        html += '<strong>Additional Information Needed:</strong> ' + data.missing_info.join(', ');
        html += '</div>';
    }
    
    html += '</div>';
    resultsDiv.innerHTML = html;
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('Purposeful Live Platform loaded');
});
