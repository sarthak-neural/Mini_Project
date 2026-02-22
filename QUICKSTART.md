# Quick Start Guide

## 🚀 Getting Started in 3 Steps

### Step 1: Install Dependencies
```bash
pip install flask pandas numpy
```

### Step 2: Run the Application
```bash
python app.py
```

### Step 3: Open Your Browser
Navigate to: **http://localhost:5000**

---

## 📋 What You'll See

### Dashboard (Home Page)
- **Total Ingredients**: Number of unique ingredients tracked
- **Total Sales**: Cumulative sales across all ingredients
- **Average Daily Sales**: Mean daily sales volume
- **Sales Trend Chart**: Last 7 days visualization
- **Top Ingredients**: Best-selling items

### Forecast Page
1. Select an ingredient
2. Enter current stock level
3. Set supplier lead time (days)
4. Choose service level (0-1)
5. Click "Generate Forecast"

### Results Page
- Daily and weekly demand forecasts
- Reorder point calculation
- Safety stock recommendation
- Visual trend analysis
- Printable report

---

## 🎯 Common Tasks

### Add a New Sale Record
1. Go to Dashboard
2. Click "Add Sale Record"
3. Fill in: Ingredient, Date, Quantity
4. Click "Add Sale"

### Generate a Forecast
1. Click "Forecast" in navigation
2. Choose ingredient
3. Adjust parameters
4. Submit form

### View Historical Data
1. Go to Forecast page
2. Select an ingredient
3. Preview chart appears automatically

---

## 🔧 Configuration

### Change Server Port
Edit `app.py`, last line:
```python
app.run(debug=True, host='0.0.0.0', port=8080)  # Change 5000 to 8080
```

### Modify Forecast Parameters
Edit `model.py`:
- `window` parameter: Historical data window (default: 7 days)
- Safety stock calculation can be adjusted

---

## 📊 Sample Data

The project includes sample sales data for:
- Tomato
- Cheese
- Dough

Data range: January 1-8, 2026

---

## ✨ Features at a Glance

✅ Real-time dashboard with live statistics  
✅ Interactive charts (Chart.js)  
✅ AI-powered demand forecasting  
✅ Inventory optimization engine  
✅ REST API endpoints  
✅ Responsive design (mobile-friendly)  
✅ Modal-based data entry  
✅ Print-friendly reports  
✅ No database required (CSV-based)  

---

## 🆘 Need Help?

Check the main README.md for:
- Detailed API documentation
- Troubleshooting guide
- Architecture overview
- Customization tips

---

**Ready to optimize your restaurant inventory? Start the server and explore!**
