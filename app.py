from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import pandas as pd
import os
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
from model import (forecast_demand, optimize_inventory, generate_alerts, 
                   calculate_error_metrics, generate_training_predictions, 
                   calculate_confidence_intervals)
from alerts import init_alerts
from models import db, User, Location, SalesRecord, Forecast, AlertPreference, AlertHistory, IngredientMaster
import json
from sqlalchemy import inspect, text

load_dotenv()

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# Database configuration
database_url = os.getenv('DATABASE_URL', 'sqlite:///restaurant_ai.db')
# Only modify SQLite URIs, leave PostgreSQL URIs as-is
if database_url.startswith('sqlite'):
    database_url = database_url.replace('sqlite:///', f'sqlite:///{os.path.dirname(os.path.abspath(__file__))}/')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', True)
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@restaurantai.com')

# Initialize alert manager
alert_manager = init_alerts(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "sales_data.csv")

# Unit conversion standards by country
UNIT_STANDARDS = {
    'US': {'weight': 'lbs', 'volume': 'fl oz', 'currency': 'USD'},
    'GB': {'weight': 'lbs', 'volume': 'fl oz', 'currency': 'GBP'},
    'CA': {'weight': 'kg', 'volume': 'ml', 'currency': 'CAD'},
    'AU': {'weight': 'kg', 'volume': 'ml', 'currency': 'AUD'},
    'IN': {'weight': 'kg', 'volume': 'ml', 'currency': 'INR'},
    'DE': {'weight': 'kg', 'volume': 'ml', 'currency': 'EUR'},
    'FR': {'weight': 'kg', 'volume': 'ml', 'currency': 'EUR'},
    'JP': {'weight': 'kg', 'volume': 'ml', 'currency': 'JPY'},
    'CN': {'weight': 'kg', 'volume': 'ml', 'currency': 'CNY'},
    'MX': {'weight': 'kg', 'volume': 'ml', 'currency': 'MXN'},
    'BR': {'weight': 'kg', 'volume': 'ml', 'currency': 'BRL'},
}

# Conversion factors to metric
CONVERSION_FACTORS = {
    'lbs_to_kg': 0.453592,
    'kg_to_lbs': 2.20462,
    'fl_oz_to_ml': 29.5735,
    'ml_to_fl_oz': 0.033814,
}

# Simple Browser fallback session map (keyed by client IP + user agent)
simple_browser_sessions = {}
ALLOWED_USER_ROLES = {'admin', 'manager', 'staff'}


def get_client_key():
    return f"{request.remote_addr}|{request.headers.get('User-Agent', '')}"


def is_simple_browser_request():
    if request.args.get('simple') == '1':
        return True
    if request.args.get('vscodeBrowserReqId'):
        return True
    user_agent = request.headers.get('User-Agent', '').lower()
    return 'vscode' in user_agent or 'electron' in user_agent


def ensure_database_schema():
    """Create tables and apply lightweight schema upgrades."""
    db.create_all()

    try:
        inspector = inspect(db.engine)
        if 'users' in inspector.get_table_names():
            columns = {column['name'] for column in inspector.get_columns('users')}
            if 'role' not in columns:
                db.session.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'manager'"))
                db.session.commit()

            db.session.execute(text("UPDATE users SET role = 'manager' WHERE role IS NULL OR role = ''"))
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Schema upgrade warning: {e}")


with app.app_context():
    ensure_database_schema()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            client_key = get_client_key()
            simple_user = simple_browser_sessions.get(client_key)
            if simple_user:
                # Verify user still exists in database
                user = User.query.filter_by(email=simple_user).first()
                if user:
                    session['user'] = user.email
                    session['name'] = user.get_full_name()
                    session['restaurant'] = user.restaurant_name
                    session['role'] = user.role or 'manager'
                    if user.location:
                        session['location'] = user.location.to_dict()
                        session['units'] = user.location.get_units()
                    else:
                        session['location'] = {}
                        session['units'] = UNIT_STANDARDS.get('US', {})
                    return f(*args, **kwargs)
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def landing():
    """Landing page - public"""
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template("landing.html", simple_session=is_simple_browser_request())

@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        selected_role = (request.form.get("role") or '').strip().lower()
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        country = request.form.get("country")
        city = request.form.get("city")

        if selected_role not in ALLOWED_USER_ROLES:
            return render_template("login.html", error="Please select a valid login type")
        
        # Check credentials from database
        user = User.query.filter_by(email=email).first()
        user_role = (user.role if user and user.role else 'manager') if user else None
        if user and user.check_password(password) and user_role == selected_role:
            session['user'] = user.email
            session['name'] = user.get_full_name()
            session['restaurant'] = user.restaurant_name
            session['role'] = user_role
            
            if request.form.get('simple_session') == '1' or is_simple_browser_request():
                simple_browser_sessions[get_client_key()] = email
            
            # Update location and units if provided
            if country or (latitude and longitude):
                location = user.location
                if not location:
                    location = Location(user_id=user.id)
                    db.session.add(location)
                
                if country:
                    location.country = country
                    location.city = city or ''
                    location.set_units(UNIT_STANDARDS.get(country, UNIT_STANDARDS.get('US', {})))
                    session['units'] = location.get_units()
                
                if latitude and longitude:
                    location.latitude = float(latitude)
                    location.longitude = float(longitude)
                
                db.session.commit()
                session['location'] = location.to_dict()
                if not country:
                    session['units'] = location.get_units() or UNIT_STANDARDS.get('US', {})
            else:
                # Use stored location or default
                if user.location:
                    session['location'] = user.location.to_dict()
                    session['units'] = user.location.get_units()
                else:
                    session['location'] = {}
                    session['units'] = UNIT_STANDARDS.get('US', {})
            
            return redirect(url_for('dashboard'))
        else:
            return render_template("login.html", error="Invalid credentials or login type")
    
    # GET request - pass URL parameters to template
    country = request.args.get('country')
    city = request.args.get('city')
    return render_template("login.html", simple_session=is_simple_browser_request(), country=country, city=city)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Signup page"""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        restaurant_name = request.form.get("restaurant_name")
        role = (request.form.get("role") or 'manager').strip().lower()
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        country = request.form.get("country")
        city = request.form.get("city")

        if role not in ALLOWED_USER_ROLES:
            return render_template("signup.html", error="Please select a valid account type")
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return render_template("signup.html", error="Email already registered")
        
        try:
            # Create new user
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                restaurant_name=restaurant_name,
                role=role
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # Get the user ID
            
            # Set location and units based on provided data
            location = Location(user_id=user.id)
            if country:
                location.country = country
                location.city = city or ''
                location.set_units(UNIT_STANDARDS.get(country, UNIT_STANDARDS.get('US', {})))
            else:
                location.set_units(UNIT_STANDARDS.get('US', {}))
            
            if latitude and longitude:
                location.latitude = float(latitude)
                location.longitude = float(longitude)
            
            db.session.add(location)
            
            # Create default alert preferences
            alert_prefs = AlertPreference(
                user_id=user.id,
                email_enabled=True,
                email_address=email,
                threshold_percentage=25
            )
            db.session.add(alert_prefs)
            
            db.session.commit()
            
            if request.form.get('simple_session') == '1' or is_simple_browser_request():
                simple_browser_sessions[get_client_key()] = email
            
            # Auto login after signup
            session['user'] = user.email
            session['name'] = user.get_full_name()
            session['restaurant'] = user.restaurant_name
            session['role'] = user.role or 'manager'
            session['location'] = location.to_dict()
            session['units'] = location.get_units()
            
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            db.session.rollback()
            return render_template("signup.html", error=f"Signup error: {str(e)}")
        
        return redirect(url_for('dashboard'))
    
    # GET request - pass URL parameters to template
    country = request.args.get('country')
    city = request.args.get('city')
    return render_template("signup.html", simple_session=is_simple_browser_request(), country=country, city=city)

@app.route("/logout")
def logout():
    """Logout user"""
    client_key = get_client_key()
    if client_key in simple_browser_sessions:
        simple_browser_sessions.pop(client_key, None)
    session.clear()
    return redirect(url_for('landing'))


@app.route("/guest-login")
def guest_login():
    """Guest login - creates a temporary session using demo account"""
    # Use the demo account as guest login
    demo_user = User.query.filter_by(email='demo@restaurant.com').first()
    
    if not demo_user:
        # Fallback: create demo account if it doesn't exist
        demo_user = User(
            email='demo@restaurant.com',
            first_name='Demo',
            last_name='User',
            restaurant_name='Demo Restaurant',
            role='staff'
        )
        demo_user.set_password('demo123')
        db.session.add(demo_user)
        
        location = Location(user_id=demo_user.id, country='US')
        location.set_units(UNIT_STANDARDS.get('US', {}))
        db.session.add(location)
        
        db.session.commit()
    
    # Create guest session
    client_key = get_client_key()
    session['user'] = demo_user.email
    session['name'] = demo_user.get_full_name()
    session['restaurant'] = demo_user.restaurant_name
    session['role'] = demo_user.role or 'staff'
    
    # Check if user provided location from landing page
    country = request.args.get('country') or request.form.get('country')
    city = request.args.get('city') or request.form.get('city')
    
    # If country was specified, update demo user's location
    if country:
        if not demo_user.location:
            demo_user.location = Location(user_id=demo_user.id)
            db.session.add(demo_user.location)
        
        demo_user.location.country = country
        demo_user.location.city = city or ''
        demo_user.location.set_units(UNIT_STANDARDS.get(country, UNIT_STANDARDS.get('US', {})))
        db.session.commit()
        session['location'] = demo_user.location.to_dict()
        session['units'] = demo_user.location.get_units()
    elif demo_user.location:
        session['location'] = demo_user.location.to_dict()
        session['units'] = demo_user.location.get_units()
    else:
        session['location'] = {}
        session['units'] = UNIT_STANDARDS.get('US', {})
    
    if is_simple_browser_request():
        simple_browser_sessions[client_key] = demo_user.email

    return redirect(url_for('dashboard'))

@app.route("/auth/<provider>")
def oauth_login(provider):
    """OAuth authentication endpoint"""
    # OAuth configuration URLs
    oauth_urls = {
        'google': 'https://accounts.google.com/o/oauth2/v2/auth',
        'microsoft': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
        'apple': 'https://appleid.apple.com/auth/authorize'
    }
    
    if provider not in oauth_urls:
        return redirect(url_for('login'))
    
    # OAuth parameters (these would need to be configured with actual client IDs)
    params = {
        'google': {
            'client_id': 'YOUR_GOOGLE_CLIENT_ID',
            'redirect_uri': request.url_root + 'auth/callback/google',
            'response_type': 'code',
            'scope': 'openid email profile'
        },
        'microsoft': {
            'client_id': 'YOUR_MICROSOFT_CLIENT_ID',
            'redirect_uri': request.url_root + 'auth/callback/microsoft',
            'response_type': 'code',
            'scope': 'openid email profile'
        },
        'apple': {
            'client_id': 'YOUR_APPLE_CLIENT_ID',
            'redirect_uri': request.url_root + 'auth/callback/apple',
            'response_type': 'code',
            'scope': 'email name'
        }
    }
    
    # Build OAuth URL
    from urllib.parse import urlencode
    auth_url = f"{oauth_urls[provider]}?{urlencode(params[provider])}"
    
    return redirect(auth_url)

@app.route("/auth/callback/<provider>")
def oauth_callback(provider):
    """OAuth callback endpoint"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return redirect(url_for('login', error=f'Social login failed: {error}'))
    
    # In production, you would:
    # 1. Exchange code for access token
    # 2. Get user info from provider
    # 3. Create or update user in database
    # 4. Set session
    
    # For demo purposes, create a mock social user
    email = f'social.user+{provider}@restaurant-ai.local'
    user = User.query.filter_by(email=email).first()
    
    if not user:
        user = User(
            email=email,
            first_name=provider.capitalize(),
            last_name='User',
            restaurant_name=f'{provider.capitalize()} Restaurant',
            role='manager'
        )
        # OAuth users have no password
        user.password_hash = ''
        db.session.add(user)
        
        # Create default location
        location = Location(user_id=user.id, country='US')
        location.set_units(UNIT_STANDARDS.get('US', {}))
        db.session.add(location)
        
        db.session.commit()
    
    session['user'] = user.email
    session['name'] = user.get_full_name()
    session['restaurant'] = user.restaurant_name
    session['role'] = user.role or 'manager'
    
    if user.location:
        session['location'] = user.location.to_dict()
        session['units'] = user.location.get_units()
    else:
        session['location'] = {}
        session['units'] = UNIT_STANDARDS.get('US', {})
    
    return redirect(url_for('dashboard'))

@app.route("/dashboard")
@login_required
def dashboard():
    """Dashboard page - protected"""
    user = session.get('user')
    location = session.get('location', {})
    units = session.get('units', UNIT_STANDARDS.get('US', {}))
    
    return render_template(
        "dashboard.html",
        user=session.get('name'),
        restaurant=session.get('restaurant'),
        location=location,
        units=units
    )

@app.route("/forecast")
@login_required
def forecast_page():
    try:
        df = pd.read_csv(DATA_PATH)
        ingredients = sorted(df["ingredient"].unique().tolist())
        return render_template(
            "index.html",
            ingredients=ingredients,
            user=session.get('name'),
            role=session.get('role', 'manager')
        )
    except Exception as e:
        return render_template(
            "index.html",
            ingredients=[],
            error=str(e),
            user=session.get('name'),
            role=session.get('role', 'manager')
        )

@app.route("/result", methods=["POST"])
@login_required
def result():
    ingredient = request.form.get("ingredient")
    current_stock = float(request.form.get("current_stock", 0))
    lead_time_days = int(request.form.get("lead_time_days", 3))
    service_level = float(request.form.get("service_level", 0.95))

    df = pd.read_csv(DATA_PATH)
    ingredient_df = df[df["ingredient"] == ingredient].copy()
    ingredient_df["date"] = pd.to_datetime(ingredient_df["date"])
    ingredient_df = ingredient_df.sort_values("date")

    forecast = forecast_demand(ingredient_df)
    decision = optimize_inventory(
        forecast=forecast,
        current_stock=current_stock,
        lead_time_days=lead_time_days,
        service_level=service_level,
    )
    alerts = generate_alerts(decision)

    chart_labels = ingredient_df["date"].dt.strftime("%Y-%m-%d").tolist()
    chart_sales = ingredient_df["quantity_sold"].tolist()

    last_date = ingredient_df["date"].max()
    forecast_labels = [
        (last_date + pd.Timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(1, 8)
    ]
    forecast_values = [forecast["avg_daily"]] * 7

    combined_labels = chart_labels + forecast_labels
    historical_series = chart_sales + [None] * len(forecast_values)
    forecast_series = [None] * len(chart_sales) + forecast_values

    # Calculate training predictions for performance comparison
    sales_array = ingredient_df["quantity_sold"].values
    model_name = forecast.get("model_used", "Moving Average")
    training_predictions = generate_training_predictions(sales_array, model_name, ingredient_df)
    
    # Calculate error metrics
    error_metrics = calculate_error_metrics(sales_array, training_predictions)
    
    # Calculate confidence intervals for forecast
    confidence_intervals = calculate_confidence_intervals(sales_array, forecast_values)

    # Check if alert should be sent for low stock
    alerts_sent = []
    user_email = session.get('user')
    if user_email:
        user = User.query.filter_by(email=user_email).first()
        if user:
            alert_prefs = {}
            for pref in user.alert_preferences:
                if pref.ingredient == ingredient:
                    alert_prefs = {
                        'min_stock': pref.min_stock_level,
                        'enabled': pref.enabled
                    }
                    break
            
            # Send low stock alert if stock is below reorder point
            if current_stock < decision['reorder_point']:
                alerts_sent = alert_manager.send_low_stock_alert(
                    {'email': user.email, 'name': user.get_full_name()},
                    ingredient,
                    current_stock,
                    decision['reorder_point'],
                    alert_prefs
                )

    return render_template(
        "result.html",
        ingredient=ingredient,
        forecast=forecast,
        decision=decision,
        alerts=alerts,
        alerts_sent=alerts_sent,
        chart_labels=combined_labels,
        chart_sales=historical_series,
        forecast_values=forecast_series,
        # New performance comparison data
        training_labels=chart_labels,
        training_actual=chart_sales,
        training_predicted=training_predictions.tolist() if hasattr(training_predictions, 'tolist') else training_predictions,
        error_metrics=error_metrics,
        # Confidence intervals
        confidence_lower=confidence_intervals['lower'],
        confidence_upper=confidence_intervals['upper'],
    )

@login_required
@app.route("/api/ingredients", methods=["GET"])
def get_ingredients():
    """API endpoint to get all ingredients"""
    try:
        df = pd.read_csv(DATA_PATH)
        ingredients = sorted(df["ingredient"].unique().tolist())
        return jsonify({"success": True, "ingredients": ingredients})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@login_required
@app.route("/api/dashboard-stats", methods=["GET"])
def dashboard_stats():
    """API endpoint for dashboard statistics"""
    try:
        df = pd.read_csv(DATA_PATH)
        df["date"] = pd.to_datetime(df["date"])

        today = datetime.now().date()
        stats = {
            "total_ingredients": int(df["ingredient"].nunique()),
            "total_sales": float(df["quantity_sold"].sum()),
            "avg_daily_sales": float(df.groupby("date")["quantity_sold"].sum().mean()),
            "date_range": {
                "start": (today - timedelta(days=6)).strftime("%Y-%m-%d"),
                "end": today.strftime("%Y-%m-%d")
            }
        }
        
        # Top ingredients by total sales
        top_ingredients = df.groupby("ingredient")["quantity_sold"].sum().sort_values(ascending=False).head(5)
        stats["top_ingredients"] = [
            {"name": name, "sales": float(sales)} 
            for name, sales in top_ingredients.items()
        ]
        
        # Recent trends (last 7 days)
        recent_start = today - timedelta(days=6)
        recent_df = df[df["date"].dt.date >= recent_start]
        daily_totals = recent_df.groupby("date")["quantity_sold"].sum().sort_index()
        date_index = pd.date_range(recent_start, today, freq="D")
        daily_totals = daily_totals.reindex(date_index, fill_value=0)
        stats["recent_trend"] = {
            "labels": [d.strftime("%Y-%m-%d") for d in date_index],
            "values": [float(v) for v in daily_totals.values]
        }
        
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@login_required
@app.route("/api/forecast", methods=["POST"])
def api_forecast():
    """API endpoint for getting forecast data with time horizon support"""
    try:
        data = request.get_json()
        ingredient = data.get("ingredient")
        current_stock = float(data.get("current_stock", 0))
        lead_time_days = int(data.get("lead_time_days", 3))
        service_level = float(data.get("service_level", 0.95))
        days_ahead = int(data.get("days_ahead", 7))  # Time horizon: 7, 14, or 30 days
        
        if not ingredient:
            return jsonify({"success": False, "error": "Ingredient is required"}), 400
        
        if days_ahead not in [7, 14, 30]:
            return jsonify({"success": False, "error": "days_ahead must be 7, 14, or 30"}), 400
        
        df = pd.read_csv(DATA_PATH)
        ingredient_df = df[df["ingredient"] == ingredient].copy()
        
        if ingredient_df.empty:
            return jsonify({"success": False, "error": f"No data found for {ingredient}"}), 404
        
        ingredient_df["date"] = pd.to_datetime(ingredient_df["date"])
        ingredient_df = ingredient_df.sort_values("date")
        
        # Generate forecast with specified time horizon
        forecast = forecast_demand(ingredient_df, periods=days_ahead)
        decision = optimize_inventory(
            forecast=forecast,
            current_stock=current_stock,
            lead_time_days=lead_time_days,
            service_level=service_level,
        )
        alerts = generate_alerts(decision)
        
        # Chart data
        chart_labels = ingredient_df["date"].dt.strftime("%Y-%m-%d").tolist()
        chart_sales = ingredient_df["quantity_sold"].tolist()
        
        last_date = ingredient_df["date"].max()
        forecast_labels = [
            (last_date + pd.Timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(1, days_ahead + 1)
        ]
        
        return jsonify({
            "success": True,
            "ingredient": ingredient,
            "days_ahead": days_ahead,
            "forecast": forecast,
            "decision": decision,
            "alerts": alerts,
            "chart_data": {
                "labels": chart_labels + forecast_labels,
                "historical": chart_sales + [None] * len(forecast_labels),
                "forecast": [None] * len(chart_sales) + forecast.get("predictions", [forecast["avg_daily"]] * days_ahead),
                "upper_bound": [None] * len(chart_sales) + (forecast.get("upper_bound") or []),
                "lower_bound": [None] * len(chart_sales) + (forecast.get("lower_bound") or [])
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/forecast-batch", methods=["POST"])
def api_forecast_batch():
    """API endpoint for batch forecasting multiple ingredients"""
    try:
        data = request.get_json()
        ingredients = data.get("ingredients", [])
        days_ahead = int(data.get("days_ahead", 7))
        current_stocks = data.get("current_stocks", {})
        lead_time_days = int(data.get("lead_time_days", 3))
        service_level = float(data.get("service_level", 0.95))
        
        if not ingredients:
            return jsonify({"success": False, "error": "At least one ingredient is required"}), 400
        
        if days_ahead not in [7, 14, 30]:
            return jsonify({"success": False, "error": "days_ahead must be 7, 14, or 30"}), 400
        
        df = pd.read_csv(DATA_PATH)
        results = []
        
        for ingredient in ingredients:
            try:
                ingredient_df = df[df["ingredient"] == ingredient].copy()
                
                if ingredient_df.empty:
                    results.append({
                        "ingredient": ingredient,
                        "success": False,
                        "error": f"No data found for {ingredient}"
                    })
                    continue
                
                ingredient_df["date"] = pd.to_datetime(ingredient_df["date"])
                ingredient_df = ingredient_df.sort_values("date")
                
                current_stock = float(current_stocks.get(ingredient, 0))
                forecast = forecast_demand(ingredient_df, periods=days_ahead)
                decision = optimize_inventory(
                    forecast=forecast,
                    current_stock=current_stock,
                    lead_time_days=lead_time_days,
                    service_level=service_level,
                )
                alerts = generate_alerts(decision)
                
                # Generate chart data
                last_date = ingredient_df["date"].max()
                forecast_labels = [
                    (last_date + pd.Timedelta(days=i)).strftime("%Y-%m-%d")
                    for i in range(1, days_ahead + 1)
                ]
                
                results.append({
                    "ingredient": ingredient,
                    "success": True,
                    "forecast": forecast,
                    "decision": decision,
                    "alerts": alerts,
                    "forecast_labels": forecast_labels
                })
            except Exception as e:
                results.append({
                    "ingredient": ingredient,
                    "success": False,
                    "error": str(e)
                })
        
        return jsonify({
            "success": True,
            "days_ahead": days_ahead,
            "results": results
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/upload-csv", methods=["POST"])
@login_required
def api_upload_csv():
    """API endpoint for uploading CSV training data"""
    try:
        if session.get('role') != 'admin':
            return jsonify({"success": False, "error": "Only admin can upload training data"}), 403

        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files["file"]
        
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        if not file.filename.endswith(".csv"):
            return jsonify({"success": False, "error": "File must be a CSV"}), 400
        
        # Read and validate CSV
        df = pd.read_csv(file)
        
        required_columns = ["date", "ingredient", "quantity_sold"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                "success": False,
                "error": f"Missing required columns: {', '.join(missing_columns)}. Required: date, ingredient, quantity_sold"
            }), 400
        
        # Validate date format
        try:
            df["date"] = pd.to_datetime(df["date"])
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Invalid date format. Use YYYY-MM-DD format. Error: {str(e)}"
            }), 400
        
        # Validate quantity_sold is numeric
        if not pd.api.types.is_numeric_dtype(df["quantity_sold"]):
            try:
                df["quantity_sold"] = pd.to_numeric(df["quantity_sold"])
            except:
                return jsonify({
                    "success": False,
                    "error": "quantity_sold column must contain numeric values"
                }), 400
        
        # Add location column if not present
        if "location" not in df.columns:
            df["location"] = "Unknown"
        
        # Load existing data and merge
        try:
            existing_df = pd.read_csv(DATA_PATH)
            existing_df["date"] = pd.to_datetime(existing_df["date"])
            
            # Combine and remove duplicates (keep newer data)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(
                subset=["date", "ingredient", "location"],
                keep="last"
            )
            combined_df = combined_df.sort_values("date")
            
            # Save back to CSV
            combined_df.to_csv(DATA_PATH, index=False)
            
            return jsonify({
                "success": True,
                "message": "CSV uploaded and merged successfully",
                "rows_added": len(df),
                "total_rows": len(combined_df),
                "ingredients": df["ingredient"].unique().tolist()
            })
        except FileNotFoundError:
            # If no existing file, save as new
            df.to_csv(DATA_PATH, index=False)
            return jsonify({
                "success": True,
                "message": "CSV uploaded successfully (new file)",
                "rows_added": len(df),
                "total_rows": len(df),
                "ingredients": df["ingredient"].unique().tolist()
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@login_required
@app.route("/api/ingredient-history/<ingredient>", methods=["GET"])
def ingredient_history(ingredient):
    """Get historical data for a specific ingredient"""
    try:
        df = pd.read_csv(DATA_PATH)
        ingredient_df = df[df["ingredient"] == ingredient].copy()
        
        if ingredient_df.empty:
            return jsonify({"success": False, "error": f"No data found for {ingredient}"}), 404
        
        ingredient_df["date"] = pd.to_datetime(ingredient_df["date"])
        ingredient_df = ingredient_df.sort_values("date")
        
        history = [
            {
                "date": row["date"].strftime("%Y-%m-%d"),
                "quantity": float(row["quantity_sold"])
            }
            for _, row in ingredient_df.iterrows()
        ]
        
        return jsonify({"success": True, "history": history})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/location/country", methods=["POST"])
def get_country_from_coordinates():
    """Get country code from latitude and longitude (public endpoint)"""
    try:
        data = request.get_json()
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        
        if not latitude or not longitude:
            return jsonify({"success": False, "error": "Latitude and longitude required"}), 400
        
        # Simple country detection based on coordinates
        # In production, use a proper reverse geocoding service like Google Maps or Nominatim
        country_map = {
            (6, 37, 68, 98): 'IN',      # India - check first for priority
            (24, 50, -125, -66): 'US',  # USA (continental)
            (50, 59, -8, 2): 'GB',      # UK
            (41, 84, -141, -52): 'CA',  # Canada
            (-44, -10, 113, 154): 'AU', # Australia
            (47, 55, 5, 15): 'DE',      # Germany
            (41, 51, -5, 10): 'FR',     # France
            (24, 46, 122, 146): 'JP',   # Japan
            (18, 54, 73, 135): 'CN',    # China
            (14, 33, -118, -86): 'MX',  # Mexico
            (-34, 6, -74, -34): 'BR',   # Brazil
        }
        
        detected_country = 'US'  # Default
        for (lat_min, lat_max, lon_min, lon_max), country in country_map.items():
            if lat_min <= latitude <= lat_max and lon_min <= longitude <= lon_max:
                detected_country = country
                print(f"Location detected: {country} (Lat: {latitude}, Lon: {longitude})")
                break
        
        # Update user's location and units if logged in
        user_email = session.get('user')
        if user_email:
            user = User.query.filter_by(email=user_email).first()
            if user:
                if not user.location:
                    user.location = Location(user_id=user.id)
                user.location.country = detected_country
                user.location.latitude = latitude
                user.location.longitude = longitude
                user.location.weight_unit = UNIT_STANDARDS.get(detected_country, UNIT_STANDARDS['US']).get('weight', 'kg')
                user.location.volume_unit = UNIT_STANDARDS.get(detected_country, UNIT_STANDARDS['US']).get('volume', 'ml')
                user.location.currency = UNIT_STANDARDS.get(detected_country, UNIT_STANDARDS['US']).get('currency', 'USD')
                db.session.commit()
                session['location'] = user.location.to_dict()
                session['units'] = user.location.get_units()
        
        return jsonify({
            "success": True,
            "country": detected_country,
            "units": UNIT_STANDARDS.get(detected_country, UNIT_STANDARDS['US']),
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "country": detected_country
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@login_required
@app.route("/api/user/location", methods=["GET"])
@login_required
def get_user_location():
    """Get user's location and unit settings"""
    try:
        # Get from session first (faster)
        location_data = session.get('location', {})
        units_data = session.get('units', UNIT_STANDARDS.get('US', {}))
        return jsonify({
            "success": True,
            "location": location_data,
            "units": units_data
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@login_required
@app.route("/api/convert-units", methods=["POST"])
def convert_units():
    """Convert units based on user's location"""
    try:
        data = request.get_json()
        value = float(data.get("value"))
        from_unit = data.get("from_unit")  # 'kg', 'lbs', 'ml', 'fl_oz'
        to_unit = data.get("to_unit")
        
        if from_unit == to_unit:
            return jsonify({"success": True, "converted_value": value})
        
        # Get conversion factor
        conversion_key = f"{from_unit}_to_{to_unit}".replace(' ', '_')
        if conversion_key in CONVERSION_FACTORS:
            converted_value = value * CONVERSION_FACTORS[conversion_key]
            return jsonify({
                "success": True,
                "original_value": value,
                "original_unit": from_unit,
                "converted_value": round(converted_value, 2),
                "converted_unit": to_unit
            })
        
        return jsonify({"success": False, "error": f"Conversion not supported"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def add_sale():
    """Add a new sales record"""
    try:
        data = request.get_json()
        ingredient = data.get("ingredient")
        date = data.get("date")
        quantity = data.get("quantity")
        
        if not all([ingredient, date, quantity]):
            return jsonify({"success": False, "error": "All fields are required"}), 400
        
        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Read existing data
        df = pd.read_csv(DATA_PATH)
        
        # Add new record
        new_record = pd.DataFrame([{
            "date": date,
            "ingredient": ingredient,
            "quantity_sold": float(quantity)
        }])
        
        df = pd.concat([df, new_record], ignore_index=True)
        df.to_csv(DATA_PATH, index=False)
        
        return jsonify({"success": True, "message": "Sale added successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@login_required
@app.route("/api/alerts/preferences", methods=["GET"])
def get_alert_preferences():
    """Get user's alert preferences"""
    try:
        user_email = session.get('user')
        user = User.query.filter_by(email=user_email).first()
        if user:
            prefs = {}
            for pref in user.alert_preferences:
                prefs[pref.ingredient] = {
                    'min_stock': pref.min_stock_level,
                    'max_stock': pref.max_stock_level,
                    'enabled': pref.enabled
                }
            return jsonify({
                "success": True,
                "preferences": prefs,
                "alerts_available": {
                    "email": alert_manager.mail is not None,
                    "sms": alert_manager.twilio_client is not None
                }
            })
        return jsonify({"success": False, "error": "User not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@login_required
@app.route("/api/alerts/preferences", methods=["POST"])
def update_alert_preferences():
    """Update user's alert preferences"""
    try:
        user_email = session.get('user')
        user = User.query.filter_by(email=user_email).first()
        data = request.get_json()
        
        if user:
            # Clear existing preferences
            AlertPreference.query.filter_by(user_id=user.id).delete()
            
            # Add new preferences from request
            ingredients = data.get('ingredients', [])
            for ing_data in ingredients:
                pref = AlertPreference(
                    user_id=user.id,
                    ingredient=ing_data.get('ingredient'),
                    min_stock_level=float(ing_data.get('min_stock', 0)),
                    max_stock_level=float(ing_data.get('max_stock', 1000)),
                    enabled=ing_data.get('enabled', True)
                )
                db.session.add(pref)
            
            # Update email if provided
            if data.get('email'):
                user.email = data.get('email')
            
            db.session.commit()
            
            prefs = {}
            for pref in user.alert_preferences:
                prefs[pref.ingredient] = {
                    'min_stock': pref.min_stock_level,
                    'max_stock': pref.max_stock_level,
                    'enabled': pref.enabled
                }
            
            return jsonify({
                "success": True,
                "message": "Alert preferences updated successfully",
                "preferences": prefs
            })
        return jsonify({"success": False, "error": "User not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@login_required
@app.route("/api/alerts/test", methods=["POST"])
def test_alert():
    """Send a test alert to verify configuration"""
    try:
        user_email = session.get('user')
        user = User.query.filter_by(email=user_email).first()
        data = request.get_json()
        channel = data.get('channel', 'email')  # 'email' or 'sms'
        
        if user:
            if channel == 'email':
                contact = user.email
                success = alert_manager.test_alert(contact, 'email')
            elif channel == 'sms':
                contact = user.phone_number if hasattr(user, 'phone_number') else None
                success = alert_manager.test_alert(contact, 'sms')
            else:
                return jsonify({"success": False, "error": "Invalid channel"}), 400
            
            if success:
                return jsonify({
                    "success": True,
                    "message": f"Test {channel} alert sent successfully"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"Failed to send test {channel} alert. Check configuration."
                }), 500
        
        return jsonify({"success": False, "error": "User not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@login_required
@app.route("/api/alerts/check-stock", methods=["POST"])
def check_stock_and_alert():
    """Check stock levels and send alerts if needed"""
    try:
        user_email = session.get('user')
        user = User.query.filter_by(email=user_email).first()
        data = request.get_json()
        ingredient = data.get('ingredient')
        current_stock = float(data.get('current_stock', 0))
        reorder_point = float(data.get('reorder_point', 0))
        
        if user:
            alert_prefs = {}
            for pref in user.alert_preferences:
                if pref.ingredient == ingredient:
                    alert_prefs = {
                        'min_stock': pref.min_stock_level,
                        'enabled': pref.enabled
                    }
                    break
            
            # Check if alert should be sent
            if current_stock < reorder_point:
                alerts_sent = alert_manager.send_low_stock_alert(
                    {'email': user.email, 'name': user.get_full_name()},
                    ingredient,
                    current_stock,
                    reorder_point,
                    alert_prefs
                )
                
                return jsonify({
                    "success": True,
                    "alert_triggered": True,
                    "alerts_sent": alerts_sent,
                    "message": f"Low stock alert sent via {', '.join(alerts_sent) if alerts_sent else 'no configured channels'}"
                })
            else:
                return jsonify({
                    "success": True,
                    "alert_triggered": False,
                    "message": "Stock level is sufficient"
                })
        
        return jsonify({"success": False, "error": "User not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ===== SETTINGS ROUTES =====

@app.route("/settings")
@login_required
def settings():
    """User settings page"""
    return render_template("settings.html", user=session.get('name'), restaurant=session.get('restaurant'))


@app.route("/api/user/profile", methods=["GET", "POST"])
@login_required
def user_profile():
    """Get or update user profile"""
    try:
        user = User.query.filter_by(email=session.get('user')).first()
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        if request.method == "GET":
            return jsonify({
                "success": True,
                "user": {
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "restaurant_name": user.restaurant_name,
                    "role": user.role
                }
            })

        elif request.method == "POST":
            data = request.get_json()
            user.first_name = data.get('first_name', user.first_name)
            user.last_name = data.get('last_name', user.last_name)
            user.restaurant_name = data.get('restaurant_name', user.restaurant_name)
            user.updated_at = datetime.utcnow()
            db.session.commit()

            # Update session
            session['name'] = user.get_full_name()
            session['restaurant'] = user.restaurant_name

            return jsonify({"success": True, "message": "Profile updated successfully"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/user/change-password", methods=["POST"])
@login_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        user = User.query.filter_by(email=session.get('user')).first()
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        # Verify current password
        if not user.check_password(current_password):
            return jsonify({"success": False, "error": "Current password is incorrect"}), 401

        # Validate new password
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        if not __import__('re').match(password_regex, new_password):
            return jsonify({
                "success": False,
                "error": "Password must be at least 8 characters with uppercase, lowercase, number, and special character"
            }), 400

        # Update password
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({"success": True, "message": "Password changed successfully"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/user/delete-account", methods=["POST"])
@login_required
def delete_account():
    """Delete user account and all associated data"""
    try:
        user = User.query.filter_by(email=session.get('user')).first()
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        # Delete all user data
        db.session.delete(user)
        db.session.commit()

        # Clear session and redirect to logout
        session.clear()

        return jsonify({"success": True, "message": "Account deleted successfully"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ===== PASSWORD RECOVERY ROUTES =====

# limiter = Limiter(
#     app=app,
#     key_func=get_remote_address,
#     default_limits=["200 per day", "50 per hour"]
# )


def generate_recovery_token(email):
    """Generate a 6-digit recovery token"""
    import random
    return str(random.randint(100000, 999999))


def store_recovery_token(email, token):
    """Store recovery token temporarily (in session or cache)"""
    if 'recovery_tokens' not in app.config:
        app.config['recovery_tokens'] = {}
    app.config['recovery_tokens'][email] = {
        'token': token,
        'timestamp': datetime.utcnow(),
        'expires_in': 3600  # 1 hour
    }


def verify_recovery_token(email, token):
    """Verify recovery token"""
    if 'recovery_tokens' not in app.config:
        return False
    
    stored = app.config['recovery_tokens'].get(email)
    if not stored:
        return False
    
    if datetime.utcnow() - stored['timestamp'] > timedelta(seconds=stored['expires_in']):
        return False
    
    return stored['token'] == token


@app.route("/password-recovery")
def password_recovery():
    """Password recovery page"""
    return render_template("password_recovery.html")


@app.route("/api/auth/request-recovery-code", methods=["POST"])
# @limiter.limit("3 per hour")
def request_recovery_code():
    """Request password recovery code"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()

        if not email:
            return jsonify({"success": False, "error": "Email is required"}), 400

        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user:
            # Don't reveal if email exists for security
            return jsonify({"success": True, "message": "If email exists, recovery code will be sent"}), 200

        # Generate and store recovery token
        token = generate_recovery_token(email)
        store_recovery_token(email, token)

        # Send email with recovery code
        try:
            from flask_mail import Message, Mail
            mail = Mail(app)
            msg = Message(
                subject="Password Recovery Code",
                recipients=[email],
                body=f"""
Hello {user.get_full_name()},

Your password recovery code is: {token}

This code will expire in 1 hour.

If you didn't request this, please ignore this email.

Best regards,
Restaurant Inventory AI Team
                """
            )
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Email error: {e}")
            # Return success even if email fails (user will see they need to check)

        return jsonify({
            "success": True,
            "message": "Recovery code sent to your email"
        })

    except Exception as e:
        app.logger.error(f"Recovery code error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/auth/verify-recovery-code", methods=["POST"])
# @limiter.limit("10 per hour")
def verify_recovery_code():
    """Verify password recovery code"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        code = data.get('code', '').strip()

        if not email or not code:
            return jsonify({"success": False, "error": "Email and code are required"}), 400

        if verify_recovery_token(email, code):
            return jsonify({"success": True, "message": "Code verified successfully"})
        else:
            return jsonify({"success": False, "error": "Invalid or expired code"}), 401

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/auth/reset-password", methods=["POST"])
# @limiter.limit("5 per hour")
def reset_password():
    """Reset password with verified code"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        new_password = data.get('new_password')

        if not email or not new_password:
            return jsonify({"success": False, "error": "Email and password are required"}), 400

        # Validate password
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        if not __import__('re').match(password_regex, new_password):
            return jsonify({
                "success": False,
                "error": "Password must be at least 8 characters with uppercase, lowercase, number, and special character"
            }), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        # Update password
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()

        # Clean up recovery token
        if 'recovery_tokens' in app.config and email in app.config['recovery_tokens']:
            del app.config['recovery_tokens'][email]

        return jsonify({"success": True, "message": "Password reset successfully"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
