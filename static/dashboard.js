// Dashboard JavaScript for real-time interactivity

let trendChart = null;
let topIngredientsChart = null;

// Load dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
    loadIngredients();
    setDefaultDate();
    
    // Attach form event listeners after DOM is ready
    const addSaleForm = document.getElementById('addSaleForm');
    if (addSaleForm) {
        addSaleForm.addEventListener('submit', handleAddSaleSubmit);
    }
    
    // Close modal when clicking outside
    window.onclick = function(event) {
        const modal = document.getElementById('addSaleModal');
        if (event.target === modal) {
            closeAddSaleModal();
        }
    }
});

// Load dashboard statistics
async function loadDashboard() {
    try {
        showLoading(true);
        const response = await fetch('/api/dashboard-stats');
        const data = await response.json();

        if (data.success) {
            console.log('Dashboard data received:', data.stats);
            updateStats(data.stats);
            renderCharts(data.stats);
            showLoading(false);
        } else {
            console.error('API returned error:', data.error);
            showError('Failed to load dashboard: ' + data.error);
        }
    } catch (error) {
        console.error('JavaScript error in loadDashboard:', error);
        showError('Error loading dashboard: ' + error.message);
    }
}

// Update statistics cards
function updateStats(stats) {
    try {
        const totalIngredientsEl = document.getElementById('total-ingredients');
        const totalSalesEl = document.getElementById('total-sales');
        const avgDailySalesEl = document.getElementById('avg-daily-sales');
        const dateRangeEl = document.getElementById('date-range');
        
        if (!totalIngredientsEl || !totalSalesEl || !avgDailySalesEl || !dateRangeEl) {
            console.error('One or more stat card elements not found');
            return;
        }
        
        totalIngredientsEl.textContent = stats.total_ingredients;
        totalSalesEl.textContent = stats.total_sales.toFixed(0);
        avgDailySalesEl.textContent = stats.avg_daily_sales.toFixed(1);

        const dateRange = `${stats.date_range.start} to ${stats.date_range.end}`;
        dateRangeEl.textContent = dateRange;
        
        console.log('Stats updated successfully');
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

// Render charts
function renderCharts(stats) {
    try {
        console.log('Starting to render charts...');
        
        // Check if Chart library is loaded
        if (typeof Chart === 'undefined') {
            console.error('Chart.js library not loaded');
            showError('Chart library failed to load');
            return;
        }
        
        // Trend Chart
        const trendCtx = document.getElementById('trendChart');
        if (!trendCtx) {
            console.error('Canvas element trendChart not found');
            return;
        }
        
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
        
        console.log('Trend chart rendered successfully');

        // Top Ingredients Chart
        const topCtx = document.getElementById('topIngredientsChart');
        if (!topCtx) {
            console.error('Canvas element topIngredientsChart not found');
            return;
        }
        
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
        
        console.log('Top ingredients chart rendered successfully');
    } catch (error) {
        console.error('Error rendering charts:', error);
        showError('Error rendering charts: ' + error.message);
    }
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
    loadIngredients(); // Ensure ingredients are loaded when modal opens
    document.getElementById('addSaleModal').style.display = 'flex';
    // Focus on the select element to enable dropdown
    setTimeout(() => {
        document.getElementById('sale-ingredient').focus();
    }, 100);
}

function closeAddSaleModal() {
    document.getElementById('addSaleModal').style.display = 'none';
    document.getElementById('addSaleForm').reset();
}

// Handle add sale form submission
async function handleAddSaleSubmit(e) {
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
}
