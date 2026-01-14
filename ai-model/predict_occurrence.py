import pandas as pd
import numpy as np
import joblib
from datetime import datetime

# Load trained model and scaler
print("Loading model...")
model = joblib.load('occurrence_model.pkl')
scaler = joblib.load('scaler.pkl')
feature_cols = joblib.load('feature_columns.pkl')

def predict_occurrence(lat, lon, temp_max, temp_min, precip, 
                      wind, sunshine, rain_hours=0):
    """
    Predict occurrence likelihood for a location
    
    Parameters:
    - lat, lon: coordinates
    - temp_max, temp_min: temperature in Celsius
    - precip: precipitation in mm
    - wind: wind speed in km/h
    - sunshine: sunshine duration in seconds
    - rain_hours: hours of rain (0-24)
    
    Returns:
    - likelihood: 'Low', 'Medium', or 'High'
    - probabilities: dict with probabilities for each class
    """
    
    # Calculate derived features
    temp_mean = (temp_max + temp_min) / 2
    temp_range = temp_max - temp_min
    is_tropical = 1 if 20 < temp_mean < 30 else 0
    lat_abs = abs(lat)
    is_equatorial = 1 if lat_abs < 10 else 0
    is_humid = 1 if precip > 10 else 0
    rain_hours_ratio = rain_hours / 24
    temp_precip_interaction = temp_mean * precip
    
    # Create feature array matching training data
    features = pd.DataFrame({
        'decimalLatitude': [lat],
        'decimalLongitude': [lon],
        'lat_abs': [lat_abs],
        'is_equatorial': [is_equatorial],
        'temperature_max_C': [temp_max],
        'temperature_min_C': [temp_min],
        'temperature_mean_C': [temp_mean],
        'temp_range': [temp_range],
        'is_tropical': [is_tropical],
        'precipitation_mm': [precip],
        'rain_mm': [precip],
        'precipitation_hours': [rain_hours],
        'is_humid': [is_humid],
        'rain_hours_ratio': [rain_hours_ratio],
        'windspeed_max_kmh': [wind],
        'windgusts_max_kmh': [wind * 1.5],  # Approximation
        'sunshine_duration_s': [sunshine],
        'temp_precip_interaction': [temp_precip_interaction]
    })
    
    # Scale features
    features_scaled = scaler.transform(features)
    
    # Predict
    pred_class = model.predict(features_scaled)[0]
    pred_proba = model.predict_proba(features_scaled)[0]
    
    likelihood_names = ['Low', 'Medium', 'High']
    
    return {
        'likelihood': likelihood_names[pred_class],
        'probabilities': {
            'Low': pred_proba[0],
            'Medium': pred_proba[1],
            'High': pred_proba[2]
        },
        'confidence': pred_proba[pred_class]
    }

# Example usage
if __name__ == "__main__":
    print("\n" + "="*50)
    print("OCCURRENCE LIKELIHOOD PREDICTOR")
    print("="*50)
    
    # Test cases
    test_locations = [
        {
            'name': 'Manila, Philippines (High likelihood area)',
            'lat': 14.6, 'lon': 121.0,
            'temp_max': 32, 'temp_min': 24,
            'precip': 15, 'wind': 12, 'sunshine': 36000, 'rain_hours': 8
        },
        {
            'name': 'Singapore (Medium likelihood)',
            'lat': 1.3, 'lon': 103.8,
            'temp_max': 31, 'temp_min': 25,
            'precip': 8, 'wind': 10, 'sunshine': 28000, 'rain_hours': 4
        },
        {
            'name': 'Cold region (Low likelihood)',
            'lat': 45.0, 'lon': 90.0,
            'temp_max': 15, 'temp_min': 5,
            'precip': 2, 'wind': 20, 'sunshine': 25000, 'rain_hours': 1
        }
    ]
    
    for loc in test_locations:
        result = predict_occurrence(
            loc['lat'], loc['lon'], loc['temp_max'], loc['temp_min'],
            loc['precip'], loc['wind'], loc['sunshine'], loc['rain_hours']
        )
        
        print(f"\n{loc['name']}")
        print(f"  Coordinates: ({loc['lat']}, {loc['lon']})")
        print(f"  Predicted Likelihood: {result['likelihood']}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Probabilities:")
        for level, prob in result['probabilities'].items():
            print(f"    {level}: {prob:.2%}")
