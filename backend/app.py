"""
IMPORTANT: This file should not be used directly in production.
Use the app package and create_app() factory pattern instead.

For backwards compatibility with existing scripts:
- init_db.py
- tests.py

This module re-exports the app instance created with the proper factory pattern.
For all new code, use:
    from app import create_app
    app = create_app(os.getenv('FLASK_ENV', 'development'))
"""

import os
import re
from dotenv import load_dotenv
from functools import wraps
from flask import session, request, redirect, url_for, render_template, jsonify, flash
from datetime import datetime, timedelta
from sqlalchemy import text, inspect
import pandas as pd
import numpy as np
from model import (
    forecast_demand,
    optimize_inventory,
    generate_alerts,
    generate_training_predictions,
    calculate_error_metrics,
    calculate_confidence_intervals,
    prepare_daily_sales_series,
)

# Load environment variables
load_dotenv()

# Import the factory function and create app instance
from app import create_app
from models import db, User, Location, SalesRecord, Forecast, AlertPreference, AlertHistory, IngredientMaster

# Create production-safe app instance (uses environment to determine config)
_config = os.getenv('FLASK_ENV', 'development')
app = create_app(_config)

# Data path for CSV files
DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'sales_data.csv')

# Global variables for session management
simple_browser_sessions = {}
otp_storage = {}

# Constants
ALLOWED_USER_ROLES = ['manager', 'admin', 'chef']
GUEST_DEMO_EMAIL = 'demo@restaurant.com'


class CountryUnitMap(dict):
    """Dictionary-like unit map with sensible defaults for all countries."""

    IMPERIAL_UNIT_COUNTRIES = {'US', 'LR', 'MM'}
    CURRENCY_BY_COUNTRY = {
        'AE': 'AED', 'AR': 'ARS', 'AT': 'EUR', 'AU': 'AUD', 'BD': 'BDT', 'BE': 'EUR',
        'BG': 'BGN', 'BH': 'BHD', 'BR': 'BRL', 'CA': 'CAD', 'CH': 'CHF', 'CL': 'CLP',
        'CN': 'CNY', 'CO': 'COP', 'CZ': 'CZK', 'DE': 'EUR', 'DK': 'DKK', 'EG': 'EGP',
        'ES': 'EUR', 'FI': 'EUR', 'FR': 'EUR', 'GB': 'GBP', 'GR': 'EUR', 'HK': 'HKD',
        'HR': 'EUR', 'HU': 'HUF', 'ID': 'IDR', 'IE': 'EUR', 'IL': 'ILS', 'IN': 'INR',
        'IS': 'ISK', 'IT': 'EUR', 'JP': 'JPY', 'KE': 'KES', 'KR': 'KRW', 'KW': 'KWD',
        'LK': 'LKR', 'MA': 'MAD', 'MX': 'MXN', 'MY': 'MYR', 'NG': 'NGN', 'NL': 'EUR',
        'NO': 'NOK', 'NZ': 'NZD', 'OM': 'OMR', 'PE': 'PEN', 'PH': 'PHP', 'PK': 'PKR',
        'PL': 'PLN', 'PT': 'EUR', 'QA': 'QAR', 'RO': 'RON', 'RS': 'RSD', 'RU': 'RUB',
        'SA': 'SAR', 'SE': 'SEK', 'SG': 'SGD', 'TH': 'THB', 'TR': 'TRY', 'TW': 'TWD',
        'UA': 'UAH', 'US': 'USD', 'VN': 'VND', 'ZA': 'ZAR'
    }

    def units_for_country(self, country_code):
        code = (country_code or 'US').upper()
        if code in self:
            return dict(super().get(code))

        weight = 'lbs' if code in self.IMPERIAL_UNIT_COUNTRIES else 'kg'
        volume = 'fl oz' if code in self.IMPERIAL_UNIT_COUNTRIES else 'ml'
        currency = self.CURRENCY_BY_COUNTRY.get(code, 'USD')
        return {'weight': weight, 'volume': volume, 'currency': currency}

    def get(self, key, default=None):
        if key is None:
            return dict(super().get('US', default or {}))
        return self.units_for_country(str(key))


UNIT_STANDARDS = CountryUnitMap({
    'US': {'weight': 'lbs', 'volume': 'fl oz', 'currency': 'USD'},
    'CA': {'weight': 'kg', 'volume': 'ml', 'currency': 'CAD'},
    'GB': {'weight': 'kg', 'volume': 'ml', 'currency': 'GBP'},
    'AU': {'weight': 'kg', 'volume': 'ml', 'currency': 'AUD'},
    'IN': {'weight': 'kg', 'volume': 'ml', 'currency': 'INR'},
    'DE': {'weight': 'kg', 'volume': 'ml', 'currency': 'EUR'},
    'FR': {'weight': 'kg', 'volume': 'ml', 'currency': 'EUR'},
    'JP': {'weight': 'kg', 'volume': 'ml', 'currency': 'JPY'},
    'CN': {'weight': 'kg', 'volume': 'ml', 'currency': 'CNY'},
    'MX': {'weight': 'kg', 'volume': 'ml', 'currency': 'MXN'},
    'BR': {'weight': 'kg', 'volume': 'ml', 'currency': 'BRL'},
})

# Re-export models for backwards compatibility
__all__ = [
    'app',
    'db',
    'User',
    'Location', 
    'SalesRecord',
    'Forecast',
    'AlertPreference',
    'AlertHistory',
    'IngredientMaster'
]

def verify_otp(phone_number, otp):
    """Verify OTP and check if not expired"""
    if phone_number not in otp_storage:
        return False
    
    stored = otp_storage[phone_number]
    if datetime.now() > stored['expires']:
        del otp_storage[phone_number]
        return False
    
    if stored['otp'] == otp:
        # OTP is valid, remove it from storage
        del otp_storage[phone_number]
        return True
    
    return False

def get_otp_role(phone_number):
    """Get the role associated with a pending OTP"""
    if phone_number in otp_storage:
        return otp_storage[phone_number].get('role')
    return None


def get_client_key():
    return f"{request.remote_addr}|{request.headers.get('User-Agent', '')}"


def is_simple_browser_request():
    if request.args.get('simple') == '1':
        return True 
    if request.args.get('vscodeBrowserReqId'):
        return True
    user_agent = request.headers.get('User-Agent', '').lower()
    return 'vscode' in user_agent or 'electron' in user_agent


def get_current_user():
    """Get currently logged-in user from session."""
    user_email = session.get('user')
    if not user_email:
        return None
    return User.query.filter_by(email=user_email).first()


def _normalize_ingredient_name(name):
    return (name or '').strip().lower()


def _get_ingredient_dataframe(ingredient, user=None):
    """Return historical sales for an ingredient, preferring user data over shared CSV data."""
    normalized_ingredient = _normalize_ingredient_name(ingredient)
    if not normalized_ingredient:
        return pd.DataFrame(columns=["date", "ingredient", "quantity_sold"])

    # 1) Use current user's sales records when available for personalized forecasting.
    if user:
        sales_rows = SalesRecord.query.filter_by(user_id=user.id).all()
        if sales_rows:
            user_df = pd.DataFrame([
                {
                    "date": row.sale_date,
                    "ingredient": row.ingredient,
                    "quantity_sold": row.quantity_sold,
                }
                for row in sales_rows
            ])

            user_df["ingredient_norm"] = user_df["ingredient"].astype(str).str.strip().str.lower()
            user_df = user_df[user_df["ingredient_norm"] == normalized_ingredient].copy()
            if not user_df.empty:
                user_df["date"] = pd.to_datetime(user_df["date"])
                user_df = user_df.sort_values("date")
                return user_df[["date", "ingredient", "quantity_sold"]]

    # 2) Fallback to shared CSV dataset.
    df = pd.read_csv(DATA_PATH)
    df["ingredient_norm"] = df["ingredient"].astype(str).str.strip().str.lower()
    ingredient_df = df[df["ingredient_norm"] == normalized_ingredient].copy()
    if ingredient_df.empty:
        return pd.DataFrame(columns=["date", "ingredient", "quantity_sold"])

    ingredient_df["date"] = pd.to_datetime(ingredient_df["date"])
    ingredient_df = ingredient_df.sort_values("date")
    return ingredient_df[["date", "ingredient", "quantity_sold"]]


def ensure_database_schema():
    """Create tables and apply lightweight schema upgrades."""
    db.create_all()

    try:
        inspector = inspect(db.engine)
        if 'users' in inspector.get_table_names():
            columns = {column['name'] for column in inspector.get_columns('users')}
            
            # Add role column if missing
            if 'role' not in columns:
                db.session.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'manager'"))
                db.session.commit()
                print("✓ Added 'role' column to users table")

            # Add phone_number column if missing
            if 'phone_number' not in columns:
                db.session.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR(20)"))
                db.session.commit()
                print("✓ Added 'phone_number' column to users table")

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
        phone_number = request.form.get("phone_number")
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
        
        # Check if phone number already exists
        if phone_number and User.query.filter_by(phone_number=phone_number).first():
            return render_template("signup.html", error="Phone number already registered")
        
        try:
            # Create new user
            user = User(
                email=email,
                phone_number=phone_number,
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
            
            # Create default alert preferences with auto-synced email and phone
            alert_prefs = AlertPreference(
                user_id=user.id,
                email_enabled=True,
                email_address=email,
                sms_enabled=bool(phone_number),  # Enable SMS if phone number provided
                phone_number=phone_number,  # Auto-sync phone number
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

@app.route("/login/phone/send-otp", methods=["POST"])
def send_phone_otp():
    """Send OTP to phone number for login"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        role = (data.get('role') or '').strip().lower()
        
        if not phone_number:
            return jsonify({'success': False, 'error': 'Phone number is required'}), 400
        
        if role not in ALLOWED_USER_ROLES:
            return jsonify({'success': False, 'error': 'Invalid login type'}), 400
        
        # Check if user exists with this phone number and role
        user = User.query.filter_by(phone_number=phone_number).first()
        if not user:
            return jsonify({'success': False, 'error': 'Phone number not registered'}), 404
        
        user_role = (user.role if user and user.role else 'manager')
        if user_role != role:
            return jsonify({'success': False, 'error': 'Invalid phone number or login type'}), 401
        
        # Generate and store OTP
        otp = generate_otp()
        store_otp(phone_number, otp, role)
        
        # Send OTP via SMS using Twilio
        sms_sent = False
        sms_error = None
        
        if TWILIO_AVAILABLE:
            twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
            twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
            twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
            
            if twilio_sid and twilio_token and twilio_phone:
                try:
                    client = Client(twilio_sid, twilio_token)
                    message = client.messages.create(
                        body=f"Your Restaurant Inventory AI login code is: {otp}. Valid for 5 minutes.",
                        from_=twilio_phone,
                        to=phone_number
                    )
                    sms_sent = True
                    print(f"✓ SMS sent to {phone_number} (SID: {message.sid})")
                except Exception as e:
                    sms_error = str(e)
                    print(f"✗ Failed to send SMS to {phone_number}: {e}")
            else:
                print("⚠ Twilio credentials not configured in .env file")
        
        # For development or when SMS fails, log OTP to console
        if not sms_sent:
            print(f"\n{'='*50}")
            print(f"📱 OTP for {phone_number}: {otp}")
            print(f"⏰ Valid for 5 minutes")
            print(f"{'='*50}\n")
        
        response_data = {
            'success': True, 
            'message': 'OTP sent successfully' if sms_sent else 'OTP generated (check console)',
        }
        
        # Include OTP in response only in development mode (DEBUG=True)
        if app.debug:
            response_data['otp'] = otp
            response_data['dev_mode'] = True
        
        if sms_error:
            response_data['sms_error'] = sms_error
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/login/phone/verify-otp", methods=["POST"])
def verify_phone_otp():
    """Verify OTP and login user"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        otp = data.get('otp')
        role = (data.get('role') or '').strip().lower()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        country = data.get('country')
        city = data.get('city')
        
        if not phone_number or not otp:
            return jsonify({'success': False, 'error': 'Phone number and OTP are required'}), 400
        
        # Verify OTP
        if not verify_otp(phone_number, otp):
            return jsonify({'success': False, 'error': 'Invalid or expired OTP'}), 401
        
        # Get user by phone number
        user = User.query.filter_by(phone_number=phone_number).first()
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user_role = (user.role if user and user.role else 'manager')
        if user_role != role:
            return jsonify({'success': False, 'error': 'Invalid login type'}), 401
        
        # Login successful - create session
        session['user'] = user.email
        session['name'] = user.get_full_name()
        session['restaurant'] = user.restaurant_name
        session['role'] = user_role
        
        if data.get('simple_session') == '1' or is_simple_browser_request():
            simple_browser_sessions[get_client_key()] = user.email
        
        # Update location if provided
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
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'redirect': url_for('dashboard')
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
    demo_user = User.query.filter_by(email=GUEST_DEMO_EMAIL).first()
    
    if not demo_user:
        # Fallback: create demo account if it doesn't exist
        demo_user = User(
            email=GUEST_DEMO_EMAIL,
            first_name='Demo',
            last_name='User',
            restaurant_name='Demo Restaurant',
            role='staff'
        )
        # Keep a valid password for compatibility with stricter password policy.
        demo_user.set_password('DemoGuest123!')
        db.session.add(demo_user)
        db.session.flush()
        
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
    
    # Get OAuth credentials from environment
    oauth_credentials = {
        'google': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        },
        'microsoft': {
            'client_id': os.getenv('MICROSOFT_CLIENT_ID'),
            'client_secret': os.getenv('MICROSOFT_CLIENT_SECRET'),
        },
        'apple': {
            'client_id': os.getenv('APPLE_CLIENT_ID'),
            'client_secret': os.getenv('APPLE_CLIENT_SECRET'),
        }
    }
    
    # Check if credentials are configured
    creds = oauth_credentials.get(provider)
    if not creds or not creds['client_id'] or 'your-' in creds['client_id']:
        return redirect(url_for('login', error=f'{provider.capitalize()} OAuth not configured yet'))
    
    # OAuth parameters
    params = {
        'google': {
            'client_id': creds['client_id'],
            'redirect_uri': request.url_root.rstrip('/') + url_for('oauth_callback', provider='google'),
            'response_type': 'code',
            'scope': 'openid email profile'
        },
        'microsoft': {
            'client_id': creds['client_id'],
            'redirect_uri': request.url_root.rstrip('/') + url_for('oauth_callback', provider='microsoft'),
            'response_type': 'code',
            'scope': 'openid email profile'
        },
        'apple': {
            'client_id': creds['client_id'],
            'redirect_uri': request.url_root.rstrip('/') + url_for('oauth_callback', provider='apple'),
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
    import requests
    import jwt
    
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return redirect(url_for('login', error=f'Social login failed: {error}'))
    
    if not code:
        return redirect(url_for('login', error='No authorization code received'))
    
    # Get OAuth credentials from environment
    oauth_credentials = {
        'google': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'token_url': 'https://oauth2.googleapis.com/token'
        },
        'microsoft': {
            'client_id': os.getenv('MICROSOFT_CLIENT_ID'),
            'client_secret': os.getenv('MICROSOFT_CLIENT_SECRET'),
            'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
        },
        'apple': {
            'client_id': os.getenv('APPLE_CLIENT_ID'),
            'client_secret': os.getenv('APPLE_CLIENT_SECRET'),
            'token_url': 'https://appleid.apple.com/auth/oauth2/token'
        }
    }
    
    creds = oauth_credentials.get(provider)
    if not creds or not creds['client_id']:
        return redirect(url_for('login', error=f'{provider.capitalize()} OAuth not configured'))
    
    try:
        # Exchange authorization code for access token
        token_data = {
            'client_id': creds['client_id'],
            'client_secret': creds['client_secret'],
            'code': code,
            'redirect_uri': request.url_root.rstrip('/') + url_for('oauth_callback', provider=provider),
            'grant_type': 'authorization_code'
        }
        
        token_response = requests.post(creds['token_url'], data=token_data, timeout=10)
        token_response.raise_for_status()
        token_info = token_response.json()
        
        # Get user info from provider
        user_info = None
        
        if provider == 'google':
            userinfo_response = requests.get(
                'https://openidconnect.googleapis.com/v1/userinfo',
                headers={'Authorization': f"Bearer {token_info.get('access_token')}"},
                timeout=10
            )
            userinfo_response.raise_for_status()
            user_info = userinfo_response.json()
        
        elif provider == 'microsoft':
            userinfo_response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers={'Authorization': f"Bearer {token_info.get('access_token')}"},
                timeout=10
            )
            userinfo_response.raise_for_status()
            user_info = userinfo_response.json()
        
        elif provider == 'apple':
            try:
                decoded = jwt.decode(token_info.get('id_token', ''), options={"verify_signature": False})
                user_info = decoded
            except:
                user_info = {'email': 'apple.user@icloud.com', 'given_name': 'Apple', 'family_name': 'User'}
        
        if not user_info:
            return redirect(url_for('login', error='Failed to get user information from ' + provider))
        
        # Extract email and name
        email = user_info.get('email') or user_info.get('mail') or user_info.get('preferred_username')
        first_name = user_info.get('given_name') or user_info.get('givenName') or provider.capitalize()
        last_name = user_info.get('family_name') or user_info.get('surname') or 'User'
        
        if not email:
            return redirect(url_for('login', error='Could not retrieve email from ' + provider))
        
        # Find or create user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                restaurant_name=f'{first_name} Restaurant',
                role='manager'
            )
            # OAuth users have no password
            user.password_hash = ''
            db.session.add(user)
            db.session.flush()
            
            # Create default location
            location = Location(user_id=user.id, country='US')
            location.set_units(UNIT_STANDARDS.get('US', {}))
            db.session.add(location)
            
            db.session.commit()
        
        # Set session
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
    
    except requests.RequestException as e:
        return redirect(url_for('login', error=f'OAuth error: {str(e)}'))
    except Exception as e:
        print(f'OAuth callback error: {str(e)}')
        return redirect(url_for('login', error='Authentication failed with ' + provider))
    
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
        csv_ingredients = set(df["ingredient"].dropna().astype(str).str.strip().tolist())

        user = get_current_user()
        db_ingredients = set()
        sales_ingredients = set()
        if user:
            db_items = IngredientMaster.query.filter_by(user_id=user.id).all()
            db_ingredients = {
                (item.ingredient or '').strip()
                for item in db_items
                if item.ingredient and item.ingredient.strip()
            }

            sales_rows = SalesRecord.query.filter_by(user_id=user.id).all()
            sales_ingredients = {
                (row.ingredient or '').strip()
                for row in sales_rows
                if row.ingredient and row.ingredient.strip()
            }

        ingredients = sorted(csv_ingredients.union(db_ingredients).union(sales_ingredients))
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
    days_ahead = int(request.form.get("days_ahead", 7))

    if days_ahead not in [7, 14, 30]:
        days_ahead = 7

    user = get_current_user()
    ingredient_df = _get_ingredient_dataframe(ingredient, user)

    sales_df = prepare_daily_sales_series(ingredient_df)
    has_history = not sales_df.empty

    forecast = forecast_demand(ingredient_df, periods=days_ahead)
    decision = optimize_inventory(
        forecast=forecast,
        current_stock=current_stock,
        lead_time_days=lead_time_days,
        service_level=service_level,
    )
    alerts = generate_alerts(decision)

    if has_history:
        chart_labels = sales_df["date"].dt.strftime("%Y-%m-%d").tolist()
        chart_sales = sales_df["quantity_sold"].tolist()
        last_date = sales_df["date"].max()
    else:
        chart_labels = []
        chart_sales = []
        last_date = pd.Timestamp.now().normalize()
    forecast_labels = [
        (last_date + pd.Timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(1, days_ahead + 1)
    ]
    forecast_values = list(forecast.get("predictions") or [])
    if len(forecast_values) < days_ahead:
        forecast_values.extend([forecast["avg_daily"]] * (days_ahead - len(forecast_values)))
    elif len(forecast_values) > days_ahead:
        forecast_values = forecast_values[:days_ahead]

    combined_labels = chart_labels + forecast_labels
    historical_series = chart_sales + [None] * len(forecast_values)
    forecast_series = [None] * len(chart_sales) + forecast_values

    # Calculate training predictions for performance comparison
    sales_array = sales_df["quantity_sold"].values if has_history else np.array([])
    model_name = forecast.get("model_used", "Moving Average")
    training_predictions = generate_training_predictions(sales_array, model_name, sales_df)
    
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
        user = get_current_user()
        if not user:
            return jsonify({"success": False, "error": "User not authenticated"}), 401

        inventory_ingredients = {
            (item.ingredient or '').strip()
            for item in IngredientMaster.query.filter_by(user_id=user.id).all()
            if item.ingredient and item.ingredient.strip()
        }

        sales_ingredients = {
            (record.ingredient or '').strip()
            for record in SalesRecord.query.filter_by(user_id=user.id).all()
            if record.ingredient and record.ingredient.strip()
        }

        ingredients = sorted(inventory_ingredients.union(sales_ingredients))
        if not ingredients:
            try:
                sample_df = pd.read_csv(DATA_PATH)
                sample_ingredients = set(
                    sample_df["ingredient"].dropna().astype(str).str.strip().tolist()
                )
                ingredients = sorted(sample_ingredients)
            except Exception:
                pass
        return jsonify({"success": True, "ingredients": ingredients})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@login_required
@app.route("/api/inventory/items", methods=["POST"])
def add_inventory_item():
    """Add a custom inventory item for the current user."""
    try:
        user = get_current_user()
        if not user:
            return jsonify({"success": False, "error": "User not authenticated"}), 401

        data = request.get_json() or {}
        ingredient = (data.get("ingredient") or "").strip()

        if not ingredient:
            return jsonify({"success": False, "error": "Ingredient name is required"}), 400

        existing_item = IngredientMaster.query.filter_by(user_id=user.id, ingredient=ingredient).first()
        if existing_item:
            return jsonify({"success": True, "message": "Ingredient already exists", "ingredient": ingredient})

        new_item = IngredientMaster(user_id=user.id, ingredient=ingredient)
        db.session.add(new_item)
        db.session.commit()

        return jsonify({"success": True, "message": "Ingredient added", "ingredient": ingredient})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@login_required
@app.route("/api/dashboard-stats", methods=["GET"])
def dashboard_stats():
    """API endpoint for dashboard statistics"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({"success": False, "error": "User not authenticated"}), 401

        sales_rows = SalesRecord.query.filter_by(user_id=user.id).all()
        has_products = IngredientMaster.query.filter_by(user_id=user.id).count() > 0

        today = datetime.now().date()
        date_index = pd.date_range(today - timedelta(days=6), today, freq="D")

        if not sales_rows:
            try:
                sample_df = pd.read_csv(DATA_PATH)
                sample_df["date"] = pd.to_datetime(sample_df["date"])

                recent_end = sample_df["date"].max().date()
                recent_start = recent_end - timedelta(days=6)
                sample_date_index = pd.date_range(recent_start, recent_end, freq="D")

                top_ingredients = (
                    sample_df.groupby("ingredient")["quantity_sold"]
                    .sum()
                    .sort_values(ascending=False)
                    .head(5)
                )

                recent_df = sample_df[sample_df["date"].dt.date >= recent_start]
                daily_totals = recent_df.groupby("date")["quantity_sold"].sum().sort_index()
                daily_totals = daily_totals.reindex(sample_date_index, fill_value=0)

                stats = {
                    "total_ingredients": int(sample_df["ingredient"].nunique()),
                    "total_sales": float(sample_df["quantity_sold"].sum()),
                    "avg_daily_sales": float(sample_df.groupby("date")["quantity_sold"].sum().mean()),
                    "date_range": {
                        "start": recent_start.strftime("%Y-%m-%d"),
                        "end": recent_end.strftime("%Y-%m-%d")
                    },
                    "top_ingredients": [
                        {"name": name, "sales": float(sales)}
                        for name, sales in top_ingredients.items()
                    ],
                    "recent_trend": {
                        "labels": [d.strftime("%Y-%m-%d") for d in sample_date_index],
                        "values": [float(v) for v in daily_totals.values]
                    },
                    "has_sales": True,
                    "has_products": True,
                    "total_records": int(len(sample_df))
                }
                return jsonify({"success": True, "stats": stats})
            except Exception:
                # Fall through to empty stats if sample data can't be loaded.
                pass

        if not sales_rows:
            stats = {
                "total_ingredients": 0,
                "total_sales": 0.0,
                "avg_daily_sales": 0.0,
                "date_range": {
                    "start": (today - timedelta(days=6)).strftime("%Y-%m-%d"),
                    "end": today.strftime("%Y-%m-%d")
                },
                "top_ingredients": [],
                "recent_trend": {
                    "labels": [d.strftime("%Y-%m-%d") for d in date_index],
                    "values": [0.0 for _ in date_index]
                },
                "has_sales": False,
                "has_products": has_products,
                "total_records": 0
            }
            return jsonify({"success": True, "stats": stats})

        df = pd.DataFrame([
            {
                "date": row.sale_date,
                "ingredient": row.ingredient,
                "quantity_sold": row.quantity_sold,
            }
            for row in sales_rows
        ])
        df["date"] = pd.to_datetime(df["date"])

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
        daily_totals = daily_totals.reindex(date_index, fill_value=0)
        stats["recent_trend"] = {
            "labels": [d.strftime("%Y-%m-%d") for d in date_index],
            "values": [float(v) for v in daily_totals.values]
        }
        stats["has_sales"] = True
        stats["has_products"] = has_products
        stats["total_records"] = int(len(df))
        
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
        
        user = get_current_user()
        ingredient_df = _get_ingredient_dataframe(ingredient, user)
        sales_df = prepare_daily_sales_series(ingredient_df)
        has_history = not sales_df.empty
        
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
        if has_history:
            chart_labels = sales_df["date"].dt.strftime("%Y-%m-%d").tolist()
            chart_sales = sales_df["quantity_sold"].tolist()
            last_date = sales_df["date"].max()
        else:
            chart_labels = []
            chart_sales = []
            last_date = pd.Timestamp.now().normalize()
        forecast_labels = [
            (last_date + pd.Timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(1, days_ahead + 1)
        ]

        forecast_values = list(forecast.get("predictions") or [])
        if len(forecast_values) < days_ahead:
            forecast_values.extend([forecast["avg_daily"]] * (days_ahead - len(forecast_values)))
        elif len(forecast_values) > days_ahead:
            forecast_values = forecast_values[:days_ahead]

        upper_bound = list(forecast.get("upper_bound") or [])
        lower_bound = list(forecast.get("lower_bound") or [])
        if len(upper_bound) < days_ahead:
            upper_bound.extend([upper_bound[-1]] * (days_ahead - len(upper_bound)) if upper_bound else [])
        if len(lower_bound) < days_ahead:
            lower_bound.extend([lower_bound[-1]] * (days_ahead - len(lower_bound)) if lower_bound else [])
        if len(upper_bound) > days_ahead:
            upper_bound = upper_bound[:days_ahead]
        if len(lower_bound) > days_ahead:
            lower_bound = lower_bound[:days_ahead]
        
        return jsonify({
            "success": True,
            "ingredient": ingredient,
            "days_ahead": days_ahead,
            "forecast": forecast,
            "decision": decision,
            "alerts": alerts,
            "has_history": has_history,
            "chart_data": {
                "labels": chart_labels + forecast_labels,
                "historical": chart_sales + [None] * len(forecast_labels),
                "forecast": [None] * len(chart_sales) + forecast_values,
                "upper_bound": [None] * len(chart_sales) + upper_bound,
                "lower_bound": [None] * len(chart_sales) + lower_bound
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
        
        user = get_current_user()
        results = []
        
        for ingredient in ingredients:
            try:
                ingredient_df = _get_ingredient_dataframe(ingredient, user)
                sales_df = prepare_daily_sales_series(ingredient_df)
                has_history = not sales_df.empty
                
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
                if has_history:
                    last_date = sales_df["date"].max()
                else:
                    last_date = pd.Timestamp.now().normalize()
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
                    "forecast_labels": forecast_labels,
                    "has_history": has_history
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


@app.route("/api/sales/import", methods=["POST"])
@login_required
def import_user_sales_file():
    """Import user historical sales from CSV/Excel with flexible column names."""
    try:
        user = get_current_user()
        if not user:
            return jsonify({"success": False, "error": "User not authenticated"}), 401

        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400

        file = request.files["file"]
        if not file or not file.filename:
            return jsonify({"success": False, "error": "No file selected"}), 400

        filename = file.filename.lower()
        if filename.endswith(".csv"):
            source_df = pd.read_csv(file)
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            try:
                source_df = pd.read_excel(file)
            except Exception:
                return jsonify({
                    "success": False,
                    "error": "Excel file support requires engine dependencies (e.g., openpyxl). You can upload CSV now or install openpyxl."
                }), 400
        else:
            return jsonify({"success": False, "error": "Unsupported file type. Use CSV, XLSX, or XLS."}), 400

        if source_df.empty:
            return jsonify({"success": False, "error": "Uploaded file is empty"}), 400

        def parse_dates(series: pd.Series) -> pd.Series:
            parsed = pd.to_datetime(series, errors="coerce", infer_datetime_format=True)
            parsed_count = int(parsed.notna().sum())

            if parsed_count < max(1, int(len(series) * 0.5)):
                parsed_dayfirst = pd.to_datetime(
                    series,
                    errors="coerce",
                    infer_datetime_format=True,
                    dayfirst=True
                )
                if int(parsed_dayfirst.notna().sum()) > parsed_count:
                    parsed = parsed_dayfirst

            numeric = pd.to_numeric(series, errors="coerce")
            if numeric.notna().any():
                excel_parsed = pd.to_datetime(
                    numeric,
                    unit="D",
                    origin="1899-12-30",
                    errors="coerce"
                )
                parsed = parsed.fillna(excel_parsed)

            return parsed

        def parse_quantities(series: pd.Series) -> pd.Series:
            def normalize_value(value):
                if value is None:
                    return None
                text = str(value).strip()
                if not text:
                    return None

                if text.startswith('(') and text.endswith(')'):
                    text = f"-{text[1:-1]}"

                text = re.sub(r"[^0-9,\.\-]", "", text)

                if "," in text and "." not in text:
                    text = text.replace(",", ".")
                else:
                    text = text.replace(",", "")

                try:
                    return float(text)
                except ValueError:
                    return None

            return series.apply(normalize_value)

        def normalize_col(col_name):
            return re.sub(r"[^a-z0-9]", "", str(col_name).strip().lower())

        normalized_to_original = {normalize_col(c): c for c in source_df.columns}

        def resolve_column(candidates):
            for candidate in candidates:
                key = normalize_col(candidate)
                if key in normalized_to_original:
                    return normalized_to_original[key]

            for key, original in normalized_to_original.items():
                for candidate in candidates:
                    candidate_key = normalize_col(candidate)
                    if candidate_key and (candidate_key in key or key in candidate_key):
                        return original
            return None

        date_col = resolve_column(["date", "sale_date", "sold_date", "transaction_date", "day"])
        ingredient_col = resolve_column([
            "ingredient",
            "ingredient_name",
            "item",
            "item_name",
            "product",
            "product_name",
            "name",
            "sku"
        ])
        quantity_col = resolve_column(["quantity_sold", "quantity", "qty", "units", "units_sold", "sold", "amount"])

        stock_col = resolve_column([
            "current_stock",
            "stock",
            "on_hand",
            "qty_on_hand",
            "quantity_on_hand",
            "inventory",
            "balance"
        ])
        reorder_col = resolve_column(["reorder_point", "reorder_level", "reorder", "min_stock", "minimum_stock"])
        unit_col = resolve_column(["unit", "unit_of_measure", "uom", "measure", "measurement"])

        is_inventory_import = bool(ingredient_col and (stock_col or reorder_col) and not date_col and not quantity_col)
        if is_inventory_import:
            ingredient_series = source_df[ingredient_col].astype(str).str.strip()
            ingredient_series = ingredient_series.mask(
                ingredient_series.str.lower().isin(["nan", "none", "null", ""]),
                pd.NA
            )

            stock_series = parse_quantities(source_df[stock_col]) if stock_col else pd.Series([None] * len(source_df))
            reorder_series = parse_quantities(source_df[reorder_col]) if reorder_col else pd.Series([None] * len(source_df))
            unit_series = source_df[unit_col].astype(str).str.strip() if unit_col else pd.Series([None] * len(source_df))
            unit_series = unit_series.mask(
                unit_series.str.lower().isin(["nan", "none", "null", ""]),
                pd.NA
            )

            inventory_df = pd.DataFrame({
                "ingredient": ingredient_series,
                "current_stock": stock_series,
                "reorder_point": reorder_series,
                "unit_of_measure": unit_series
            })

            inventory_df = inventory_df.dropna(subset=["ingredient"])
            inventory_df = inventory_df[inventory_df["ingredient"] != ""]
            inventory_df = inventory_df.drop_duplicates(subset=["ingredient"], keep="last")

            if inventory_df.empty:
                invalid_ingredients = int(pd.Series(ingredient_series).isna().sum())
                return jsonify({
                    "success": False,
                    "error": "No valid inventory rows found after parsing. Ensure your file has item names and stock values.",
                    "details": {
                        "total_rows": int(len(source_df)),
                        "invalid_ingredients": invalid_ingredients
                    }
                }), 400

            existing_items = {
                (item.ingredient or "").strip(): item
                for item in IngredientMaster.query.filter_by(user_id=user.id).all()
            }

            items_added = 0
            items_updated = 0

            for row in inventory_df.itertuples(index=False):
                ingredient_value = str(row.ingredient).strip()
                if not ingredient_value:
                    continue

                item = existing_items.get(ingredient_value)
                if not item:
                    item = IngredientMaster(user_id=user.id, ingredient=ingredient_value)
                    db.session.add(item)
                    existing_items[ingredient_value] = item
                    items_added += 1
                else:
                    items_updated += 1

                if pd.notna(row.current_stock):
                    item.current_stock = float(row.current_stock)
                if pd.notna(row.reorder_point):
                    item.reorder_point = float(row.reorder_point)
                if isinstance(row.unit_of_measure, str) and row.unit_of_measure.strip():
                    item.unit_of_measure = row.unit_of_measure.strip()

            db.session.commit()

            total_items = items_added + items_updated
            return jsonify({
                "success": True,
                "import_type": "inventory",
                "items_added": items_added,
                "items_updated": items_updated,
                "items_total": total_items
            })

        missing = []
        if not date_col:
            missing.append("date")
        if not ingredient_col:
            missing.append("ingredient/item")
        if not quantity_col:
            missing.append("quantity")

        if missing:
            return jsonify({
                "success": False,
                "error": f"Could not detect required columns: {', '.join(missing)}",
                "available_columns": [str(c) for c in source_df.columns]
            }), 400

        ingredient_series = source_df[ingredient_col].astype(str).str.strip()
        ingredient_series = ingredient_series.mask(
            ingredient_series.str.lower().isin(["nan", "none", "null", ""]),
            pd.NA
        )

        date_series = parse_dates(source_df[date_col])
        quantity_series = parse_quantities(source_df[quantity_col])

        working_df = pd.DataFrame({
            "date": date_series,
            "ingredient": ingredient_series,
            "quantity_sold": quantity_series
        })

        working_df = working_df.dropna(subset=["date", "ingredient", "quantity_sold"])
        working_df = working_df[working_df["ingredient"] != ""]

        if working_df.empty:
            invalid_dates = int(date_series.isna().sum())
            invalid_quantities = int(pd.Series(quantity_series).isna().sum())
            invalid_ingredients = int(pd.Series(ingredient_series).isna().sum())
            return jsonify({
                "success": False,
                "error": "No valid rows found after parsing. Ensure your file has valid dates, item names, and numeric quantities.",
                "details": {
                    "total_rows": int(len(source_df)),
                    "invalid_dates": invalid_dates,
                    "invalid_quantities": invalid_quantities,
                    "invalid_ingredients": invalid_ingredients
                }
            }), 400

        unique_ingredients = sorted(set(working_df["ingredient"].tolist()))
        existing_items = {
            (item.ingredient or "").strip()
            for item in IngredientMaster.query.filter_by(user_id=user.id).all()
            if item.ingredient
        }

        added_ingredients = 0
        for ingredient in unique_ingredients:
            if ingredient not in existing_items:
                db.session.add(IngredientMaster(user_id=user.id, ingredient=ingredient))
                added_ingredients += 1

        imported_count = 0
        for row in working_df.itertuples(index=False):
            db.session.add(SalesRecord(
                user_id=user.id,
                ingredient=str(row.ingredient),
                quantity_sold=float(row.quantity_sold),
                sale_date=row.date.date()
            ))
            imported_count += 1

        # Keep legacy CSV data source in sync for existing forecast/reporting flows.
        csv_rows = working_df.copy()
        csv_rows["date"] = csv_rows["date"].dt.strftime("%Y-%m-%d")
        csv_rows = csv_rows[["date", "ingredient", "quantity_sold"]]

        try:
            existing_df = pd.read_csv(DATA_PATH)
            combined_df = pd.concat([existing_df, csv_rows], ignore_index=True)
            combined_df.to_csv(DATA_PATH, index=False)
        except FileNotFoundError:
            csv_rows.to_csv(DATA_PATH, index=False)

        db.session.commit()

        total_user_sales = SalesRecord.query.filter_by(user_id=user.id).count()
        return jsonify({
            "success": True,
            "message": "Sales imported successfully",
            "rows_imported": imported_count,
            "ingredients_added": added_ingredients,
            "total_user_sales": total_user_sales
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@login_required
@app.route("/api/ingredient-history/<ingredient>", methods=["GET"])
def ingredient_history(ingredient):
    """Get historical data for a specific ingredient"""
    try:
        user = get_current_user()
        ingredient_df = _get_ingredient_dataframe(ingredient, user)
        sales_df = prepare_daily_sales_series(ingredient_df)
        
        if sales_df.empty:
            return jsonify({"success": False, "error": f"No data found for {ingredient}"}), 404
        
        history = [
            {
                "date": row["date"].strftime("%Y-%m-%d"),
                "quantity": float(row["quantity_sold"])
            }
            for _, row in sales_df.iterrows()
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
        
        if latitude is None or longitude is None:
            return jsonify({"success": False, "error": "Latitude and longitude required"}), 400

        latitude = float(latitude)
        longitude = float(longitude)
        
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
                user.location.set_units(UNIT_STANDARDS.get(detected_country, UNIT_STANDARDS['US']))
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


@login_required
@app.route("/api/add-sale", methods=["POST"])
def add_sale():
    """Add a new sales record"""
    try:
        data = request.get_json()
        ingredient = (data.get("ingredient") or '').strip()
        date = data.get("date")
        quantity = data.get("quantity")
        
        if not all([ingredient, date, quantity]):
            return jsonify({"success": False, "error": "All fields are required"}), 400
        
        # Validate date format
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400

        user = get_current_user()
        if not user:
            return jsonify({"success": False, "error": "User not authenticated"}), 401

        quantity_value = float(quantity)

        # Ensure ingredient exists in user's inventory list
        inventory_item = IngredientMaster.query.filter_by(user_id=user.id, ingredient=ingredient).first()
        if not inventory_item:
            inventory_item = IngredientMaster(user_id=user.id, ingredient=ingredient)
            db.session.add(inventory_item)

        # Save in relational DB
        sales_record = SalesRecord(
            user_id=user.id,
            ingredient=ingredient,
            quantity_sold=quantity_value,
            sale_date=parsed_date,
        )
        db.session.add(sales_record)
        
        # Read existing data
        df = pd.read_csv(DATA_PATH)
        
        # Add new record
        new_record = pd.DataFrame([{
            "date": date,
            "ingredient": ingredient,
            "quantity_sold": quantity_value
        }])
        
        df = pd.concat([df, new_record], ignore_index=True)
        df.to_csv(DATA_PATH, index=False)

        db.session.commit()
        
        return jsonify({"success": True, "message": "Sale added successfully"})
    except Exception as e:
        db.session.rollback()
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
    """Generate a secure password reset token"""
    import secrets
    return secrets.token_urlsafe(32)


def store_recovery_token(email, token):
    """Store recovery token in database with 24-hour expiry"""
    from datetime import datetime, timedelta
    
    user = User.query.filter_by(email=email).first()
    if user:
        user.reset_token = token
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()


def verify_recovery_token(email, token):
    """Verify password reset token"""
    from datetime import datetime
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return False
    
    if not user.reset_token or user.reset_token != token:
        return False
    
    if not user.reset_token_expiry or datetime.utcnow() > user.reset_token_expiry:
        return False
    
    return True


def clear_recovery_token(user):
    """Clear password reset token after use"""
    user.reset_token = None
    user.reset_token_expiry = None
    db.session.commit()


@app.route("/password-recovery")
def password_recovery():
    """Password recovery page"""
    return render_template("password_recovery.html")


@app.route("/api/auth/request-password-reset", methods=["POST"])
# @limiter.limit("3 per hour")
def request_password_reset():
    """Request password reset link via email"""
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()

        if not email:
            return jsonify({"success": False, "error": "Email is required"}), 400

        # Check if user exists (don't reveal if email exists for security)
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({
                "success": True,
                "message": "If an account exists with this email, a password reset link will be sent"
            }), 200

        # Generate secure reset token
        token = generate_recovery_token(email)
        store_recovery_token(email, token)

        # Build reset URL (uses environment variable for domain)
        domain = os.getenv('APP_DOMAIN', 'http://localhost:5000')
        reset_url = f"{domain}/reset-password?token={token}"

        # Send email with reset link
        try:
            from flask_mail import Message, Mail
            mail = Mail(app)
            msg = Message(
                subject="Password Reset Request - Restaurant Inventory AI",
                recipients=[email],
                html=f"""
<html>
  <body>
    <h2>Password Reset Request</h2>
    <p>Hello {user.get_full_name() or 'User'},</p>
    <p>You requested to reset your password. Click the link below to set a new password:</p>
    <p>
      <a href="{reset_url}" style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
        Reset Your Password
      </a>
    </p>
    <p>Or copy and paste this link in your browser:</p>
    <p><code>{reset_url}</code></p>
    <p><strong>This link will expire in 24 hours.</strong></p>
    <p>If you didn't request this password reset, please ignore this email and your password will remain unchanged.</p>
    <p>Best regards,<br>Restaurant Inventory AI Team</p>
  </body>
</html>
                """
            )
            mail.send(msg)
            
            # Log security event
            from app.security import log_security_event
            log_security_event('PASSWORD_RESET_REQUESTED', user.id, request.remote_addr)
            
        except Exception as e:
            app.logger.error(f"Email error: {e}")
            # Log the error but still return success for security
            return jsonify({
                "success": True,
                "message": "If an account exists with this email, a password reset link will be sent"
            }), 200

        return jsonify({
            "success": True,
            "message": "Password reset link sent to your email"
        }), 200

    except Exception as e:
        app.logger.error(f"Password reset request error: {e}")
        return jsonify({"success": False, "error": "An error occurred"}), 500


@app.route("/reset-password", methods=["GET"])
def reset_password_page():
    """Display password reset form when user clicks email link"""
    try:
        token = request.args.get('token', '').strip()
        
        if not token:
            flash("Invalid or missing reset token", "error")
            return redirect('/password-recovery')
        
        # Verify token exists and hasn't expired
        user = User.query.filter_by(reset_token=token).first()
        if not user:
            flash("Invalid or expired reset link", "error")
            return redirect('/password-recovery')
        
        from datetime import datetime
        if not user.reset_token_expiry or datetime.utcnow() > user.reset_token_expiry:
            flash("Reset link has expired. Please request a new one.", "error")
            return redirect('/password-recovery')
        
        # Render password reset form with embedded token
        return render_template("reset_password.html", token=token)
    
    except Exception as e:
        app.logger.error(f"Reset password page error: {e}")
        flash("An error occurred", "error")
        return redirect('/password-recovery')


@app.route("/api/auth/reset-password-with-token", methods=["POST"])
# @limiter.limit("5 per hour")
def reset_password_with_token():
    """Reset password using valid token"""
    try:
        data = request.get_json()
        token = data.get('token', '').strip()
        new_password = data.get('new_password', '')

        if not token or not new_password:
            return jsonify({"success": False, "error": "Token and password are required"}), 400

        # Find user by reset token
        user = User.query.filter_by(reset_token=token).first()
        if not user:
            return jsonify({"success": False, "error": "Invalid reset token"}), 401

        from datetime import datetime
        if not user.reset_token_expiry or datetime.utcnow() > user.reset_token_expiry:
            return jsonify({"success": False, "error": "Reset token has expired"}), 401

        # Validate password
        try:
            user.set_password(new_password)
            clear_recovery_token(user)
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Log security event
            from app.security import log_security_event
            log_security_event('PASSWORD_RESET_COMPLETED', user.id, request.remote_addr)
            
            return jsonify({
                "success": True,
                "message": "Password reset successfully. You can now log in."
            }), 200
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Password validation error: {e}")
            return jsonify({"success": False, "error": str(e)}), 400

    except Exception as e:
        app.logger.error(f"Password reset error: {e}")
        return jsonify({"success": False, "error": "An error occurred"}), 500


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
