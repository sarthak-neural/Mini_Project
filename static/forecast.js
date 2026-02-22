// Forecast page JavaScript

let previewChart = null;

document.addEventListener('DOMContentLoaded', function() {
    // Add ingredient change listener for preview
    document.getElementById('ingredient').addEventListener('change', function() {
        const ingredient = this.value;
        if (ingredient) {
            loadIngredientPreview(ingredient);
        }
    });
});

// Load and display ingredient history preview
async function loadIngredientPreview(ingredient) {
    try {
        const response = await fetch(`/api/ingredient-history/${ingredient}`);
        const data = await response.json();

        if (data.success) {
            showPreviewChart(data.history);
        }
    } catch (error) {
        console.error('Error loading preview:', error);
    }
}

// Show preview chart
function showPreviewChart(history) {
    const previewSection = document.getElementById('quickPreview');
    previewSection.style.display = 'block';

    const ctx = document.getElementById('previewChart');
    
    if (previewChart) {
        previewChart.destroy();
    }

    const labels = history.map(item => item.date);
    const data = history.map(item => item.quantity);

    previewChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Historical Sales',
                data: data,
                borderColor: '#2b3a67',
                backgroundColor: 'rgba(43, 58, 103, 0.1)',
                tension: 0.3,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Units Sold'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            }
        }
    });
}

// Reset form
function resetForm() {
    document.getElementById('forecastForm').reset();
    document.getElementById('quickPreview').style.display = 'none';
    if (previewChart) {
        previewChart.destroy();
        previewChart = null;
    }
}
