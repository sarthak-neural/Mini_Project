// Advanced charting module for enhanced dashboard visualizations

const advancedCharts = {
    inventoryLevelChart: null,
    seasonalTrendChart: null,
    costAnalysisChart: null,
    predictionChart: null,
    ingredientHeatmap: null,
    
    /**
     * Render inventory level gauge chart
     */
    renderInventoryLevelChart: function(containerId, inventoryData) {
        const ctx = document.getElementById(containerId);
        if (!ctx) return;
        
        if (this.inventoryLevelChart) {
            this.inventoryLevelChart.destroy();
        }
        
        const totalCapacity = inventoryData.total_capacity || 1;
        const currentStock = inventoryData.current_stock || 0;
        const safetyStock = inventoryData.safety_stock || totalCapacity * 0.3;
        const reorderPoint = inventoryData.reorder_point || totalCapacity * 0.5;
        
        const percentage = (currentStock / totalCapacity) * 100;
        const safetyPercentage = (safetyStock / totalCapacity) * 100;
        const reorderPercentage = (reorderPoint / totalCapacity) * 100;
        
        // Determine color based on stock level
        let borderColor = '#4CAF50'; // Green - good
        if (currentStock <= safetyStock) {
            borderColor = '#F44336'; // Red - critical
        } else if (currentStock <= reorderPoint) {
            borderColor = '#FF9800'; // Orange - warning
        }
        
        this.inventoryLevelChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Current Stock', 'Remaining Capacity'],
                datasets: [{
                    data: [percentage, 100 - percentage],
                    backgroundColor: [borderColor, '#E8E8E8'],
                    borderColor: [borderColor, '#D0D0D0'],
                    borderWidth: 2,
                    circumference: 180,
                    rotation: 270
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + percentage.toFixed(1) + '%';
                            }
                        }
                    }
                }
            }
        });
    },
    
    /**
     * Render seasonal trend analysis
     */
    renderSeasonalTrendChart: function(containerId, seasonalData) {
        const ctx = document.getElementById(containerId);
        if (!ctx) return;
        
        if (this.seasonalTrendChart) {
            this.seasonalTrendChart.destroy();
        }
        
        this.seasonalTrendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: seasonalData.labels || [],
                datasets: [
                    {
                        label: 'Actual Sales',
                        data: seasonalData.actual || [],
                        borderColor: '#2196F3',
                        backgroundColor: 'rgba(33, 150, 243, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 3,
                        borderWidth: 2
                    },
                    {
                        label: 'Seasonal Average',
                        data: seasonalData.seasonal_avg || [],
                        borderColor: '#FF9800',
                        borderDash: [5, 5],
                        backgroundColor: 'rgba(255, 152, 0, 0.05)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 3,
                        borderWidth: 2
                    },
                    {
                        label: 'Trend Line',
                        data: seasonalData.trend || [],
                        borderColor: '#1976D2',
                        borderDash: [10, 10],
                        pointRadius: 0,
                        borderWidth: 2,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
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
                            text: 'Time Period'
                        }
                    }
                }
            }
        });
    },
    
    /**
     * Render cost analysis chart
     */
    renderCostAnalysisChart: function(containerId, costData) {
        const ctx = document.getElementById(containerId);
        if (!ctx) return;
        
        if (this.costAnalysisChart) {
            this.costAnalysisChart.destroy();
        }
        
        this.costAnalysisChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: costData.labels || [],
                datasets: [
                    {
                        label: 'Current Cost',
                        data: costData.current_cost || [],
                        borderColor: '#FF6384',
                        backgroundColor: 'rgba(255, 99, 132, 0.15)',
                        borderWidth: 2,
                        pointRadius: 4
                    },
                    {
                        label: 'Average Cost',
                        data: costData.average_cost || [],
                        borderColor: '#36A2EB',
                        backgroundColor: 'rgba(54, 162, 235, 0.15)',
                        borderWidth: 2,
                        pointRadius: 4
                    },
                    {
                        label: 'Target Cost',
                        data: costData.target_cost || [],
                        borderColor: '#4BC0C0',
                        backgroundColor: 'rgba(75, 192, 192, 0.15)',
                        borderWidth: 2,
                        pointRadius: 4
                    }
                ]
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
                    r: {
                        beginAtZero: true
                    }
                }
            }
        });
    },
    
    /**
     * Render forecast vs actual comparison
     */
    renderPredictionChart: function(containerId, predictionData) {
        const ctx = document.getElementById(containerId);
        if (!ctx) return;
        
        if (this.predictionChart) {
            this.predictionChart.destroy();
        }
        
        this.predictionChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: predictionData.labels || [],
                datasets: [
                    {
                        label: 'Actual Sales',
                        data: predictionData.actual || [],
                        borderColor: '#2196F3',
                        backgroundColor: 'rgba(33, 150, 243, 0.1)',
                        tension: 0.4,
                        fill: true,
                        borderWidth: 2,
                        pointRadius: 4
                    },
                    {
                        label: 'Predicted (Point)',
                        data: predictionData.predicted || [],
                        borderColor: '#FF9800',
                        backgroundColor: 'rgba(255, 152, 0, 0.05)',
                        tension: 0.4,
                        fill: true,
                        borderWidth: 2,
                        pointRadius: 4
                    },
                    {
                        label: 'Upper Bound (95%)',
                        data: predictionData.upper_bound || [],
                        borderColor: '#90EE90',
                        borderDash: [5, 5],
                        fill: false,
                        pointRadius: 0,
                        borderWidth: 1
                    },
                    {
                        label: 'Lower Bound (95%)',
                        data: predictionData.lower_bound || [],
                        borderColor: '#90EE90',
                        borderDash: [5, 5],
                        fill: false,
                        pointRadius: 0,
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    filler: {
                        propagate: true
                    },
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
                            text: 'Units'
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
    },
    
    /**
     * Render ingredient usage heatmap
     */
    renderIngredientHeatmap: function(containerId, heatmapData) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = '';
        
        const table = document.createElement('table');
        table.className = 'ingredient-heatmap';
        
        // Header row
        const headerRow = document.createElement('tr');
        headerRow.innerHTML = '<th>Ingredient</th>';
        heatmapData.days?.forEach(day => {
            const th = document.createElement('th');
            th.textContent = day;
            headerRow.appendChild(th);
        });
        table.appendChild(headerRow);
        
        // Data rows
        heatmapData.data?.forEach(row => {
            const tr = document.createElement('tr');
            
            const nameCell = document.createElement('td');
            nameCell.className = 'ingredient-name';
            nameCell.textContent = row.name;
            tr.appendChild(nameCell);
            
            row.values?.forEach(value => {
                const td = document.createElement('td');
                td.className = 'heatmap-cell';
                td.textContent = value.toFixed(1);
                
                // Color intensity based on value
                const maxValue = Math.max(...heatmapData.data.flatMap(r => r.values));
                const intensity = value / maxValue;
                const hue = (1 - intensity) * 120; // Green to Red
                td.style.backgroundColor = `hsl(${hue}, 100%, 50%)`;
                td.style.color = intensity > 0.7 ? 'white' : 'black';
                
                tr.appendChild(td);
            });
            
            table.appendChild(tr);
        });
        
        container.appendChild(table);
    },
    
    /**
     * Render inventory optimization recommendations
     */
    renderOptimizationRecommendations: function(containerId, recommendations) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        let html = '';
        
        recommendations.forEach(rec => {
            const urgency = rec.urgency || 'info';
            const urgencyClass = `urgency-${urgency}`;
            
            html += `
                <div class="recommendation-card ${urgencyClass}">
                    <div class="recommendation-header">
                        <h4>${rec.ingredient}</h4>
                        <span class="urgency-badge">${urgency.toUpperCase()}</span>
                    </div>
                    <div class="recommendation-body">
                        <p><strong>Current Stock:</strong> ${rec.current_stock?.toFixed(2) || 'N/A'}</p>
                        <p><strong>Reorder Point:</strong> ${rec.reorder_point?.toFixed(2) || 'N/A'}</p>
                        <p><strong>Recommended Order:</strong> ${rec.recommended_order?.toFixed(2) || 'N/A'}</p>
                        <p><strong>Days Until Stockout:</strong> ${rec.days_until_stockout || 'N/A'}</p>
                        <p class="recommendation-text">${rec.message}</p>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = advancedCharts;
}
