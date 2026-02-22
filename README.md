# AI-Based Supply Chain Demand Forecasting & Inventory Optimization Platform

## Overview
Mini project web app for restaurant inventory management with:
1. Ingredient Stock Tracking
2. Demand Forecasting (AI)
3. Inventory Optimization (Decision Making)
4. Data Visualization
5. Basic Alert Logic
6. Ingredients Scope

## How it works
- Uploads/uses historical sales data from `data/sales_data.csv`.
- Forecasts demand using a moving-average model.
- Calculates reorder point and recommended order quantity.
- Displays results and alerts in a web UI.

## Run
1. Install dependencies: `pip install -r requirements.txt`
2. Start app: `python app.py`
3. Open: `http://127.0.0.1:5000`

## Data Scope
- `date`: sales date
- `ingredient`: ingredient name
- `quantity_sold`: units used per day
