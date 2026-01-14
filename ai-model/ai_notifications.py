from firebase_admin import firestore, credentials
import firebase_admin
from uuid import uuid4
from datetime import datetime

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate("../florai/model_server/serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()


def save_ai_prediction_to_firestore(user_id, latitude, longitude, weather_data, prediction_result):
    """
    Save AI model prediction to Firestore
    
    Args:
        user_id: User ID (can be None for anonymous predictions)
        latitude: Location latitude
        longitude: Location longitude
        weather_data: Dict with weather information
        prediction_result: Dict with AI prediction results (likelihood, confidence, probabilities)
    
    Returns:
        prediction_id: The ID of the saved prediction
    """
    prediction_id = str(uuid4())

    prediction_doc = {
        "predictionID": prediction_id,
        "userID": user_id,
        "modelType": "XGBoost_ML",
        "modelVersion": "1.0.0",
        
        # Location
        "latitude": float(latitude),
        "longitude": float(longitude),
        
        # Weather data
        "temperature_max": float(weather_data.get("temperatureMax", 0)),
        "temperature_min": float(weather_data.get("temperatureMin", 0)),
        "temperature_mean": float((weather_data.get("temperatureMax", 0) + weather_data.get("temperatureMin", 0)) / 2),
        "precipitation": float(weather_data.get("precipitation", 0)),
        "wind_speed": float(weather_data.get("windSpeed", 0)),
        "sunshine_duration": float(weather_data.get("sunshineDuration", 0)),
        "rain_hours": float(weather_data.get("rainHours", 0)),
        
        # AI Prediction results
        "predicted_likelihood": prediction_result.get("likelihood"),  # "Low", "Medium", "High"
        "confidence": float(prediction_result.get("confidence", 0)),
        "probability_low": float(prediction_result.get("probabilities", {}).get("Low", 0)),
        "probability_medium": float(prediction_result.get("probabilities", {}).get("Medium", 0)),
        "probability_high": float(prediction_result.get("probabilities", {}).get("High", 0)),
        
        # Metadata
        "source": "ai_model_click",
        "createdAt": firestore.SERVER_TIMESTAMP,
    }

    db.collection("ai_predictions").document(prediction_id).set(prediction_doc)
    return prediction_id


def create_ai_prediction_alert(prediction_id, user_id, latitude, longitude, prediction_result, weather_data):
    """
    Create notification alert for AI prediction
    
    Args:
        prediction_id: ID of the prediction
        user_id: User ID (skip notification if None)
        latitude, longitude: Location coordinates
        prediction_result: AI prediction results
        weather_data: Weather information
    
    Returns:
        notification_id or None
    """
    # Skip if no user ID
    if not user_id:
        return None
    
    # Check user notification preferences
    pref_ref = db.collection("notificationPreferences").document(user_id)
    pref_doc = pref_ref.get()

    if pref_doc.exists:
        prefs = pref_doc.to_dict()
        if not prefs.get("enableAiAlerts", True):
            return None  # User disabled AI alerts
        if not prefs.get("channelInApp", True):
            return None  # In-app notifications disabled
        
        # Severity filter
        min_severity = prefs.get("minSeverity", "low").lower()
        likelihood = prediction_result.get("likelihood", "").lower()
        
        if min_severity == "high" and likelihood != "high":
            return None  # Only notify for high risk
        elif min_severity == "medium" and likelihood == "low":
            return None  # Skip low risk notifications

    likelihood = prediction_result.get("likelihood", "Unknown")
    confidence = prediction_result.get("confidence", 0)
    
    # Create notification
    notification_id = str(uuid4())
    
    # Custom message based on risk level
    if likelihood == "High":
        description = f"⚠️ High risk ({confidence*100:.0f}% confidence) of invasive species occurrence detected at your selected location."
        severity = "high"
    elif likelihood == "Medium":
        description = f"⚡ Medium risk ({confidence*100:.0f}% confidence) of invasive species occurrence detected at your selected location."
        severity = "medium"
    else:
        description = f"✓ Low risk ({confidence*100:.0f}% confidence) of invasive species occurrence at your selected location."
        severity = "low"

    notif_doc = {
        "userID": user_id,
        "notificationID": notification_id,
        "type": "ai_prediction_alert",
        "source": "ai_model_prediction",
        "severity": severity,
        "title": f"AI Prediction: {likelihood} Risk",
        "description": description,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "read": False,
        "receiveNotifications": True,
        "predictionID": prediction_id,

        # Embedded prediction details
        "latitude": float(latitude),
        "longitude": float(longitude),
        "predictedLikelihood": likelihood,
        "confidence": float(confidence),
        "temperature": float((weather_data.get("temperatureMax", 0) + weather_data.get("temperatureMin", 0)) / 2),
        "precipitation": float(weather_data.get("precipitation", 0)),
        
        # Model info
        "modelType": "XGBoost_ML",
        "modelVersion": "1.0.0",
    }

    db.collection("notifications").document(notification_id).set(notif_doc)
    return notification_id


def create_batch_prediction_summary(user_id, predictions_summary):
    """
    Create a summary notification for batch predictions (grid predictions)
    
    Args:
        user_id: User ID
        predictions_summary: Dict with summary statistics
    
    Returns:
        notification_id or None
    """
    if not user_id:
        return None
    
    notification_id = str(uuid4())
    
    high_count = predictions_summary.get("high_count", 0)
    medium_count = predictions_summary.get("medium_count", 0)
    low_count = predictions_summary.get("low_count", 0)
    total_count = predictions_summary.get("total_count", 0)
    
    # Determine overall risk
    if high_count > total_count * 0.4:
        severity = "high"
        description = f"⚠️ Area analysis complete: {high_count}/{total_count} grid points show HIGH risk."
    elif medium_count + high_count > total_count * 0.5:
        severity = "medium"
        description = f"⚡ Area analysis complete: {high_count} high, {medium_count} medium risk points detected."
    else:
        severity = "low"
        description = f"✓ Area analysis complete: Mostly low risk detected ({low_count}/{total_count} points)."
    
    notif_doc = {
        "userID": user_id,
        "notificationID": notification_id,
        "type": "ai_batch_analysis",
        "source": "ai_grid_prediction",
        "severity": severity,
        "title": "AI Area Analysis Complete",
        "description": description,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "read": False,
        "receiveNotifications": True,
        
        # Summary stats
        "totalPoints": total_count,
        "highRiskCount": high_count,
        "mediumRiskCount": medium_count,
        "lowRiskCount": low_count,
        "centerLat": predictions_summary.get("center_lat", 0),
        "centerLon": predictions_summary.get("center_lon", 0),
        
        "modelType": "XGBoost_ML",
        "modelVersion": "1.0.0",
    }

    db.collection("notifications").document(notification_id).set(notif_doc)
    return notification_id
