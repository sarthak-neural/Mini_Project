// Dashboard JavaScript for real-time interactivity

let trendChart = null;
let topIngredientsChart = null;

// Load dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
    loadIngredients();
    setDefaultDate();
});

// Load dashboard statistics
async function loadDashboard() {
    try {
        showLoading(true);
        const response = await fetch('/api/dashboard-stats');
        const data = await response.json();

        if (data.success) {
            updateStats(data.stats);
            renderCharts(data.stats);
            showLoading(false);
        } else {
            showError('Failed to load dashboard: ' + data.error);
        }
    } catch (error) {
        showError('Error loading dashboard: ' + error.message);
    }
}

// Update statistics cards
function updateStats(stats) {
    document.getElementById('total-ingredients').textContent = stats.total_ingredients;
    document.getElementById('total-sales').textContent = stats.total_sales.toFixed(0);
    document.getElementById('avg-daily-sales').textContent = stats.avg_daily_sales.toFixed(1);

    const dateRange = `${stats.date_range.start} to ${stats.date_range.end}`;
    document.getElementById('date-range').textContent = dateRange;
}

// Render charts
function renderCharts(stats) {
    // Trend Chart
    const trendCtx = document.getElementById('trendChart');
    if (trendChart) {
        trendChart.destroy();
    }
    
    trendChart = new Chart(trendCtx, {
        type: 'line',
        data: {
            labels: stats.recent_trend.labels,
            datasets: [{
                label: 'Daily Sales',
                data: stats.recent_trend.values,
                borderColor: '#2196F3',
                backgroundColor: 'rgba(33, 150, 243, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 5,
                pointHoverRadius: 7
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

    // Top Ingredients Chart
    const topCtx = document.getElementById('topIngredientsChart');
    if (topIngredientsChart) {
        topIngredientsChart.destroy();
    }

    const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'];
    
    topIngredientsChart = new Chart(topCtx, {
        type: 'bar',
        data: {
            labels: stats.top_ingredients.map(item => item.name),
            datasets: [{
                label: 'Total Sales',
                data: stats.top_ingredients.map(item => item.sales),
                backgroundColor: colors,
                borderColor: colors.map(color => color),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
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
                        text: 'Ingredient'
                    }
                }
            }
        }
    });
}

// Load ingredients for the modal
async function loadIngredients() {
    try {
        const response = await fetch('/api/ingredients');
        const data = await response.json();

        if (data.success) {
            const select = document.getElementById('sale-ingredient');
            select.innerHTML = '<option value="">Select ingredient...</option>';
            data.ingredients.forEach(ingredient => {
                const option = document.createElement('option');
                option.value = ingredient;
                option.textContent = ingredient;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading ingredients:', error);
    }
}

// Set default date to today
function setDefaultDate() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('sale-date').value = today;
}


// Show/hide loading indicator
function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'flex' : 'none';
    document.getElementById('dashboard-content').style.display = show ? 'none' : 'block';
}

// Show error message
function showError(message) {
    showLoading(false);
    alert(message);
}

// Refresh dashboard
function refreshDashboard() {
    loadDashboard();
}

// Modal functions
function showAddSaleModal() {
    document.getElementById('addSaleModal').style.display = 'flex';
}

function closeAddSaleModal() {
    document.getElementById('addSaleModal').style.display = 'none';
    document.getElementById('addSaleForm').reset();
}

// Handle add sale form submission
document.getElementById('addSaleForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const ingredient = document.getElementById('sale-ingredient').value;
    const date = document.getElementById('sale-date').value;
    const quantity = document.getElementById('sale-quantity').value;

    try {
        const response = await fetch('/api/add-sale', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ingredient: ingredient,
                date: date,
                quantity: parseFloat(quantity)
            })
        });

        const data = await response.json();

        if (data.success) {
            alert('Sale added successfully!');
            closeAddSaleModal();
            refreshDashboard();
        } else {
            alert('Error adding sale: ' + data.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
});

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('addSaleModal');
    if (event.target === modal) {
        closeAddSaleModal();
    }
}
