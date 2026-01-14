from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Optional
import os

# Import notification functions
try:
    from ai_notifications import (
        save_ai_prediction_to_firestore,
        create_ai_prediction_alert,
        create_batch_prediction_summary
    )
    NOTIFICATIONS_ENABLED = True
except Exception as e:
    print(f"⚠️ Notifications disabled: {e}")
    NOTIFICATIONS_ENABLED = False

# Initialize FastAPI app
app = FastAPI(
    title="Mikania micrantha Occurrence Prediction API",
    description="Predict species occurrence likelihood based on location and weather data",
    version="1.0.0"
)

# Add CORS middleware to allow requests from your UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://*.vercel.app",  # All Vercel deployments
        "https://yourdomain.com",  # Your custom domain (if you have one)
        "*"  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the trained model, scaler, and feature columns
MODEL_PATH = "occurrence_model.pkl"
SCALER_PATH = "scaler.pkl"
FEATURES_PATH = "feature_columns.pkl"

try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    feature_cols = joblib.load(FEATURES_PATH)
    print("✓ Model, scaler, and features loaded successfully")
except Exception as e:
    print(f"Error loading model files: {e}")
    model = None
    scaler = None
    feature_cols = None


# Request model
class WeatherData(BaseModel):
    """Weather data from the user's clicked location"""
    latitude: float = Field(..., description="Latitude of the location", ge=-90, le=90)
    longitude: float = Field(..., description="Longitude of the location", ge=-180, le=180)
    temperature_max: float = Field(..., description="Maximum temperature in Celsius", alias="temperatureMax")
    temperature_min: float = Field(..., description="Minimum temperature in Celsius", alias="temperatureMin")
    precipitation: float = Field(..., description="Precipitation in mm", ge=0)
    wind_speed: float = Field(..., description="Wind speed in km/h", ge=0, alias="windSpeed")
    sunshine_duration: float = Field(..., description="Sunshine duration in seconds", ge=0, alias="sunshineDuration")
    rain_hours: float = Field(0, description="Hours of rain (0-24)", ge=0, le=24, alias="rainHours")
    user_id: Optional[str] = Field(None, description="User ID for notifications", alias="userId")
    create_notification: bool = Field(False, description="Create notification for this prediction", alias="createNotification")
    save_prediction: bool = Field(False, description="Save prediction to database", alias="savePrediction")

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "latitude": 14.6,
                "longitude": 121.0,
                "temperatureMax": 32,
                "temperatureMin": 24,
                "precipitation": 15,
                "windSpeed": 12,
                "sunshineDuration": 36000,
                "rainHours": 8,
                "userId": "user123",
                "createNotification": True,
                "savePrediction": True
            }
        }
    }


# Response model
class PredictionResponse(BaseModel):
    """Prediction result"""
    likelihood: str = Field(..., description="Predicted likelihood: Low, Medium, or High")
    confidence: float = Field(..., description="Confidence score (0-1)")
    probabilities: Dict[str, float] = Field(..., description="Probabilities for each class")
    location: Dict[str, float] = Field(..., description="Input location coordinates")
    weather_summary: Dict[str, float] = Field(..., description="Input weather data summary")


def prepare_features(data: WeatherData) -> pd.DataFrame:
    """
    Prepare features from input data to match training data format
    """
    # Calculate derived features
    temp_mean = (data.temperature_max + data.temperature_min) / 2
    temp_range = data.temperature_max - data.temperature_min
    is_tropical = 1 if 20 < temp_mean < 30 else 0
    lat_abs = abs(data.latitude)
    is_equatorial = 1 if lat_abs < 10 else 0
    is_humid = 1 if data.precipitation > 10 else 0
    rain_hours_ratio = data.rain_hours / 24
    temp_precip_interaction = temp_mean * data.precipitation
    
    # Create feature DataFrame matching training data
    features = pd.DataFrame({
        'decimalLatitude': [data.latitude],
        'decimalLongitude': [data.longitude],
        'lat_abs': [lat_abs],
        'is_equatorial': [is_equatorial],
        'temperature_max_C': [data.temperature_max],
        'temperature_min_C': [data.temperature_min],
        'temperature_mean_C': [temp_mean],
        'temp_range': [temp_range],
        'is_tropical': [is_tropical],
        'precipitation_mm': [data.precipitation],
        'rain_mm': [data.precipitation],
        'precipitation_hours': [data.rain_hours],
        'is_humid': [is_humid],
        'rain_hours_ratio': [rain_hours_ratio],
        'windspeed_max_kmh': [data.wind_speed],
        'windgusts_max_kmh': [data.wind_speed * 1.5],  # Approximation
        'sunshine_duration_s': [data.sunshine_duration],
        'temp_precip_interaction': [temp_precip_interaction]
    })
    
    return features


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Mikania micrantha Occurrence Prediction API",
        "status": "active",
        "model_loaded": model is not None,
        "endpoints": {
            "predict": "/predict",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "scaler_loaded": scaler is not None,
        "features_loaded": feature_cols is not None
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict_occurrence(data: WeatherData):
    """
    Predict species occurrence likelihood based on location and weather data
    
    Returns:
    - likelihood: Low, Medium, or High
    - confidence: Confidence score for the prediction
    - probabilities: Probabilities for each likelihood class
    """
    
    # Check if model is loaded
    if model is None or scaler is None or feature_cols is None:
        raise HTTPException(
            status_code=500,
            detail="Model not loaded. Please ensure model files exist."
        )
    
    try:
        # Prepare features
        print(f"📍 Prediction request: lat={data.latitude}, lon={data.longitude}")
        features = prepare_features(data)
        print(f"✓ Features prepared: {features.shape}")
        
        # Scale features
        features_scaled = scaler.transform(features)
        print(f"✓ Features scaled")
        
        # Make prediction
        pred_class = model.predict(features_scaled)[0]
        pred_proba = model.predict_proba(features_scaled)[0]
        print(f"✓ Prediction made: class={pred_class}, proba={pred_proba}")
        
        # Define likelihood names
        likelihood_names = ['Low', 'Medium', 'High']
        
        prediction_result = {
            'likelihood': likelihood_names[pred_class],
            'confidence': float(pred_proba[pred_class]),
            'probabilities': {
                'Low': float(pred_proba[0]),
                'Medium': float(pred_proba[1]),
                'High': float(pred_proba[2])
            }
        }
        
        # Save prediction to Firestore if requested
        prediction_id = None
        notification_id = None
        
        if NOTIFICATIONS_ENABLED and (data.save_prediction or data.create_notification):
            weather_data_dict = {
                'temperatureMax': data.temperature_max,
                'temperatureMin': data.temperature_min,
                'precipitation': data.precipitation,
                'windSpeed': data.wind_speed,
                'sunshineDuration': data.sunshine_duration,
                'rainHours': data.rain_hours
            }
            
            if data.save_prediction:
                prediction_id = save_ai_prediction_to_firestore(
                    user_id=data.user_id,
                    latitude=data.latitude,
                    longitude=data.longitude,
                    weather_data=weather_data_dict,
                    prediction_result=prediction_result
                )
            
            if data.create_notification and data.user_id:
                notification_id = create_ai_prediction_alert(
                    prediction_id=prediction_id or "temp_" + str(int(data.latitude * 1000)),
                    user_id=data.user_id,
                    latitude=data.latitude,
                    longitude=data.longitude,
                    prediction_result=prediction_result,
                    weather_data=weather_data_dict
                )
        
        # Prepare response
        response = PredictionResponse(
            likelihood=likelihood_names[pred_class],
            confidence=float(pred_proba[pred_class]),
            probabilities={
                'Low': float(pred_proba[0]),
                'Medium': float(pred_proba[1]),
                'High': float(pred_proba[2])
            },
            location={
                'latitude': data.latitude,
                'longitude': data.longitude
            },
            weather_summary={
                'temperature_max': data.temperature_max,
                'temperature_min': data.temperature_min,
                'temperature_mean': (data.temperature_max + data.temperature_min) / 2,
                'precipitation': data.precipitation,
                'wind_speed': data.wind_speed
            }
        )
        
        # Add notification info if created
        if notification_id:
            response.weather_summary['notification_id'] = notification_id
        if prediction_id:
            response.weather_summary['prediction_id'] = prediction_id
        
        return response
        
    except Exception as e:
        import traceback
        error_msg = f"Prediction error: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )


@app.post("/predict/batch")
async def predict_batch(data_list: list[WeatherData]):
    """
    Predict occurrence likelihood for multiple locations
    """
    
    if model is None or scaler is None or feature_cols is None:
        raise HTTPException(
            status_code=500,
            detail="Model not loaded. Please ensure model files exist."
        )
    
    try:
        results = []
        
        for data in data_list:
            # Prepare and scale features
            features = prepare_features(data)
            features_scaled = scaler.transform(features)
            
            # Make prediction
            pred_class = model.predict(features_scaled)[0]
            pred_proba = model.predict_proba(features_scaled)[0]
            
            likelihood_names = ['Low', 'Medium', 'High']
            
            results.append({
                'location': {
                    'latitude': data.latitude,
                    'longitude': data.longitude
                },
                'likelihood': likelihood_names[pred_class],
                'confidence': float(pred_proba[pred_class]),
                'probabilities': {
                    'Low': float(pred_proba[0]),
                    'Medium': float(pred_proba[1]),
                    'High': float(pred_proba[2])
                }
            })
        
        return {
            'count': len(results),
            'predictions': results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch prediction error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
