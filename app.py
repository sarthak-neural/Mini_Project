from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import pandas as pd
import os
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
from model import forecast_demand, optimize_inventory, generate_alerts
from alerts import init_alerts

load_dotenv()

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.secret_key = 'your-secret-key-change-in-production'  # Change this in production!

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

# Simple in-memory user storage (replace with database in production)
users_db = {
    'demo@restaurant.com': {
        'password': 'demo123',
        'name': 'Demo User',
        'email': 'demo@restaurant.com',
        'restaurant': 'Demo Restaurant',
        'location': {'latitude': 40.7128, 'longitude': -74.0060, 'country': 'US', 'city': 'New York'},
        'units': UNIT_STANDARDS.get('US', {}),
        'alert_preferences': {
            'email_enabled': False,
            'sms_enabled': False,
            'phone_number': '',
            'alert_threshold_percentage': 20  # Alert when stock falls below 20% of reorder point
        }
    }
}

# Simple Browser fallback session map (keyed by client IP + user agent)
simple_browser_sessions = {}


def get_client_key():
    return f"{request.remote_addr}|{request.headers.get('User-Agent', '')}"


def is_simple_browser_request():
    if request.args.get('simple') == '1':
        return True
    if request.args.get('vscodeBrowserReqId'):
        return True
    user_agent = request.headers.get('User-Agent', '').lower()
    return 'vscode' in user_agent or 'electron' in user_agent

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            client_key = get_client_key()
            simple_user = simple_browser_sessions.get(client_key)
            if simple_user and simple_user in users_db:
                session['user'] = simple_user
                session['name'] = users_db[simple_user].get('name')
                session['restaurant'] = users_db[simple_user].get('restaurant')
                session['location'] = users_db[simple_user].get('location', {})
                session['units'] = users_db[simple_user].get('units', UNIT_STANDARDS.get('US', {}))
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
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        
        # Check credentials
        if email in users_db and users_db[email]['password'] == password:
            session['user'] = email
            session['name'] = users_db[email]['name']
            session['restaurant'] = users_db[email]['restaurant']
            if request.form.get('simple_session') == '1' or is_simple_browser_request():
                simple_browser_sessions[get_client_key()] = email
            
            # Update location if provided
            if latitude and longitude:
                users_db[email]['location'] = {
                    'latitude': float(latitude),
                    'longitude': float(longitude)
                }
                session['location'] = users_db[email]['location']
                session['units'] = users_db[email].get('units', UNIT_STANDARDS.get('US', {}))
            else:
                session['location'] = users_db[email].get('location', {})
                session['units'] = users_db[email].get('units', UNIT_STANDARDS.get('US', {}))
            
            return redirect(url_for('dashboard'))
        else:
            return render_template("login.html", error="Invalid email or password")
    
    return render_template("login.html", simple_session=is_simple_browser_request())

@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Signup page"""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        restaurant_name = request.form.get("restaurant_name")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        
        # Check if user already exists
        if email in users_db:
            return render_template("signup.html", error="Email already registered")
        
        # Create new user
        user_data = {
            'password': password,
            'name': f"{first_name} {last_name}",
            'restaurant': restaurant_name,
            'location': {}
        }
        
        # Add location if provided
        if latitude and longitude:
            user_data['location'] = {
                'latitude': float(latitude),
                'longitude': float(longitude)
            }
        
        users_db[email] = user_data

        if request.form.get('simple_session') == '1' or is_simple_browser_request():
            simple_browser_sessions[get_client_key()] = email
        
        # Auto login after signup
        session['user'] = email
        session['name'] = users_db[email]['name']
        session['restaurant'] = users_db[email]['restaurant']
        session['location'] = users_db[email].get('location', {})
        session['units'] = users_db[email].get('units', UNIT_STANDARDS.get('US', {}))
        
        return redirect(url_for('dashboard'))
    
    return render_template("signup.html", simple_session=is_simple_browser_request())

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
    """Guest login - creates a temporary session"""
    client_key = get_client_key()
    guest_email = f"guest_{abs(hash(client_key))}@local"
    if guest_email not in users_db:
        users_db[guest_email] = {
            'password': '',
            'name': 'Guest User',
            'restaurant': 'Guest Restaurant',
            'location': {},
            'units': UNIT_STANDARDS.get('US', {})
        }

    session['user'] = guest_email
    session['name'] = users_db[guest_email]['name']
    session['restaurant'] = users_db[guest_email]['restaurant']
    session['location'] = users_db[guest_email].get('location', {})
    session['units'] = users_db[guest_email].get('units', UNIT_STANDARDS.get('US', {}))

    if is_simple_browser_request():
        simple_browser_sessions[client_key] = guest_email

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
    email = f'social.user@{provider}.com'
    if email not in users_db:
        users_db[email] = {
            'password': '',  # No password for OAuth users
            'name': f'{provider.capitalize()} User',
            'restaurant': f'{provider.capitalize()} Restaurant',
            'provider': provider
        }
    
    session['user'] = email
    session['name'] = users_db[email]['name']
    session['restaurant'] = users_db[email]['restaurant']
    
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
        return render_template("index.html", ingredients=ingredients, user=session.get('name'))
    except Exception as e:
        return render_template("index.html", ingredients=[], error=str(e), user=session.get('name'))

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

    # Check if alert should be sent for low stock
    alerts_sent = []
    user = session.get('user')
    if user and user in users_db:
        user_data = users_db[user]
        alert_prefs = user_data.get('alert_preferences', {})
        
        # Send low stock alert if stock is below reorder point
        if current_stock < decision['reorder_point']:
            alerts_sent = alert_manager.send_low_stock_alert(
                user_data,
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
    """API endpoint for getting forecast data"""
    try:
        data = request.get_json()
        ingredient = data.get("ingredient")
        current_stock = float(data.get("current_stock", 0))
        lead_time_days = int(data.get("lead_time_days", 3))
        service_level = float(data.get("service_level", 0.95))
        
        if not ingredient:
            return jsonify({"success": False, "error": "Ingredient is required"}), 400
        
        df = pd.read_csv(DATA_PATH)
        ingredient_df = df[df["ingredient"] == ingredient].copy()
        
        if ingredient_df.empty:
            return jsonify({"success": False, "error": f"No data found for {ingredient}"}), 404
        
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
        
        # Chart data
        chart_labels = ingredient_df["date"].dt.strftime("%Y-%m-%d").tolist()
        chart_sales = ingredient_df["quantity_sold"].tolist()
        
        last_date = ingredient_df["date"].max()
        forecast_labels = [
            (last_date + pd.Timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(1, 8)
        ]
        forecast_values = [forecast["avg_daily"]] * 7
        
        return jsonify({
            "success": True,
            "ingredient": ingredient,
            "forecast": forecast,
            "decision": decision,
            "alerts": alerts,
            "chart_data": {
                "labels": chart_labels + forecast_labels,
                "historical": chart_sales + [None] * len(forecast_values),
                "forecast": [None] * len(chart_sales) + forecast_values
            }
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
        user = session.get('user')
        if user and user in users_db:
            users_db[user]['location'] = {
                'latitude': latitude,
                'longitude': longitude,
                'country': detected_country,
                'city': ''  # Would be populated by reverse geocoding service
            }
            users_db[user]['units'] = UNIT_STANDARDS.get(detected_country, UNIT_STANDARDS['US'])
            session['location'] = users_db[user]['location']
            session['units'] = users_db[user]['units']
        
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
def get_user_location():
    """Get user's location and unit settings"""
    try:
        user = session.get('user')
        if user and user in users_db:
            return jsonify({
                "success": True,
                "location": users_db[user].get('location', {}),
                "units": users_db[user].get('units', UNIT_STANDARDS.get('US', {}))
            })
        return jsonify({"success": False, "error": "User not found"}), 404
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
        user = session.get('user')
        if user and user in users_db:
            prefs = users_db[user].get('alert_preferences', {})
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
        user = session.get('user')
        data = request.get_json()
        
        if user and user in users_db:
            users_db[user]['alert_preferences'] = {
                'email_enabled': data.get('email_enabled', False),
                'sms_enabled': data.get('sms_enabled', False),
                'phone_number': data.get('phone_number', ''),
                'alert_threshold_percentage': int(data.get('alert_threshold_percentage', 20))
            }
            
            # Update email if provided
            if data.get('email'):
                users_db[user]['email'] = data.get('email')
            
            return jsonify({
                "success": True,
                "message": "Alert preferences updated successfully",
                "preferences": users_db[user]['alert_preferences']
            })
        return jsonify({"success": False, "error": "User not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@login_required
@app.route("/api/alerts/test", methods=["POST"])
def test_alert():
    """Send a test alert to verify configuration"""
    try:
        user = session.get('user')
        data = request.get_json()
        channel = data.get('channel', 'email')  # 'email' or 'sms'
        
        if user and user in users_db:
            user_data = users_db[user]
            
            if channel == 'email':
                contact = user_data.get('email')
                success = alert_manager.test_alert(contact, 'email')
            elif channel == 'sms':
                contact = user_data['alert_preferences'].get('phone_number')
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
        user = session.get('user')
        data = request.get_json()
        ingredient = data.get('ingredient')
        current_stock = float(data.get('current_stock', 0))
        reorder_point = float(data.get('reorder_point', 0))
        
        if user and user in users_db:
            user_data = users_db[user]
            alert_prefs = user_data.get('alert_preferences', {})
            
            # Check if alert should be sent
            if current_stock < reorder_point:
                alerts_sent = alert_manager.send_low_stock_alert(
                    user_data,
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

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
