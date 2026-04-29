/**
 * Forecast Module
 * Handles ingredient forecasting and prediction display
 */

import { apiService, ApiError } from './api.js';
import { uiService } from './ui.js';
import { chartManager } from './charts.js';

/**
 * Forecast Manager Class
 */
class ForecastManager {
  constructor() {
    this.forecastResult = null;
    this.currentLocation = null;
    this.selectedIngredients = [];
    this.initializeEventListeners();
    this.initSearchableSelects();
  }

  /**
   * Initialize event listeners
   */
  initializeEventListeners() {
    // Forecast form submission
    const forecastForm = document.getElementById('forecast-form');
    if (forecastForm) {
      forecastForm.addEventListener('submit', (e) => this.handleForecastSubmit(e));
    }

    // Ingredient selector (single or multiple)
    const ingredientSelect = document.getElementById('forecast-ingredient');
    if (ingredientSelect) {
      ingredientSelect.addEventListener('change', (e) => {
        if (ingredientSelect.multiple) {
          this.selectedIngredients = Array.from(e.target.selectedOptions).map(opt => opt.value);
        } else {
          this.onIngredientChange(e.target.value);
        }
      });
    }

    // Location selector
    const locationSelect = document.getElementById('forecast-location');
    if (locationSelect) {
      locationSelect.addEventListener('change', (e) => {
        this.currentLocation = e.target.value;
      });
    }

    // CSV Upload
    const csvUploadBtn = document.getElementById('csv-upload-btn');
    if (csvUploadBtn) {
      csvUploadBtn.addEventListener('click', () => this.handleCsvUpload());
    }

    // Reset button
    const resetBtn = document.getElementById('reset-forecast-btn');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => this.resetForm());
    }

    // Ensure numeric stock input remains editable on all browsers.
    const currentStockInput = document.getElementById('current_stock');
    if (currentStockInput) {
      currentStockInput.disabled = false;
      currentStockInput.readOnly = false;
      currentStockInput.removeAttribute('disabled');
      currentStockInput.removeAttribute('readonly');
    }
  }

  /**
   * Make select elements searchable by typing
   */
  initSearchableSelects() {
    const selects = document.querySelectorAll('.searchable-select');
    
    selects.forEach(select => {
      let searchTimeout;
      let searchString = '';
      
      select.addEventListener('keydown', (e) => {
        const char = String.fromCharCode(e.which).toLowerCase();
        
        // Only process alphanumeric characters
        if (/[a-z0-9]/i.test(char)) {
          e.preventDefault();
          
          // Reset search string after 500ms of inactivity
          clearTimeout(searchTimeout);
          searchString += char;
          
          // Find matching option
          const options = Array.from(select.options);
          for (let option of options) {
            if (option.value === '') continue; // Skip empty option
            if (option.textContent.toLowerCase().startsWith(searchString)) {
              select.value = option.value;
              break;
            }
          }
          
          // Reset search string after timeout
          searchTimeout = setTimeout(() => {
            searchString = '';
          }, 500);
        }
        // Allow arrow keys and enter to work normally
        else if ([13, 27, 38, 40].includes(e.which)) {
          searchString = '';
        }
      });
    });
  }

  /**
   * Handle forecast form submission
   */
  async handleForecastSubmit(event) {
    event.preventDefault();

    try {
      const form = event.target;
      const formData = new FormData(form);

      // Get ingredient(s)
      const ingredientSelect = document.getElementById('forecast-ingredient');
      let ingredients = [];
      
      if (ingredientSelect) {
        if (ingredientSelect.multiple) {
          ingredients = Array.from(ingredientSelect.selectedOptions).map(opt => opt.value);
        } else {
          const singleIngredient = formData.get('ingredient');
          if (singleIngredient) {
            ingredients = [singleIngredient];
          }
        }
      }

      if (ingredients.length === 0) {
        uiService.showWarning('Please select at least one ingredient');
        return;
      }

      // Get time horizon
      const daysAhead = parseInt(formData.get('days_ahead') || '7');
      if (![7, 14, 30].includes(daysAhead)) {
        uiService.showWarning('Time horizon must be 7, 14, or 30 days');
        return;
      }

      // Get other parameters
      const currentStockRaw = String(formData.get('current_stock') || '0').trim().replace(',', '.');
      const currentStock = Number(currentStockRaw);
      const leadTimeDays = parseInt(formData.get('lead_time_days') || '3');
      const serviceLevel = parseFloat(formData.get('service_level') || '0.95');

      if (!Number.isFinite(currentStock) || currentStock < 0) {
        uiService.showWarning('Current stock must be a number greater than or equal to 0');
        return;
      }

      const button = form.querySelector('button[type="submit"]');
      uiService.showLoading(true, button);

      // Single ingredient or batch?
      if (ingredients.length === 1) {
        const forecastData = {
          ingredient: ingredients[0],
          days_ahead: daysAhead,
          current_stock: currentStock,
          lead_time_days: leadTimeDays,
          service_level: serviceLevel
        };

        const response = await apiService.post('/api/forecast', forecastData);

        if (!response || typeof response !== 'object' || response.success !== true || !response.forecast) {
          throw new Error(response?.error || 'Invalid forecast response');
        }

        this.forecastResult = response;
        this.displayForecast(response);
        uiService.showSuccess('Forecast generated successfully');
      } else {
        // Batch forecast
        const currentStocks = {};
        ingredients.forEach(ing => {
          currentStocks[ing] = currentStock; // You could customize per ingredient
        });

        const batchData = {
          ingredients: ingredients,
          days_ahead: daysAhead,
          current_stocks: currentStocks,
          lead_time_days: leadTimeDays,
          service_level: serviceLevel
        };

        const response = await apiService.post('/api/forecast-batch', batchData);

        if (!response || response.success !== true || !response.results) {
          throw new Error(response?.error || 'Invalid batch forecast response');
        }

        this.forecastResult = response;
        this.displayBatchForecast(response);
        uiService.showSuccess(`Forecast generated for ${ingredients.length} ingredients`);
      }
    } catch (error) {
      this.handleError(error, 'Failed to generate forecast');
    } finally {
      const button = event.target.querySelector('button[type="submit"]');
      uiService.showLoading(false, button);
    }
  }

  /**
   * Handle CSV upload
   */
  async handleCsvUpload() {
    const fileInput = document.getElementById('csv-file-input');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
      uiService.showWarning('Please select a CSV file');
      return;
    }

    const file = fileInput.files[0];
    
    if (!file.name.endsWith('.csv')) {
      uiService.showWarning('Please select a valid CSV file');
      return;
    }

    try {
      uiService.showLoading(true);

      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/upload-csv', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.error || 'Upload failed');
      }

      uiService.showSuccess(`CSV uploaded: ${result.rows_added} rows for ${result.ingredients.length} ingredients`);
      
      // Optionally refresh ingredient list
      if (result.ingredients && result.ingredients.length > 0) {
        console.log('New ingredients:', result.ingredients);
      }
    } catch (error) {
      this.handleError(error, 'Failed to upload CSV');
    } finally {
      uiService.showLoading(false);
      if (fileInput) {
        fileInput.value = ''; // Clear file input
      }
    }
  }

  /**
   * Display forecast results
   */
  displayForecast(forecast) {
    if (!forecast || !forecast.forecast) {
      uiService.showWarning('No forecast data available');
      return;
    }

    // Show results section
    const resultsSection = document.getElementById('forecast-results');
    if (resultsSection) {
      resultsSection.style.display = 'block';
      uiService.scrollToElement('#forecast-results');
    }

    // Display stats
    this.displayForecastStats(forecast.forecast);

    // Display chart
    this.renderForecastChart(forecast);

    // Display table
    this.displayForecastTable(forecast.forecast, forecast.chart_data);

    // Display decision and alerts if available
    if (forecast.decision) {
      this.displayDecision(forecast.decision);
    }
    if (forecast.alerts && forecast.alerts.length > 0) {
      this.displayAlerts(forecast.alerts);
    }
  }

  /**
   * Display batch forecast results (multiple ingredients)
   */
  displayBatchForecast(batchResponse) {
    if (!batchResponse || !batchResponse.results) {
      uiService.showWarning('No forecast data available');
      return;
    }

    // Show results section
    const resultsSection = document.getElementById('forecast-results');
    if (resultsSection) {
      resultsSection.style.display = 'block';
      uiService.scrollToElement('#forecast-results');
    }

    const results = batchResponse.results;
    const successfulResults = results.filter(r => r.success);

    if (successfulResults.length === 0) {
      uiService.showError('No successful forecasts generated');
      return;
    }

    // Display comparison chart
    this.renderBatchForecastChart(successfulResults, batchResponse.days_ahead);

    // Display individual result cards
    this.displayBatchResultCards(results);
  }

  /**
   * Render batch forecast comparison chart
   */
  renderBatchForecastChart(results, daysAhead) {
    const chartElement = document.getElementById('forecast-chart');
    if (!chartElement) return;

    const today = new Date();
    const dates = Array.from({ length: daysAhead }, (_, i) => {
      const date = new Date(today);
      date.setDate(date.getDate() + i + 1);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    const colors = [
      '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
      '#1abc9c', '#34495e', '#e67e22', '#95a5a6', '#d35400'
    ];

    const datasets = results.map((result, index) => ({
      label: result.ingredient,
      data: result.forecast.predictions || [],
      borderColor: colors[index % colors.length],
      backgroundColor: `${colors[index % colors.length]}33`,
      borderWidth: 2,
      fill: false,
      tension: 0.4,
      pointRadius: 3,
      pointHoverRadius: 5
    }));

    const config = {
      type: 'line',
      data: {
        labels: dates,
        datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            display: true,
            position: 'top'
          },
          title: {
            display: true,
            text: `${daysAhead}-Day Forecast Comparison`
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Quantity' }
          }
        }
      }
    };

    chartManager.createChart('forecast-chart', config);
  }

  /**
   * Display batch result cards
   */
  displayBatchResultCards(results) {
    const tableContainer = document.getElementById('forecast-table');
    if (!tableContainer) return;

    const cardsHtml = results.map(result => {
      if (!result.success) {
        return `
          <div class="forecast-result-card error">
            <h3>${result.ingredient}</h3>
            <p class="error-message">Error: ${result.error}</p>
          </div>
        `;
      }

      const forecast = result.forecast;
      const predictions = forecast.predictions || [];
      const avg = predictions.length > 0
        ? (predictions.reduce((a, b) => a + b, 0) / predictions.length).toFixed(2)
        : 0;
      const total = predictions.length > 0
        ? predictions.reduce((a, b) => a + b, 0).toFixed(2)
        : 0;

      let alertsHtml = '';
      if (result.alerts && result.alerts.length > 0) {
        alertsHtml = `
          <div class="alerts">
            ${result.alerts.map(alert => `
              <span class="alert-badge ${alert.severity}">${alert.message}</span>
            `).join('')}
          </div>
        `;
      }

      return `
        <div class="forecast-result-card">
          <h3>${result.ingredient}</h3>
          <div class="forecast-stats-mini">
            <div class="stat-mini">
              <span class="label">Avg Daily:</span>
              <span class="value">${avg}</span>
            </div>
            <div class="stat-mini">
              <span class="label">Total:</span>
              <span class="value">${total}</span>
            </div>
            ${result.decision ? `
              <div class="stat-mini">
                <span class="label">Reorder:</span>
                <span class="value ${result.decision.reorder_needed ? 'warning' : 'success'}">
                  ${result.decision.reorder_needed ? 'Yes' : 'No'}
                </span>
              </div>
            ` : ''}
          </div>
          ${alertsHtml}
        </div>
      `;
    }).join('');

    tableContainer.innerHTML = `
      <div class="batch-forecast-results">
        ${cardsHtml}
      </div>
    `;
  }

  /**
   * Display forecast statistics
   */
  displayForecastStats(forecast) {
    const statsContainer = document.getElementById('forecast-stats');
    if (!statsContainer) return;

    const predictions = forecast.predictions || [];
    const avg = predictions.length > 0
      ? (predictions.reduce((a, b) => a + b, 0) / predictions.length).toFixed(2)
      : 0;
    const max = predictions.length > 0
      ? Math.max(...predictions).toFixed(2)
      : 0;
    const min = predictions.length > 0
      ? Math.min(...predictions).toFixed(2)
      : 0;

    const modelName = forecast.model_used || 'Model';
    let modelDetail = '';

    if (forecast.validation_metrics && typeof forecast.validation_metrics === 'object') {
      const windowDays = forecast.validation_metrics.window_days;
      const mae = forecast.validation_metrics.mae;
      const rmse = forecast.validation_metrics.rmse;

      const windowLabel = Number.isFinite(windowDays) ? `${windowDays}d` : windowDays;
      const maeLabel = Number.isFinite(mae) ? mae.toFixed(2) : mae;
      const rmseLabel = Number.isFinite(rmse) ? rmse.toFixed(2) : rmse;

      modelDetail = `Validated on last ${windowLabel} | MAE ${maeLabel} | RMSE ${rmseLabel}`;
    } else if (forecast.selection_reason) {
      modelDetail = forecast.selection_reason;
    }

    statsContainer.innerHTML = `
      <div class="stat-card">
        <h4>Average Prediction</h4>
        <p class="stat-value">${avg}</p>
      </div>
      <div class="stat-card">
        <h4>Peak Expected</h4>
        <p class="stat-value">${max}</p>
      </div>
      <div class="stat-card">
        <h4>Minimum Expected</h4>
        <p class="stat-value">${min}</p>
      </div>
      <div class="stat-card">
        <h4>Model Used</h4>
        <p class="stat-value">${modelName}</p>
        ${modelDetail ? `<small>${modelDetail}</small>` : ''}
      </div>
    `;
  }

  /**
   * Render forecast chart (single ingredient)
   */
  renderForecastChart(response) {
    const chartElement = document.getElementById('forecast-chart');
    if (!chartElement || !response.chart_data) {
      return;
    }

    const chartData = response.chart_data;

    const datasets = [{
      label: 'Historical Sales',
      data: chartData.historical,
      borderColor: '#95a5a6',
      backgroundColor: 'rgba(149, 165, 166, 0.1)',
      borderWidth: 2,
      fill: false,
      tension: 0.4,
      pointRadius: 3
    }, {
      label: 'Forecast',
      data: chartData.forecast,
      borderColor: '#3498db',
      backgroundColor: 'rgba(52, 152, 219, 0.1)',
      borderWidth: 2,
      fill: true,
      tension: 0.4,
      pointRadius: 4,
      pointHoverRadius: 6
    }];

    // Add confidence intervals if available
    if (chartData.upper_bound && chartData.upper_bound.length > 0) {
      datasets.push({
        label: 'Upper Bound',
        data: chartData.upper_bound,
        borderColor: 'rgba(52, 152, 219, 0.3)',
        borderDash: [5, 5],
        fill: false,
        pointRadius: 0
      });
    }

    if (chartData.lower_bound && chartData.lower_bound.length > 0) {
      datasets.push({
        label: 'Lower Bound',
        data: chartData.lower_bound,
        borderColor: 'rgba(52, 152, 219, 0.3)',
        borderDash: [5, 5],
        fill: false,
        pointRadius: 0
      });
    }

    const config = {
      type: 'line',
      data: {
        labels: chartData.labels,
        datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            display: true,
            position: 'top'
          },
          title: {
            display: true,
            text: `${response.ingredient || 'Ingredient'} - ${response.days_ahead} Day Forecast`
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Quantity' }
          }
        }
      }
    };

    chartManager.createChart('forecast-chart', config);
  }

  /**
   * Display decision information
   */
  displayDecision(decision) {
    const decisionContainer = document.getElementById('forecast-decision');
    if (!decisionContainer) return;

    decisionContainer.innerHTML = `
      <div class="decision-card ${decision.reorder_needed ? 'warning' : 'success'}">
        <h4>Inventory Decision</h4>
        <p><strong>Reorder Needed:</strong> ${decision.reorder_needed ? 'Yes' : 'No'}</p>
        ${decision.reorder_point ? `<p><strong>Reorder Point:</strong> ${decision.reorder_point.toFixed(2)}</p>` : ''}
        ${decision.safety_stock ? `<p><strong>Safety Stock:</strong> ${decision.safety_stock.toFixed(2)}</p>` : ''}
      </div>
    `;
    decisionContainer.style.display = 'block';
  }

  /**
   * Display alerts
   */
  displayAlerts(alerts) {
    const alertsContainer = document.getElementById('forecast-alerts');
    if (!alertsContainer) return;

    const alertsHtml = alerts.map(alert => `
      <div class="alert alert-${alert.severity || 'info'}">
        ${alert.message}
      </div>
    `).join('');

    alertsContainer.innerHTML = alertsHtml;
    alertsContainer.style.display = 'block';
  }

  /**
   * Display forecast as table
   */
  displayForecastTable(forecast, chartData) {
    const tableContainer = document.getElementById('forecast-table');
    if (!tableContainer || !forecast.predictions) {
      return;
    }

    const predictions = forecast.predictions || [];
    const labels = Array.isArray(chartData?.labels) ? chartData.labels : [];
    const forecastLabels = labels.length >= predictions.length
      ? labels.slice(-predictions.length)
      : [];

    const today = new Date();
    const rows = predictions.map((value, index) => {
      const label = forecastLabels[index];
      let dateLabel = label;

      if (!dateLabel) {
        const date = new Date(today);
        date.setDate(date.getDate() + index + 1);
        dateLabel = date.toLocaleDateString();
      }

      return `
        <tr>
          <td>${dateLabel}</td>
          <td>${parseFloat(value).toFixed(2)}</td>
          ${forecast.upper_bound && forecast.upper_bound[index] ? `<td>${parseFloat(forecast.upper_bound[index]).toFixed(2)}</td>` : '<td>-</td>'}
          ${forecast.lower_bound && forecast.lower_bound[index] ? `<td>${parseFloat(forecast.lower_bound[index]).toFixed(2)}</td>` : '<td>-</td>'}
        </tr>
      `;
    }).join('');

    tableContainer.innerHTML = `
      <table class="forecast-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Prediction</th>
            <th>Upper Bound</th>
            <th>Lower Bound</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  }

  /**
   * Handle ingredient change
   */
  async onIngredientChange(ingredient) {
    // Could load historical data here
    console.log('Ingredient selected:', ingredient);
  }

  /**
   * Reset form
   */
  resetForm() {
    const form = document.getElementById('forecast-form');
    if (form) {
      form.reset();
    }

    const resultsSection = document.getElementById('forecast-results');
    if (resultsSection) {
      resultsSection.style.display = 'none';
    }

    chartManager.destroyChart('forecast-chart');
    this.forecastResult = null;

    uiService.showSuccess('Form cleared');
  }

  /**
   * Handle errors
   */
  handleError(error, defaultMessage = 'An error occurred') {
    let message = defaultMessage;

    if (error instanceof ApiError) {
      console.error(`[API Error] ${error.code}: ${error.message}`);
    } else if (error instanceof Error) {
      console.error(`[Error] ${error.message}`);
      message = error.message;
    }

    uiService.showError(message);
  }

  /**
   * Cleanup
   */
  destroy() {
    chartManager.destroyChart('forecast-chart');
  }
}

// Initialize on DOM ready
let forecastManager = null;

document.addEventListener('DOMContentLoaded', () => {
  forecastManager = new ForecastManager();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (forecastManager) {
    forecastManager.destroy();
  }
});

export { ForecastManager };
