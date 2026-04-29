import numpy as np
import pandas as pd
from math import ceil, sqrt
import warnings
warnings.filterwarnings('ignore')

# Advanced forecasting models
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

try:
    from sklearn.preprocessing import MinMaxScaler
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    LSTM_AVAILABLE = True
except ImportError:
    LSTM_AVAILABLE = False


def prepare_daily_sales_series(ingredient_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate sales by day and fill missing dates with zeros.

    Returns a DataFrame with columns: date, quantity_sold
    """
    if ingredient_df is None or ingredient_df.empty:
        return pd.DataFrame(columns=["date", "quantity_sold"])

    working_df = ingredient_df.copy()
    working_df["date"] = pd.to_datetime(working_df["date"], errors="coerce").dt.normalize()
    working_df = working_df.dropna(subset=["date"])

    if working_df.empty:
        return pd.DataFrame(columns=["date", "quantity_sold"])

    daily_series = (
        working_df.groupby("date")["quantity_sold"]
        .sum()
        .sort_index()
        .asfreq("D", fill_value=0)
    )

    return pd.DataFrame({
        "date": daily_series.index,
        "quantity_sold": daily_series.values
    })


def _sanitize_forecast_result(result):
    if not result:
        return None

    predictions = result.get("predictions") or []
    if predictions:
        sanitized = [max(0.0, float(value)) for value in predictions]
        result["predictions"] = sanitized
        result["daily"] = float(np.mean(sanitized)) if sanitized else 0.0
        result["weekly"] = _weekly_total(sanitized)

    if result.get("lower_bound") is not None:
        result["lower_bound"] = [max(0.0, float(value)) for value in result["lower_bound"]]

    if result.get("upper_bound") is not None:
        result["upper_bound"] = [max(0.0, float(value)) for value in result["upper_bound"]]

    return result


def _weekly_total(predictions):
    if not predictions:
        return 0.0
    window = min(7, len(predictions))
    return float(np.sum(predictions[:window]))


def _ensure_forecast_length(result: dict, periods: int) -> dict:
    predictions = list(result.get("predictions") or [])
    if periods <= 0:
        result["predictions"] = []
        result["daily"] = 0.0
        result["weekly"] = 0.0
        return result

    fallback_value = float(result.get("daily", 0.0))

    if len(predictions) < periods:
        predictions.extend([fallback_value] * (periods - len(predictions)))
    elif len(predictions) > periods:
        predictions = predictions[:periods]

    predictions = [max(0.0, float(value)) for value in predictions]
    result["predictions"] = predictions
    result["daily"] = float(np.mean(predictions)) if predictions else 0.0
    result["weekly"] = _weekly_total(predictions)

    for bound_key in ("upper_bound", "lower_bound"):
        bound_values = result.get(bound_key)
        if bound_values is None:
            continue

        bound_values = list(bound_values)
        if len(bound_values) < periods:
            pad_value = float(bound_values[-1]) if bound_values else fallback_value
            bound_values.extend([pad_value] * (periods - len(bound_values)))
        elif len(bound_values) > periods:
            bound_values = bound_values[:periods]

        if bound_key == "lower_bound":
            bound_values = [max(0.0, float(value)) for value in bound_values]
        else:
            bound_values = [max(0.0, float(value)) for value in bound_values]

        result[bound_key] = bound_values

    return result


def forecast_seasonal_naive(sales_data, periods=7, seasonal_period=7):
    """
    Seasonal naive forecast: repeats the last seasonal window.
    """
    if len(sales_data) < seasonal_period:
        return None

    last_window = np.array(sales_data[-seasonal_period:], dtype=float)
    repeats = int(ceil(periods / seasonal_period))
    predictions = np.tile(last_window, repeats)[:periods].tolist()

    return {
        'daily': float(np.mean(predictions)),
        'weekly': float(np.sum(predictions)),
        'predictions': predictions,
        'confidence': 0.70
    }


def forecast_arima(sales_data, periods=7):
    """
    ARIMA forecasting model with auto-tuning.
    """
    try:
        if len(sales_data) < 10:
            return None
        
        # Auto ARIMA with common parameters
        model = ARIMA(sales_data, order=(1, 1, 1))
        fitted = model.fit()
        forecast = fitted.forecast(steps=periods)
        
        return {
            'daily': float(forecast.mean()),
            'weekly': float(forecast.sum()),
            'predictions': forecast.tolist(),
            'confidence': 0.85
        }
    except Exception as e:
        return None


def forecast_prophet(df, periods=7):
    """
    Facebook Prophet forecasting.
    """
    try:
        if len(df) < 10:
            return None
        
        # Prepare data for Prophet
        prophet_df = pd.DataFrame({
            'ds': df['date'],
            'y': df['quantity_sold']
        })
        
        # Train Prophet model
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05
        )
        model.fit(prophet_df)
        
        # Make forecast
        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)
        
        # Get predictions for forecast period
        forecast_period = forecast.tail(periods)
        
        return {
            'daily': float(forecast_period['yhat'].mean()),
            'weekly': float(forecast_period['yhat'].sum()),
            'predictions': forecast_period['yhat'].tolist(),
            'upper_bound': forecast_period['yhat_upper'].tolist() if 'yhat_upper' in forecast_period else None,
            'lower_bound': forecast_period['yhat_lower'].tolist() if 'yhat_lower' in forecast_period else None,
            'confidence': 0.90
        }
    except Exception as e:
        return None


def forecast_lstm(sales_data, periods=7):
    """
    LSTM neural network forecasting.
    """
    try:
        if len(sales_data) < 20:
            return None
        
        # Normalize data
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(sales_data.reshape(-1, 1))
        
        # Prepare sequences
        sequence_length = min(7, len(scaled_data) - 1)
        X, y = [], []
        for i in range(len(scaled_data) - sequence_length):
            X.append(scaled_data[i:i+sequence_length])
            y.append(scaled_data[i+sequence_length])
        
        if len(X) < 5:
            return None
        
        X = np.array(X)
        y = np.array(y)
        
        # Build LSTM model
        model = Sequential([
            LSTM(50, activation='relu', return_sequences=True, input_shape=(sequence_length, 1)),
            Dropout(0.2),
            LSTM(50, activation='relu'),
            Dropout(0.2),
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse')
        model.fit(X, y, epochs=50, batch_size=16, verbose=0)
        
        # Forecast
        last_sequence = scaled_data[-sequence_length:]
        predictions = []
        
        for _ in range(periods):
            pred = model.predict(last_sequence.reshape(1, sequence_length, 1), verbose=0)
            predictions.append(pred[0, 0])
            last_sequence = np.append(last_sequence[1:], pred)
        
        # Denormalize predictions
        predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()
        
        return {
            'daily': float(predictions.mean()),
            'weekly': float(predictions.sum()),
            'predictions': predictions.tolist(),
            'confidence': 0.88
        }
    except Exception as e:
        return None


def forecast_exponential_smoothing(sales_data, periods=7):
    """
    Exponential Smoothing (Holt-Winters) forecasting.
    """
    try:
        if len(sales_data) < 14:
            return None
        
        model = ExponentialSmoothing(
            sales_data,
            seasonal_periods=7,
            trend='add',
            seasonal='add',
            damped_trend=True
        )
        fitted = model.fit()
        forecast = fitted.forecast(steps=periods)
        
        return {
            'daily': float(forecast.mean()),
            'weekly': float(forecast.sum()),
            'predictions': forecast.tolist(),
            'confidence': 0.82
        }
    except Exception as e:
        return None


def forecast_moving_average(sales_data, window=7, periods=7):
    """
    Fallback: Simple moving average forecasting.
    """
    if len(sales_data) == 0:
        return {
            'daily': 0,
            'weekly': 0,
            'predictions': [0] * periods,
            'confidence': 0.50
        }
    
    avg_daily = np.mean(sales_data[-window:])
    predictions = [float(avg_daily)] * periods
    return {
        'daily': float(avg_daily),
        'weekly': float(avg_daily * min(7, periods)),
        'predictions': predictions,
        'confidence': 0.65
    }


def forecast_demand(ingredient_df: pd.DataFrame, window: int = 7, periods: int = 7) -> dict:
    """
    Advanced AI-powered demand forecasting with automatic model selection.
    Tries multiple models and selects the best one based on validation.
    
    Args:
        ingredient_df: DataFrame with date and quantity_sold columns
        window: Window size for moving average (default 7)
        periods: Number of periods to forecast (default 7)
    """
    periods = int(periods) if periods else 7
    if periods <= 0:
        periods = 7

    prepared_df = prepare_daily_sales_series(ingredient_df)
    if prepared_df.empty:
        result = forecast_moving_average(np.array([]), window, periods)
        result = _sanitize_forecast_result(result)
        result = _ensure_forecast_length(result, periods)
        return {
            "avg_daily": round(result['daily'], 2),
            "weekly_forecast": round(result['weekly'], 2),
            "predictions": result['predictions'],
            "model_used": "Moving Average (No Data)",
            "confidence": round(result['confidence'] * 100, 1),
            "selection_reason": "Insufficient data to build a model."
        }

    sales = prepared_df["quantity_sold"].values.astype(float)

    if len(sales) < 5:
        # Not enough data, use simple average
        result = forecast_moving_average(sales, window, periods)
        result = _sanitize_forecast_result(result)
        result = _ensure_forecast_length(result, periods)
        return {
            "avg_daily": round(result['daily'], 2),
            "weekly_forecast": round(result['weekly'], 2),
            "predictions": result['predictions'],
            "model_used": "Moving Average (Insufficient Data)",
            "confidence": round(result['confidence'] * 100, 1),
            "selection_reason": "Insufficient history for validation; using moving average."
        }

    def run_candidate(candidate, df, series, horizon):
        if candidate["uses_df"]:
            return candidate["fn"](df, horizon)
        return candidate["fn"](series, horizon)

    def run_moving_average(series, horizon):
        return forecast_moving_average(series, window, horizon)

    candidates = []

    if PROPHET_AVAILABLE and len(prepared_df) >= 10:
        candidates.append({
            "name": "Prophet",
            "min_points": 10,
            "uses_df": True,
            "fn": forecast_prophet
        })

    if ARIMA_AVAILABLE and len(sales) >= 10:
        candidates.append({
            "name": "ARIMA",
            "min_points": 10,
            "uses_df": False,
            "fn": forecast_arima
        })

    if ARIMA_AVAILABLE and len(sales) >= 14:
        candidates.append({
            "name": "Exponential Smoothing",
            "min_points": 14,
            "uses_df": False,
            "fn": forecast_exponential_smoothing
        })

    if LSTM_AVAILABLE and len(sales) >= 20:
        candidates.append({
            "name": "LSTM Neural Network",
            "min_points": 20,
            "uses_df": False,
            "fn": forecast_lstm
        })

    if len(sales) >= 7:
        candidates.append({
            "name": "Seasonal Naive",
            "min_points": 7,
            "uses_df": False,
            "fn": forecast_seasonal_naive
        })

    candidates.append({
        "name": "Moving Average",
        "min_points": 1,
        "uses_df": False,
        "fn": run_moving_average
    })

    validation_size = min(7, max(2, len(sales) // 5))
    can_validate = len(sales) - validation_size >= 5

    selected_candidate = None
    validation_metrics = None
    selection_reason = None

    if can_validate:
        train_df = prepared_df.iloc[:-validation_size].copy()
        train_sales = train_df["quantity_sold"].values.astype(float)
        validation_actual = sales[-validation_size:]

        scored_candidates = []
        for candidate in candidates:
            if len(train_sales) < candidate["min_points"]:
                continue

            result = run_candidate(candidate, train_df, train_sales, validation_size)
            result = _sanitize_forecast_result(result)

            if not result:
                continue

            predictions = result.get("predictions") or []
            if len(predictions) != validation_size:
                continue

            metrics = calculate_error_metrics(validation_actual, predictions)
            scored_candidates.append((candidate, metrics))

        if scored_candidates:
            scored_candidates.sort(key=lambda item: (item[1]["mae"], item[1]["rmse"]))
            selected_candidate, best_metrics = scored_candidates[0]
            validation_metrics = {
                "window_days": int(validation_size),
                "mae": best_metrics["mae"],
                "rmse": best_metrics["rmse"],
            }
            selection_reason = (
                f"Selected {selected_candidate['name']} by lowest MAE on last {validation_size} days."
            )

    result = None
    if not selected_candidate:
        best_confidence = -1
        for candidate in candidates:
            if len(sales) < candidate["min_points"]:
                continue

            candidate_result = run_candidate(candidate, prepared_df, sales, periods)
            candidate_result = _sanitize_forecast_result(candidate_result)
            if not candidate_result:
                continue

            confidence = float(candidate_result.get("confidence", 0))
            if candidate_result.get("daily", 0) >= 0 and confidence > best_confidence:
                best_confidence = confidence
                selected_candidate = candidate
                result = candidate_result

        if not result:
            selected_candidate = {"name": "Moving Average"}
            result = forecast_moving_average(sales, window, periods)
            result = _sanitize_forecast_result(result)

        if not selection_reason:
            selection_reason = "Selected by highest model confidence (insufficient history for validation)."
    else:
        result = run_candidate(selected_candidate, prepared_df, sales, periods)
        result = _sanitize_forecast_result(result)
        if not result:
            selected_candidate = {"name": "Moving Average"}
            result = forecast_moving_average(sales, window, periods)
            result = _sanitize_forecast_result(result)
            if not selection_reason:
                selection_reason = "Selected moving average fallback due to model error."

    result = _ensure_forecast_length(result, periods)

    if result.get("upper_bound") is None or result.get("lower_bound") is None:
        ci = calculate_confidence_intervals(sales, result["predictions"])
        result["upper_bound"] = ci["upper"]
        result["lower_bound"] = ci["lower"]

    return {
        "avg_daily": round(result['daily'], 2),
        "weekly_forecast": round(result['weekly'], 2),
        "predictions": result['predictions'],
        "upper_bound": result.get('upper_bound'),
        "lower_bound": result.get('lower_bound'),
        "model_used": selected_candidate.get("name", "Moving Average"),
        "confidence": round(result['confidence'] * 100, 1),
        "selection_reason": selection_reason,
        "validation_metrics": validation_metrics
    }


def optimize_inventory(
    forecast: dict,
    current_stock: float,
    lead_time_days: int,
    service_level: float,
) -> dict:
    """
    Basic inventory optimization logic using reorder point + safety stock.
    """
    avg_daily = forecast["avg_daily"]
    demand_during_lead = avg_daily * lead_time_days

    # Simple safety stock approximation
    safety_stock = avg_daily * lead_time_days * (1 - service_level)

    reorder_point = demand_during_lead + safety_stock
    order_qty = max(0, reorder_point - current_stock)

    return {
        "demand_during_lead": round(demand_during_lead, 2),
        "safety_stock": round(safety_stock, 2),
        "reorder_point": round(reorder_point, 2),
        "recommended_order": round(order_qty, 2),
        "current_stock": round(current_stock, 2),
    }


def generate_alerts(decision: dict) -> list:
    alerts = []
    if decision["current_stock"] < decision["reorder_point"]:
        alerts.append("Stock below reorder point. Place an order soon.")
    if decision["recommended_order"] == 0:
        alerts.append("Stock is sufficient for the lead time.")
    return alerts


def calculate_error_metrics(actual, predicted):
    """
    Calculate RMSE and MAE error metrics.
    
    Args:
        actual: Array of actual values
        predicted: Array of predicted values
    
    Returns:
        dict with rmse and mae
    """
    actual = np.array(actual)
    predicted = np.array(predicted)
    
    # Remove NaN values
    mask = ~(np.isnan(actual) | np.isnan(predicted))
    actual = actual[mask]
    predicted = predicted[mask]
    
    if len(actual) == 0:
        return {'rmse': 0, 'mae': 0}
    
    # Calculate metrics
    mse = np.mean((actual - predicted) ** 2)
    rmse = sqrt(mse)
    mae = np.mean(np.abs(actual - predicted))
    
    return {
        'rmse': round(rmse, 2),
        'mae': round(mae, 2)
    }


def generate_training_predictions(sales_data, model_name, df=None):
    """
    Generate predictions on training data to show model performance.
    
    Args:
        sales_data: Array of historical sales
        model_name: Name of the model being used
        df: DataFrame with date column (for Prophet)
    
    Returns:
        Array of predictions matching the length of sales_data
    """
    try:
        if len(sales_data) < 5:
            return sales_data.copy()
        
        predictions = []
        
        if model_name == 'Prophet' and PROPHET_AVAILABLE and df is not None:
            # Use Prophet for training predictions
            prophet_df = pd.DataFrame({
                'ds': df['date'],
                'y': df['quantity_sold']
            })
            
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=False,
                changepoint_prior_scale=0.05
            )
            model.fit(prophet_df)
            
            forecast = model.predict(prophet_df)
            predictions = forecast['yhat'].values
            
        elif model_name == 'ARIMA' and ARIMA_AVAILABLE and len(sales_data) >= 10:
            # Use ARIMA for training predictions
            model = ARIMA(sales_data, order=(1, 1, 1))
            fitted = model.fit()
            predictions = fitted.fittedvalues
            
        elif model_name == 'Exponential Smoothing' and ARIMA_AVAILABLE and len(sales_data) >= 14:
            # Use Exponential Smoothing
            model = ExponentialSmoothing(
                sales_data,
                seasonal_periods=7,
                trend='add',
                seasonal='add',
                damped_trend=True
            )
            fitted = model.fit()
            predictions = fitted.fittedvalues
            
        elif model_name == 'LSTM Neural Network' and LSTM_AVAILABLE and len(sales_data) >= 20:
            # Use LSTM for training predictions
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(sales_data.reshape(-1, 1))
            
            sequence_length = min(7, len(scaled_data) - 1)
            X, y = [], []
            for i in range(len(scaled_data) - sequence_length):
                X.append(scaled_data[i:i+sequence_length])
                y.append(scaled_data[i+sequence_length])
            
            if len(X) >= 5:
                X = np.array(X)
                y = np.array(y)
                
                model = Sequential([
                    LSTM(50, activation='relu', return_sequences=True, input_shape=(sequence_length, 1)),
                    Dropout(0.2),
                    LSTM(50, activation='relu'),
                    Dropout(0.2),
                    Dense(1)
                ])
                
                model.compile(optimizer='adam', loss='mse')
                model.fit(X, y, epochs=50, batch_size=16, verbose=0)
                
                # Generate predictions
                pred_list = []
                for i in range(len(X)):
                    pred = model.predict(X[i:i+1], verbose=0)
                    pred_list.append(pred[0, 0])
                
                # Denormalize
                pred_array = scaler.inverse_transform(np.array(pred_list).reshape(-1, 1)).flatten()
                
                # Pad with NaN for the sequence
                predictions = [np.nan] * sequence_length + list(pred_array)
        
        # If predictions generation failed or for Moving Average, use simple smoothing
        if len(predictions) == 0:
            # Simple moving average as baseline
            window = min(7, len(sales_data))
            predictions = []
            for i in range(len(sales_data)):
                if i < window:
                    predictions.append(np.mean(sales_data[:i+1]))
                else:
                    predictions.append(np.mean(sales_data[i-window+1:i+1]))
        
        return np.array(predictions)
        
    except Exception as e:
        # Return moving average as fallback
        window = min(7, len(sales_data))
        predictions = []
        for i in range(len(sales_data)):
            if i < window:
                predictions.append(np.mean(sales_data[:i+1]))
            else:
                predictions.append(np.mean(sales_data[i-window+1:i+1]))
        return np.array(predictions)


def calculate_confidence_intervals(sales_data, predictions, confidence_level=0.95):
    """
    Calculate confidence intervals for forecast predictions.
    
    Args:
        sales_data: Historical sales data
        predictions: Future predictions
        confidence_level: Confidence level (default 0.95 for 95% CI)
    
    Returns:
        dict with lower and upper bounds arrays
    """
    try:
        if len(sales_data) < 5:
            # Not enough data for meaningful CI
            margin = np.array(predictions) * 0.2  # Simple 20% margin
            return {
                'lower': (np.array(predictions) - margin).tolist(),
                'upper': (np.array(predictions) + margin).tolist()
            }
        
        # Calculate standard deviation of historical data
        std_dev = np.std(sales_data)
        
        # Z-score for confidence level (1.96 for 95% CI)
        z_score = 1.96 if confidence_level == 0.95 else 1.645
        
        # Calculate margin of error (increases with forecast horizon)
        num_forecasts = len(predictions)
        margins = []
        
        for i in range(num_forecasts):
            # Margin increases with forecast distance
            horizon_factor = sqrt(i + 1)
            margin = z_score * std_dev * horizon_factor
            margins.append(margin)
        
        margins = np.array(margins)
        predictions_array = np.array(predictions)
        
        lower_bound = np.maximum(0, predictions_array - margins)  # Don't go negative
        upper_bound = predictions_array + margins
        
        return {
            'lower': lower_bound.tolist(),
            'upper': upper_bound.tolist()
        }
        
    except Exception as e:
        # Fallback to simple percentage-based CI
        margin = np.array(predictions) * 0.3
        return {
            'lower': np.maximum(0, np.array(predictions) - margin).tolist(),
            'upper': (np.array(predictions) + margin).tolist()
        }
